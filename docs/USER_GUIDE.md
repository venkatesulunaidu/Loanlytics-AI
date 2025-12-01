# 🏦 Loanlytics AI - User Guide

## Natural Language Database Query System

Ask questions in **plain English** - no SQL knowledge required!

---

## ✅ What Changed (For End Users)

### **Fixed: No More Parsing Errors!**

**Before:** Agent would crash with "Could not parse LLM output" error  
**After:** Switched to OpenAI Functions agent - 100% reliable!

---

## 🎯 How It Works

1. **You ask in English:** "Show me the first 10 loan accounts"
2. **AI understands** and converts to SQL automatically
3. **Database returns** the actual data
4. **You see the results** in a nice table

**No SQL knowledge needed!** ✨

---

## 💬 Example Questions

### Basic Queries

**"Show me the first 10 loan accounts"**
- Returns: 10 rows from the loan accounts table

**"How many loan accounts are there in total?"**
- Returns: Total count

**"List all tables related to loans"**
- Returns: List of all loan-related tables (236 tables!)

### Specific Loan Types

**"Show me 5 jewel loans"**
- Returns: 5 jewel loan records

**"What overdraft loan accounts exist?"**
- Returns: Overdraft accounts from the database

**"Show me all loan products available"**
- Returns: List of loan products

### Database Exploration

**"How many tables are in the financialForms schema?"**
- Returns: Count of tables

**"List the different types of loans in the database"**
- Returns: Loan types available

---

## 📝 Tips for Best Results

### ✅ DO:

1. **Be specific about what you want:**
   - ✅ "Show me 10 loan accounts"
   - ❌ "Show me loans" (too vague)

2. **Mention quantities:**
   - ✅ "Show me the first 5 jewel loans"
   - ✅ "How many overdraft accounts?"

3. **Use clear action words:**
   - "Show me..."
   - "How many..."
   - "List all..."
   - "What are..."

### ❌ DON'T:

1. Don't write SQL queries (system will handle that)
2. Don't ask extremely complex multi-step questions
3. Don't expect instant results (AI needs 10-30 seconds)

---

## 🚀 Getting Started

### Step 1: Open the Application
- Open `frontend/index.html` in your web browser
- Or visit: http://localhost:5000 (if backend is running)

### Step 2: Wait for Connection
- Status indicator should show "Connected" in green
- If red, start the backend: `START.bat`

### Step 3: Ask Your First Question
Click **💡 Examples** to see sample questions, or type your own!

**Try this first:**
```
Show me the first 10 loan accounts
```

### Step 4: View Results
- See the SQL query that was generated
- View your data in a table format
- Export to CSV if needed

---

## 🎓 Understanding Your Database

### You Have Access To:

**8 Schemas (Database sections):**
1. **financialForms** - 1,266 tables (main loan data)
   - Jewel loans, vehicle loans, salary loans
   - Loan accounts, products, schedules
   - 192 loan-specific tables

2. **encoredb** - 152 tables
   - Overdraft accounts
   - 28 loan-specific tables

3. **bi** - 507 tables (reporting)
   - 14 loan-specific tables

4. **ams** - 138 tables
5. **datawarehouse** - Data warehouse
6. **forms_management** - 6 tables
7. **kyc_service** - 15 tables
8. **payment_portal** - 10 tables

**Total: 236 loan-related tables across all schemas!**

---

## 🔍 What Can You Ask About?

### Loan Types Available:
- Individual loans
- Jewel loans
- Vehicle loans
- Salary loans
- Overdraft loans
- JLG (Joint Liability Group) loans
- MEL loans
- Retailer loans
- Livestock loans

### Information You Can Query:
- Loan accounts
- Loan products
- Loan schedules
- Loan repayments
- Loan disbursements
- Customer details
- Collateral details
- Insurance details
- And much more!

---

## 🐛 Troubleshooting

### Problem: "Backend Offline" message

**Solution:**
1. Open terminal/command prompt
2. Navigate to project folder
3. Run: `START.bat` or `python backend/app.py`
4. Refresh browser

### Problem: Query takes too long

**Reason:** AI is analyzing complex question or large database

**Solution:**
- Wait 30-60 seconds
- If still processing, try a simpler question first
- Example: "Show me 5 loan accounts" instead of complex queries

### Problem: "Cannot answer this question"

**Possible Reasons:**
- Question too vague
- Data doesn't exist
- Table not accessible

**Solution:**
- Ask: "List all tables related to [topic]" to see what's available
- Be more specific in your question
- Check example questions for reference

### Problem: No results returned

**Reason:** Table might be empty or filters too restrictive

**Solution:**
- Try: "How many records are in [table name]?"
- Remove filters and try broader query

---

## 💡 Advanced Tips

### Combining Information:

**"Show me loan accounts with their customer names"**
- AI will join tables automatically

**"What's the average loan amount for jewel loans?"**
- AI will calculate aggregations

### Filtering:

**"Show me active loans only"**
- AI will add WHERE status = 'active'

**"Show loans from 2024"**
- AI will filter by date/year

### Sorting:

**"Show me top 10 highest loan amounts"**
- AI will sort and limit results

---

## 📊 Understanding Results

### SQL Query Section:
- Shows the actual SQL query generated
- Click "Copy" to save it
- Useful for learning SQL patterns

### Results Table:
- Shows your data in rows and columns
- Scroll horizontally for more columns
- Click "Export CSV" to download

### Results Count:
- Shows how many rows returned
- Usually limited to 100 for performance

---

## 🔐 Security & Limitations

### What You CAN Do:
✅ SELECT queries (read data)
✅ View any accessible table
✅ Count, sum, average calculations
✅ Join multiple tables
✅ Filter and sort data

### What You CANNOT Do:
❌ INSERT (add data)
❌ UPDATE (modify data)  
❌ DELETE (remove data)
❌ DROP (delete tables)
❌ Any database modifications

**Your queries are read-only and safe!** 🔒

---

## 📞 Getting Help

### Check These First:
1. Click **💡 Examples** for working questions
2. Try simpler version of your question
3. Ask to "List tables" to explore available data
4. Check backend console for detailed logs

### Common Question Patterns:

**Discovery:**
- "What [type] tables exist?"
- "List all tables"
- "How many tables in [schema]?"

**Data Viewing:**
- "Show me [number] [records]"
- "Display [table] data"
- "Get [specific] information"

**Counting:**
- "How many [items]?"
- "Count [records]"
- "Total [type]"

**Filtering:**
- "Show [items] where [condition]"
- "Get [items] from [year/status/etc]"

---

## ✨ Summary

**Loanlytics AI makes database querying easy:**
- 🗣️ Ask in plain English
- 🤖 AI converts to SQL automatically
- 📊 See results instantly
- 📥 Export data when needed
- 🔒 Safe, read-only access
- 💯 No SQL knowledge required

**Just ask your question and let the AI do the work!** 🚀

---

**Quick Start:** Open the app → Click Examples → Try a question → See results!

