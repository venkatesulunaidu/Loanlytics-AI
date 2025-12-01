# Schema Training Guide for Loanlytics AI

## Overview
This system allows you to train the AI on your database schema by providing table relationships and business context. This ensures **accurate** and **fast** query generation.

## Step 1: Collect Schema Metadata

Run this command to collect all table information including indexes:

```bash
python collect_schema_metadata.py
```

This will create two files:
- `schema_metadata.json` - Complete technical metadata (columns, indexes, foreign keys)
- `SCHEMA_TRAINING.txt` - Template for you to fill in relationships

## Step 2: Fill in SCHEMA_TRAINING.txt

Open `SCHEMA_TRAINING.txt` and for **key tables** (the ones you query most), fill in:

### What to Fill:

1. **DESCRIPTION**: What data does this table hold?
   - Example: "Stores loan disbursement transactions with amounts and dates"

2. **BUSINESS MEANING**: What business entity?
   - Example: "Loan Disbursements", "Customer Information", "Product Catalog"

3. **COMMON JOINS**: How does it join with other tables?
   - Example: `JOIN account_profiles ON loan_od_disbursements.tenant_code = account_profiles.tenant_code AND loan_od_disbursements.account_id = account_profiles.account_id`

### Priority Tables to Train:

Focus on these first:
- ✅ `customers` - Customer master data
- ✅ `account_holders` - Links customers to accounts
- ✅ `loan_od_working_registers` - Loan balances and amounts
- ✅ `loan_od_disbursements` - Disbursement transactions
- ✅ `account_profiles` - Account details with product_code
- ✅ `loan_od_profiles` - Loan product information
- ✅ `loan_od_products` - Product master
- ✅ `branches` or branch-related tables
- ✅ Any other frequently queried tables

## Step 3: Update schema_metadata.json

After filling `SCHEMA_TRAINING.txt`, manually copy the information into `schema_metadata.json` for the tables you trained:

```json
{
  "encoredb.loan_od_disbursements": {
    "description": "Stores loan disbursement transactions",
    "business_meaning": "Loan Disbursements",
    "common_joins": [
      "JOIN account_profiles ON loan_od_disbursements.tenant_code = account_profiles.tenant_code AND loan_od_disbursements.account_id = account_profiles.account_id"
    ]
  }
}
```

## Step 4: Test the System

The AI will now use this knowledge to generate accurate queries!

### Example Queries That Will Work:

- "Show me product wise total disbursement amount"
  - ✅ Will properly join `loan_od_disbursements` with `account_profiles`
  - ✅ Will use indexes on `tenant_code` and `account_id`
  - ✅ Will GROUP BY `product_code`

- "Top 10 customers by loan amount"
  - ✅ Will join customers → account_holders → loan_od_working_registers
  - ✅ Will use customer_id and account_id indexes

## Benefits

1. **⚡ Fast Queries** - Uses proper indexes automatically
2. **🎯 Accurate Results** - Correct joins based on your training
3. **🔄 Dynamic** - Adapts to schema changes
4. **📚 Self-Documenting** - Creates documentation of your schema

## Example Training Entry

```
TABLE: encoredb.loan_od_disbursements
Indexes: tenant_code, account_id, disbursement_date

DESCRIPTION:
  Stores all loan disbursement transactions including amount, date, and account details.
  Each row represents a single disbursement event.

BUSINESS MEANING:
  Loan Disbursements / Payout Transactions

COMMON JOINS:
  JOIN account_profiles 
    ON loan_od_disbursements.tenant_code = account_profiles.tenant_code 
    AND loan_od_disbursements.account_id = account_profiles.account_id
  
  JOIN loan_od_profiles
    ON loan_od_disbursements.account_id = loan_od_profiles.account_id
```

## Need Help?

The system will still work without training but may:
- Generate slower queries (no index optimization)
- Use incorrect joins
- Miss important relationships

**Train at least 10-15 key tables for best results!**

