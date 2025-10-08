import os
import requests
import pandas as pd

# 🔧 Settings
xls_url = "https://www.kgkite.ac.in/wp-content/uploads/2023/08/5.3.1-first-link.xlsx"
save_dir = "kgkite_excel"
os.makedirs(save_dir, exist_ok=True)

# ✅ Download the Excel file
def download_excel(url, save_dir):
    filename = os.path.basename(url.split('?')[0])
    file_path = os.path.join(save_dir, filename)
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return file_path

# ✅ Read Excel contents
def read_excel(file_path):
    try:
        df = pd.read_excel(file_path)
        return df
    except Exception as e:
        print(f"❌ Error reading Excel file: {e}")
        return None

# ✅ Main workflow
def main():
    print("⬇️ Downloading Excel file...")
    file_path = download_excel(xls_url, save_dir)
    print(f"✅ Saved to: {file_path}")

    print("📊 Reading Excel contents...")
    df = read_excel(file_path)
    if df is not None:
        print("\n✅ Preview of data:")
        print(df.head())

        # Optional: Save to JSON
        df.to_json("excel_data.json", orient="records", indent=2)
        print("\n✅ Data saved to excel_data.json")

if __name__ == '__main__':
    main()
