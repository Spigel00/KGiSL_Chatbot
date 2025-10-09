import os
import json
import fitz  # PyMuPDF
import requests

# 🔧 Settings
save_dir = 'kgkite_pdfs'
link_file = 'pdf_links.txt'
os.makedirs(save_dir, exist_ok=True)

# ✅ Load and clean links
def load_unique_links(file_path):
    with open(file_path, 'r') as f:
        links = set(line.strip() for line in f if line.strip().endswith('.pdf'))
    return sorted(links)

# ✅ Download PDF
def download_file(url, save_dir):
    filename = os.path.basename(url.split('?')[0])
    file_path = os.path.join(save_dir, filename)
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return file_path

# ✅ Extract text from PDF
def extract_pdf_text(file_path):
    try:
        doc = fitz.open(file_path)
        return "\n".join(page.get_text() for page in doc)
    except Exception as e:
        return f"Error extracting text: {e}"

# ✅ Main workflow
def main():
    print("📄 Loading and cleaning PDF links...")
    pdf_links = load_unique_links(link_file)
    print(f"✅ Found {len(pdf_links)} unique PDFs.\n")

    pdf_data = {}
    for pdf_url in pdf_links:
        pdf_name = os.path.basename(pdf_url.split('?')[0])
        pdf_path = os.path.join(save_dir, pdf_name)

        if not os.path.exists(pdf_path):
            try:
                print(f"⬇️ Downloading: {pdf_name}")
                file_path = download_file(pdf_url, save_dir)
                text = extract_pdf_text(file_path)
                pdf_data[pdf_url] = {'text': text}
            except Exception as e:
                print(f"❌ Error downloading {pdf_url}: {e}")
                pdf_data[pdf_url] = {'error': str(e)}
        else:
            print(f"📁 Already downloaded: {pdf_name}")
            text = extract_pdf_text(pdf_path)
            pdf_data[pdf_url] = {'text': text}

    with open('all_pdf_data.json', 'w', encoding='utf-8') as f:
        json.dump(pdf_data, f, indent=2)

    print("\n✅ Done! Extracted data saved to all_pdf_data.json.")

if __name__ == '__main__':
    main()
