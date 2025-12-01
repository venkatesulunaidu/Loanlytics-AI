"""
Loanlytics AI - Backend API
Flask API with LangChain for Natural Language to SQL queries
"""

import sys
import re
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent, SQLDatabaseToolkit
from langchain.agents.agent_types import AgentType
import mysql.connector
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime
import tempfile

# Import AI Knowledge Base
from ai_knowledge_loader import get_knowledge_base

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Database configuration
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', '3306')),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE')
}

# Multiple schemas to query (comma-separated list)
MYSQL_SCHEMAS = [s.strip() for s in os.getenv('MYSQL_SCHEMAS', '').split(',') if s.strip()]
if not MYSQL_SCHEMAS and DB_CONFIG.get('database'):
    MYSQL_SCHEMAS = [DB_CONFIG['database']]  # Use default database if no schemas specified

# If still no schemas, use common defaults based on available databases
if not MYSQL_SCHEMAS:
    # Try to discover available schemas and use common ones
    try:
        temp_conn = mysql.connector.connect(
            host=DB_CONFIG.get('host', ''),
            port=int(DB_CONFIG.get('port', 3306)),
            user=DB_CONFIG.get('user', ''),
            password=DB_CONFIG.get('password', '')
        )
        cursor = temp_conn.cursor()
        cursor.execute("SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys') ORDER BY SCHEMA_NAME")
        available_schemas = [row[0] for row in cursor.fetchall()]
        temp_conn.close()
        
        # Prefer encoredb and financialForms if they exist
        preferred = ['encoredb', 'financialForms']
        MYSQL_SCHEMAS = []
        for pref in preferred:
            if pref in available_schemas:
                MYSQL_SCHEMAS.append(pref)
        # Add other schemas if preferred ones not found
        if not MYSQL_SCHEMAS and available_schemas:
            MYSQL_SCHEMAS = available_schemas[:3]  # Take first 3 non-system schemas
        
        if MYSQL_SCHEMAS:
            print(f"[CONFIG] Auto-discovered schemas: {', '.join(MYSQL_SCHEMAS)}")
    except Exception as e:
        print(f"[CONFIG] Could not auto-discover schemas: {e}")
        # Fallback to common defaults
        MYSQL_SCHEMAS = ['encoredb', 'financialForms']
        print(f"[CONFIG] Using default schemas: {', '.join(MYSQL_SCHEMAS)}")

# OpenAI configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview')

# Lazy initialization of database connection and agent
langchain_db = None
sql_agent = None

