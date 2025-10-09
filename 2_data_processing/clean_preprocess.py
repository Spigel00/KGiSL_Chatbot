import json
import re
import os

def clean_html_data(data):
    """Cleans data extracted from HTML."""
    cleaned_data = {}
    for url, content in data.items():
        # Clean the title by stripping whitespace
        if 'title' in content and isinstance(content['title'], str):
            content['title'] = content['title'].strip()

        # Clean the headings list
        if 'headings' in content and isinstance(content['headings'], list):
            # 1. Strip whitespace from each heading.
            # 2. Remove any headings that are empty after stripping.
            cleaned_headings = [h.strip() for h in content['headings'] if h and h.strip()]
            content['headings'] = cleaned_headings

        cleaned_data[url] = content
    return cleaned_data

def clean_pdf_data(data):
    """Cleans text extracted from PDFs."""
    cleaned_data = {}
    for url, content in data.items():
        if 'text' in content and isinstance(content['text'], str):
            raw_text = content['text']

            # 1. Split text into lines to process them individually
            lines = raw_text.splitlines()

            cleaned_lines = []
            for line in lines:
                # 2. Strip leading/trailing whitespace from each line
                line = line.strip()

                # 3. Skip lines that are empty or are repetitive headers/footers from PDF extraction
                if not line or 'KiTE Explorer' in line:
                    continue

                cleaned_lines.append(line)

            # 4. Join the cleaned lines back with a single newline
            cleaned_text = "\n".join(cleaned_lines)

            # 5. Replace multiple spaces with a single space for better readability
            cleaned_text = re.sub(r'\s{2,}', ' ', cleaned_text)

            content['text'] = cleaned_text

        cleaned_data[url] = content
    return cleaned_data

def clean_excel_data(data):
    """
    Cleans data extracted from Excel.
    This version handles both a single dictionary and a list of dictionaries.
    """
    # Case 1: The data is a list of dictionaries (most common for Excel)
    if isinstance(data, list):
        cleaned_list = []
        for row_dict in data:
            cleaned_row = {}
            if isinstance(row_dict, dict):
                for key, value in row_dict.items():
                    # Strip whitespace from both the key (column) and the value
                    cleaned_key = key.strip() if isinstance(key, str) else key
                    cleaned_value = value.strip() if isinstance(value, str) else value
                    cleaned_row[cleaned_key] = cleaned_value
            else:
                 # If an item in the list is not a dictionary, keep it as is
                cleaned_row = row_dict
            cleaned_list.append(cleaned_row)
        return cleaned_list

    # Case 2: The data is a single dictionary (as in your original sample)
    elif isinstance(data, dict):
        cleaned_data = {}
        for key, value in data.items():
            cleaned_key = key.strip() if isinstance(key, str) else key
            cleaned_value = value.strip() if isinstance(value, str) else value
            cleaned_data[cleaned_key] = cleaned_value
        return cleaned_data

    # If it's neither a list nor a dict, return it unchanged
    return data

def main():
    """Main function to load, clean, and combine data."""
    # Define file paths
    html_file = 'html_data.json'
    pdf_file = 'all_pdf_data.json'
    excel_file = 'excel_data.json'
    output_file = 'cleaned_combined_data.json'

    # Dictionary to hold the final combined data
    combined_data = {}

    # Process each file if it exists
    try:
        if os.path.exists(html_file):
            with open(html_file, 'r', encoding='utf-8') as f:
                html_data = json.load(f)
            combined_data['html_data'] = clean_html_data(html_data)
            print(f"✅ Successfully cleaned '{html_file}'.")
        else:
            print(f"⚠️ Warning: '{html_file}' not found. Skipping.")

        if os.path.exists(pdf_file):
            with open(pdf_file, 'r', encoding='utf-8') as f:
                pdf_data = json.load(f)
            combined_data['pdf_data'] = clean_pdf_data(pdf_data)
            print(f"✅ Successfully cleaned '{pdf_file}'.")
        else:
            print(f"⚠️ Warning: '{pdf_file}' not found. Skipping.")

        if os.path.exists(excel_file):
            with open(excel_file, 'r', encoding='utf-8') as f:
                excel_data = json.load(f)
            combined_data['excel_data'] = clean_excel_data(excel_data)
            print(f"✅ Successfully cleaned '{excel_file}'.")
        else:
            print(f"⚠️ Warning: '{excel_file}' not found. Skipping.")

        # Write the combined, cleaned data to a new JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            # indent=4 makes the JSON file readable
            # ensure_ascii=False preserves characters like ’
            json.dump(combined_data, f, indent=4, ensure_ascii=False)

        print(f"\n🎉 All data has been processed and saved to '{output_file}'.")

    except json.JSONDecodeError as e:
        print(f"❌ Error: Could not decode JSON. Please check the format of your input files. Details: {e}")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

if __name__ == '__main__':
    main()