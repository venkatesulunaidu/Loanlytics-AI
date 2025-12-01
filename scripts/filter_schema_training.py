"""
Filter SCHEMA_TRAINING.txt to only include encoredb and financialForms schemas
"""

import json
import os

# Read the full metadata
with open('schema_metadata.json', 'r', encoding='utf-8') as f:
    metadata = json.load(f)

# Filter to only encoredb and financialForms
filtered_metadata = {
    table_name: info 
    for table_name, info in metadata.items() 
    if info['schema'] in ['encoredb', 'financialForms']
}

print(f"Original tables: {len(metadata)}")
print(f"Filtered tables: {len(filtered_metadata)}")

# Create filtered training file
with open('SCHEMA_TRAINING_FILTERED.txt', 'w', encoding='utf-8') as f:
    f.write("="*100 + "\n")
    f.write("LOANLYTICS AI - SCHEMA TRAINING FILE (encoredb & financialForms only)\n")
    f.write("="*100 + "\n\n")
    f.write("Instructions: Fill in the descriptions, common_joins, and business_meaning for each table.\n")
    f.write("This will help the AI understand your database structure and generate accurate queries.\n\n")
    
    for table_name, info in sorted(filtered_metadata.items()):
        f.write("\n" + "="*100 + "\n")
        f.write(f"TABLE: {table_name}\n")
        f.write("="*100 + "\n")
        f.write(f"Schema: {info['schema']}\n")
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

print("Filtered training file created: SCHEMA_TRAINING_FILTERED.txt")
print(f"File size reduced significantly - only {len(filtered_metadata)} tables")

# Also save filtered metadata
with open('schema_metadata_filtered.json', 'w', encoding='utf-8') as f:
    json.dump(filtered_metadata, f, indent=2, ensure_ascii=False)

print("Filtered metadata saved: schema_metadata_filtered.json")

