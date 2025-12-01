"""
Test database connection
Run this to verify your .env credentials are correct
"""

import os
import sys
from dotenv import load_dotenv
import mysql.connector

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

print("\n" + "="*70)
print("  Testing Database Connection")
print("="*70 + "\n")

# Show what we're trying to connect to (hide password)
host = os.getenv('MYSQL_HOST', 'NOT_SET')
port = os.getenv('MYSQL_PORT', '3306')
user = os.getenv('MYSQL_USER', 'NOT_SET')
password = os.getenv('MYSQL_PASSWORD', 'NOT_SET')
database = os.getenv('MYSQL_DATABASE', 'NOT_SET')

print(f"Host:     {host}")
print(f"Port:     {port}")
print(f"User:     {user}")
print(f"Password: {'*' * len(password) if password != 'NOT_SET' else 'NOT_SET'}")
print(f"Database: {database}")
print()

# Check if values are set
if 'NOT_SET' in [host, user, password, database]:
    print("[ERROR] Some values are not set in .env file!")
    print("\nPlease edit .env file with your actual credentials:")
    print("  MYSQL_HOST=localhost")
    print("  MYSQL_PORT=3306")
    print("  MYSQL_USER=your_username")
    print("  MYSQL_PASSWORD=your_password")
    print("  MYSQL_DATABASE=your_database")
    print()
    exit(1)

# Try to connect
print("Attempting connection...")
try:
    conn = mysql.connector.connect(
        host=host,
        port=int(port),
        user=user,
        password=password,
        database=database,
        connection_timeout=10
    )
    
    print("[SUCCESS] Connection successful!")
    print()
    
    # Get database info
    cursor = conn.cursor()
    cursor.execute("SELECT DATABASE()")
    db_name = cursor.fetchone()[0]
    print(f"[SUCCESS] Connected to database: {db_name}")
    
    # Get table count
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    print(f"[SUCCESS] Found {len(tables)} tables")
    
    if tables:
        print(f"\nFirst 10 tables:")
        for i, table in enumerate(tables[:10], 1):
            print(f"  {i}. {table[0]}")
    
    cursor.close()
    conn.close()
    
    print()
    print("="*70)
    print("  [SUCCESS] Database configuration is correct!")
    print("  You can now run: python backend/app.py")
    print("="*70 + "\n")
    
except mysql.connector.Error as e:
    print(f"[ERROR] Connection failed!")
    print(f"\nError: {e}")
    print()
    print("Common issues:")
    print("  1. Wrong host/port - Check if MySQL server is running")
    print("  2. Wrong credentials - Verify username/password")
    print("  3. Database doesn't exist - Check database name")
    print("  4. Firewall blocking - Check network/VPN connection")
    print("  5. Wrong port - Try port 3306 (default)")
    print()
    exit(1)

except Exception as e:
    print(f"[ERROR] Unexpected error: {e}")
    exit(1)

