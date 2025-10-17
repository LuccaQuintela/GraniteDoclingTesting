from engine import Engine

def main() -> None:
    engine = Engine()
    # data = ["medical_3d_printing.pdf", "trace_anything.pdf", "vision_language_models.pdf", "farm.pdf"]
    data = "farm.pdf"
    export_formats = ["doctags", "markdown"]
    engine.run(data, export_formats=export_formats)

if __name__ == "__main__":
    main()
