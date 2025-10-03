1. Create a virtualenv (recommended):
python -m venv venv
source venv/bin/activate # or venv\Scripts\activate on Windows


2. Install dependencies:
pip install -r requirements.txt


3. Run the app:
python app.py


4. Open your browser at http://127.0.0.1:5000


Notes:
- Upload CSVs must contain at least 'Date' and 'Close' columns.
- You can provide up to two tickers / two CSVs to compare (optional).
- The app saves a generated plot to static/images/plot.png