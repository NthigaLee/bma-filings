import pdfplumber

pdf_path = r'pdfs\2025-07-02-11-39-02-Brit-Reinsurance-Bermuda-Limited---2024-Financial-Statement.pdf'

with pdfplumber.open(pdf_path) as pdf:
    print(f'Total pages: {len(pdf.pages)}')
    found_text = False
    for i in range(len(pdf.pages)):
        text = pdf.pages[i].extract_text() or ''
        words = pdf.pages[i].extract_words()
        if text.strip() or words:
            found_text = True
            print(f'\n--- PAGE {i+1} (text_len={len(text)}, words={len(words)}) ---')
            print(text[:800])
        if i >= 25:
            break
    if not found_text:
        print('No text found in first 26 pages - likely image-based PDF')
