import logging
import os
from datetime import datetime
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from typing import Union, List, Optional, Literal, Set
from pathlib import Path
from google import genai
from google.genai import types
from PIL import Image
from dotenv import load_dotenv

ExportFormat = Literal["markdown", "doctags"]

load_dotenv()

logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)
log_file = logs_dir / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    file_handler = logging.FileHandler(log_file, mode='w')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

class Engine:
    def __init__(self):
        logger.info("Initializing Engine")
        logger.info("Using Docling for text extraction")

        pipeline_options = PdfPipelineOptions(
            generate_page_images=True,
            images_scale=2.00,
            do_picture_description=False,
        )

        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options,
                ),
            }
        )

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY not found in environment")

        self.gemini_client = genai.Client(api_key=api_key)
        logger.info("Gemini client initialized for image descriptions")

        self.results_dir = Path("results")
        self.results_dir.mkdir(exist_ok=True)
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        logger.info(f"Data directory: {self.data_dir}")
        logger.info(f"Results directory: {self.results_dir}")

    def run(
        self,
        file_names: Union[str, List[str]],
        export_formats: Optional[Union[ExportFormat, List[ExportFormat]]] = None
    ) -> None:
        if isinstance(file_names, str):
            file_names = [file_names]

        if export_formats is None:
            export_formats = ["markdown"]
        elif isinstance(export_formats, str):
            export_formats = [export_formats]

        export_formats_set: Set[ExportFormat] = set(export_formats)

        logger.info(f"Starting conversion process for {len(file_names)} file(s)")
        logger.info(f"Export formats: {', '.join(export_formats_set)}")

        for idx, name in enumerate(file_names, 1):
            logger.info(f"[{idx}/{len(file_names)}] Processing: {name}")

            path = self.data_dir / name

            output_paths = {}
            if "markdown" in export_formats_set:
                output_paths["markdown"] = self.results_dir / f"{path.stem}.md"
            if "doctags" in export_formats_set:
                output_paths["doctags"] = self.results_dir / f"{path.stem}_doctags.xml"

            if all(p.exists() for p in output_paths.values()):
                logger.info(f"All outputs already exist for {name}, skipping conversion")
                continue

            logger.info(f"Converting {name}...")
            result = self.convert(path)
            logger.info(f"Conversion complete for {name}")

            logger.info(f"Running post-processing for images...")
            outputs = self.post_processing(result, path.stem, export_formats_set)

            for format_type, content in outputs.items():
                output_path = output_paths[format_type]
                logger.info(f"Writing {format_type} to: {output_path}")
                output_path.write_text(content, encoding="utf-8")

            logger.info(f"[{idx}/{len(file_names)}] Completed: {name}")

        logger.info("All conversions complete")

    def convert(self, path: Path):
        return self.converter.convert(str(path))

    def describe_image_with_gemini(self, image_path: Path, context: str = "") -> Optional[str]:
        try:
            with open(image_path, "rb") as f:
                image_data = f.read()

            prompt = "Describe this image in detail, focusing on the key content and information it conveys."
            if context:
                prompt = f"{context}\n\n{prompt}"

            response = self.gemini_client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=[
                    types.Part(text=prompt),
                    types.Part(inline_data=types.Blob(data=image_data, mime_type="image/png"))
                ]
            )

            description = response.text
            logger.info(f"Generated description for {image_path.name}")
            return description

        except Exception as e:
            logger.error(f"Error describing image {image_path}: {e}")
            return None

    def post_processing(
        self,
        result,
        output_stem: str,
        export_formats: Set[ExportFormat],
        context: str = ""
    ) -> dict[ExportFormat, str]:
        logger.info("Starting post-processing for image descriptions")

        outputs = {}
        if "markdown" in export_formats:
            outputs["markdown"] = result.document.export_to_markdown()
        if "doctags" in export_formats:
            outputs["doctags"] = result.document.export_to_document_tokens()

        images = result.document.pictures
        if not images:
            logger.info("No images found in document")
            return outputs

        logger.info(f"Found {len(images)} images to process")

        image_descriptions = []
        for idx, image in enumerate(images, 1):
            logger.info(f"Processing image {idx}/{len(images)}")

            try:
                image_path = self.results_dir / f"{output_stem}_image_{idx}.png"
                pil_image = image.get_image(result.document)

                if pil_image is None:
                    logger.warning(f"Could not extract image {idx}, skipping")
                    image_descriptions.append(None)
                    continue

                pil_image.save(image_path)
                logger.info(f"Saved image to {image_path}")

                description = self.describe_image_with_gemini(image_path, context)
                image_descriptions.append({
                    "index": idx,
                    "path": image_path.name,
                    "description": description
                })

            except Exception as e:
                logger.error(f"Error processing image {idx}: {e}")
                image_descriptions.append(None)
                continue

        for format_type in export_formats:
            if format_type == "markdown":
                for img_data in image_descriptions:
                    if img_data and img_data["description"]:
                        placeholder = "<!-- image -->"
                        if placeholder in outputs["markdown"]:
                            replacement = f"![Image {img_data['index']}]({img_data['path']})\n\n**Image Description:** {img_data['description']}"
                            outputs["markdown"] = outputs["markdown"].replace(placeholder, replacement, 1)

            elif format_type == "doctags":
                for img_data in image_descriptions:
                    if img_data and img_data["description"]:
                        placeholder = "<picture>"
                        if placeholder in outputs["doctags"]:
                            replacement = f'<picture description="{img_data["description"]}">'
                            outputs["doctags"] = outputs["doctags"].replace(placeholder, replacement, 1)

        logger.info("Post-processing complete")
        return outputs 
