#!/usr/bin/env python3
"""
Extract paragraphs from a .docx file, preserving basic formatting info.

Usage: python extract_paragraphs.py input.docx output.json

Output: JSON array of {text, bold, font_size, is_bib}
- text: paragraph text (concatenated from all runs)
- bold: whether first run is bold
- font_size: font size in half-points from first run
- is_bib: whether this appears to be a bibliography entry
"""

import sys, json, xml.etree.ElementTree as ET
from zipfile import ZipFile
from io import BytesIO

ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

def extract_paragraphs(docx_path):
    """Extract paragraphs from docx file."""
    with ZipFile(docx_path, 'r') as z:
        xml_bytes = z.read('word/document.xml')
    
    tree = ET.parse(BytesIO(xml_bytes))
    root = tree.getroot()
    body = root.find('.//w:body', ns)
    
    paragraphs = []
    in_bib = False
    
    for p in body.findall('w:p', ns):
        texts = []
        is_bold = False
        font_size = None
        
        for r in p.findall('w:r', ns):
            t_elem = r.find('w:t', ns)
            rpr = r.find('w:rPr', ns)
            
            if t_elem is not None and t_elem.text:
                texts.append(t_elem.text)
            
            if rpr is not None:
                if rpr.find('w:b', ns) is not None:
                    is_bold = True
                sz = rpr.find('w:sz', ns)
                if sz is not None:
                    font_size = sz.get(
                        '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val'
                    )
        
        full_text = ''.join(texts).strip()
        if not full_text:
            continue
        
        # Detect bibliography section
        # Common patterns: starts with [1] or ［1］
        if re.match(r'^[\[［]\d+[\]］]', full_text) or full_text == '参考文献':
            in_bib = True
        
        paragraphs.append({
            'text': full_text,
            'bold': is_bold,
            'font_size': font_size,
            'is_bib': in_bib
        })
    
    return paragraphs

if __name__ == '__main__':
    import re
    if len(sys.argv) < 2:
        print("Usage: python extract_paragraphs.py input.docx [output.json]")
        sys.exit(1)
    
    docx_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    paragraphs = extract_paragraphs(docx_path)
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(paragraphs, f, ensure_ascii=False, indent=2)
        print(f"Extracted {len(paragraphs)} paragraphs → {output_path}")
    else:
        print(json.dumps(paragraphs, ensure_ascii=False, indent=2))
