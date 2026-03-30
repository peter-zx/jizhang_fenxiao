@echo off
cd /d "%~dp0"
call venv\Scripts\activate.bat
python backend\init_data.py
streamlit run backend\app.py
