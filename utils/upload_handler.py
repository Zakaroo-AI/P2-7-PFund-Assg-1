import os, json
from werkzeug.utils import secure_filename
import pandas as pd

# ALLOWED_EXTENSIONS = {'csv', 'xls', 'xlsx', 'json'}
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'json'}

def validate_csv_columns(df, required_cols=("Date", "Close")):
    """
    Validate that a CSV file contains the required columns.

    Args:
        df (pd.DataFrame):      User's uploaded dataframe
        required_cols (tuple):  Required column names (case-insensitive)

    Returns:
        bool:                   True if columns are missing
        missing_cols (list):    List of all missing columns, if any
    """
    # standardise to lowercase
    df_cols = [c.lower() for c in df.columns]
    missing_cols = [col for col in required_cols if col.lower() not in df_cols]
    
    return bool(missing_cols), missing_cols

def upload_handling(uploaded, filepath):
    if uploaded is not None:
        # quick sanitising of filename
        filename = secure_filename(uploaded.filename)
    else:
        filename = filepath
    # extracts .extension from filename, then remove .
    label, extension = os.path.splitext(filename)
    extension = extension.lstrip('.')

    if extension not in ALLOWED_EXTENSIONS:
        if extension == 'xls':
            e = 'Try converting xls file into xlsx'
        else:
            e = f'Invalid file type: {extension}.\nAllowed types: {', '.join(ALLOWED_EXTENSIONS)}'
        raise ValueError(e)

    try:
        uploaded.save(filepath) # into designated uploads folder
    except Exception as e:
        pass

    if extension == 'csv':
        df = pd.read_csv(filepath)
    elif extension in ['xls', 'xlsx']:
        try:
            df = pd.read_excel(filepath)
        except ImportError:
            raise ImportError(f'Try converting {extension} file into csv or json')
    elif extension == 'json':
        with open(filepath, 'r') as file:
            data = json.load(file)
        # handles both JSON array of objects and single object
        df = pd.DataFrame(data) if isinstance(data, list) else pd.DataFrame([data])
    
    isMissing, missing_cols = validate_csv_columns(df)
    if isMissing:
        raise ValueError(f"CSV missing required column: {missing_cols}")

    # converts dates to datetime objects, invalid dates become NaT
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce', utc=True)
    df.sort_values("Date", inplace=True)

    return df, label

