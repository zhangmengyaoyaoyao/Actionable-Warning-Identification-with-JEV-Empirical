import os
import pandas as pd

def find_error_files(root_dir="results"):
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".xlsx"):
                file_path = os.path.join(subdir, file)
                try:
                    df = pd.read_excel(file_path, engine="openpyxl")
                    if "Status" in df.columns and "File Name" in df.columns:
                        error_rows = df[df["Status"] == "error"]
                        for file_name in error_rows["File Name"].dropna():
                            print(f"File: {file_path}, Error File Name: {file_name}")
                except Exception as e:
                    print(f"Failed to read {file_path}: {e}")

if __name__ == "__main__":
    find_error_files()
