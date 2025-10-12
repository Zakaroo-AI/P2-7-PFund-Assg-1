from pathlib import Path
folder_path = Path("uploads")
file_paths = list(folder_path.glob("*.csv"))

print(file_paths)