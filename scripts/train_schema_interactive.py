"""
Interactive Schema Training Tool
Makes it easy to train the AI on your database schema
"""

import json
import os
from collections import defaultdict

def load_metadata(filename='schema_metadata_filtered.json'):
    """Load the schema metadata"""
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_metadata(metadata, filename='schema_metadata_filtered.json'):
    """Save the updated metadata"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Saved to {filename}")

def get_priority_tables(metadata):
    """Get tables that should be trained first based on importance"""
    scored_tables = []
    
    for table_name, info in metadata.items():
        score = 0
        
        # Score by row count (more rows = more important)
        if info['row_count'] > 100000:
            score += 10
        elif info['row_count'] > 10000:
            score += 5
        elif info['row_count'] > 1000:
            score += 2
        
        # Score by foreign keys (more relationships = more important)
        score += len(info.get('foreign_keys', [])) * 3
        
        # Score by indexes (more indexes = more queried)
        score += len(info.get('indexes', [])) * 1
        
        # Bonus for common table names
        table_lower = table_name.lower()
        if 'customer' in table_lower:
            score += 15
        if 'loan' in table_lower and 'account' in table_lower:
            score += 12
        if 'disbursement' in table_lower:
            score += 10
        if 'product' in table_lower:
            score += 8
        if 'account' in table_lower and 'profile' in table_lower:
            score += 10
        if 'account_holder' in table_lower:
            score += 12
        
        # Skip if already trained
        if info.get('description') and info.get('business_meaning'):
            score = -1  # Already trained
        
        scored_tables.append((table_name, info, score))
    
    # Sort by score
    scored_tables.sort(key=lambda x: x[2], reverse=True)
    
    return scored_tables

def show_table_info(table_name, info):
    """Display table information"""
    print("\n" + "="*80)
    print(f"TABLE: {table_name}")
    print("="*80)
    print(f"Schema: {info['schema']}")
    print(f"Row Count: {info['row_count']:,}")
    
    # Show key columns
    print("\nKEY COLUMNS:")
    key_cols = [col for col in info['columns'] if col['key'] or 'id' in col['name'].lower() or 'code' in col['name'].lower()][:8]
    for col in key_cols:
        key_marker = f"[{col['key']}]" if col['key'] else ""
        print(f"  - {col['name']} ({col['type']}) {key_marker}")
    
    # Show indexes
    print("\nINDEXES:")
    for idx in info['indexes'][:5]:
        unique = "UNIQUE" if idx['unique'] else ""
        cols = ', '.join(idx['columns'][:3])
        if len(idx['columns']) > 3:
            cols += '...'
        print(f"  - {idx['name']} {unique} on ({cols})")
    
    # Show foreign keys
    if info.get('foreign_keys'):
        print("\nFOREIGN KEYS:")
        for fk in info['foreign_keys'][:5]:
            print(f"  - {fk['column']} -> {fk['references']}")

def suggest_joins(table_name, info, all_metadata):
    """Auto-suggest common joins based on column names and foreign keys"""
    suggestions = []
    
    # From foreign keys
    for fk in info.get('foreign_keys', []):
        ref_parts = fk['references'].split('.')
        if len(ref_parts) == 3:
            ref_schema, ref_table, ref_col = ref_parts
            suggestions.append(
                f"JOIN {ref_schema}.{ref_table} ON {table_name}.{fk['column']} = {ref_schema}.{ref_table}.{ref_col}"
            )
    
    # Common patterns based on column names
    table_parts = table_name.split('.')
    if len(table_parts) == 2:
        schema, table = table_parts
        
        # Look for matching columns in other tables
        my_cols = {col['name'] for col in info['columns']}
        
        for other_name, other_info in all_metadata.items():
            if other_name == table_name:
                continue
            
            # Check for common join columns
            other_cols = {col['name'] for col in other_info['columns']}
            common = my_cols & other_cols
            
            # Suggest joins on common columns with 'id' or 'code'
            for col in common:
                if ('id' in col.lower() or 'code' in col.lower()) and col not in ['id', 'version']:
                    # Check if it's a composite key pattern (tenant_code + account_id)
                    if 'tenant_code' in common and 'account_id' in common and col == 'tenant_code':
                        suggestions.append(
                            f"JOIN {other_name} ON {table_name}.tenant_code = {other_name}.tenant_code AND {table_name}.account_id = {other_name}.account_id"
                        )
                        break
                    else:
                        suggestions.append(f"JOIN {other_name} ON {table_name}.{col} = {other_name}.{col}")
                    
                    if len(suggestions) >= 5:
                        break
            
            if len(suggestions) >= 5:
                break
    
    return suggestions[:5]  # Return top 5

def train_table(table_name, info, all_metadata):
    """Interactive training for a single table"""
    
    show_table_info(table_name, info)
    
    print("\n" + "-"*80)
    print("Let's train this table!")
    print("-"*80)
    
    # Get description
    print("\n1️⃣  DESCRIPTION (what data does this table hold?)")
    print("   Examples:")
    print("   - 'Customer master data with personal and contact information'")
    print("   - 'Loan disbursement transactions with amounts and dates'")
    print("   - 'Links customers to their loan accounts'")
    description = input("\n   Your answer: ").strip()
    
    # Get business meaning
    print("\n2️⃣  BUSINESS MEANING (what business entity?)")
    print("   Examples: 'Customers', 'Loan Disbursements', 'Products', 'Accounts'")
    business_meaning = input("\n   Your answer: ").strip()
    
    # Get joins
    print("\n3️⃣  COMMON JOINS (how does it join with other tables?)")
    print("\n   📋 Suggested joins based on your schema:")
    suggestions = suggest_joins(table_name, info, all_metadata)
    
    if suggestions:
        for i, suggestion in enumerate(suggestions, 1):
            print(f"   {i}. {suggestion}")
        
        print("\n   Enter numbers to accept suggestions (e.g., '1,2,3') or 'n' to skip:")
        choice = input("   Your choice: ").strip()
        
        common_joins = []
        if choice.lower() != 'n':
            try:
                indices = [int(x.strip()) - 1 for x in choice.split(',') if x.strip()]
                common_joins = [suggestions[i] for i in indices if 0 <= i < len(suggestions)]
            except:
                print("   Invalid input, skipping joins")
        
        # Option to add custom joins
        print("\n   Add custom join? (press Enter to skip)")
        custom = input("   Custom JOIN: ").strip()
        if custom:
            common_joins.append(custom)
    else:
        print("   No suggestions available. Add manually? (press Enter to skip)")
        custom = input("   Your JOIN: ").strip()
        common_joins = [custom] if custom else []
    
    # Update metadata
    info['description'] = description
    info['business_meaning'] = business_meaning
    info['common_joins'] = common_joins
    
    print("\n✅ Table trained successfully!")
    return True

def main():
    """Main interactive training loop"""
    print("="*80)
    print("🎓 INTERACTIVE SCHEMA TRAINING TOOL")
    print("="*80)
    print("\nThis tool will help you train the AI on your database schema.")
    print("We'll focus on the most important tables first.\n")
    
    # Load metadata
    metadata = load_metadata()
    
    # Get priority tables
    priority_tables = get_priority_tables(metadata)
    
    # Filter out already trained
    untrained = [(name, info, score) for name, info, score in priority_tables if score > 0]
    trained = [(name, info, score) for name, info, score in priority_tables if score < 0]
    
    print(f"📊 Status:")
    print(f"   - Already trained: {len(trained)} tables")
    print(f"   - Ready to train: {len(untrained)} tables")
    print(f"   - Total tables: {len(metadata)}")
    
    if len(trained) > 0:
        print(f"\n✓ Previously trained tables:")
        for name, _, _ in trained[:5]:
            print(f"   - {name}")
        if len(trained) > 5:
            print(f"   ... and {len(trained) - 5} more")
    
    if len(untrained) == 0:
        print("\n🎉 All important tables are already trained!")
        return
    
    print(f"\n📚 Top {min(20, len(untrained))} tables to train (by importance):")
    for i, (name, info, score) in enumerate(untrained[:20], 1):
        rows = f"{info['row_count']:,}" if info['row_count'] > 0 else "empty"
        print(f"   {i}. {name} ({rows} rows)")
    
    print("\n" + "-"*80)
    input("Press Enter to start training...")
    
    # Training loop
    trained_count = 0
    for name, info, score in untrained[:20]:
        print("\n\n")
        try:
            if train_table(name, info, metadata):
                trained_count += 1
                
                # Save after each table
                save_metadata(metadata)
                
                # Ask to continue
                print(f"\n📈 Progress: {trained_count} tables trained")
                cont = input("\nContinue to next table? (y/n, default=y): ").strip().lower()
                if cont == 'n':
                    break
        except KeyboardInterrupt:
            print("\n\n⚠️  Training interrupted")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            cont = input("Continue anyway? (y/n): ").strip().lower()
            if cont == 'n':
                break
    
    # Final summary
    print("\n" + "="*80)
    print(f"🎉 Training Complete!")
    print("="*80)
    print(f"✓ Trained {trained_count} tables in this session")
    print(f"✓ Total trained: {len(trained) + trained_count} tables")
    print(f"\nThe AI will now use this training to generate accurate queries!")
    print("Restart your backend server to apply the changes.")
    print("="*80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")


