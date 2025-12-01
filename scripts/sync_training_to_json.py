"""
Sync SCHEMA_TRAINING_FILTERED.txt to schema_metadata_filtered.json
Reads the filled training data and updates the JSON file
"""

import json
import re

def parse_training_file(filename='SCHEMA_TRAINING_FILTERED.txt'):
    """Parse the training file and extract filled information"""
    
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by table sections
    tables = {}
    table_sections = content.split('='*100)
    
    for section in table_sections:
        if not section.strip() or 'TABLE:' not in section:
            continue
        
        # Extract table name
        table_match = re.search(r'TABLE:\s+(\S+)', section)
        if not table_match:
            continue
        
        table_name = table_match.group(1)
        
        # Extract the filled sections
        description = ""
        business_meaning = ""
        common_joins = []
        
        # Look for filled content after "FILL IN BELOW"
        if 'FILL IN BELOW' in section:
            fill_section = section.split('FILL IN BELOW')[1]
            
            # Extract DESCRIPTION
            desc_match = re.search(r'DESCRIPTION.*?:\s*\n\s*(.*?)\n\n', fill_section, re.DOTALL)
            if desc_match:
                description = desc_match.group(1).strip()
            
            # Extract BUSINESS MEANING
            bm_match = re.search(r'BUSINESS MEANING.*?:\s*\n\s*(.*?)\n\n', fill_section, re.DOTALL)
            if bm_match:
                business_meaning = bm_match.group(1).strip()
            
            # Extract COMMON JOINS
            joins_match = re.search(r'COMMON JOINS.*?:\s*\n(.*?)(?:\n\n|$)', fill_section, re.DOTALL)
            if joins_match:
                joins_text = joins_match.group(1)
                # Parse each line that starts with JOIN
                for line in joins_text.split('\n'):
                    line = line.strip()
                    if line and line.startswith('JOIN') and 'Example:' not in line:
                        common_joins.append(line)
        
        # Only add if something was filled
        if description or business_meaning or common_joins:
            tables[table_name] = {
                'description': description,
                'business_meaning': business_meaning,
                'common_joins': common_joins
            }
    
    return tables


def update_json_metadata(training_data, json_file='schema_metadata_filtered.json'):
    """Update the JSON metadata with training data"""
    
    # Read existing JSON
    with open(json_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    # Update tables with training data
    updated_count = 0
    for table_name, training in training_data.items():
        if table_name in metadata:
            metadata[table_name]['description'] = training['description']
            metadata[table_name]['business_meaning'] = training['business_meaning']
            metadata[table_name]['common_joins'] = training['common_joins']
            updated_count += 1
            print(f"✓ Updated: {table_name}")
        else:
            print(f"✗ Not found: {table_name}")
    
    # Save updated JSON
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    return updated_count


if __name__ == "__main__":
    print("Parsing training file...")
    training_data = parse_training_file()
    
    print(f"\nFound {len(training_data)} trained tables:")
    for table in list(training_data.keys())[:10]:
        print(f"  - {table}")
    if len(training_data) > 10:
        print(f"  ... and {len(training_data) - 10} more")
    
    print("\nUpdating JSON metadata...")
    count = update_json_metadata(training_data)
    
    print(f"\n{'='*60}")
    print(f"✓ Successfully updated {count} tables in schema_metadata_filtered.json")
    print(f"{'='*60}")
    
    # Show summary
    if count > 0:
        print("\nThe AI will now use this training data to generate accurate queries!")
        print("Restart the backend server to apply changes.")
    else:
        print("\nNo tables were updated. Make sure you filled in the training data in SCHEMA_TRAINING_FILTERED.txt")


