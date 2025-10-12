import pytest
import pandas as pd
from pathlib import Path
from utils.upload_handler import upload_handling


@pytest.mark.parametrize("filename", [
    "sample.csv",
    "sample.xlsx", 
    "sample.json"
])
def test_upload_handling_file_types(filename):

    """Test upload_handling with different file types using parameterization."""
    test_data_dir = Path(__file__).parent.parent / "tests_data"
    file_path = test_data_dir / filename
    
    result, _ = upload_handling(None, str(file_path))
    
    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0