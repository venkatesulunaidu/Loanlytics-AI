"""
Schema Metadata Collector for Loanlytics AI
Collects comprehensive table information including indexes
"""

import mysql.connector
from dotenv import load_dotenv
import os
import json

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST'),
    'port': int(os.getenv('MYSQL_PORT', '3306')),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE')
}

# Only collect these schemas for training
SCHEMAS = ['encoredb', 'financialForms']

def collect_metadata():
    """Collect comprehensive metadata about all tables"""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    
    metadata = {}
    
    for schema in SCHEMAS:
        print(f"\n{'='*80}")
        print(f"Schema: {schema}")
        print(f"{'='*80}")
        
        # Get all tables
        cursor.execute(f"""
            SELECT table_name, table_comment, table_rows
            FROM information_schema.tables 
            WHERE table_schema = '{schema}' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table['table_name']
            full_name = f"{schema}.{table_name}"
            
            print(f"\nTable: {table_name}")
            print(f"  Rows: {table['table_rows']:,}")
            print(f"  Comment: {table['table_comment'] or 'None'}")
            
            # Get columns
            cursor.execute(f"""
                SELECT 
                    column_name,
                    column_type,
                    column_key,
                    column_comment,
                    is_nullable
                FROM information_schema.columns
                WHERE table_schema = '{schema}' AND table_name = '{table_name}'
                ORDER BY ordinal_position
            """)
            
            columns = cursor.fetchall()
            
            # Get indexes
            cursor.execute(f"""
                SELECT 
                    index_name,
                    GROUP_CONCAT(column_name ORDER BY seq_in_index) as columns,
                    non_unique,
                    index_type
                FROM information_schema.statistics
                WHERE table_schema = '{schema}' AND table_name = '{table_name}'
                GROUP BY index_name, non_unique, index_type
            """)
            
            indexes = cursor.fetchall()
            
            # Get foreign keys
            cursor.execute(f"""
                SELECT 
                    constraint_name,
                    column_name,
                    referenced_table_schema,
                    referenced_table_name,
                    referenced_column_name
                FROM information_schema.key_column_usage
                WHERE table_schema = '{schema}' 
                AND table_name = '{table_name}'
                AND referenced_table_name IS NOT NULL
            """)
            
            foreign_keys = cursor.fetchall()
            
            # Store metadata
            metadata[full_name] = {
                'schema': schema,
                'table': table_name,
                'comment': table['table_comment'] or '',
                'row_count': table['table_rows'],
                'columns': [
                    {
                        'name': col['column_name'],
                        'type': col['column_type'],
                        'nullable': col['is_nullable'] == 'YES',
                        'key': col['column_key'],
                        'comment': col['column_comment'] or ''
                    }
                    for col in columns
                ],
                'indexes': [
                    {
                        'name': idx['index_name'],
                        'columns': idx['columns'].split(','),
                        'unique': idx['non_unique'] == 0,
                        'type': idx['index_type']
                    }
                    for idx in indexes
                ],
                'foreign_keys': [
                    {
                        'column': fk['column_name'],
                        'references': f"{fk['referenced_table_schema']}.{fk['referenced_table_name']}.{fk['referenced_column_name']}"
                    }
                    for fk in foreign_keys
                ],
                # User fills these in:
                'description': '',  # What data does this table hold?
                'common_joins': [],  # How does it join with other tables?
                'business_meaning': ''  # What business entity does this represent?
            }
            
            print(f"  Columns: {len(columns)}")
            print(f"  Indexes: {', '.join([idx['index_name'] for idx in indexes])}")
            if foreign_keys:
                print(f"  Foreign Keys: {len(foreign_keys)}")
    
    conn.close()
    
    # Save to JSON file
    with open('schema_metadata.json', 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*80}")
    print(f"Metadata collected for {len(metadata)} tables")
    print(f"Saved to: schema_metadata.json")
    print(f"{'='*80}")
    
    # Create human-readable format for user to fill in
    create_training_template(metadata)
    
    return metadata


def create_training_template(metadata):
    """Create a template file for user to fill in relationships"""
    
    with open('SCHEMA_TRAINING.txt', 'w', encoding='utf-8') as f:
        f.write("="*100 + "\n")
        f.write("LOANLYTICS AI - SCHEMA TRAINING FILE\n")
        f.write("="*100 + "\n\n")
        f.write("Instructions: Fill in the descriptions, common_joins, and business_meaning for each table.\n")
        f.write("This will help the AI understand your database structure and generate accurate queries.\n\n")
        
        for table_name, info in sorted(metadata.items()):
            f.write("\n" + "="*100 + "\n")
            f.write(f"TABLE: {table_name}\n")
            f.write("="*100 + "\n")
            f.write(f"Row Count: {info['row_count']:,}\n")
            f.write(f"Current Comment: {info['comment']}\n\n")
            
            # Show key columns
            f.write("KEY COLUMNS:\n")
            for col in info['columns']:
                if col['key'] or 'id' in col['name'].lower() or 'code' in col['name'].lower():
                    f.write(f"  - {col['name']} ({col['type']}) {col['key']}\n")
            
            # Show indexes
            f.write("\nINDEXES:\n")
            for idx in info['indexes']:
                unique = "UNIQUE" if idx['unique'] else ""
                f.write(f"  - {idx['name']} {unique} on ({', '.join(idx['columns'])})\n")
            
            # Show foreign keys if any
            if info['foreign_keys']:
                f.write("\nFOREIGN KEYS:\n")
                for fk in info['foreign_keys']:
                    f.write(f"  - {fk['column']} -> {fk['references']}\n")
            
            f.write("\n")
            f.write("="*50 + " FILL IN BELOW " + "="*50 + "\n\n")
            f.write("DESCRIPTION (what data does this table hold?):\n")
            f.write("  \n\n")
            f.write("BUSINESS MEANING (what business entity does this represent?):\n")
            f.write("  \n\n")
            f.write("COMMON JOINS (how does it join with other tables?):\n")
            f.write("  Example: JOIN {other_table} ON {this_table}.{column} = {other_table}.{column}\n")
            f.write("  \n\n")
            f.write("\n\n")
    
    print(f"Training template created: SCHEMA_TRAINING.txt")
    print(f"Please fill in the descriptions and relationships in this file.")


if __name__ == "__main__":
    print("Collecting schema metadata...")
    metadata = collect_metadata()
    print("\nNext steps:")
    print("1. Open SCHEMA_TRAINING.txt")
    print("2. Fill in descriptions and relationships for key tables")
    print("3. The system will use this to generate accurate queries")