def initialize_agent():
    """Initialize LangChain SQL Agent with multiple schema support (lazy loading)"""
    global langchain_db, sql_agent
    
    if sql_agent is not None:
        return sql_agent
    
    try:
        # Validate configuration - ensure all required values are not None
        host = DB_CONFIG.get('host') or ''
        user = DB_CONFIG.get('user') or ''
        password = DB_CONFIG.get('password') or ''
        
        if not all([host, user, password]):
            raise ValueError("Missing database configuration. Please check your .env file.")
        
        # Ensure all values are strings (not None)
        host = str(host).strip()
        user = str(user).strip()
        password = str(password).strip()
        
        # URL encode username and password to handle special characters
        encoded_user = quote_plus(user)
        encoded_password = quote_plus(password)
        
        # Create connection URI - connect to server or default database
        # Ensure port is converted to string for the URI
        port = str(DB_CONFIG.get('port', 3306))
        db_uri = f"mysql+mysqlconnector://{encoded_user}:{encoded_password}@{host}:{port}"
        
        # Determine which database to connect to
        # Priority: 1) MYSQL_DATABASE from .env, 2) First schema from MYSQL_SCHEMAS, 3) Discover and use first available
        database_name = DB_CONFIG.get('database') or ''
        if database_name:
            database_name = str(database_name).strip()
        
        # If no database specified, try to use first schema from MYSQL_SCHEMAS
        if not database_name and MYSQL_SCHEMAS:
            database_name = str(MYSQL_SCHEMAS[0]).strip()
            print(f"[INIT] No MYSQL_DATABASE set, using first schema from MYSQL_SCHEMAS: {database_name}")
        
        # If still no database, discover and use first available non-system schema
        if not database_name:
            try:
                temp_conn = mysql.connector.connect(
                    host=host,
                    port=int(port),
                    user=user,
                    password=password
                )
                temp_cursor = temp_conn.cursor()
                temp_cursor.execute("""
                    SELECT SCHEMA_NAME 
                    FROM information_schema.SCHEMATA 
                    WHERE SCHEMA_NAME NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys', '#innodb_redo', '#innodb_temp')
                    ORDER BY SCHEMA_NAME
                    LIMIT 1
                """)
                result = temp_cursor.fetchone()
                if result and result[0]:
                    database_name = result[0]
                    print(f"[INIT] Auto-discovered and using database: {database_name}")
                temp_conn.close()
            except Exception as discover_error:
                print(f"[INIT] Could not discover database: {discover_error}")
        
        # Last resort: use information_schema (always exists but limited)
        if not database_name:
            database_name = 'information_schema'
            print(f"[INIT] Using 'information_schema' as fallback connection database")
            print(f"[INIT] Note: You can query other schemas using schema.table syntax")
        
        # Add database to URI
        if database_name:
            db_uri += f"/{database_name}"
        
        print(f"[INIT] Connecting to: {host}:{port}")
        print(f"[INIT] User: {user}")
        print(f"[INIT] Connection Database: {database_name}")
        print(f"[INIT] Schemas to query: {', '.join(MYSQL_SCHEMAS) if MYSQL_SCHEMAS else 'All accessible'}")
        
        # Create LangChain SQL Database connection
        # Note: We connect to a database but can query other schemas using schema.table syntax
        try:
            langchain_db = SQLDatabase.from_uri(db_uri, sample_rows_in_table_info=2)
        except Exception as db_init_error:
            error_msg = str(db_init_error)
            print(f"[INIT ERROR] Database connection failed: {error_msg}")
            if 'replace' in error_msg.lower() or 'NoneType' in error_msg:
                raise ValueError(
                    f"Database connection failed due to configuration issue. "
                    f"Error: {error_msg}\n"
                    f"Please check your .env file and ensure MYSQL_DATABASE or MYSQL_SCHEMAS is set correctly."
                ) from db_init_error
            raise
        
        # Create SQL Agent with LangChain
        llm = ChatOpenAI(
            model=OPENAI_MODEL,
            temperature=0,
            api_key=OPENAI_API_KEY
        )
        
        # Add schema context to agent instructions
        schema_info = ""
        if MYSQL_SCHEMAS and len(MYSQL_SCHEMAS) > 1:
            # Filter out None values and ensure all are strings
            valid_schemas = [str(s).strip() for s in MYSQL_SCHEMAS if s and str(s).strip()]
            if valid_schemas:
                schema_info = f"""
IMPORTANT - MULTIPLE SCHEMAS AVAILABLE:
This MySQL database has {len(valid_schemas)} schemas: {', '.join(valid_schemas)}

To query tables from different schemas, you MUST use the syntax: schema_name.table_name
Examples:
  - SELECT * FROM encoredb.loan_od_accounts LIMIT 10
  - SELECT * FROM financialForms.loan_accounts LIMIT 10
  - SELECT COUNT(*) FROM bi.loan_information

To find tables across schemas, query information_schema:
  SELECT table_schema, table_name 
  FROM information_schema.tables 
  WHERE table_schema IN ({', '.join([f"'{s}'" for s in valid_schemas])})
  AND table_name LIKE '%your_search%'

When answering questions about loans or any domain, ALWAYS search for relevant tables across ALL schemas first.
"""
        
        # Create toolkit (required for newer LangChain versions)
        toolkit = SQLDatabaseToolkit(db=langchain_db, llm=llm)
        
        # Build schema context for agent
        schema_context = ""
        if MYSQL_SCHEMAS:
            schema_list = ', '.join(MYSQL_SCHEMAS)
            schema_context = f"""
AVAILABLE SCHEMAS: {schema_list}
When querying tables, use schema.table_name format (e.g., encoredb.loan_od_working_registers, financialForms.customer)
"""
        else:
            schema_context = """
SCHEMAS: Multiple schemas available. Use schema.table_name format when querying.
Common schemas: encoredb, financialForms
"""
        
        # Use OPENAI_FUNCTIONS agent - more reliable, no parsing errors
        sql_agent = create_sql_agent(
            llm=llm,
            toolkit=toolkit,
            agent_type=AgentType.OPENAI_FUNCTIONS,
            verbose=True,
            max_iterations=8,
            agent_executor_kwargs={"return_intermediate_steps": True},
            prefix=f"""SQL agent trained on 274 production reports. Execute, return data only.
{schema_context}
KEY TABLES (by usage in production):
- customer (financialForms/encoredb): 255 reports - URN, customer_id
- branch_master (financialForms): 215 reports - branch hierarchy
- loan_accounts (financialForms): 177 reports - account_number links
- loan_od_working_registers (encoredb): 29 reports - current balances
- loan_od_disbursements (encoredb): DISBURSEMENT data only (NOT repayments)
- loan_od_repayments (encoredb): REPAYMENT data (collections, repayments)

CRITICAL: TABLE DISTINCTIONS:
- loan_od_disbursements = DISBURSEMENTS only (money given out)
- loan_od_repayments = REPAYMENTS/COLLECTIONS (money received back)
- NEVER use loan_od_disbursements for repayment/collection queries!

CRITICAL JOINS (from production):
1. Customer→Loan: customers.customer_id = account_holders.customer_id, 
   account_holders.account_id = loan_od_working_registers.account_id
2. Product→Disbursement: loan_od_disbursements JOIN account_profiles 
   ON (tenant_code AND account_id), then product_code
3. Repayment→Account: loan_od_repayments JOIN loan_od_working_registers 
   ON (tenant_code AND account_id) OR loan_od_repayments JOIN account_holders 
   ON account_id, then to loan_od_working_registers
4. Branch→Hub: branch_master.hub_id = hub_master.id

PATTERNS (learned from 1315 SUM operations):
- Amounts: SUM(amount_magnitude), SUM(principal_magnitude), SUM(total_disbursed_magnitude)
- Repayment amounts: SUM(principal_magnitude) FROM loan_od_repayments
- Composite keys: tenant_code + account_id
- Active records: is_closed=0, status='ACTIVE'
- Product grouping: GROUP BY product_code
- Branch grouping: GROUP BY branch_id

RULES:
1. Execute immediately, return data
2. "wise"/"by" → GROUP BY
3. Use composite keys (tenant_code, account_id)
4. CRITICAL: ALWAYS use schema.table_name format (e.g., encoredb.loan_od_working_registers, financialForms.loan_accounts)
5. Common tables:
   - encoredb.loan_od_working_registers (loan balances)
   - encoredb.loan_od_disbursements (DISBURSEMENTS - money given out)
   - encoredb.loan_od_repayments (REPAYMENTS/COLLECTIONS - money received)
   - financialForms.loan_accounts (loan accounts)
   - financialForms.customer (customers)
6. NEVER use table names without schema prefix - queries will fail!
7. For repayment/collection queries: ALWAYS use loan_od_repayments, NEVER loan_od_disbursements!
"""
        )
        
        print("[INIT] LangChain SQL Agent initialized successfully")
        return sql_agent
        
    except Exception as e:
        print(f"[INIT ERROR] Failed to initialize SQL Agent: {e}")
        print("[INIT] Check your .env file has correct database credentials")
        raise


