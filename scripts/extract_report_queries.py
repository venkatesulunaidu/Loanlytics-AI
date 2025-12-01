"""
Extract queries from bi.report_master to learn join patterns
"""

import mysql.connector
from dotenv import load_dotenv
import os
import json
import re

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST'),
    'port': int(os.getenv('MYSQL_PORT', '3306')),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE')
}

def extract_queries():
    """Extract all queries from bi.report_master"""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    
    print("Extracting queries from bi.report_master...")
    cursor.execute("""
        SELECT id, report_name, query 
        FROM bi.report_master 
        WHERE query IS NOT NULL AND query != ''
        ORDER BY id
    """)
    
    reports = cursor.fetchall()
    conn.close()
    
    print(f"Found {len(reports)} reports with queries\n")
    
    # Save raw queries
    with open('report_queries.json', 'w', encoding='utf-8') as f:
        json.dump(reports, f, indent=2, ensure_ascii=False)
    
    return reports

def parse_joins_from_query(query):
    """Extract JOIN information from a SQL query"""
    joins = []
    
    # Normalize query
    query = query.upper()
    
    # Find all JOIN patterns
    join_pattern = r'JOIN\s+(\w+\.?\w+)\s+(?:AS\s+)?(\w+)?\s+ON\s+([^\n;]+?)(?:WHERE|GROUP|ORDER|INNER|LEFT|RIGHT|JOIN|$)'
    matches = re.finditer(join_pattern, query, re.IGNORECASE | re.DOTALL)
    
    for match in matches:
        table = match.group(1)
        alias = match.group(2)
        condition = match.group(3).strip()
        
        joins.append({
            'table': table,
            'alias': alias,
            'condition': condition
        })
    
    return joins

def extract_table_references(query):
    """Extract all table references from query"""
    tables = set()
    
    # Find schema.table patterns
    pattern = r'\b(\w+)\.(\w+)\b'
    matches = re.finditer(pattern, query, re.IGNORECASE)
    
    for match in matches:
        schema = match.group(1).lower()
        table = match.group(2).lower()
        # Skip common SQL keywords
        if schema not in ['select', 'from', 'where', 'group', 'order', 'having', 'inner', 'left', 'right']:
            tables.add(f"{schema}.{table}")
    
    return list(tables)

def analyze_queries(reports):
    """Analyze queries to find common patterns"""
    
    print("="*80)
    print("ANALYZING QUERIES TO LEARN JOIN PATTERNS")
    print("="*80)
    
    join_patterns = {}
    table_relationships = {}
    
    for report in reports:
        query = report['query']
        report_name = report['report_name']
        
        # Extract joins
        joins = parse_joins_from_query(query)
        tables = extract_table_references(query)
        
        if joins or tables:
            print(f"\n[Report] {report_name}")
            
            if tables:
                print(f"   Tables: {', '.join(tables[:5])}")
                if len(tables) > 5:
                    print(f"           ... and {len(tables) - 5} more")
            
            if joins:
                print("   Joins:")
                for join in joins:
                    print(f"      JOIN {join['table']} ON {join['condition'][:80]}")
                    
                    # Store join pattern
                    key = f"{join['table']}"
                    if key not in join_patterns:
                        join_patterns[key] = []
                    join_patterns[key].append({
                        'condition': join['condition'],
                        'report': report_name
                    })
    
    return join_patterns, table_relationships

def generate_training_data(join_patterns):
    """Generate training data from learned patterns"""
    
    print("\n" + "="*80)
    print("LEARNED JOIN PATTERNS")
    print("="*80)
    
    training_data = {}
    
    for table, patterns in join_patterns.items():
        # Count most common join patterns
        pattern_counts = {}
        for p in patterns:
            condition = p['condition']
            if condition not in pattern_counts:
                pattern_counts[condition] = []
            pattern_counts[condition].append(p['report'])
        
        # Get most common patterns
        sorted_patterns = sorted(pattern_counts.items(), key=lambda x: len(x[1]), reverse=True)
        
        print(f"\n[Table] {table}")
        print(f"   Used in {len(patterns)} queries")
        print("   Common join patterns:")
        
        common_joins = []
        for condition, reports in sorted_patterns[:3]:
            print(f"      - {condition}")
            print(f"        (used in {len(reports)} reports)")
            common_joins.append(f"JOIN {table} ON {condition}")
        
        training_data[table] = {
            'common_joins': common_joins,
            'usage_count': len(patterns),
            'example_reports': [p['report'] for p in patterns[:3]]
        }
    
    return training_data

def save_training_data(training_data):
    """Save learned patterns"""
    with open('learned_join_patterns.json', 'w', encoding='utf-8') as f:
        json.dump(training_data, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*80)
    print("✓ Saved learned patterns to: learned_join_patterns.json")
    print("="*80)

if __name__ == "__main__":
    try:
        # Extract queries
        reports = extract_queries()
        
        # Analyze patterns
        join_patterns, table_relationships = analyze_queries(reports)
        
        # Generate training data
        training_data = generate_training_data(join_patterns)
        
        # Save
        save_training_data(training_data)
        
        print(f"\n[SUCCESS] Analysis complete!")
        print(f"   - Analyzed {len(reports)} reports")
        print(f"   - Learned {len(join_patterns)} table join patterns")
        print(f"\nNext step: Use this data to auto-train schema metadata")
        
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()

