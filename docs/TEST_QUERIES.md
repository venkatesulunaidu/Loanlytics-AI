# Test Queries for Loanlytics AI

## ✅ Changes Made to Fix UI Issues

### Backend Improvements:
1. **Better SQL Extraction** - Now looks for multiple tool names: `sql_db_query`, `sql_db_query_checker`, `query_sql_db`
2. **Query Filtering** - Filters out `information_schema` queries to show only data queries
3. **Fallback Response** - If agent provides an answer without SQL, it's still displayed
4. **Better Logging** - Shows all intermediate steps for debugging
5. **Helpful Error Messages** - Includes suggestions when queries fail

### Frontend Improvements:
1. **Better Response Handling** - Displays agent output even when SQL can't be extracted
2. **Note Display** - Shows notes from backend when available
3. **Updated Examples** - Multi-schema friendly examples
4. **Long Text Support** - Handles long text in answer fields

---

## 🧪 Test These Queries (In Order)

### Test 1: Table Discovery (Should Work)
```
Show me all tables with loan in the name
```

**Expected Result:**
- SQL query searching information_schema
- List of loan-related tables across schemas
- Should show ~236 loan tables

### Test 2: Simple Count Query (Should Work)
```
How many tables are in the financialForms schema?
```

**Expected Result:**
- SQL: `SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'financialForms'`
- Result: 1266 tables

### Test 3: Direct Schema Query (Should Work)
```
Show me the first 5 rows from financialForms.loan_accounts
```

**Expected Result:**
- SQL: `SELECT * FROM financialForms.loan_accounts LIMIT 5`
- 5 rows of loan account data

### Test 4: Count Loan Accounts (Should Work)
```
How many loan accounts are there in total?
```

**Expected Result:**
- Agent searches for loan_accounts table
- Finds: financialForms.loan_accounts
- SQL: `SELECT COUNT(*) FROM financialForms.loan_accounts`
- Result: Total count

### Test 5: List Schemas (Should Work)
```
List all schemas in the database
```

**Expected Result:**
- SQL: `SELECT DISTINCT table_schema FROM information_schema.tables`
- Result: List of 8 schemas

### Test 6: Jewel Loans (Should Work)
```
Show me the first 10 jewel loans
```

**Expected Result:**
- Agent searches for jewel_loan tables
- Finds: financialForms.jewel_loan_details
- SQL: `SELECT * FROM financialForms.jewel_loan_details LIMIT 10`
- Result: 10 jewel loan records

### Test 7: Overdraft Accounts (Should Work)
```
Count overdraft loan accounts in encoredb schema
```

**Expected Result:**
- SQL: `SELECT COUNT(*) FROM encoredb.loan_od_accounts`
- Result: Total overdraft accounts

### Test 8: Complex Query (May Need Refinement)
```
What are the different loan product types available?
```

**Expected Result:**
- Agent searches for loan_product tables
- Queries multiple loan product tables
- Result: List of loan product types

---

## 🐛 Debugging Tips

### If you see "Cannot answer this question":

**Check Backend Console:**
The backend will now log:
```
[API] Agent returned X intermediate steps
[API] Tool used: tool_name
[API] Found SQL: SELECT ...
[API] Total SQL queries found: X
[API] Final SQL query: ...
```

**What to Look For:**
1. **No tools used?** - Agent didn't try to query at all
2. **Only information_schema queries?** - Agent found tables but didn't query them
3. **SQL found but no results?** - Query syntax error or empty table

**Solutions:**
1. **Be more specific** - Instead of "show loans", say "show me 10 rows from financialForms.loan_accounts"
2. **Ask about table discovery first** - "What loan tables are available?"
3. **Specify the schema** - "Show overdraft loans from encoredb schema"

### Backend Console Output Example:

**Good Query:**
```
[API] Received question: Show me 5 jewel loans
[API] Agent returned 3 intermediate steps
[API] Tool used: sql_db_list_tables
[API] Tool used: sql_db_query
[API] Found SQL: SELECT * FROM financialForms.jewel_loan_details LIMIT 5
[API] Total SQL queries found: 1
[API] Final SQL query: SELECT * FROM financialForms.jewel_loan_details LIMIT 5
```

**Problem Query:**
```
[API] Received question: Show me loans
[API] Agent returned 5 intermediate steps
[API] Tool used: sql_db_list_tables
[API] Tool used: sql_db_query
[API] Found SQL: SELECT table_name FROM information_schema.tables WHERE table_name LIKE '%loan%'
[API] Total SQL queries found: 1
[API] Final SQL query: None
[API] No SQL query found but agent provided output
```
*(This will now show the list of tables as a result)*

---

## 📊 What Each Query Type Does

### Discovery Queries
- "Show me all tables with X in the name"
- "What tables are in the Y schema?"
- "List all schemas"

**Backend Process:**
1. Queries information_schema
2. Returns table/schema names
3. Helpful for exploring data structure

### Data Queries
- "Show me 10 rows from table_name"
- "Count records in table_name"
- "What's the total of column_name?"

**Backend Process:**
1. May search for tables first
2. Executes actual data query
3. Returns structured results

### Complex Queries
- "Show customers with loans above X"
- "What's the average loan amount?"
- "List active loans with customer details"

**Backend Process:**
1. Searches for relevant tables
2. May join multiple tables
3. Applies filters and aggregations
4. Returns results

---

## 🎯 Best Practices

### ✅ DO:
- Start with table discovery queries
- Be specific about what you want
- Use schema.table notation when you know it
- Ask for limited results first (10-100 rows)
- Check backend console for debugging

### ❌ DON'T:
- Ask extremely vague questions ("show data")
- Request all columns from large tables
- Expect complex joins without specifying tables
- Give up after one failed query - refine and retry!

---

## 🔄 Restart Backend to Apply Changes

The backend has been updated with better error handling. Restart it:

```bash
# Stop current backend (Ctrl+C)
# Then restart:
python backend/app.py
```

Or use:
```bash
START.bat
```

---

## ✨ Summary

**What Was Fixed:**
1. ✅ Better SQL extraction from agent responses
2. ✅ Fallback for when agent provides answers without SQL
3. ✅ Improved error messages with suggestions
4. ✅ Frontend now handles more response types
5. ✅ Better debugging information in console
6. ✅ Updated example queries for multi-schema environment

**Your system should now:**
- Show results even when SQL extraction is tricky
- Provide helpful error messages
- Handle multi-schema queries properly
- Display agent answers in the UI

**Try the test queries above to verify everything works!** 🚀