def get_db_connection():
    """Create database connection"""
    return mysql.connector.connect(**DB_CONFIG)


def get_database_schema():
    """Get database schema for all configured schemas (optimized for large databases)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        all_tables = []
        schema_info = ""
        
        # Use MYSQL_SCHEMAS if available, otherwise discover schemas
        schemas_to_query = MYSQL_SCHEMAS if MYSQL_SCHEMAS else []
        
        if not schemas_to_query:
            # Discover available schemas (excluding system schemas)
            cursor.execute("""
                SELECT DISTINCT table_schema 
                FROM information_schema.tables 
                WHERE table_schema NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys', '#innodb_redo', '#innodb_temp')
                ORDER BY table_schema
            """)
            schemas_to_query = [row[0] for row in cursor.fetchall()]
            if not schemas_to_query:
                # Fallback: use current database
                cursor.execute("SELECT DATABASE()")
                db_result = cursor.fetchone()
                if db_result and db_result[0]:
                    schemas_to_query = [db_result[0]]
        
        # Query each schema
        if schemas_to_query:
            for schema_name in schemas_to_query:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '{schema_name}'")
                    table_count = cursor.fetchone()[0]
                    
                    cursor.execute(f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{schema_name}' ORDER BY table_name")
                    tables = [f"{schema_name}.{row[0]}" for row in cursor.fetchall()]
                    all_tables.extend(tables)
                    
                    schema_info += f"Schema: {schema_name} ({table_count} tables)\n"
                    if table_count <= 20:
                        schema_info += f"Tables: {', '.join([t.split('.')[1] for t in tables])}\n\n"
                    else:
                        schema_info += f"Tables (first 20): {', '.join([t.split('.')[1] for t in tables[:20]])}\n\n"
                except Exception as schema_error:
                    print(f"[WARNING] Could not query schema {schema_name}: {schema_error}")
                    continue
        else:
            # Last resort: use current database
            cursor.execute("SELECT DATABASE()")
            db_result = cursor.fetchone()
            db_name = db_result[0] if db_result and db_result[0] else 'unknown'
            
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]
            all_tables = tables
            
            schema_info = f"Database: {db_name}\n"
            schema_info += f"Total tables: {len(tables)}\n\n"
            if len(tables) <= 50:
                schema_info += "Tables: " + ", ".join(tables)
            else:
                schema_info += "Tables (first 50): " + ", ".join(tables[:50])
                schema_info += "\n\nNote: Large database. Query specific tables by name."
        
        conn.close()
        return schema_info, all_tables
    
    except Exception as e:
        print(f"[ERROR] get_database_schema failed: {e}")
        import traceback
        traceback.print_exc()
        return str(e), []


def quick_pattern_match(question):
    """Fast template-based query generation for common patterns (learned from 274 production reports)"""
    q = question.lower()
    
    # Product-wise disbursement (21 production examples)
    if 'product' in q and 'disburs' in q:
        return """
