import json
import re
import os

def chunk_text(text, chunk_size=1000, chunk_overlap=150):
    """
    Splits a long text into smaller chunks of a specified size with overlap.
    """
    if not isinstance(text, str) or not text.strip():
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        # Move the start position forward, considering the overlap
        start += chunk_size - chunk_overlap
        if start >= len(text):
            break

    return chunks

def main():
    """Main function to load, chunk, and save the data."""
    input_file = 'cleaned_combined_data.json'
    output_file = 'chunked_data.json'

    all_chunks = []

    try:
        # Check if the input file exists
        if not os.path.exists(input_file):
            print(f"❌ Error: Input file '{input_file}' not found.")
            print("Please make sure the file is in the same directory as the script.")
            return

        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 1. Process HTML data
        if 'html_data' in data:
            for url, content in data['html_data'].items():
                # Combine title and headings into a single text block
                full_text = content.get('title', '') + '. ' + '. '.join(content.get('headings', []))

                # Use the chunk_text function
                text_chunks = chunk_text(full_text)

                for i, chunk in enumerate(text_chunks):
                    all_chunks.append({
                        'source_type': 'html',
                        'source_url': url,
                        'chunk_id': f'html_{len(all_chunks)}',
                        'content': chunk
                    })
            print("✅ Successfully chunked HTML data.")

        # 2. Process PDF data
        if 'pdf_data' in data:
            for url, content in data['pdf_data'].items():
                full_text = content.get('text', '')

                # Use the chunk_text function
                text_chunks = chunk_text(full_text)

                for i, chunk in enumerate(text_chunks):
                    all_chunks.append({
                        'source_type': 'pdf',
                        'source_url': url,
                        'chunk_id': f'pdf_{len(all_chunks)}',
                        'content': chunk
                    })
            print("✅ Successfully chunked PDF data.")

        # 3. Process Excel data (treat each row as a chunk)
        if 'excel_data' in data:
            excel_rows = data['excel_data']
            if isinstance(excel_rows, list): # Handle if it's a list of rows
                for row in excel_rows:
                    # Convert the dictionary row to a readable string format
                    row_text = ", ".join([f"{k}: {v}" for k, v in row.items()])
                    all_chunks.append({
                        'source_type': 'excel',
                        'source_file': 'excel_data.json',
                        'chunk_id': f'excel_{len(all_chunks)}',
                        'content': row_text
                    })
            elif isinstance(excel_rows, dict): # Handle if it's a single dictionary
                 row_text = ", ".join([f"{k}: {v}" for k, v in excel_rows.items()])
                 all_chunks.append({
                        'source_type': 'excel',
                        'source_file': 'excel_data.json',
                        'chunk_id': f'excel_{len(all_chunks)}',
                        'content': row_text
                    })
            print("✅ Successfully chunked Excel data.")

        # Write the combined chunks to the output JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_chunks, f, indent=4, ensure_ascii=False)

        print(f"\n🎉 Success! All data has been chunked and saved to '{output_file}'.")
        print(f"Total chunks created: {len(all_chunks)}")

    except json.JSONDecodeError as e:
        print(f"❌ Error: Could not decode JSON from '{input_file}'. Please check its format. Details: {e}")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

if __name__ == '__main__':
    main()