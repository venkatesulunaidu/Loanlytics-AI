"""
Deep Analysis of All Reports from bi.report_master
Comprehensive understanding of business logic, joins, aggregations, and patterns
"""

import mysql.connector
from dotenv import load_dotenv
import os
import json
import re
from collections import defaultdict

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST'),
    'port': int(os.getenv('MYSQL_PORT', '3306')),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE')
}

class SQLAnalyzer:
    """Deep SQL query analyzer"""
    
    def __init__(self):
        self.table_usage = defaultdict(lambda: {
            'select_count': 0,
            'join_count': 0,
            'where_count': 0,
            'group_by_count': 0,
            'columns_used': set(),
            'joined_with': set(),
            'common_filters': [],
            'aggregations': []
        })
        
        self.join_patterns = defaultdict(list)
        self.aggregation_patterns = []
        self.business_patterns = defaultdict(list)
    
    def analyze_query(self, report_name, query):
        """Comprehensive query analysis"""
        result = {
            'report_name': report_name,
            'tables': [],
            'joins': [],
            'columns': [],
            'aggregations': [],
            'filters': [],
            'group_by': [],
            'order_by': [],
            'business_logic': []
        }
        
        query_upper = query.upper()
        
        # Extract tables from FROM and JOIN
        result['tables'] = self.extract_tables(query)
        
        # Extract JOIN conditions
        result['joins'] = self.extract_joins(query)
        
        # Extract columns being selected
        result['columns'] = self.extract_select_columns(query)
        
        # Extract aggregations (SUM, COUNT, AVG, MAX, MIN)
        result['aggregations'] = self.extract_aggregations(query)
        
        # Extract WHERE conditions
        result['filters'] = self.extract_where_conditions(query)
        
        # Extract GROUP BY
        result['group_by'] = self.extract_group_by(query)
        
        # Extract ORDER BY
        result['order_by'] = self.extract_order_by(query)
        
        # Infer business logic
        result['business_logic'] = self.infer_business_logic(report_name, query, result)
        
        return result
    
    def extract_tables(self, query):
        """Extract all tables mentioned in query"""
        tables = set()
        
        # FROM clause
        from_pattern = r'FROM\s+(\w+\.?\w+)(?:\s+(?:AS\s+)?(\w+))?'
        for match in re.finditer(from_pattern, query, re.IGNORECASE):
            table = match.group(1)
            alias = match.group(2)
            tables.add((table.lower(), alias.lower() if alias else None))
        
        # JOIN clauses
        join_pattern = r'JOIN\s+(\w+\.?\w+)(?:\s+(?:AS\s+)?(\w+))?'
        for match in re.finditer(join_pattern, query, re.IGNORECASE):
            table = match.group(1)
            alias = match.group(2)
            tables.add((table.lower(), alias.lower() if alias else None))
        
        return list(tables)
    
    def extract_joins(self, query):
        """Extract detailed JOIN information"""
        joins = []
        
        # Pattern: JOIN table ON condition
        pattern = r'((?:INNER|LEFT|RIGHT|OUTER)?\s*JOIN)\s+(\w+\.?\w+)(?:\s+(?:AS\s+)?(\w+))?\s+ON\s+([^\n;]+?)(?=(?:INNER|LEFT|RIGHT|JOIN|WHERE|GROUP|ORDER|HAVING|LIMIT|$))'
        
        for match in re.finditer(pattern, query, re.IGNORECASE | re.DOTALL):
            join_type = match.group(1).strip()
            table = match.group(2)
            alias = match.group(3)
            condition = match.group(4).strip()
            
            joins.append({
                'type': join_type,
                'table': table.lower(),
                'alias': alias.lower() if alias else None,
                'condition': condition[:200]  # Limit length
            })
        
        return joins
    
    def extract_select_columns(self, query):
        """Extract columns being selected"""
        columns = []
        
        # Find SELECT clause
        select_match = re.search(r'SELECT\s+(.*?)\s+FROM', query, re.IGNORECASE | re.DOTALL)
        if select_match:
            select_clause = select_match.group(1)
            
            # Split by comma (rough parsing)
            parts = re.split(r',(?![^()]*\))', select_clause)
            
            for part in parts[:50]:  # Limit to first 50 columns
                part = part.strip()
                if part:
                    # Extract alias if present
                    as_match = re.search(r'(?:AS\s+)?(\w+)\s*$', part, re.IGNORECASE)
                    if as_match:
                        col_name = as_match.group(1)
                    else:
                        # Try to get column name
                        col_match = re.search(r'(\w+\.)?(\w+)', part)
                        if col_match:
                            col_name = col_match.group(2)
                        else:
                            col_name = part[:30]
                    
                    columns.append({
                        'expression': part[:100],
                        'name': col_name.lower()
                    })
        
        return columns
    
    def extract_aggregations(self, query):
        """Extract aggregation functions"""
        aggregations = []
        
        agg_pattern = r'(SUM|COUNT|AVG|MAX|MIN|GROUP_CONCAT)\s*\([^)]+\)(?:\s+AS\s+(\w+))?'
        
        for match in re.finditer(agg_pattern, query, re.IGNORECASE):
            func = match.group(1).upper()
            alias = match.group(2)
            full_expr = match.group(0)
            
            aggregations.append({
                'function': func,
                'expression': full_expr[:100],
                'alias': alias.lower() if alias else None
            })
        
        return aggregations
    
    def extract_where_conditions(self, query):
        """Extract WHERE clause conditions"""
        filters = []
        
        # Find WHERE clause
        where_match = re.search(r'WHERE\s+(.*?)(?=GROUP BY|HAVING|ORDER BY|LIMIT|$)', query, re.IGNORECASE | re.DOTALL)
        if where_match:
            where_clause = where_match.group(1).strip()
            
            # Extract conditions (simplified)
            # Look for common patterns
            patterns = [
                (r'(\w+\.?\w+)\s*=\s*', 'equality'),
                (r'(\w+\.?\w+)\s+IN\s*\(', 'in_list'),
                (r'(\w+\.?\w+)\s+LIKE\s+', 'like'),
                (r'(\w+\.?\w+)\s+BETWEEN\s+', 'between'),
                (r'(\w+\.?\w+)\s+IS\s+NULL', 'is_null'),
                (r'(\w+\.?\w+)\s+IS\s+NOT\s+NULL', 'is_not_null'),
                (r'(\w+\.?\w+)\s*>\s*', 'greater_than'),
                (r'(\w+\.?\w+)\s*<\s*', 'less_than')
            ]
            
            for pattern, condition_type in patterns:
                for match in re.finditer(pattern, where_clause, re.IGNORECASE):
                    column = match.group(1)
                    filters.append({
                        'column': column.lower(),
                        'type': condition_type
                    })
        
        return filters[:20]  # Limit
    
    def extract_group_by(self, query):
        """Extract GROUP BY columns"""
        group_by = []
        
        gb_match = re.search(r'GROUP\s+BY\s+(.*?)(?=HAVING|ORDER BY|LIMIT|$)', query, re.IGNORECASE | re.DOTALL)
        if gb_match:
            gb_clause = gb_match.group(1).strip()
            parts = [p.strip() for p in gb_clause.split(',')]
            group_by = [p[:50] for p in parts[:10]]  # Limit
        
        return group_by
    
    def extract_order_by(self, query):
        """Extract ORDER BY columns"""
        order_by = []
        
        ob_match = re.search(r'ORDER\s+BY\s+(.*?)(?=LIMIT|$)', query, re.IGNORECASE | re.DOTALL)
        if ob_match:
            ob_clause = ob_match.group(1).strip()
            parts = [p.strip() for p in ob_clause.split(',')]
            order_by = [p[:50] for p in parts[:5]]  # Limit
        
        return order_by
    
    def infer_business_logic(self, report_name, query, analysis):
        """Infer business logic from query structure"""
        logic = []
        
        report_lower = report_name.lower()
        query_lower = query.lower()
        
        # Identify report type
        if 'collection' in report_lower:
            logic.append('Type: Collections/Repayment Report')
        elif 'disbursement' in report_lower:
            logic.append('Type: Disbursement Report')
        elif 'portfolio' in report_lower or 'outstanding' in report_lower:
            logic.append('Type: Portfolio/Outstanding Report')
        elif 'par' in report_lower or 'npa' in report_lower:
            logic.append('Type: Asset Quality Report')
        elif 'customer' in report_lower:
            logic.append('Type: Customer Report')
        elif 'loan' in report_lower:
            logic.append('Type: Loan Report')
        
        # Check for common calculations
        if any('sum' in a['function'].lower() for a in analysis['aggregations']):
            logic.append('Calculation: Aggregating amounts (SUM)')
        
        if any('count' in a['function'].lower() for a in analysis['aggregations']):
            logic.append('Calculation: Counting records')
        
        # Check for date filters
        if any('date' in f.get('column', '') for f in analysis['filters']):
            logic.append('Filter: Date-based filtering')
        
        # Check for branch/region grouping
        if any('branch' in gb.lower() for gb in analysis['group_by']):
            logic.append('Grouping: Branch-wise analysis')
        
        if any('product' in gb.lower() for gb in analysis['group_by']):
            logic.append('Grouping: Product-wise analysis')
        
        # Check for customer joins
        customer_tables = [t for t in analysis['tables'] if 'customer' in t[0]]
        if customer_tables:
            logic.append('Scope: Customer-level data')
        
        # Check for account joins
        account_tables = [t for t in analysis['tables'] if 'account' in t[0] or 'loan' in t[0]]
        if account_tables:
            logic.append('Scope: Account/Loan-level data')
        
        return logic

