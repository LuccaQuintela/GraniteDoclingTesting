from pathlib import Path
from docling.document_converter import DocumentConverter

def main() -> None:
    converter = DocumentConverter()

    pdf_path = Path("data/farm.pdf")
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

    output_path = results_dir / f"{pdf_path.stem}.md"

    if output_path.exists():
        print(f"Markdown already exists at: {output_path}")
        return

    print(f"Converting {pdf_path}...")
    result = converter.convert(str(pdf_path))

    markdown_output = result.document.export_to_markdown()

    output_path.write_text(markdown_output, encoding="utf-8")
    print(f"Markdown saved to: {output_path}")

if __name__ == "__main__":
    main()
