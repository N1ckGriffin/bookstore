# Bookstore Project

## Quick Start

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set database environment variable (example for MySQL):
   ```
   # PowerShell
   $env:DATABASE_URL = "mysql+pymysql://user:pass@localhost:3306/bookstore"
   ```

3. Start the backend:
   ```
   python -u -m backend.app
   ```

4. In a new terminal, start the GUI:
   ```
   python -m frontend
   ```

## Notes
- The backend runs on http://127.0.0.1:5000 by default
- For remote backend, set API_BASE_URL environment variable in the GUI terminal
