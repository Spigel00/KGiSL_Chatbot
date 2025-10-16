import json
import re
import pandas as pd
from bs4 import BeautifulSoup

def clean_web_text(raw_text: str) -> str:
    """
    Cleans raw text extracted from web pages by removing common boilerplate,
    HTML tags, and excessive whitespace.

    Args:
        raw_text: The raw string content from the webpage.

    Returns:
        A cleaned string containing the main content.
    """
    # 1. Use BeautifulSoup to parse the text and remove any potential leftover HTML tags.
    soup = BeautifulSoup(raw_text, 'html.parser')
    text = soup.get_text(separator=' ')

    # 2. Define and remove common, repetitive text blocks (headers, footers, menus).
    boilerplate_patterns = [
        "EDU Home Counselling Code 2751 24x7 Women's Help line Environmental Clearance Online Fees Payment || Screen Reader",
        "Home About Us About KITE KITE Virtual Tour Quality Policy Vision And Mission Administration Governing Council Mandatory Disclosure Financials HR Directory Press Release Blogs News and Events Careers Contact Us",
        "Admission Institution Scholarship Approval Letters Brochure Academics Programmes UG Programmes PG Programmes Ph.D Programmes Departments",
        "Information Technology About Department Vision & Mission PEOs | POs | PSOs Programmes Offered Faculty Facilities Regulations & Curriculum Research Value Added Courses Placement Achievements E-newsletter Innovative Learning Club and Association Star Alumni Gallery",
        "Computer Science and Engineering About Department Vision & Mission PEOs | POs | PSOs Programmes Offered Faculty Facilities Regulations & Curriculum Research Value Added Courses Placements Achievements E-News Letter",
        "Computer Science and Business Systems About Department",
        "Artificial Intelligence & Data Science About Department PEOs | POs | PSOs Programmes Offered Faculty Facilities Regulations & Curriculum Achievements",
        "Electronics and Communication Engineering About Department Vision & Mission PEOS, POS, PSOS Programmes Offered Faculty Facilities Regulation & Curriculum Value Added Courses Placements MoUs Achievements E-newsletter Events Organized Clubs and Association Alumni",
        "Mechanical Engineering About Department Vision & Mission PEOs | POs | PSOs Programmes Offered Faculty Facilities Regulations & Curriculum Research Value Added Courses Placement Alumni",
        "Science & Humanities About Department Faculty Facilities Regulations & Curriculum Research",
        "Master of Business Administration About Department Vision & Mission",
        "Artificial Intelligence And Machine Learning Cyber Security Research Research Committee Research Promotion Policy Research Centres Anna University Regulation Recognized Research Supervisors Area of Research Ongoing and Completed Research Projects Grants Received Patents Journal Reviewers Conference and Books Research Fellowship",
        "Alumni Distinguished Alumni Alumni Registration Gallery",
        "IIIC Industry-Institute Interaction Cell (IIIC) MoUs",
        "CII Centre for Innovation and Incubation Skill Labs Venture Incubation Park KiTE-CII NISP NISP Policy Nisp startup policy State Policy of Tamilnadu Government (2018-2023) State Policy of Tamilnadu Government 2023",
        "Campus Life Learning Management System e-Campus Infrastructure Environmental Clearance Physical Education Amenities Hostel Transport Feedback",
        "NAAC Self Declaration Statutory Declaration NBA Approval Letters Auditor statements Faculty Information",
        "Placement Details Computer Science and Engineering Electronics and Communication Engineering.",
        "IQAC About IQAC IQAC Composition IQAC Minutes & ATR AQAR Strategic Plan Academic Calendar Stakeholders Feedback NIRF Contact",
        "Placements About the training and placement Training and Placement Process Placement Record Placement details – 2024 – 2025 Testimonials Contact Us",
        "Library About library Library Services Digital Library Titles And Volumes Journals And Magazines Audio Visual Section Book Lending Services Library Sections Rules And Regulations Library Team Library Events And Photo Gallery Book Donation Camp First Year Orientation Program Ndli Club Events World Book Day Pledge Central Library & National Digital Library of India (NDLI) Organized Photo Gallery Contact Us",
        "Clubs and Cells Professional Society ISTE CSI IETE Institute of Engineers(IE) Indian Welding Society (IWS) Women Empowerment cell Tech Community Fine Arts Tamil Mandram ICT Academy Book Donation Camp Faculty Participation Tech 4 all Membership Certificate",
        "COMMITTEE ANTIRAGGING COMMITTEE Grievance Redressal Committee SC / ST Committee INTERNAL COMPLAINTS COMMITTEE",
        "IDEA Lab School of Innovation Vision & Mission Strategic Objectives Lab Ecosystem Signature Initiatives Student Journey at a Glance Phase – Wise Roll-out",
        "COE End Semester Time Table Apr/May 2025 (R2021) End Semester Time Table Result End Semester Result – Apr/May 2025",
        "Quick Links Campus Life Admission Placement Cell Research",
    ]
    
    for pattern in boilerplate_patterns:
        text = text.replace(pattern, " ")

    # 3. Normalize whitespace
    text = re.sub(r'\s+', ' ', text)

    # 4. Remove any leading or trailing whitespace
    cleaned_text = text.strip()

    return cleaned_text

# --- Main Script ---

file_path = 'kgisl_pages_content.json'

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    df = pd.DataFrame(data)

    # Apply the cleaning function
    df['cleaned_text'] = df['text'].apply(clean_web_text)
    
    # Add length columns for comparison
    df['original_length'] = df['text'].str.len()
    df['cleaned_length'] = df['cleaned_text'].str.len()

    print("Successfully processed the data.")
    print(f"Total pages processed: {len(df)}")
    
    print("\n--- Sample of Cleaned Data (first 5 pages) ---")
    pd.set_option('display.max_colwidth', 400)
    print(df[['url', 'cleaned_text', 'original_length', 'cleaned_length']].head())

    # --- Save the Cleaned Data to JSON ---
    output_filename_json = 'cleaned_kgisl_data.json'
    
    # We convert the DataFrame back to a list of dictionaries to save it.
    # `orient='records'` creates a JSON array of objects, similar to the input file.
    # `indent=4` makes the JSON file human-readable.
    # `force_ascii=False` ensures proper handling of non-English characters.
    df.to_json(output_filename_json, orient='records', indent=4, force_ascii=False)
    
    print(f"\n✅ Cleaned data has been saved to '{output_filename_json}'")

except FileNotFoundError:
    print(f"Error: The file '{file_path}' was not found.")
except Exception as e:
    print(f"An error occurred: {e}")