SELECT 
    ap.product_code,
    SUM(lod.amount_magnitude) AS total_disbursement_amount
FROM encoredb.loan_od_disbursements lod
INNER JOIN encoredb.account_profiles ap 
    ON lod.tenant_code = ap.tenant_code AND lod.account_id = ap.account_id
GROUP BY ap.product_code
ORDER BY total_disbursement_amount DESC
LIMIT 100
"""
    
    # Top customers by loan amount (162 customer reports learned)
    if ('top' in q or 'customer' in q) and ('loan' in q and 'amount' in q):
        limit = 10
        if 'top' in q:
            import re
            match = re.search(r'top\s+(\d+)', q)
            if match:
                limit = int(match.group(1))
        
        return f"""
SELECT 
    c.id,
    c.customer_id,
    c.first_name,
    c.last_name,
    SUM(lw.total_disbursed_magnitude) as total_loan_amount
FROM encoredb.customers c
INNER JOIN encoredb.account_holders ah ON c.customer_id = ah.customer_id
INNER JOIN encoredb.loan_od_working_registers lw ON ah.account_id = lw.account_id
GROUP BY c.id, c.customer_id, c.first_name, c.last_name
ORDER BY total_loan_amount DESC
LIMIT {limit}
"""
    
    # Product-wise loan count
    if 'product' in q and ('count' in q or 'number' in q) and 'loan' in q:
        return """
SELECT 
    ap.product_code,
    COUNT(DISTINCT lw.account_id) AS loan_count
FROM encoredb.loan_od_working_registers lw
INNER JOIN encoredb.account_profiles ap 
    ON lw.tenant_code = ap.tenant_code AND lw.account_id = ap.account_id
GROUP BY ap.product_code
ORDER BY loan_count DESC
LIMIT 100
"""
    
    # Loan accounts query (first N, show, list)
    if ('loan' in q and 'account' in q) and ('first' in q or 'show' in q or 'list' in q or 'top' in q):
        limit = 10
        if 'first' in q:
            import re
            match = re.search(r'first\s+(\d+)', q)
            if match:
                limit = int(match.group(1))
        elif 'top' in q:
            import re
            match = re.search(r'top\s+(\d+)', q)
            if match:
                limit = int(match.group(1))
        
        return f"""
SELECT 
    la.id,
    la.account_number,
    la.customer_id,
    la.loan_amount,
    la.loan_disbursement_date,
    la.is_closed
FROM financialForms.loan_accounts la
WHERE la.loan_disbursement_date IS NOT NULL
ORDER BY la.id DESC
LIMIT {limit}
"""
    
    # Outstanding/Portfolio (6 production examples)
    if ('outstanding' in q or 'portfolio' in q) and ('total' in q or 'sum' in q):
        return """
SELECT 
    SUM(total_disbursed_magnitude) AS total_outstanding,
    COUNT(DISTINCT account_id) AS total_accounts
FROM encoredb.loan_od_working_registers
WHERE is_closed = 0
"""
    
    # Branch-wise collection (35 production examples)
    if 'branch' in q and ('collection' in q or 'repayment' in q):
        return """
SELECT 
    b.branch_name,
    b.branch_code,
    SUM(lor.principal_magnitude) AS total_collection
FROM encoredb.loan_od_repayments lor
INNER JOIN encoredb.loan_od_working_registers lowr 
    ON lor.tenant_code = lowr.tenant_code AND lor.account_id = lowr.account_id
INNER JOIN encoredb.account_holders ah ON lowr.account_id = ah.account_id
INNER JOIN financialForms.loan_accounts la ON ah.customer_id = la.customer_id
INNER JOIN financialForms.branch_master b ON la.branch_id = b.id
GROUP BY b.branch_name, b.branch_code
ORDER BY total_collection DESC
LIMIT 100
"""
    
    # Repayment queries - use loan_od_repayments
    if ('repayment' in q or 'collection' in q) and 'disbursement' not in q:
        return """
SELECT 
    lor.tenant_code,
    lor.account_id,
    SUM(lor.principal_magnitude) AS total_repayment,
    SUM(lor.interest_magnitude) AS total_interest
