"""
Test LangChain SQL Database and Agent
This verifies that LangChain can connect and query your database
"""

import os
import sys
from urllib.parse import quote_plus
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import create_sql_agent, SQLDatabaseToolkit
from langchain.agents.agent_types import AgentType
from langchain.agents import create_react_agent, AgentExecutor
from langchain import hub

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

print("\n" + "="*70)
print("  Testing LangChain SQL Database Integration")
print("="*70 + "\n")

# Get config
host = os.getenv('MYSQL_HOST')
port = os.getenv('MYSQL_PORT', '3306')
user = os.getenv('MYSQL_USER')
password = os.getenv('MYSQL_PASSWORD')
database = os.getenv('MYSQL_DATABASE')
api_key = os.getenv('OPENAI_API_KEY')

# Get schemas
schemas_str = os.getenv('MYSQL_SCHEMAS', '')
schemas = [s.strip() for s in schemas_str.split(',') if s.strip()]

print(f"Database: {host}:{port}/{database}")
print(f"User: {user}")
print(f"Schemas: {', '.join(schemas) if schemas else 'All accessible'}")
print(f"OpenAI Key: {'Set' if api_key else 'NOT SET'}")
print()

# Test 1: LangChain SQLDatabase connection
print("[TEST 1] Testing LangChain SQLDatabase connection...")
try:
    # URL encode username and password to handle special characters
    encoded_user = quote_plus(user)
    encoded_password = quote_plus(password)
    db_uri = f"mysql+mysqlconnector://{encoded_user}:{encoded_password}@{host}:{port}/{database}"
    langchain_db = SQLDatabase.from_uri(db_uri, sample_rows_in_table_info=2)
    print("[SUCCESS] LangChain SQLDatabase connected successfully")
    
    # Get table names
    tables = langchain_db.get_usable_table_names()
    print(f"[SUCCESS] Found {len(tables)} usable tables in default database")
    print(f"   First 10 tables: {tables[:10]}")
    print()
    
except Exception as e:
    print(f"[ERROR] LangChain SQLDatabase connection failed!")
    print(f"   Error: {e}")
    print()
    exit(1)

# Test 2: Run a simple SQL query through LangChain
print("[TEST 2] Testing direct SQL query through LangChain...")
try:
    result = langchain_db.run("SELECT DATABASE() as current_db")
    print(f"[SUCCESS] Query executed successfully")
    print(f"   Current database: {result}")
    print()
    
except Exception as e:
    print(f"[ERROR] Query execution failed!")
    print(f"   Error: {e}")
    print()
    exit(1)

# Test 2b: Query multiple schemas if configured
if schemas:
    print("[TEST 2b] Testing multi-schema query...")
    try:
        query = "SELECT table_schema, COUNT(*) as table_count FROM information_schema.tables WHERE table_schema IN ("
        query += ",".join([f"'{schema}'" for schema in schemas])
        query += ") GROUP BY table_schema"
        
        result = langchain_db.run(query)
        print(f"[SUCCESS] Multi-schema query executed successfully")
        print(f"   Result:\n{result}")
        print()
        
    except Exception as e:
        print(f"[ERROR] Multi-schema query failed!")
        print(f"   Error: {e}")
        print()

# Test 3: Get table info
print("[TEST 3] Testing table info retrieval...")
try:
    if tables:
        # Get info for first table
        table_name = tables[0]
        table_info = langchain_db.get_table_info([table_name])
        print(f"[SUCCESS] Retrieved table info for: {table_name}")
        print(f"   Sample:\n{table_info[:500]}...")
        print()
except Exception as e:
    print(f"[ERROR] Table info retrieval failed!")
    print(f"   Error: {e}")
    print()

# Test 4: Create SQL Agent
print("[TEST 4] Testing LangChain SQL Agent creation...")
try:
    if not api_key:
        print("[WARNING] Skipping - OpenAI API key not set")
        print()
    else:
        llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0,
            api_key=api_key
        )
        
        # Create toolkit first (required for newer LangChain versions)
        toolkit = SQLDatabaseToolkit(db=langchain_db, llm=llm)
        
        sql_agent = create_sql_agent(
            llm=llm,
            toolkit=toolkit,
            agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=False,
            handle_parsing_errors=True,
            max_iterations=5
        )
        
        print("[SUCCESS] SQL Agent created successfully")
        print()
        
        # Test 5: Run a simple query through the agent
        print("[TEST 5] Testing Agent with simple question...")
        try:
            question = "How many tables are in this database?"
            if schemas:
                question = f"How many tables are in each of these schemas: {', '.join(schemas[:3])}?"
            
            response = sql_agent.invoke({"input": question})
            
            output = response.get('output', 'No output')
            print(f"[SUCCESS] Agent responded successfully")
            print(f"   Question: {question}")
            print(f"   Answer: {output}")
            print()
            
        except Exception as e:
            print(f"[ERROR] Agent query failed!")
            print(f"   Error: {e}")
            print()
            
except Exception as e:
    print(f"[ERROR] SQL Agent creation failed!")
    print(f"   Error: {e}")
    import traceback
    traceback.print_exc()
    print()

print("="*70)
print("  LangChain Setup Test Complete")
print("="*70 + "\n")

