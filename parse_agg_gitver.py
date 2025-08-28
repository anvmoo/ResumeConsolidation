import os
import json
import PyPDF2
from docx import Document

# Define the section headings in  resumes.
SECTION_HEADINGS = [
    "AREAS OF EXPERTISE",
    "HIGHLIGHTED ACCOMPLISHMENTS",
    "PROFESSIONAL EXPERIENCE",
    "EDUCATION",
    "TRAINING & CERTIFICATIONS"
]

def extract_text_from_pdf(file_path):
    """Extracts text from a PDF file."""
    text = ""
    try:
        with open(file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() or ""
    except Exception as e:
        print(f"Could not read PDF {file_path}: {e}")
    return text

def extract_text_from_docx(file_path):
    """Extracts text from a DOCX file."""
    text = ""
    try:
        doc = Document(file_path)
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
    except Exception as e:
        print(f"Could not read DOCX {file_path}: {e}")
    return text

def parse_sections(full_text):
    """Parses text into sections based on defined headings."""
    content = {heading: [] for heading in SECTION_HEADINGS}
    current_section = None
    
    lines = full_text.splitlines()
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        is_heading = False
        for heading in SECTION_HEADINGS:
            # Using startswith() is a good way to handle bolding and formatting
            if line.upper().startswith(heading.upper()):
                current_section = heading
                is_heading = True
                break
        
        if not is_heading and current_section:
            if len(line.split()) > 2:
                content[current_section].append(line)
    
    return content

def main(db_name):
    json_file_path = f"{db_name}.json"
    psv_file_path = f"{db_name}.psv" # New file for the pipe-delimited output
    resume_dir = "C:/Users"
    
    if not os.path.exists(resume_dir):
        print(f"Error: The directory '{resume_dir}' was not found.")
        return

    # 1. Read existing data to get a list of already processed files
    # The JSON file remains the source of truth for processed files
    if os.path.exists(json_file_path):
        with open(json_file_path, "r", encoding="utf-8") as f:
            aggregated_data = json.load(f)
        processed_files = {item['filename'] for item in aggregated_data}
    else:
        aggregated_data = []
        processed_files = set()

    newly_processed_count = 0
    for filename in os.listdir(resume_dir):
        file_path = os.path.join(resume_dir, filename)
        
        if filename in processed_files:
            continue
        
        full_text = ""
        if filename.endswith(".pdf"):
            full_text = extract_text_from_pdf(file_path)
        elif filename.endswith(".docx"):
            full_text = extract_text_from_docx(file_path)
        else:
            continue
        
        if full_text:
            parsed_content = parse_sections(full_text)
            
            # --- UPDATED LOGIC TO HANDLE SKILLS AND AGGREGATE ---
            for section, bullets in parsed_content.items():
                if not bullets:
                    continue
                
                # Special case for "AREAS OF EXPERTISE"
                if section == "AREAS OF EXPERTISE":
                    for bullet in bullets:
                        skill_phrases = [s.strip() for s in bullet.split('|') if s.strip()]
                        for skill in skill_phrases:
                            aggregated_data.append({
                                "filename": filename,
                                "section": section,
                                "content": skill
                            })
                # General case for all other sections
                else:
                    for bullet in bullets:
                        aggregated_data.append({
                            "filename": filename,
                            "section": section,
                            "content": bullet
                        })
            newly_processed_count += 1
    
    if newly_processed_count > 0:
        # 2. Save the complete, updated list back to the JSON file
        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(aggregated_data, f, indent=4)
        
        # 3. Save to the new pipe-delimited file
        with open(psv_file_path, "w", encoding="utf-8") as f_psv:
            f_psv.write("filename|section|content\n") # Write header
            for item in aggregated_data:
                # Replace any internal pipes to prevent data corruption
                clean_content = item['content'].replace('|', ' ').replace('\n', ' ')
                f_psv.write(f"{item['filename']}|{item['section']}|{clean_content}\n")
        
        print(f"Successfully processed {newly_processed_count} new resume(s).")
        print(f"Aggregated data saved to '{json_file_path}' and '{psv_file_path}'.")
    else:
        print("No new resumes found to process.")

if __name__ == "__main__":
    main("masterdata")