FROM encoredb.loan_od_repayments lor
GROUP BY lor.tenant_code, lor.account_id
ORDER BY total_repayment DESC
LIMIT 100
"""
    
    return None  # No pattern matched, use LLM


def generate_sql_with_agent(question):
    """Use LangChain SQL Agent to generate SQL query"""
    try:
        print(f"\n[DEBUG] Processing question: {question}")
        print(f"[DEBUG] Available schemas: {', '.join(MYSQL_SCHEMAS) if MYSQL_SCHEMAS else 'default'}")
        
        # Try fast pattern matching first
        quick_sql = quick_pattern_match(question)
        if quick_sql:
            print("[DEBUG] Using quick pattern match")
            # Execute the template query
            try:
                results = execute_query(quick_sql)
                return {
                    "output": "Query executed successfully",
                    "intermediate_steps": [(type('obj', (), {'tool': 'sql_db_query', 'tool_input': quick_sql})(), results)]
                }
            except Exception as e:
                print(f"[DEBUG] Quick pattern failed: {e}, falling back to LLM")
        
        # Initialize agent
        agent = initialize_agent()
        
        # Use AI Knowledge Base to enhance question with production patterns
        try:
            kb = get_knowledge_base()
            enhanced_question = kb.enhance_question(question) if question else question
            print(f"[DEBUG] Enhanced question with knowledge base")
        except Exception as kb_error:
            print(f"[DEBUG] Knowledge base enhancement failed: {kb_error}, using original question")
            enhanced_question = question
        
        # Use the agent to generate and run the query
        result = agent.invoke({"input": enhanced_question})
        
        print(f"[DEBUG] Agent result type: {type(result)}")
        print(f"[DEBUG] Agent output: {result.get('output', 'No output')[:200]}")
        
        return result
    
    except Exception as e:
        print(f"[ERROR] Agent failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


def validate_sql_query(sql):
    """
    Validate SQL query - only allow SELECT statements
    Returns: (is_valid, error_message)
    """
    if not sql or not sql.strip():
        return False, "Query cannot be empty"
    
    sql_upper = sql.strip().upper()
    
    # Block dangerous operations (data modification and schema changes)
    dangerous_keywords = [
        'INSERT', 'UPDATE', 'DELETE', 'DROP', 'TRUNCATE', 
        'ALTER', 'CREATE', 'GRANT', 'REVOKE', 'EXEC', 'EXECUTE',
        'CALL', 'MERGE', 'REPLACE', 'LOAD', 'COPY', 'LOCK',
        'UNLOCK'
    ]
    
    # Note: DESC, DESCRIBE, EXPLAIN, SHOW are read-only and safe, so not blocked
    
    # Check for dangerous keywords (not in comments)
    for keyword in dangerous_keywords:
        # Simple check - keyword not part of a word and not in comments
        pattern = r'\b' + keyword + r'\b'
        if re.search(pattern, sql_upper):
            return False, f"Operation '{keyword}' is not allowed. Only SELECT queries are permitted."
    
    # Must start with SELECT
    if not sql_upper.startswith('SELECT'):
        return False, "Only SELECT queries are allowed. Query must start with SELECT."
    
    # Block semicolon injection attempts (multiple statements)
    if sql_upper.count(';') > 1 or (sql_upper.count(';') == 1 and not sql_upper.rstrip().endswith(';')):
        return False, "Multiple statements are not allowed. Only single SELECT queries are permitted."
    
    # Additional safety: Check for UNION with dangerous operations
    if 'UNION' in sql_upper:
        # Allow UNION SELECT but validate it's safe
        union_parts = sql_upper.split('UNION')
        for part in union_parts:
            part_stripped = part.strip()
            if part_stripped and not part_stripped.startswith('SELECT'):
                return False, "UNION queries must only contain SELECT statements."
    
    return True, None


def fix_sql_schema_prefixes(sql):
    """Add schema prefixes to table names if missing"""
    # Common tables that need schema prefixes
    table_schema_map = {
        'loan_od_working_registers': 'encoredb',
        'loan_od_disbursements': 'encoredb',
        'account_profiles': 'encoredb',
        'account_holders': 'encoredb',
        'customers': 'encoredb',
        'loan_accounts': 'financialForms',
        'customer': 'financialForms',
        'branch_master': 'financialForms',
        'loan_repayment_details': 'financialForms'
    }
    
    sql_upper = sql.upper()
    fixed_sql = sql
    
    # Check if query already has schema prefixes for our known schemas
    has_schema_prefix = any(
        f'FROM {schema}.' in sql_upper or f'JOIN {schema}.' in sql_upper 
        for schema in ['ENCOREDB', 'FINANCIALFORMS']
    )
    
    # Only fix if schema prefixes are missing
    if not has_schema_prefix:
        for table, schema in table_schema_map.items():
            # Pattern: FROM table_name or JOIN table_name (but not schema.table_name)
            # Match: FROM table_name, JOIN table_name, UPDATE table_name
            # Don't match if already has schema prefix
            pattern = r'\b(FROM|JOIN|UPDATE)\s+(?!' + schema + r'\.)' + table + r'\b'
            replacement = r'\1 ' + schema + '.' + table
            fixed_sql = re.sub(pattern, replacement, fixed_sql, flags=re.IGNORECASE)
    
    return fixed_sql


def execute_query(sql):
    """Execute SQL query and return results"""
    try:
        # Fix schema prefixes if missing
        sql = fix_sql_schema_prefixes(sql)
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql)
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    except Exception as e:
        raise Exception(f"Query execution failed: {str(e)}")


# API Routes

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "Backend is running"})


@app.route('/api/diagnose', methods=['GET'])
def diagnose():
    """Diagnostic endpoint to check agent and database status"""
    try:
        diagnosis = {
            "backend": "running",
            "database_config": {
                "host": DB_CONFIG.get('host', 'Not set'),
                "port": DB_CONFIG.get('port', 'Not set'),
                "user": DB_CONFIG.get('user', 'Not set'),
                "database": DB_CONFIG.get('database', 'Not set'),
                "schemas": MYSQL_SCHEMAS if MYSQL_SCHEMAS else "Not set (will auto-discover)"
            },
            "agent_status": "not_initialized" if sql_agent is None else "initialized",
            "tables": []
        }
        
        # Try to get tables
        try:
            _, tables = get_database_schema()
            diagnosis["tables"] = {
                "count": len(tables),
                "first_10": tables[:10] if tables else []
            }
        except Exception as e:
            diagnosis["tables"] = {"error": str(e)}
        
        # Try to initialize agent if not already done
        if sql_agent is None:
            try:
                agent = initialize_agent()
                diagnosis["agent_status"] = "initialized_successfully"
            except Exception as e:
                diagnosis["agent_status"] = f"initialization_failed: {str(e)}"
        
        return jsonify(diagnosis)
    except Exception as e:
        return jsonify({
            "error": str(e),
            "backend": "running"
        }), 500


@app.route('/api/tables', methods=['GET'])
def get_tables():
    """Get list of all database tables"""
    try:
        _, tables = get_database_schema()
        return jsonify({
            "success": True,
            "tables": tables,
            "count": len(tables)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/table/<table_name>', methods=['GET'])
def get_table_info(table_name):
    """Get columns for a specific table"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"SHOW COLUMNS FROM {table_name}")
        columns = [{"name": row[0], "type": row[1]} for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            "success": True,
            "table": table_name,
            "columns": columns
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400


@app.route('/api/autocomplete', methods=['GET'])
def get_autocomplete_data():
    """Get all tables and columns for autocomplete suggestions"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        autocomplete_data = {
            "tables": [],
            "columns": {},
            "schemas": MYSQL_SCHEMAS if MYSQL_SCHEMAS else []
        }
        
        # Get all tables with their schemas
        schemas_to_query = MYSQL_SCHEMAS if MYSQL_SCHEMAS else []
        
        if not schemas_to_query:
            # Discover schemas
            cursor.execute("""
                SELECT DISTINCT table_schema 
                FROM information_schema.tables 
                WHERE table_schema NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys', '#innodb_redo', '#innodb_temp')
                ORDER BY table_schema
                LIMIT 10
            """)
            schemas_to_query = [row[0] for row in cursor.fetchall()]
        
        # Get tables and columns for each schema
        for schema in schemas_to_query[:5]:  # Limit to 5 schemas for performance
            try:
                # Get tables
                cursor.execute(f"""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = '{schema}'
                    ORDER BY table_name
                    LIMIT 100
                """)
                tables = [row[0] for row in cursor.fetchall()]
                
                for table in tables:
                    full_table_name = f"{schema}.{table}"
                    autocomplete_data["tables"].append(full_table_name)
                    autocomplete_data["tables"].append(table)  # Also add without schema
                    
                    # Get columns for this table
                    try:
                        cursor.execute(f"""
                            SELECT column_name, data_type 
                            FROM information_schema.columns 
                            WHERE table_schema = '{schema}' AND table_name = '{table}'
                            ORDER BY ordinal_position
                        """)
                        columns = [{"name": row[0], "type": row[1]} for row in cursor.fetchall()]
                        autocomplete_data["columns"][full_table_name] = [col["name"] for col in columns]
                        autocomplete_data["columns"][table] = [col["name"] for col in columns]  # Also without schema
                    except Exception as col_error:
                        print(f"[WARNING] Could not get columns for {full_table_name}: {col_error}")
                        continue
            except Exception as schema_error:
                print(f"[WARNING] Could not query schema {schema}: {schema_error}")
                continue
        
        conn.close()
        
        return jsonify({
            "success": True,
            "data": autocomplete_data
        })
    except Exception as e:
        print(f"[ERROR] Autocomplete data fetch failed: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "data": {"tables": [], "columns": {}, "schemas": []}
        }), 500


@app.route('/api/query', methods=['POST'])
def process_query():
    """Main endpoint: Process natural language question using LangChain SQL Agent"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({
                "success": False,
                "error": "Question is required"
            }), 400
        
        print(f"\n{'='*70}")
        print(f"[API] Received question: {question}")
        print(f"{'='*70}")
        
        # Use LangChain SQL Agent
        result = generate_sql_with_agent(question)
        
        if isinstance(result, dict) and "error" in result:
            return jsonify({
                "success": False,
                "error": result["error"]
            }), 500
        
        # Extract information from agent result
        output = result.get('output', '')
        intermediate_steps = result.get('intermediate_steps', [])
        
        print(f"[API] Agent returned {len(intermediate_steps)} intermediate steps")
        
        # Extract SQL query from intermediate steps
        sql_query = None
        query_results = None
        all_queries = []
        
        for i, step in enumerate(intermediate_steps):
            print(f"[API] Step {i}: {type(step)}")
            if len(step) >= 2:
                action, observation = step[0], step[1]
                
                # Check if this step executed a query
                tool_name = None
                if hasattr(action, 'tool'):
                    tool_name = action.tool
                elif hasattr(action, 'tool_name'):
                    tool_name = action.tool_name
                elif isinstance(action, dict):
                    tool_name = action.get('tool') or action.get('tool_name')
                
                if tool_name:
                    print(f"[API] Tool used: {tool_name}")
                    
                    # Check for various SQL execution tool names
                    if tool_name in ['sql_db_query', 'sql_db_query_checker', 'query_sql_db', 'query_sql_database']:
                        # This is the actual SQL query execution
                        query = None
                        if hasattr(action, 'tool_input'):
                            query = action.tool_input
                        elif hasattr(action, 'tool_input_str'):
                            query = action.tool_input_str
                        elif isinstance(action, dict):
                            query = action.get('tool_input') or action.get('tool_input_str')
                        
                        if query:
                            all_queries.append(query)
                            # Use the last SELECT query - keep it simple
                            # Always prefer the last query executed (most relevant to user's question)
                            if 'SELECT' in str(query).upper():
                                sql_query = str(query)
                                query_results = observation
                            print(f"[API] Found SQL: {str(query)[:100]}...")
                            print(f"[API] Query results: {str(observation)[:200]}...")
                
                # Also check if observation contains SQL
                obs_str = str(observation)
                if 'SELECT' in obs_str.upper() and len(obs_str) > 20 and len(obs_str) < 2000:
                    # Might be SQL in the observation
                    import re
                    sql_match = re.search(r'SELECT.*?(?:;|$)', obs_str, re.IGNORECASE | re.DOTALL)
                    if sql_match:
                        potential_sql = sql_match.group(0).strip()
                        if potential_sql and 'SELECT' in potential_sql.upper():
                            print(f"[API] Found SQL in observation: {potential_sql[:100]}...")
                            if not sql_query:  # Only use if we haven't found one yet
                                sql_query = potential_sql
                                all_queries.append(potential_sql)
        
        print(f"[API] Total SQL queries found: {len(all_queries)}")
        print(f"[API] Final SQL query: {sql_query[:100] if sql_query else 'None'}")
        print(f"[API] Agent output: {output[:500] if output else 'No output'}")
        
        # If we found a SQL query, re-execute it to get structured data
        if sql_query:
            try:
                # Fix schema prefixes if missing (auto-add encoredb/financialForms)
                original_sql = sql_query
                sql_query = fix_sql_schema_prefixes(sql_query)
                if sql_query != original_sql:
                    print(f"[SQL FIX] Added schema prefixes: {original_sql[:50]}... -> {sql_query[:50]}...")
                
                results = execute_query(sql_query)
                return jsonify({
                    "success": True,
                    "sql": sql_query,
                    "results": results,
                    "count": len(results),
                    "agent_output": output
                })
            except Exception as query_error:
                print(f"[API] Query execution failed: {query_error}")
                # Return what we have
                return jsonify({
                    "success": True,
                    "sql": sql_query,
                    "results": [],
                    "count": 0,
                    "agent_output": output,
                    "note": f"Query generated but execution failed: {str(query_error)}"
                })
        elif output and len(output) > 10:
            # Agent provided an answer but we couldn't extract SQL
            # This means the agent failed to execute - return a clean error
            print(f"[API] No SQL query found but agent provided output")
            print(f"[API] Agent output: {output[:500]}")
            
            # Check if output contains error information
            error_hints = []
            if "error" in output.lower() or "failed" in output.lower():
                error_hints.append("The agent encountered an error while processing your question.")
            if "table" in output.lower() and "not found" in output.lower():
                error_hints.append("The requested table may not exist or may not be accessible.")
            if "syntax" in output.lower() or "invalid" in output.lower():
                error_hints.append("There may be a syntax issue with the generated query.")
            
            error_msg = "Could not generate query for this question."
            if error_hints:
                error_msg += " " + " ".join(error_hints)
            else:
                error_msg += " The database structure may not support this query."
            
            # Return a user-friendly error instead of verbose explanation
            return jsonify({
                "success": False,
                "error": error_msg,
                "sql": None,
                "results": [],
                "count": 0,
                "agent_output": output[:500] if len(output) > 500 else output,
                "suggestion": "Try rephrasing your question, ask to see available tables first, or use the custom SQL mode to write your own query."
            }), 400
        else:
            # No SQL found and no useful output
            print(f"[API] No SQL query found in agent steps")
            print(f"[API] Agent output: {output[:500] if output else 'No output'}")
            print(f"[API] Intermediate steps count: {len(intermediate_steps)}")
            print(f"[API] All intermediate steps:")
            for i, step in enumerate(intermediate_steps):
                step_str = str(step)[:200] if step else "None"
                print(f"  Step {i}: {step_str}")
            
            # Try to extract any error messages from steps
            error_details = []
            for i, step in enumerate(intermediate_steps):
                if len(step) >= 2:
                    observation = step[1]
                    obs_str = str(observation)
                    if "error" in obs_str.lower() or "failed" in obs_str.lower():
                        error_details.append(f"Step {i}: {obs_str[:200]}")
            
            error_msg = "Cannot answer this question with available data."
            if error_details:
                error_msg += f" Details: {'; '.join(error_details[:2])}"
            
            return jsonify({
                "success": False,
                "error": error_msg,
                "agent_output": output[:500] if output else "No output from agent",
                "debug": f"Agent returned {len(intermediate_steps)} steps but no SQL query was found",
                "suggestion": "Try asking: 'Show me all tables' or 'List tables in encoredb schema' to discover available data. You can also use the custom SQL mode."
            }), 400
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[API ERROR] {error_trace}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/execute', methods=['POST'])
def execute_custom_query():
    """Execute a custom SQL query (for advanced users) - SELECT only"""
    try:
        data = request.get_json()
        sql = data.get('sql', '').strip()
        
        if not sql:
            return jsonify({
                "success": False,
                "error": "SQL query is required"
            }), 400
        
        # Comprehensive security validation
        is_valid, error_message = validate_sql_query(sql)
        if not is_valid:
            return jsonify({
                "success": False,
                "error": error_message,
                "sql": sql,
                "results": [],
                "count": 0
            }), 403
        
        # Fix schema prefixes if missing (auto-add encoredb/financialForms)
        original_sql = sql
        sql = fix_sql_schema_prefixes(sql)
        if sql != original_sql:
            print(f"[SQL FIX] Added schema prefixes: {original_sql[:50]}... -> {sql[:50]}...")
        
        # Execute the validated query
        results = execute_query(sql)
        
        return jsonify({
            "success": True,
            "sql": sql,
            "results": results,
            "count": len(results)
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Query execution failed: {str(e)}",
            "sql": sql if 'sql' in locals() else None,
            "results": [],
            "count": 0
        }), 500


if __name__ == '__main__':
    print("\n" + "="*70)
    print("  Loanlytics AI Backend Starting...")
    print("="*70)
    
    # Check .env file
    if not os.path.exists('.env'):
        print("\n  [WARNING] .env file not found!")
        print("  Create .env file with your database credentials")
        print("\n" + "="*70 + "\n")
    else:
        print(f"\n  [Database] {DB_CONFIG.get('database', 'Not configured')}")
        if MYSQL_SCHEMAS:
            print(f"  [Schemas]  {len(MYSQL_SCHEMAS)} schemas: {', '.join(MYSQL_SCHEMAS[:3])}{'...' if len(MYSQL_SCHEMAS) > 3 else ''}")
        print(f"  [AI Model] {OPENAI_MODEL}")
        print(f"  [Server]   http://localhost:5000")
        print(f"  [Info]     Database connection will be established on first query")
        print(f"  [Info]     Multi-schema support enabled for cross-schema queries")
        print("\n" + "="*70 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)

