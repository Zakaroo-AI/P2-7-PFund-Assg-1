import os
import pandas as pd

ALLOWED_EXTENSIONS = {"csv"}

def allowed_file(filename: str) -> bool:
    """
    Check if the uploaded file has an allowed extension.

    Args:
        filename (str): The uploaded file's name

    Returns:
        bool: True if extension is allowed, else False
    """
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_csv_columns(filepath: str, required_cols=("Date", "Close")) -> bool:
    """
    Validate that a CSV file contains the required columns.

    Args:
        filepath (str): Path to the CSV file
        required_cols (tuple): Required column names (case-insensitive)

    Returns:
        bool: True if valid, else raises ValueError
    """
    try:
        df = pd.read_csv(filepath, nrows=1)  # read only first row for speed
    except Exception as e:
        raise ValueError(f"Could not read CSV file: {e}")

    file_cols = [c.lower() for c in df.columns]
    for col in required_cols:
        if col.lower() not in file_cols:
            raise ValueError(f"CSV missing required column: {col}")

    return True
