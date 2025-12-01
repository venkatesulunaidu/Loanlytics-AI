"""
Organize project structure for git
Moves files to appropriate directories and cleans up
"""

import os
import shutil
from pathlib import Path

# Define directory structure
DIRS = {
    'scripts': 'scripts',
    'data': 'data',
    'docs': 'docs'
}

# Files to organize
FILE_MAPPING = {
    # Training/analysis scripts → scripts/
    'collect_schema_metadata.py': 'scripts/',
    'comprehensive_ai_training.py': 'scripts/',
    'deep_analysis_reports.py': 'scripts/',
    'extract_report_queries.py': 'scripts/',
    'filter_schema_training.py': 'scripts/',
    'sync_training_to_json.py': 'scripts/',
    'train_schema_interactive.py': 'scripts/',
    'apply_learned_patterns.py': 'scripts/',
    'schema_knowledge.py': 'scripts/',
    'test_db_connection.py': 'scripts/',
    'test_langchain.py': 'scripts/',
    
    # Data files → data/
    'ai_comprehensive_knowledge.json': 'data/',
    'learned_join_patterns.json': 'data/',
    'report_queries.json': 'data/',
    'reports_analysis_summary.json': 'data/',
    'reports_deep_analysis.json': 'data/',
    'schema_metadata.json': 'data/',
    'schema_metadata_filtered.json': 'data/',
    'SCHEMA_TRAINING.txt': 'data/',
    'SCHEMA_TRAINING_FILTERED.txt': 'data/',
    
    # Documentation → docs/
    'AI_AGENT_GUIDE.txt': 'docs/',
    'PARSING_ERROR_FIXED.md': 'docs/',
    'QUERY_EXAMPLES.md': 'docs/',
    'QUICK_TEST.md': 'docs/',
    'SCHEMA_TRAINING_GUIDE.md': 'docs/',
    'SETUP_GUIDE.txt': 'docs/',
    'TEST_QUERIES.md': 'docs/',
    'USER_GUIDE.md': 'docs/',
}

# Files to delete (temporary/test files)
FILES_TO_DELETE = [
    # Keep these - they're useful
]

def create_directories():
    """Create directory structure"""
    for dir_name in DIRS.values():
        os.makedirs(dir_name, exist_ok=True)
        print(f"Created/verified: {dir_name}/")

def move_files():
    """Move files to appropriate directories"""
    moved = 0
    for file_name, target_dir in FILE_MAPPING.items():
        if os.path.exists(file_name):
            target_path = os.path.join(target_dir, file_name)
            # Create subdirectory if needed
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            shutil.move(file_name, target_path)
            print(f"Moved: {file_name} -> {target_path}")
            moved += 1
        else:
            print(f"Skipped (not found): {file_name}")
    return moved

def update_gitignore():
    """Update .gitignore to ignore data files"""
    gitignore_path = '.gitignore'
    
    additions = [
        '',
        '# Generated data files (too large for git)',
        'data/reports_deep_analysis.json',
        'data/reports_analysis_summary.json',
        'data/report_queries.json',
        'data/schema_metadata.json',
        'data/schema_metadata_filtered.json',
        'data/learned_join_patterns.json',
        '',
        '# Keep knowledge base in git (small and needed)',
        '!data/ai_comprehensive_knowledge.json',
        '',
        '# Training data (optional - can be regenerated)',
        'data/SCHEMA_TRAINING*.txt',
    ]
    
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add if not already present
        for line in additions:
            if line and line not in content:
                with open(gitignore_path, 'a', encoding='utf-8') as f:
                    f.write(line + '\n')
                print(f"Added to .gitignore: {line}")
    else:
        # Create .gitignore if it doesn't exist
        with open(gitignore_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(additions))
        print("Created .gitignore")

def update_backend_paths():
    """Update backend paths to point to new data location"""
    backend_kb_path = 'backend/ai_knowledge_loader.py'
    if os.path.exists(backend_kb_path):
        with open(backend_kb_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update path if needed
        if 'ai_comprehensive_knowledge.json' in content:
            new_path = "os.path.join(os.path.dirname(__file__), '..', 'data', 'ai_comprehensive_knowledge.json')"
            content = content.replace(
                "os.path.join(os.path.dirname(__file__), '..', 'ai_comprehensive_knowledge.json')",
                new_path
            )
            
            with open(backend_kb_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print("Updated backend knowledge loader path")

def main():
    print("="*70)
    print("ORGANIZING PROJECT STRUCTURE")
    print("="*70)
    
    create_directories()
    moved = move_files()
    update_gitignore()
    update_backend_paths()
    
    print("\n" + "="*70)
    print(f"SUCCESS! Moved {moved} files")
    print("="*70)
    print("\nProject structure:")
    print("  scripts/  - Training and analysis scripts")
    print("  data/     - JSON data files and training data")
    print("  docs/     - Documentation files")
    print("  backend/  - Backend API code")
    print("  frontend/ - Frontend code")
    print("\nNote: Large data files are now in .gitignore")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