def deep_analyze_all_reports():
    """Perform deep analysis on all reports"""
    
    print("="*80)
    print("DEEP ANALYSIS OF ALL REPORTS")
    print("="*80)
    
    # Connect and get reports
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT id, report_name, query 
        FROM bi.report_master 
        WHERE query IS NOT NULL AND query != ''
        ORDER BY id
    """)
    
    reports = cursor.fetchall()
    conn.close()
    
    print(f"\nAnalyzing {len(reports)} reports...\n")
    
    analyzer = SQLAnalyzer()
    detailed_analysis = []
    
    for i, report in enumerate(reports, 1):
        if i % 20 == 0:
            print(f"Progress: {i}/{len(reports)} reports analyzed...")
        
        try:
            analysis = analyzer.analyze_query(report['report_name'], report['query'])
            detailed_analysis.append(analysis)
        except Exception as e:
            print(f"Error analyzing {report['report_name']}: {e}")
            continue
    
    # Save detailed analysis
    with open('reports_deep_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(detailed_analysis, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n[SUCCESS] Analyzed {len(detailed_analysis)} reports")
    print(f"[SUCCESS] Saved to: reports_deep_analysis.json")
    
    # Generate insights
    generate_insights(detailed_analysis)
    
    return detailed_analysis

def generate_insights(analysis_list):
    """Generate actionable insights from analysis"""
    
    print("\n" + "="*80)
    print("KEY INSIGHTS FROM ANALYSIS")
    print("="*80)
    
    # Table usage statistics
    table_counts = defaultdict(int)
    for analysis in analysis_list:
        for table, alias in analysis['tables']:
            table_counts[table] += 1
    
    print("\n[1] MOST USED TABLES (Top 20):")
    for table, count in sorted(table_counts.items(), key=lambda x: x[1], reverse=True)[:20]:
        print(f"   {table}: {count} reports")
    
    # Common aggregations
    agg_counts = defaultdict(int)
    for analysis in analysis_list:
        for agg in analysis['aggregations']:
            agg_counts[agg['function']] += 1
    
    print("\n[2] AGGREGATION USAGE:")
    for func, count in sorted(agg_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   {func}: {count} times")
    
    # Business logic patterns
    logic_counts = defaultdict(int)
    for analysis in analysis_list:
        for logic in analysis['business_logic']:
            logic_counts[logic] += 1
    
    print("\n[3] BUSINESS LOGIC PATTERNS (Top 15):")
    for logic, count in sorted(logic_counts.items(), key=lambda x: x[1], reverse=True)[:15]:
        print(f"   {logic}: {count} reports")
    
    # JOIN complexity
    join_counts = [len(a['joins']) for a in analysis_list]
    avg_joins = sum(join_counts) / len(join_counts) if join_counts else 0
    max_joins = max(join_counts) if join_counts else 0
    
    print(f"\n[4] JOIN COMPLEXITY:")
    print(f"   Average JOINs per report: {avg_joins:.1f}")
    print(f"   Maximum JOINs in a report: {max_joins}")
    
    # Most complex reports
    complex_reports = sorted(analysis_list, key=lambda x: len(x['joins']), reverse=True)[:5]
    print(f"\n[5] MOST COMPLEX REPORTS (by JOIN count):")
    for report in complex_reports:
        print(f"   {report['report_name']}: {len(report['joins'])} JOINs")
    
    # Save summary
    summary = {
        'total_reports': len(analysis_list),
        'most_used_tables': dict(sorted(table_counts.items(), key=lambda x: x[1], reverse=True)[:30]),
        'aggregation_usage': dict(agg_counts),
        'business_patterns': dict(sorted(logic_counts.items(), key=lambda x: x[1], reverse=True)[:20]),
        'avg_joins_per_report': avg_joins,
        'max_joins': max_joins
    }
    
    with open('reports_analysis_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n[SUCCESS] Summary saved to: reports_analysis_summary.json")

if __name__ == "__main__":
    try:
        analysis = deep_analyze_all_reports()
        print("\n" + "="*80)
        print("DEEP ANALYSIS COMPLETE!")
        print("="*80)
        print("\nGenerated files:")
        print("  1. reports_deep_analysis.json - Full detailed analysis")
        print("  2. reports_analysis_summary.json - Key insights and statistics")
        print("\nNext: Use this knowledge to train the AI comprehensively")
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

