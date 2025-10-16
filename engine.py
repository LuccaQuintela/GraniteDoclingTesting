import logging
from datetime import datetime
from docling.document_converter import DocumentConverter
from typing import Union, List
from pathlib import Path

logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)
log_file = logs_dir / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Engine:
    def __init__(self):
        logger.info("Initializing Engine")
        self.converter = DocumentConverter()
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

            logger.info(f"Exporting to markdown and HTML...")
            markdown_output = result.document.export_to_markdown()
            html_output = result.document.export_to_html()

            logger.info(f"Writing markdown to: {md_output_path}")
            md_output_path.write_text(markdown_output, encoding="utf-8")

            logger.info(f"Writing HTML to: {html_output_path}")
            html_output_path.write_text(html_output, encoding="utf-8")

            logger.info(f"[{idx}/{len(file_names)}] Completed: {name}")

        logger.info("All conversions complete")

    def convert(self, path: Path):
        return self.converter.convert(str(path))
