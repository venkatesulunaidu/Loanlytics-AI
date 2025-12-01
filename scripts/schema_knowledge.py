"""
Schema Knowledge System for Loanlytics AI
Uses trained metadata to generate accurate queries with proper indexes
"""

import json
import os
from typing import Dict, List, Optional


class SchemaKnowledge:
    """Manages schema metadata and relationships"""
    
    def __init__(self, metadata_file='schema_metadata.json'):
        self.metadata = {}
        self.load_metadata(metadata_file)
    
    def load_metadata(self, filepath):
        """Load schema metadata from JSON"""
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
            print(f"[SCHEMA] Loaded metadata for {len(self.metadata)} tables")
        else:
            print(f"[SCHEMA] Warning: {filepath} not found. Run collect_schema_metadata.py first.")
    
    def get_table_info(self, table_name: str) -> Optional[Dict]:
        """Get full metadata for a table"""
        # Try with schema prefix
        if table_name in self.metadata:
            return self.metadata[table_name]
        
        # Try without schema (search all schemas)
        for full_name, info in self.metadata.items():
            if info['table'] == table_name:
                return info
        
        return None
    
    def get_indexes(self, table_name: str) -> List[Dict]:
        """Get all indexes for a table"""
        info = self.get_table_info(table_name)
        return info['indexes'] if info else []
    
    def get_best_index(self, table_name: str, columns: List[str]) -> Optional[Dict]:
        """Find the best index for given columns"""
        indexes = self.get_indexes(table_name)
        
        # Prefer exact match
        for idx in indexes:
            if set(idx['columns']) == set(columns):
                return idx
        
        # Find index that starts with these columns
        for idx in indexes:
            idx_cols = idx['columns']
            if len(columns) <= len(idx_cols):
                if all(columns[i] == idx_cols[i] for i in range(len(columns))):
                    return idx
        
        # Find index that contains these columns
        for idx in indexes:
            if all(col in idx['columns'] for col in columns):
                return idx
        
        return None
    
    def get_join_info(self, table1: str, table2: str) -> Optional[Dict]:
        """Get join relationship between two tables"""
        info1 = self.get_table_info(table1)
        info2 = self.get_table_info(table2)
        
        if not info1 or not info2:
            return None
        
        # Check foreign keys
        for fk in info1.get('foreign_keys', []):
            if table2 in fk['references']:
                return {
                    'type': 'foreign_key',
                    'from_column': fk['column'],
                    'to_table': table2,
                    'to_column': fk['references'].split('.')[-1]
                }
        
        # Check common joins from training data
        for join in info1.get('common_joins', []):
            if table2 in join:
                return {'type': 'trained', 'join': join}
        
        # Try to infer from column names
        cols1 = {col['name'] for col in info1['columns']}
        cols2 = {col['name'] for col in info2['columns']}
        
        common_cols = cols1 & cols2
        if common_cols:
            # Prefer columns with 'id' or 'code'
            for col in common_cols:
                if 'id' in col.lower() or 'code' in col.lower():
                    return {
                        'type': 'inferred',
                        'column': col
                    }
        
        return None
    
    def build_query_with_indexes(self, tables: List[str], join_conditions: List[str], 
                                  where_conditions: List[str], select_columns: List[str],
                                  group_by: Optional[List[str]] = None,
                                  order_by: Optional[str] = None,
                                  limit: Optional[int] = None) -> str:
        """Build optimized query using index information"""
        
        # Build SELECT clause
        query = f"SELECT {', '.join(select_columns)}\n"
        
        # Build FROM clause
        query += f"FROM {tables[0]}\n"
        
        # Build JOINs with USE INDEX hints
        for i, join_cond in enumerate(join_conditions):
            if i + 1 < len(tables):
                # Extract columns used in join
                # Simple parsing - can be enhanced
                query += f"INNER JOIN {tables[i+1]}\n"
                query += f"  ON {join_cond}\n"
        
        # WHERE clause
        if where_conditions:
            query += f"WHERE {' AND '.join(where_conditions)}\n"
        
        # GROUP BY
        if group_by:
            query += f"GROUP BY {', '.join(group_by)}\n"
        
        # ORDER BY
        if order_by:
            query += f"ORDER BY {order_by}\n"
        
        # LIMIT
        if limit:
            query += f"LIMIT {limit}\n"
        
        return query.strip()
    
    def get_common_patterns(self) -> Dict[str, str]:
        """Get common query patterns based on trained data"""
        patterns = {}
        
        # Load patterns from metadata
        for table_name, info in self.metadata.items():
            if info.get('common_joins'):
                patterns[table_name] = info['common_joins']
        
        return patterns
    
    def generate_schema_context(self) -> str:
        """Generate concise schema context for LLM"""
        context = "KEY TABLE RELATIONSHIPS:\n\n"
        
        important_tables = [
            'customers', 'account_holders', 'loan_od_working_registers',
            'loan_od_disbursements', 'account_profiles', 'loan_od_profiles'
        ]
        
        for table in important_tables:
            info = self.get_table_info(table)
            if info:
                schema = info['schema']
                full_name = f"{schema}.{table}"
                context += f"{full_name}:\n"
                
                # Key columns with indexes
                indexed_cols = set()
                for idx in info.get('indexes', []):
                    indexed_cols.update(idx['columns'])
                
                key_cols = [col for col in info['columns'] 
                           if col['key'] or col['name'] in indexed_cols][:10]
                
                for col in key_cols:
                    idx_marker = "🔑" if col['name'] in indexed_cols else ""
                    context += f"  - {col['name']} {idx_marker}\n"
                
                # Foreign keys
                if info.get('foreign_keys'):
                    context += "  Foreign Keys:\n"
                    for fk in info['foreign_keys'][:3]:
                        context += f"    {fk['column']} → {fk['references']}\n"
                
                # Common joins from training
                if info.get('common_joins'):
                    context += "  Common Joins:\n"
                    for join in info['common_joins'][:2]:
                        context += f"    {join}\n"
                
                context += "\n"
        
        return context


# Global instance
_schema_knowledge = None

def get_schema_knowledge() -> SchemaKnowledge:
    """Get or create schema knowledge instance"""
    global _schema_knowledge
    if _schema_knowledge is None:
        _schema_knowledge = SchemaKnowledge()
    return _schema_knowledge

