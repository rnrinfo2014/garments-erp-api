# Garments ERP Backend API

This is a backend API for the Garments ERP system built with FastAPI, using a Python virtual environment and PostgreSQL database.

## Setup Instructions

1. **Create and activate a virtual environment**
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```

2. **Install dependencies**
   ```powershell
   pip install fastapi uvicorn psycopg2-binary sqlalchemy python-dotenv
   ```

3. **Configure PostgreSQL connection**
   - Create a `.env` file with your database credentials:
     ```env
     DATABASE_URL=postgresql://username:password@localhost:5432/garments_erp
     ```

4. **Run the server**
   ```powershell
   uvicorn main:app --reload
   ```

## Project Structure
- `main.py` — FastAPI app entry point
- `models/` — SQLAlchemy models
- `routes/` — API routes
- `database.py` — Database connection
- `.env` — Environment variables

Replace placeholders with your actual database credentials.
