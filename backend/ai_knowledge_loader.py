"""
AI Knowledge Loader
Loads comprehensive production knowledge to enhance LLM context
"""

import json
import os

class AIKnowledgeBase:
    """Comprehensive knowledge base for AI agent"""
    
    def __init__(self):
        self.knowledge = None
        self.load_knowledge()
    
    def load_knowledge(self):
        """Load comprehensive knowledge"""
        knowledge_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'ai_comprehensive_knowledge.json')
        
        if os.path.exists(knowledge_path):
            with open(knowledge_path, 'r', encoding='utf-8') as f:
                self.knowledge = json.load(f)
        else:
            self.knowledge = {}
    
    def get_table_context(self, table_name):
        """Get context for a specific table"""
        if not self.knowledge:
            return ""
        
        # Normalize table name
        table_lower = table_name.lower()
        
        context_parts = []
        
        # 1. Relationships
        relationships = self.knowledge.get('table_relationships', {})
        if table_lower in relationships:
            rel = relationships[table_lower]
            joins_with = rel.get('joins_with', [])
            if joins_with:
                context_parts.append(f"Commonly joins with: {', '.join(joins_with[:5])}")
                
                # Show example join condition
                conditions = rel.get('common_join_conditions', [])
                if conditions:
                    ex = conditions[0]
                    context_parts.append(f"Example: JOIN {ex.get('with')} ON {ex.get('condition', '')[:100]}")
        
        # 2. Aggregations
        agg_patterns = self.knowledge.get('aggregation_patterns', {})
        if table_lower in agg_patterns:
            agg = agg_patterns[table_lower]
            
            sum_cols = agg.get('sum_columns', [])
            if sum_cols:
                context_parts.append(f"Common SUM: {', '.join(sum_cols[:3])}")
        
        # 3. Filters
        filter_patterns = self.knowledge.get('filter_patterns', {})
        if table_lower in filter_patterns:
            filt = filter_patterns[table_lower]
            
            eq_filters = filt.get('common_equality_filters', [])
            if eq_filters:
                context_parts.append(f"Common filters: {', '.join(eq_filters[:3])}")
        
        return " | ".join(context_parts) if context_parts else ""
    
    def get_query_pattern(self, question_lower):
        """Get relevant query pattern based on question"""
        if not self.knowledge:
            return None
        
        common_queries = self.knowledge.get('common_queries', {})
        
        # Match question to pattern type
        if 'product' in question_lower and ('disbursement' in question_lower or 'disburse' in question_lower):
            patterns = common_queries.get('product_disbursement', [])
            if patterns:
                return self._format_pattern(patterns[0])
        
        if 'customer' in question_lower and ('outstanding' in question_lower or 'loan' in question_lower or 'amount' in question_lower):
            patterns = common_queries.get('customer_loan_amount', [])
            if patterns:
                return self._format_pattern(patterns[0])
        
        if 'branch' in question_lower and 'collection' in question_lower:
            patterns = common_queries.get('branch_collection', [])
            if patterns:
                return self._format_pattern(patterns[0])
        
        if 'outstanding' in question_lower or 'portfolio' in question_lower:
            patterns = common_queries.get('outstanding_report', [])
            if patterns:
                return self._format_pattern(patterns[0])
        
        if 'par' in question_lower or 'npa' in question_lower:
            patterns = common_queries.get('par_npa_report', [])
            if patterns:
                return self._format_pattern(patterns[0])
        
        return None
    
    def _format_pattern(self, pattern):
        """Format a query pattern for LLM context"""
        parts = []
        
        parts.append(f"Similar report: {pattern.get('report', 'N/A')}")
        
        tables = pattern.get('tables', [])
        if tables:
            parts.append(f"Tables used: {', '.join(tables[:5])}")
        
        joins = pattern.get('joins', [])
        if joins:
            join_info = joins[0]
            parts.append(f"Example JOIN: {join_info.get('table')} ON {join_info.get('condition', '')[:100]}")
        
        aggs = pattern.get('aggregations', [])
        if aggs:
            agg_funcs = [a.get('function', '') for a in aggs[:3]]
            parts.append(f"Aggregations: {', '.join(agg_funcs)}")
        
        return " | ".join(parts)
    
    def get_business_rules_context(self):
        """Get critical business rules as context"""
        if not self.knowledge:
            return ""
        
        rules = self.knowledge.get('business_rules', {})
        
        critical_rules = [
            "CRITICAL RULES:",
            "1. Customer→Loan: customers.customer_id = account_holders.customer_id, account_holders.account_id = loan_od_working_registers.account_id",
            "2. Product→Disbursement: loan_od_disbursements JOIN account_profiles ON (tenant_code AND account_id), then use product_code",
            "3. Amounts: Use magnitude columns (amount_magnitude, principal_magnitude, total_disbursed_magnitude)",
            "4. Composite Keys: Many tables use (tenant_code, account_id)",
            "5. Active records: Check is_closed=0 or status='ACTIVE'"
        ]
        
        return "\n".join(critical_rules)
    
    def enhance_question(self, question):
        """Enhance question with relevant context"""
        # Safety check: ensure question is not None
        if not question:
            return question or ""
        
        question_lower = question.lower()
        
        enhancements = []
        
        # Add business rules context
        rules_context = self.get_business_rules_context()
        if rules_context:
            enhancements.append(rules_context)
        
        # Add pattern context if relevant
        pattern = self.get_query_pattern(question_lower)
        if pattern:
            enhancements.append(f"\nSimilar Production Pattern: {pattern}")
        
        # Add specific guidance
        if 'product' in question_lower and 'disbursement' in question_lower:
            enhancements.append("\nGUIDANCE: Use loan_od_disbursements JOIN account_profiles ON (tenant_code AND account_id), GROUP BY product_code")
        
        if 'customer' in question_lower and ('top' in question_lower or 'loan' in question_lower):
            enhancements.append("\nGUIDANCE: Use 3-table join: customer → account_holders → loan_od_working_registers")
        
        if enhancements:
            return question + "\n\n" + "\n".join(enhancements)
        
        return question

# Global instance
_kb_instance = None

def get_knowledge_base():
    """Get singleton knowledge base instance"""
    global _kb_instance
    if _kb_instance is None:
        _kb_instance = AIKnowledgeBase()
    return _kb_instance

