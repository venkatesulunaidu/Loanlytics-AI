# Loanlytics AI - Query Examples

## What Was Fixed

### 1. ✅ Unicode Encoding Error
- **Issue**: Windows console couldn't display emoji characters
- **Fix**: Added UTF-8 encoding support and removed emojis from startup messages

### 2. ✅ "Cannot Answer Question" Error  
- **Issue**: Agent couldn't find tables across multiple schemas
- **Fix**: Enhanced agent with:
  - Better multi-schema awareness
  - Instructions to search information_schema first
  - Examples of schema.table syntax
  - Increased iterations (10 → 15) for complex queries

### 3. ✅ Schema Discovery
- **Fix**: Agent now automatically searches for relevant tables before querying

---

## How to Use

### Start the Backend
```bash
python backend/app.py
```

Or use:
```bash
START.bat
```

### Access the Frontend
Open `frontend/index.html` in your browser or visit:
- Backend API: http://localhost:5000
- Health Check: http://localhost:5000/api/health

---

## Example Queries

### 1. **Find Loan Tables**
```
Show me all tables related to loans
```

**What the AI does:**
1. Searches information_schema for tables with 'loan' in the name
2. Returns list of loan tables across all schemas

### 2. **Count Loans**
```
How many loan accounts are there in total?
```

**What the AI does:**
1. Searches for loan_accounts tables
2. Finds: financialForms.loan_accounts
3. Runs: `SELECT COUNT(*) FROM financialForms.loan_accounts`

### 3. **Loan Details**
```
Show me the first 10 active loans with their customer details
```

**What the AI does:**
1. Searches for relevant loan and customer tables
2. Joins tables across schemas if needed
3. Filters for active status
4. Returns 10 results

### 4. **Cross-Schema Query**
```
What's the total outstanding loan amount across all loan types?
```

**What the AI does:**
1. Searches for loan tables with amount/outstanding fields
2. Queries multiple schemas: encoredb, financialForms, etc.
3. Aggregates results

### 5. **Specific Schema Query**
```
Show me overdraft loans from the encoredb schema
```

**What the AI does:**
1. Looks in encoredb schema specifically
2. Finds: encoredb.loan_od_accounts
3. Returns overdraft loan data

---

## Your Database Structure

### Available Schemas (8 total):
- **financialForms** - 192 loan tables (main)
- **encoredb** - 28 loan tables (overdraft)
- **bi** - 14 loan tables (reporting)
- **ams** - 2 loan tables
- **datawarehouse** - Data warehouse
- **forms_management** - Form management
- **kyc_service** - KYC data
- **payment_portal** - Payment data

### Total: 236+ loan-related tables!

---

## Tips for Better Results

### ✅ DO:
- Ask specific questions: "How many jewel loans are active?"
- Mention the domain: "Show customer loan history"
- Be patient: Complex queries take 10-30 seconds
- Ask about totals, counts, and summaries

### ❌ DON'T:
- Ask vague questions: "Show me data"
- Request non-SELECT operations (no INSERT/UPDATE/DELETE)
- Ask about tables that don't exist
- Expect instant results for complex queries

---

## Troubleshooting

### If you get "Cannot answer this question":

1. **Check if the question is about available data**
   - Try: "What loan tables are available?"
   - This helps you understand what data exists

2. **Be more specific**
   - Instead of: "Show loans"
   - Try: "Show active loans from loan_accounts table"

3. **Check the backend logs**
   - The console shows what SQL queries the AI is trying
   - Look for errors or missing tables

4. **Simplify the question**
   - Break complex questions into smaller parts
   - Ask step by step

### If the backend won't start:

1. **Check .env file**
   - Ensure all values are correct
   - Run: `python test_db_connection.py`

2. **Check port 5000**
   - Make sure nothing else is using it
   - Or change the port in backend/app.py

3. **Check dependencies**
   - Run: `pip install -r requirements.txt`

---

## API Endpoints

### `/api/health` - Health Check
```bash
curl http://localhost:5000/api/health
```

### `/api/tables` - List Tables
```bash
curl http://localhost:5000/api/tables
```

### `/api/query` - Natural Language Query
```bash
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "How many loans are active?"}'
```

### `/api/execute` - Direct SQL Query
```bash
curl -X POST http://localhost:5000/api/execute \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT COUNT(*) FROM financialForms.loan_accounts LIMIT 10"}'
```

---

## Need Help?

1. Check backend console logs for detailed error messages
2. Try simpler queries first
3. Use the test scripts:
   - `python test_db_connection.py` - Test database connection
   - `python test_langchain.py` - Test AI agent

---

**Your system is now fully configured for multi-schema querying! 🚀**

