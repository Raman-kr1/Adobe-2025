import fitz  # PyMuPDF
import json
import os
import operator

def sort_blocks(blocks):
    """Sorts text blocks by their vertical position on the page."""
    return sorted(blocks, key=lambda b: b[1])

def get_font_styles(doc):
    """Extracts font styles and their counts from the document."""
    styles = {}
    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        font_size = round(span["size"])
                        font_name = span["font"]
                        style_key = (font_size, font_name)
                        styles[style_key] = styles.get(style_key, 0) + 1
    return styles

def determine_heading_levels(styles):
    """Determines heading levels based on font size."""
    if not styles:
        return {}, None

    # Sort potential heading styles by font size in descending order
    # A simple heuristic: any font style that isn't the single most common one could be a heading.
    if len(styles) > 1:
        sorted_by_freq = sorted(styles.items(), key=lambda item: item[1], reverse=True)
        most_common_style = sorted_by_freq[0][0]
        potential_heading_styles = [s for s in styles if s != most_common_style]
        sorted_by_size = sorted(potential_heading_styles, key=lambda style: style[0], reverse=True)
    else:
        sorted_by_size = sorted(styles.keys(), key=lambda style: style[0], reverse=True)

    heading_levels = {}
    if len(sorted_by_size) > 0:
        heading_levels["H1"] = sorted_by_size[0]
    if len(sorted_by_size) > 1:
        heading_levels["H2"] = sorted_by_size[1]
    if len(sorted_by_size) > 2:
        heading_levels["H3"] = sorted_by_size[2]

    # Title is assumed to be the largest font size overall
    title_style = max(styles.keys(), key=lambda style: style[0]) if styles else None
    
    return heading_levels, title_style

def extract_outline(pdf_path):
    """Extracts the title and a hierarchical outline from a PDF."""
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Error opening {pdf_path}: {e}")
        return {"title": "Error opening file", "outline": []}
    
    all_styles = get_font_styles(doc)
    heading_styles, title_style = determine_heading_levels(all_styles)
    
    title = ""
    outline = []
    
    # Find the title
    if title_style:
        for page in doc:
            blocks = page.get_text("dict")["blocks"]
            for block in sorted(blocks, key=lambda b: b['bbox'][1]):
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            if (round(span["size"]), span["font"]) == title_style:
                                title = span["text"].strip()
                                break
                        if title: break
                    if title: break
            if title: break
    
    # Extract headings
    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict")["blocks"]
        for block in sorted(blocks, key=lambda b: b['bbox'][1]):
            if "lines" in block:
                for line in block["lines"]:
                    if line["spans"]:
                        span = line["spans"][0]
                        text = " ".join(s['text'] for s in line['spans']).strip()
                        font_size = round(span["size"])
                        font_name = span["font"]
                        current_style = (font_size, font_name)

                        if not text or len(text.split()) > 20:
                            continue

                        for level, style in heading_styles.items():
                            if current_style == style:
                                # Avoid adding duplicate headings from the same text block
                                if not any(o['text'] == text and o['level'] == level for o in outline):
                                    outline.append({
                                        "level": level,
                                        "text": text,
                                        "page": page_num + 1
                                    })
                                break
    
    doc.close()
    return {"title": title if title else "Title not found", "outline": outline}

if __name__ == "__main__":
    input_dir = "/app/input"
    output_dir = "/app/output"

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    if not pdf_files:
        print("No PDF files found in the input directory.")
    else:
        for filename in pdf_files:
            pdf_path = os.path.join(input_dir, filename)
            json_filename = os.path.splitext(filename)[0] + ".json"
            output_path = os.path.join(output_dir, json_filename)
            
            print(f"Processing {filename}...")
            try:
                data = extract_outline(pdf_path)
                with open(output_path, "w", encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                print(f"Successfully created {json_filename}")
            except Exception as e:
                print(f"Failed to process {filename}: {e}")