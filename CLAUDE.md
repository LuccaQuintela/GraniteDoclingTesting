# Docling VLM Integration Project

## Project Overview

This project uses IBM's Docling library to convert PDFs and other documents into structured formats (Markdown, HTML, JSON). We're integrating Vision Language Models (VLM) to enhance document understanding and extract content from images within documents.

## Key Technologies

### Docling
- Open-source document conversion library by IBM Research
- Converts PDFs, DOCX, PPTX, XLSX, HTML, images, and audio files
- Uses AI models for layout detection, table extraction, and OCR
- Exports to Markdown, HTML, DocTags, or JSON

### Granite-Docling-258M
- 258M parameter multimodal vision-language model
- Specifically engineered for document conversion tasks
- Built on IDEFICS3 architecture with siglip2 vision encoder and Granite 165M LLM
- Handles: full-page OCR, table recognition, equation recognition (LaTeX), code recognition
- Can answer questions about document structure
- Supports flexible inference modes: full-page or bbox-guided region inference

### Current Setup
- Python 3.12 via pyenv
- NVIDIA RTX 2080 GPU with CUDA 12.1 support
- PyTorch with CUDA acceleration
- Virtual environment managed by uv

## Implementation Approaches

### 1. Local VLM Pipeline (Recommended for GPU)

Use Granite-Docling-258M model running locally on your RTX 2080:

```python
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.pipeline.vlm_pipeline import VlmPipeline

# Simple default usage - uses Granite-Docling with transformers
converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(
            pipeline_cls=VlmPipeline,
        ),
    }
)

result = converter.convert("document.pdf")
print(result.document.export_to_markdown())
```

### 2. Remote API Model Integration

For using external APIs (LM Studio, Ollama, watsonx.ai):

```python
from docling.datamodel.pipeline_options import VlmPipelineOptions
from docling.datamodel.pipeline_options_vlm_model import ApiVlmOptions, ResponseFormat

pipeline_options = VlmPipelineOptions(
    enable_remote_services=True  # Required for API models
)

# Example: Ollama
pipeline_options.vlm_options = ApiVlmOptions(
    url="http://localhost:11434/v1/chat/completions",
    params=dict(model="granite3.2-vision:2b"),
    prompt="OCR the full page to markdown.",
    timeout=90,
    scale=1.0,
    response_format=ResponseFormat.MARKDOWN,
)

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(
            pipeline_cls=VlmPipeline,
            pipeline_options=pipeline_options,
        )
    }
)
```

## Supported VLM Instructions

The Granite-Docling model supports specialized instructions:

| Task | Instruction | Short Version |
|------|-------------|---------------|
| Full conversion | "Convert this page to docling." | - |
| Chart extraction | "Convert chart to table." | `<chart>` |
| Formula extraction | "Convert formula to LaTeX." | `<formula>` |
| Code extraction | "Convert code to text." | `<code>` |
| Table extraction | "Convert table to OTSL." | `<otsl>` |

## OCR vs Vision Models

### OCR (RapidOCR - currently enabled)
- Extracts text characters from images
- Fast, runs locally, no API costs
- Already integrated in Docling by default
- Cannot describe non-text content (photos, diagrams, charts)

### Vision Models (VLM Pipeline)
- Understands and describes visual content
- Handles images, diagrams, charts, complex layouts
- More comprehensive but slower/more resource-intensive
- Can also perform OCR as part of its capabilities

### Hybrid Approach (Best Practice)
1. Use OCR for text extraction (fast, efficient)
2. Use VLM for images where OCR returns minimal/no text
3. Combines speed of OCR with comprehensive coverage of VLM

## Performance Considerations

### With RTX 2080 GPU:
- Text-based PDF (75 pages): ~2-5 minutes
- Scanned PDF with OCR (75 pages): ~10-20 minutes
- Complex layouts with VLM: Will be slower but more accurate

### First Run Notes:
- Models will be downloaded (several GB)
- Subsequent runs use cached models
- GPU acceleration significantly faster than CPU

## Model Architecture Details

Granite-Docling-258M components:
- Vision encoder: siglip2-base-patch16-512
- Vision-language connector: pixel shuffle projector
- Language model: Granite 165M
- Output format: DocTags (internal format) converted to Markdown/HTML/JSON

## Code Style Preferences

- Minimize comments - write self-documenting code
- Only comment complex or non-obvious logic
- Use clear variable and function names
- No redundant documentation

## Dependencies

Core packages (installed via uv):
- docling (main library)
- torch + torchvision (with CUDA 12.1 support from pytorch.org/whl/cu121)
- transformers (for VLM models)
- Additional dependencies installed automatically by docling

## Testing Strategy

Test with diverse document types:
1. Simple text-only PDFs
2. Scanned documents (OCR test)
3. Academic papers (layout detection, math, figures)
4. Financial reports (table extraction)
5. Documents with images/diagrams (VLM test)

## Important Notes

- VLM pipeline replaces `<!-- image -->` placeholders with actual content descriptions
- Granite-Docling is designed to work within Docling, not as standalone image understanding
- For general image tasks, use Granite Vision models instead
- Model may hallucinate on complex or ambiguous content - verify outputs
- Best used with Granite Guardian for additional safety in production

## Resources

- Docling Documentation: https://docling-project.github.io/docling/
- VLM Pipeline Examples: https://docling-project.github.io/docling/examples/minimal_vlm_pipeline/
- Granite-Docling Model: https://huggingface.co/ibm-granite/granite-docling-258M
- API Integration Guide: https://docling-project.github.io/docling/examples/vlm_pipeline_api_model/
