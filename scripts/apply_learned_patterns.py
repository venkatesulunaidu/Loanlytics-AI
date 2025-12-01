"""
Apply learned join patterns from bi.report_master to schema metadata
This automatically trains the AI based on real production queries
"""

import json

def apply_learned_patterns():
    """Apply learned patterns to schema metadata"""
    
    # Load learned patterns
    with open('learned_join_patterns.json', 'r', encoding='utf-8') as f:
        learned = json.load(f)
    
    # Load schema metadata
    with open('schema_metadata_filtered.json', 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    print("="*80)
    print("APPLYING LEARNED JOIN PATTERNS TO SCHEMA METADATA")
    print("="*80)
    
    updated_count = 0
    
    # Schema mapping from report queries to actual schema names  
    schema_mapping = {
        'perdix': 'financialForms',  # Note: capital F
        'encore': 'encoredb',
        'bi': 'bi',
        'ams': 'ams'
    }
    
    for table_key, patterns in learned.items():
        # Parse table name: PERDIX_DB.TABLE_NAME or ENCORE_DB.TABLE_NAME
        table_parts = table_key.lower().replace('_db', '').split('.')
        if len(table_parts) == 2:
            schema_key, table = table_parts
            
            # Map to actual schema name
            actual_schema = schema_mapping.get(schema_key, schema_key)
            full_name = f"{actual_schema}.{table}"
            
            # Find matching table in metadata
            if full_name in metadata:
                # Update with learned patterns
                metadata[full_name]['common_joins'] = patterns['common_joins']
                metadata[full_name]['description'] = f"Used in {patterns['usage_count']} production reports"
                metadata[full_name]['business_meaning'] = f"Production table (usage: {patterns['usage_count']} queries)"
                
                print(f"[UPDATED] {full_name}")
                print(f"   Usage: {patterns['usage_count']} reports")
                print(f"   Joins: {len(patterns['common_joins'])} patterns learned")
                updated_count += 1
    
    # Save updated metadata
    with open('schema_metadata_filtered.json', 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*80}")
    print(f"[SUCCESS] Updated {updated_count} tables with learned patterns")
    print(f"[SUCCESS] Saved to schema_metadata_filtered.json")
    print(f"{'='*80}")
    
    return updated_count

if __name__ == "__main__":
    try:
        count = apply_learned_patterns()
        print(f"\n[NEXT STEP] Restart your backend server to use the learned patterns!")
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

