import json
import pandas as pd

# --- Configuration for Chunking ---
# The target size for each text chunk in characters.
CHUNK_SIZE = 1000
# The number of characters to overlap between consecutive chunks.
CHUNK_OVERLAP = 200

def create_chunks(record: dict) -> list[dict]:
    """
    Splits the cleaned_text of a record into chunks with metadata.

    Args:
        record: A dictionary representing one page from the cleaned data.

    Returns:
        A list of dictionaries, where each dictionary is a single chunk.
    """
    # Get the main content and the primary identifier (URL)
    text = record.get('cleaned_text', '')
    url = record.get('url', '')
    
    # If there's no text, return an empty list
    if not text:
        return []

    chunks = []
    # Use a range function with a step to slide a window across the text
    for i in range(0, len(text), CHUNK_SIZE - CHUNK_OVERLAP):
        # Extract the chunk of text
        chunk_text = text[i:i + CHUNK_SIZE]
        
        # Create a new record for this chunk
        chunk_record = {
            'url': url,
            'chunk_id': len(chunks) + 1, # Simple 1-based index for chunks of a page
            'text_chunk': chunk_text,
            # You can carry over other metadata from the original record if needed
            'original_length': record.get('original_length'),
            'timestamp': record.get('timestamp')
        }
        chunks.append(chunk_record)
        
    return chunks

# --- Main Script ---

input_file = 'cleaned_kgisl_data.json'
output_file = 'chunked_kgisl_data.json'

try:
    # Load the cleaned data using pandas
    df = pd.read_json(input_file, orient='records')

    # Create a new list to store all the chunks from all documents
    all_chunks = []

    # Iterate over each row (each webpage) in the DataFrame and create chunks
    for _, row in df.iterrows():
        record_chunks = create_chunks(row.to_dict())
        all_chunks.extend(record_chunks)

    # Convert the list of chunks into a new DataFrame
    chunked_df = pd.DataFrame(all_chunks)

    # --- Display Results ---
    print(f"Successfully chunked the data.")
    print(f"Original number of pages: {len(df)}")
    print(f"Total number of chunks created: {len(chunked_df)}")
    
    print("\n--- Sample of the new Chunked Data ---")
    # Display the first 5 chunks
    pd.set_option('display.max_colwidth', 400)
    print(chunked_df.head())

    # --- Save the Chunked Data to a new JSON file ---
    chunked_df.to_json(output_file, orient='records', indent=4, force_ascii=False)
    
    print(f"\n✅ Chunked data has been saved to '{output_file}'")

except FileNotFoundError:
    print(f"Error: The file '{input_file}' was not found.")
except Exception as e:
    print(f"An error occurred: {e}")