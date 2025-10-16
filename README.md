# GraniteDoclingTesting

Local running of IBM's Granite Docling data extraction model to test its capabilities for converting PDFs to structured formats (Markdown and HTML).

## Overview

This project uses [Docling](https://github.com/DS4SD/docling) with the **Granite-Docling-258M Vision Language Model** to convert PDF documents into markdown and HTML formats. The VLM pipeline provides enhanced document understanding, including:

- Vision-based OCR for scanned documents
- Table and chart extraction
- Formula recognition (LaTeX output)
- Code block extraction
- Image and diagram understanding

The conversion pipeline is orchestrated through an `Engine` class that handles batch processing with logging and automatic caching.

## Setup

1. Install dependencies using `uv`:
   ```bash
   uv sync
   ```

2. Place your PDF files in the `data/` directory

## Usage

Edit `main.py` to specify which PDFs to convert:

```python
from engine import Engine

def main() -> None:
    engine = Engine()

    # List the names of files in the data folder
    data = ["document1.pdf", "document2.pdf", "document3.pdf"]

    engine.run(data)

if __name__ == "__main__":
    main()
```

Run the conversion:
```bash
uv run python main.py
```

## Directory Structure

- `data/` - Place your input PDF files here
- `results/` - Converted markdown and HTML files are saved here
- `logs/` - Timestamped log files for each run

## Features

- **Vision Language Model**: Uses Granite-Docling-258M for AI-powered document understanding
- **GPU Acceleration**: Leverages local GPU for fast VLM inference
- **Batch Processing**: Convert multiple PDFs in a single run
- **Automatic Caching**: Skips files that have already been converted
- **Dual Output**: Generates both markdown (.md) and HTML (.html) files
- **Comprehensive Logging**: Logs to both stdout and timestamped log files
- **UTF-8 Support**: Handles Unicode characters in PDFs correctly

## Requirements

- Python 3.12+
- CUDA-capable GPU (recommended for VLM performance)
- PyTorch with CUDA support

On first run, the Granite-Docling-258M model will be downloaded automatically (several GB).

