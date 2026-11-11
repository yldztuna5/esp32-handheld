import os, sys
sys.path.insert(0, os.path.join(os.environ["TEMP"], "khpdf"))
from pypdf import PdfReader

src, dst, last = sys.argv[1], sys.argv[2], int(sys.argv[3])
reader = PdfReader(src)
with open(dst, "w", encoding="utf-8") as f:
    for i, page in enumerate(reader.pages[:last]):
        f.write(f"\n===== PAGE {i + 1} =====\n")
        f.write(page.extract_text() or "")
