"""
Comprehensive AI Training System
Uses deep analysis to train the LLM with production knowledge
"""

import json
from collections import defaultdict

def build_comprehensive_knowledge():
    """Build comprehensive knowledge base for AI"""
    
    print("="*80)
    print("BUILDING COMPREHENSIVE AI KNOWLEDGE BASE")
    print("="*80)
    
    # Load deep analysis
    with open('reports_deep_analysis.json', 'r', encoding='utf-8') as f:
        deep_analysis = json.load(f)
    
    # Load learned patterns
    with open('learned_join_patterns.json', 'r', encoding='utf-8') as f:
        join_patterns = json.load(f)
    
    # Load schema metadata
    with open('schema_metadata_filtered.json', 'r', encoding='utf-8') as f:
        schema_metadata = json.load(f)
    
    knowledge = {
        'table_relationships': {},
        'common_queries': {},
        'aggregation_patterns': {},
        'filter_patterns': {},
        'business_rules': {}
    }
    
    # 1. Build comprehensive table relationships
    print("\n[1] Building table relationship knowledge...")
    table_joins = defaultdict(lambda: {'joins_with': set(), 'join_conditions': [], 'usage_count': 0})
    
    for analysis in deep_analysis:
        tables = [t[0] for t in analysis['tables']]
        
        for join in analysis['joins']:
            joined_table = join['table']
            condition = join['condition']
            
            for table in tables:
                if table != joined_table:
                    table_joins[table]['joins_with'].add(joined_table)
                    table_joins[table]['join_conditions'].append({
                        'with': joined_table,
                        'condition': condition,
                        'report': analysis['report_name']
                    })
                    table_joins[table]['usage_count'] += 1
    
    # Convert sets to lists for JSON serialization
    for table, data in table_joins.items():
        knowledge['table_relationships'][table] = {
            'joins_with': list(data['joins_with']),
            'common_join_conditions': data['join_conditions'][:5],  # Top 5
            'usage_count': data['usage_count']
        }
    
    print(f"   Learned relationships for {len(knowledge['table_relationships'])} tables")
    
    # 2. Extract common query patterns
    print("\n[2] Extracting common query patterns...")
    query_patterns = {
        'customer_loan_amount': [],
        'product_disbursement': [],
        'branch_collection': [],
        'outstanding_report': [],
        'par_npa_report': []
    }
    
    for analysis in deep_analysis:
        report_name = analysis['report_name'].lower()
        
        # Customer + Loan Amount pattern
        if 'customer' in report_name and ('outstanding' in report_name or 'loan' in report_name):
            query_patterns['customer_loan_amount'].append({
                'report': analysis['report_name'],
                'tables': [t[0] for t in analysis['tables']],
                'joins': analysis['joins'],
                'aggregations': analysis['aggregations']
            })
        
        # Product + Disbursement pattern
        if 'product' in report_name or 'disbursement' in report_name:
            query_patterns['product_disbursement'].append({
                'report': analysis['report_name'],
                'tables': [t[0] for t in analysis['tables']],
                'joins': analysis['joins'],
                'aggregations': analysis['aggregations']
            })
        
        # Branch + Collection pattern
        if 'branch' in report_name or 'collection' in report_name:
            query_patterns['branch_collection'].append({
                'report': analysis['report_name'],
                'tables': [t[0] for t in analysis['tables']],
                'joins': analysis['joins'],
                'aggregations': analysis['aggregations']
            })
        
        # Outstanding pattern
        if 'outstanding' in report_name or 'portfolio' in report_name:
            query_patterns['outstanding_report'].append({
                'report': analysis['report_name'],
                'tables': [t[0] for t in analysis['tables']],
                'joins': analysis['joins'],
                'aggregations': analysis['aggregations']
            })
        
        # PAR/NPA pattern
        if 'par' in report_name or 'npa' in report_name:
            query_patterns['par_npa_report'].append({
                'report': analysis['report_name'],
                'tables': [t[0] for t in analysis['tables']],
                'joins': analysis['joins'],
                'aggregations': analysis['aggregations']
            })
    
    knowledge['common_queries'] = query_patterns
    for pattern_type, patterns in query_patterns.items():
        print(f"   {pattern_type}: {len(patterns)} examples")
    
    # 3. Aggregation patterns
    print("\n[3] Learning aggregation patterns...")
    agg_by_table = defaultdict(lambda: {'sum_columns': set(), 'count_columns': set(), 'max_columns': set()})
    
    for analysis in deep_analysis:
        tables = [t[0] for t in analysis['tables']]
        for agg in analysis['aggregations']:
            func = agg['function']
            expr = agg['expression'].lower()
            
            for table in tables:
                if func == 'SUM':
                    agg_by_table[table]['sum_columns'].add(expr[:50])
                elif func == 'COUNT':
                    agg_by_table[table]['count_columns'].add(expr[:50])
                elif func == 'MAX':
                    agg_by_table[table]['max_columns'].add(expr[:50])
    
    for table, aggs in agg_by_table.items():
        knowledge['aggregation_patterns'][table] = {
            'sum_columns': list(aggs['sum_columns'])[:5],
            'count_columns': list(aggs['count_columns'])[:5],
            'max_columns': list(aggs['max_columns'])[:5]
        }
    
    print(f"   Learned aggregation patterns for {len(knowledge['aggregation_patterns'])} tables")
    
    # 4. Filter patterns
    print("\n[4] Learning filter patterns...")
    filter_by_table = defaultdict(lambda: {'equality_filters': set(), 'date_filters': set(), 'null_checks': set()})
    
    for analysis in deep_analysis:
        tables = [t[0] for t in analysis['tables']]
        for filter_cond in analysis['filters']:
            col = filter_cond['column']
            ftype = filter_cond['type']
            
            for table in tables:
                if ftype == 'equality':
                    filter_by_table[table]['equality_filters'].add(col)
                elif 'date' in col.lower():
                    filter_by_table[table]['date_filters'].add(col)
                elif 'null' in ftype:
                    filter_by_table[table]['null_checks'].add(col)
    
    for table, filters in filter_by_table.items():
        knowledge['filter_patterns'][table] = {
            'common_equality_filters': list(filters['equality_filters'])[:5],
            'date_filters': list(filters['date_filters'])[:5],
            'null_checks': list(filters['null_checks'])[:3]
        }
    
    print(f"   Learned filter patterns for {len(knowledge['filter_patterns'])} tables")
    
    # 5. Business rules
    print("\n[5] Extracting business rules...")
    knowledge['business_rules'] = {
        'customer_identification': {
            'description': 'Customers identified by URN or ID',
            'tables': ['perdix_db.customer', 'financialforms.customer'],
            'key_columns': ['urn_no', 'id', 'customer_id'],
            'usage': '255 reports use customer tables'
        },
        'loan_account_linking': {
            'description': 'Loans linked via account_number or account_id',
            'tables': ['perdix_db.loan_accounts', 'financialforms.loan_accounts', 'encoredb.loan_od_working_registers'],
            'key_columns': ['account_number', 'account_id'],
            'usage': '177 reports use loan tables'
        },
        'product_classification': {
            'description': 'Products identified by product_code',
            'tables': ['perdix_db.loan_products', 'financialforms.loan_products'],
            'key_columns': ['product_code'],
            'usage': '58 reports use product tables'
        },
        'branch_hierarchy': {
            'description': 'Branches organized hierarchically with hub relationships',
            'tables': ['perdix_db.branch_master', 'financialforms.branch_master', 'perdix_db.hub_master'],
            'key_columns': ['branch_id', 'hub_id', 'branch_code'],
            'usage': '215 reports use branch tables'
        },
        'amount_calculations': {
            'description': 'Amounts stored in magnitude fields (often in paisa, divide by 100)',
            'common_patterns': [
                'SUM(amount_magnitude)',
                'SUM(principal_magnitude)',
                'SUM(total_disbursed_magnitude)',
                'SUM(principal_outstanding)'
            ],
            'usage': '1315 SUM operations across all reports'
        },
        'disbursement_tracking': {
            'description': 'Disbursements tracked in loan_od_disbursements and related tables',
            'tables': ['encoredb.loan_od_disbursements', 'financialforms.loan_account_disbursement_schedule'],
            'key_relationships': [
                'loan_od_disbursements JOIN account_profiles ON (tenant_code AND account_id)',
                'account_profiles has product_code'
            ],
            'usage': '21 disbursement reports'
        },
        'collection_tracking': {
            'description': 'Collections tracked in loan_repayment_details and loan_od_repayments',
            'tables': ['perdix_db.loan_repayment_details', 'encoredb.loan_od_repayments', 'financialforms.loan_collections'],
            'key_relationships': [
                'JOIN via transaction_id',
                'JOIN via account_number'
            ],
            'usage': '32 collection reports'
        },
        'customer_loan_relationship': {
            'description': 'Customer to Loan via account_holders (3-table join)',
            'join_path': [
                'customer.customer_id = account_holders.customer_id',
                'account_holders.account_id = loan_od_working_registers.account_id'
            ],
            'alternative': 'Direct via loan_accounts.customer_id = customer.id',
            'usage': 'Critical relationship used in 162 customer reports'
        }
    }
    
    print(f"   Documented {len(knowledge['business_rules'])} business rules")
    
    # Save comprehensive knowledge
    with open('ai_comprehensive_knowledge.json', 'w', encoding='utf-8') as f:
        json.dump(knowledge, f, indent=2, ensure_ascii=False, default=str)
    
    print("\n" + "="*80)
    print("[SUCCESS] Comprehensive knowledge base created!")
    print("[SUCCESS] Saved to: ai_comprehensive_knowledge.json")
    print("="*80)
    
    return knowledge

