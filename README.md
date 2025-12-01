# 🏦 Loanlytics AI

**Natural Language Database Query System with Web Interface**

Ask questions about your database in plain English and get instant, accurate results powered by AI.

## ✨ Features

- 🤖 **AI-Powered**: Uses LangChain + OpenAI for natural language to SQL conversion
- 🌐 **Web Interface**: Beautiful, modern UI for easy interaction
- 📊 **Smart Results**: Displays data in clean, exportable tables
- 🔒 **Safe Queries**: Only executes SELECT queries (read-only)
- 🚀 **Large Database Support**: Optimized for databases with 1000+ tables
- 📤 **Export**: Download results as CSV
- 💡 **Examples**: Built-in example questions to get started

## 🏗️ Architecture

```
├── backend/          → Flask API with LangChain
│   ├── app.py        → Main API server
│   └── ai_knowledge_loader.py → AI knowledge base loader
├── frontend/         → Web UI
│   ├── index.html    → Main page
│   ├── style.css     → Styling
│   └── script.js     → Frontend logic
├── scripts/          → Training and analysis scripts
│   ├── deep_analysis_reports.py → Deep report analysis
│   ├── comprehensive_ai_training.py → AI training
│   └── ...           → Other training scripts
├── data/             → JSON data files and training data
│   └── ai_comprehensive_knowledge.json → AI knowledge base
├── docs/             → Documentation
│   ├── AI_AGENT_GUIDE.txt → AI training guide
│   └── ...           → Other documentation
├── requirements.txt  → Python dependencies
└── .env             → Configuration (you create this)
```

## 🚀 Quick Start

### 1. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 2. Configure

```powershell
Copy-Item .env.example .env
notepad .env
```

Fill in your credentials:

```ini
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=yourpassword
MYSQL_DATABASE=yourdatabase
OPENAI_API_KEY=sk-xxxxxxxxxxxxx
OPENAI_MODEL=gpt-4-turbo-preview
```

**Get OpenAI API Key**: https://platform.openai.com/api-keys

### 3. Run Backend

```powershell
python backend/app.py
```

Backend will start on: `http://localhost:5000`

### 4. Open Frontend

Open `frontend/index.html` in your web browser

Or use a simple HTTP server:

```powershell
# If you have Python:
cd frontend
python -m http.server 8000
```

Then visit: `http://localhost:8000`

## 💬 How to Use

1. **Open the web interface** (frontend/index.html)
2. **Type your question** in plain English
3. **Click "Ask Question"**
4. **View results** - SQL query and data table
5. **Export** if needed

### Example Questions

- "Show me top 10 customers with highest loan amounts"
- "How many loans were disbursed in 2023?"
- "What is the average interest rate?"
- "List all active personal loans"
- "Show customers from Mumbai"

## 🎯 API Endpoints

### Backend API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Check backend status |
| `/api/tables` | GET | List all tables |
| `/api/table/<name>` | GET | Get table schema |
| `/api/query` | POST | Process natural language query |
| `/api/execute` | POST | Execute custom SQL (SELECT only, validated) |

### Custom SQL Query Endpoint

The `/api/execute` endpoint allows advanced users to write and execute custom SQL queries directly.

**Security Features:**
- ✅ Only SELECT queries allowed
- ✅ Blocks INSERT, UPDATE, DELETE, DROP, ALTER, etc.
- ✅ Prevents SQL injection attempts
- ✅ Validates query structure

**Example Request:**
```json
POST /api/execute
{
  "sql": "SELECT product_code, SUM(amount_magnitude) FROM encoredb.loan_od_disbursements GROUP BY product_code"
}
```

**Example Response:**
```json
{
  "success": true,
  "sql": "SELECT product_code, SUM(amount_magnitude)...",
  "results": [...],
  "count": 10
}
```

**Error Response (for invalid queries):**
```json
{
  "success": false,
  "error": "Operation 'DELETE' is not allowed. Only SELECT queries are permitted.",
  "sql": "DELETE FROM table...",
  "results": [],
  "count": 0
}
```

## 📋 Requirements

- **Python 3.8+**
- **MySQL Database** (existing, with your data)
- **OpenAI API Key** (with credits)
- **Modern web browser** (Chrome, Firefox, Edge, Safari)

## 🐛 Troubleshooting

### Backend won't start

- Check `.env` file exists and has correct credentials
- Verify MySQL is running
- Ensure OpenAI API key is valid

### Frontend shows "Backend Offline"

- Make sure backend is running (`python backend/app.py`)
- Check backend URL in `frontend/script.js` (default: `localhost:5000`)

### "Token limit exceeded" error

- Ensure `.env` has `OPENAI_MODEL=gpt-4-turbo-preview`
- This model supports 128k tokens (handles large databases)

### Can't connect to database

- Verify MySQL credentials in `.env`
- Check database exists and is accessible
- Ensure MySQL server is running

## 🔧 Advanced Configuration

### Change Backend Port

Edit `backend/app.py`, line:
```python
app.run(debug=True, host='0.0.0.0', port=5000)
```

### Change AI Model

In `.env`:
- `gpt-4-turbo-preview` - Best for large databases (128k tokens)
- `gpt-3.5-turbo-16k` - Faster, cheaper (16k tokens)
- `gpt-4` - Original GPT-4 (8k tokens, may fail on large schemas)

### Enable HTTPS

For production, use a reverse proxy like Nginx or deploy to a platform like Heroku, Render, or AWS.

## 📊 Screenshots

**Main Interface**
- Clean, modern design
- Question input with examples
- Real-time status indicator

**Results Display**
- Generated SQL query with syntax highlighting
- Data table with export functionality
- Row count and query statistics

## 🚢 Deployment

### Deploy Backend

Options:
- **Heroku**: `heroku create && git push heroku main`
- **Render**: Connect GitHub repo
- **AWS/Azure**: Use EC2/App Service

### Deploy Frontend

Options:
- **GitHub Pages**: Push to gh-pages branch
- **Netlify**: Drag & drop frontend folder
- **Vercel**: Import repository

Update `API_URL` in `frontend/script.js` to your backend URL.

## 🛡️ Security Notes

- Backend only allows SELECT queries (no data modification)
- Use environment variables for sensitive data
- Never commit `.env` file
- Consider adding authentication for production
- Use HTTPS in production

## 📝 License

For internal/educational use.

## 🙏 Credits

Built with:
- **LangChain** - AI framework
- **OpenAI** - GPT models
- **Flask** - Backend framework
- **MySQL** - Database

---

**Ready to query your database with AI!** 🚀

For questions or issues, check the troubleshooting section above.

