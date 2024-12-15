import pymupdf  # PyMuPDF
import re

def pdf_to_text(pdf_path, txt_path):
    # Open the PDF file
    pdf_document = pymupdf.open(pdf_path)
    
    # Initialize an empty string to hold the text
    # text = ""
    text = []
    
    # Iterate over each page
    for page_num in range(len(pdf_document)):
        # page = pdf_document.load_page(page_num)
        # text += page.get_text()
        page = pdf_document[page_num]
        page_text = page.get_text(
                    "text",  # Extract plain text
                    sort=True,  # Sort blocks by reading order
                    flags=pymupdf.TEXT_PRESERVE_LIGATURES | pymupdf.TEXT_PRESERVE_WHITESPACE
                )
        text.append(page_text)

    text_string = "\n".join(text)
    
    # Write the text to a file
    with open(txt_path + "_plum.txt", 'w', encoding='utf-8') as txt_file:
        txt_file.write(text)
        txt_file.write(text_string)
    
    # Clean text
    cleaned = _clean_text(text_string)

    # Write cleaned text to a file
    with open(txt_path + "_clean.txt", 'w', encoding='utf-8') as txt_file:
        txt_file.write(cleaned)
    
    # Close the PDF file
    pdf_document.close()

def _clean_text(text: str) -> str:
    """Clean and normalize extracted text."""
    if not text:
        return text

    # Remove excessive whitespace but preserve newlines
    text = re.sub(r'[ \t]+', ' ', text)

    # Remove non-printable characters
    text = ''.join(char for char in text if char.isprintable())

    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # Remove empty lines
    text = '\n'.join(line.strip() for line in text.splitlines() if line.strip())

    # Additional cleaning specific to course information
    # Normalize course codes
    text = re.sub(r'([A-Z]{2,4})\s*(\d{4})', r'\1 \2', text)

    # Normalize times
    text = re.sub(r'(\d{1,2})\s*:\s*(\d{2})\s*(AM|PM|am|pm)', r'\1:\2 \3', text)

    return text

if __name__ == "__main__":
    pdf_path = "/Users/mitchellgerhardt/Desktop/Fall2024_AOE.pdf"
    txt_path = "./output_"
    pdf_to_text(pdf_path, txt_path)