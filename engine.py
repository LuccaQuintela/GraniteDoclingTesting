import logging
import os
import base64
from datetime import datetime
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.pipeline.vlm_pipeline import VlmPipeline
from docling.datamodel.pipeline_options import PdfPipelineOptions, RapidOcrOptions, VlmPipelineOptions, smolvlm_picture_description
from typing import Union, List, Optional
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)
log_file = logs_dir / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    force=True
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

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

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not found in environment")

        self.openai_client = OpenAI(api_key=api_key)
        logger.info("OpenAI client initialized for image descriptions")

        self.results_dir = Path("results")
        self.results_dir.mkdir(exist_ok=True)
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        logger.info(f"Data directory: {self.data_dir}")
        logger.info(f"Results directory: {self.results_dir}")

    def run(self, file_names: Union[str, List[str]]) -> None:
        if isinstance(file_names, str):
            file_names = [file_names]

        logger.info(f"Starting conversion process for {len(file_names)} file(s)")

        for idx, name in enumerate(file_names, 1):
            logger.info(f"[{idx}/{len(file_names)}] Processing: {name}")

            path = self.data_dir / name

            md_output_path = self.results_dir / f"{path.stem}.md"
            html_output_path = self.results_dir / f"{path.stem}.html"

            if md_output_path.exists() and html_output_path.exists():
                logger.info(f"Outputs already exist for {name}, skipping conversion")
                continue

            logger.info(f"Converting {name}...")
            result = self.convert(path)
            logger.info(f"Conversion complete for {name}")

            logger.info(f"Running post-processing for images...")
            markdown_output = self.post_processing(result, md_output_path)

            logger.info(f"Exporting to HTML...")
            html_output = result.document.export_to_html()

            logger.info(f"Writing markdown to: {md_output_path}")
            md_output_path.write_text(markdown_output, encoding="utf-8")

            logger.info(f"[{idx}/{len(file_names)}] Completed: {name}")

        logger.info("All conversions complete")

    def convert(self, path: Path):
        return self.converter.convert(str(path))

    def describe_image_with_chatgpt(self, image_path: Path, context: str = "") -> Optional[str]:
        try:
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')

            prompt = "Describe this image in detail, focusing on the key content and information it conveys."
            if context:
                prompt = f"{context}\n\n{prompt}"

            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )

            description = response.choices[0].message.content
            logger.info(f"Generated description for {image_path.name}")
            return description

        except Exception as e:
            logger.error(f"Error describing image {image_path}: {e}")
            return None

    def post_processing(self, result, output_path: Path, context: str = "") -> str:
        logger.info("Starting post-processing for image descriptions")

        markdown_output = result.document.export_to_markdown()

        images = result.document.pictures
        if not images:
            logger.info("No images found in document")
            return markdown_output

        logger.info(f"Found {len(images)} images to process")

        for idx, image in enumerate(images, 1):
            logger.info(f"Processing image {idx}/{len(images)}")

            try:
                image_path = self.results_dir / f"{output_path.stem}_image_{idx}.png"
                pil_image = image.get_image(result.document)

                if pil_image is None:
                    logger.warning(f"Could not extract image {idx}, skipping")
                    continue

                pil_image.save(image_path)
                logger.info(f"Saved image to {image_path}")

                description = self.describe_image_with_chatgpt(image_path, context)

                if description:
                    placeholder = f"<!-- image -->"
                    if placeholder in markdown_output:
                        replacement = f"![Image {idx}]({image_path.name})\n\n**Image Description:** {description}"
                        markdown_output = markdown_output.replace(placeholder, replacement, 1)

            except Exception as e:
                logger.error(f"Error processing image {idx}: {e}")
                continue

        logger.info("Post-processing complete")
        return markdown_output
