# GraniteDoclingTesting

PDF document conversion pipeline using Docling for text extraction with GPT-4o for image understanding.

## Overview

This project uses [Docling](https://github.com/DS4SD/docling) with RapidOCR for text extraction and OpenAI GPT-4o for image understanding to convert PDF documents into markdown format. The pipeline provides:

- RapidOCR for text and scanned document processing
- Table and chart extraction
- Image extraction and AI-powered descriptions via GPT-4o
- Automatic caching of previously converted documents

The conversion pipeline is orchestrated through an `Engine` class that handles batch processing with logging and automatic caching.

## Setup

1. Install dependencies using `uv`:
   ```bash
   uv sync
   ```

2. Create a `.env` file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_key_here
   ```

3. Place your PDF files in the `data/` directory

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
- `results/` - Converted markdown files and extracted images are saved here
- `logs/` - Timestamped log files for each run

## Requirements

- Python 3.12+
- OpenAI API key with access to GPT-4o