def generate_ai_prompt_guide():
    """Generate a comprehensive guide for the AI agent"""
    
    with open('ai_comprehensive_knowledge.json', 'r', encoding='utf-8') as f:
        knowledge = json.load(f)
    
    guide = """
# COMPREHENSIVE AI AGENT KNOWLEDGE BASE
# Auto-generated from 274 production reports

## CRITICAL TABLE RELATIONSHIPS

### Customer → Loan (3-table join):
```
customers.customer_id = account_holders.customer_id
account_holders.account_id = loan_od_working_registers.account_id
```
Alternative: `loan_accounts.customer_id = customer.id`

### Product → Disbursement (2-table join):
```
loan_od_disbursements JOIN account_profiles 
  ON (tenant_code = tenant_code AND account_id = account_id)
account_profiles has product_code
```

### Branch → Hub:
```
branch_master.hub_id = hub_master.id
```

## MOST IMPORTANT TABLES (by usage)
1. customer (perdix_db/financialforms) - 255 reports
2. branch_master - 215 reports
3. loan_accounts - 177 reports
4. users - 76 reports
5. loan_od_working_registers - 29 reports

## COMMON AGGREGATIONS
- **Amount calculations**: Use SUM(amount_magnitude) or SUM(principal_magnitude)
- **Counts**: Use COUNT(DISTINCT account_id) for loans, COUNT(DISTINCT customer_id) for customers
- **Latest records**: Use MAX(date_column) or subquery with MAX(id)

## BUSINESS PATTERNS

### Query Type: Product-wise Disbursement
Tables: loan_od_disbursements, account_profiles
Join: ON tenant_code AND account_id
Group By: product_code
Aggregate: SUM(amount_magnitude)

### Query Type: Customer Outstanding
Tables: customer, loan_accounts, loan_od_working_registers
Join: customer_id linkage
Aggregate: SUM(total_disbursed_magnitude) or SUM(principal_outstanding)

### Query Type: Branch Collections
Tables: branch_master, loan_repayment_details, loan_accounts
Join: branch_id linkage
Aggregate: SUM(repayment_amount)

## KEY RULES
1. **Amounts**: Usually in 'magnitude' columns (sometimes in paisa)
2. **Composite Keys**: Many tables use (tenant_code, account_id) as composite key
3. **Date Filters**: Most reports filter by date ranges on disbursement_date, transaction_date, value_date
4. **Status Fields**: Check is_closed, status, current_stage for active records
5. **Schema Mapping**: PERDIX_DB = financialforms, ENCORE_DB = encoredb in production reports
"""
    
    with open('AI_AGENT_GUIDE.txt', 'w', encoding='utf-8') as f:
        f.write(guide)
    
    print("\n[SUCCESS] AI Agent Guide created: AI_AGENT_GUIDE.txt")

if __name__ == "__main__":
    try:
        knowledge = build_comprehensive_knowledge()
        generate_ai_prompt_guide()
        
        print("\n" + "="*80)
        print("READY TO UPDATE AI AGENT!")
        print("="*80)
        print("\nGenerated files:")
        print("  1. ai_comprehensive_knowledge.json - Full knowledge base")
        print("  2. AI_AGENT_GUIDE.txt - Human-readable guide")
        print("\nNext: Integrate this knowledge into backend/app.py")
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

