import fitz  # PyMuPDF
import sys

def render_pages():
    doc = fitz.open("Shizu_Security_Manual.pdf")
    print(f"Total pages: {len(doc)}")
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=150)
        out_name = f"page_{i+1}.png"
        pix.save(out_name)
        print(f"Saved {out_name}: {pix.width}x{pix.height}")

if __name__ == "__main__":
    render_pages()
