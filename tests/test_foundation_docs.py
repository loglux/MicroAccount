from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_core_foundation_files_exist() -> None:
    expected = [
        ROOT / "README.md",
        ROOT / "AGENTS.md",
        ROOT / "Makefile",
        ROOT / "Dockerfile",
        ROOT / "compose.yaml",
        ROOT / ".dockerignore",
        ROOT / "pyproject.toml",
        ROOT / "requirements.txt",
        ROOT / "requirements-dev.txt",
        ROOT / "docs" / "ARCHITECTURE.md",
        ROOT / "docs" / "ROADMAP.md",
        ROOT / "docs" / "UK_RULES.md",
        ROOT / "docs" / "V1_BLUEPRINT.md",
        ROOT / "docs" / "TOOLING.md",
        ROOT / "docs" / "DEPLOYMENT.md",
        ROOT / "docs" / "DOCUMENT_PROCESSING.md",
        ROOT / "app" / "documents" / "__init__.py",
        ROOT / "app" / "documents" / "ingest.py",
        ROOT / "app" / "documents" / "extract.py",
        ROOT / "app" / "documents" / "ocr.py",
        ROOT / "app" / "documents" / "parse.py",
        ROOT / "app" / "documents" / "schemas.py",
        ROOT / "scripts" / "import_claude_pdfs.py",
    ]
    missing = [str(path) for path in expected if not path.exists()]
    assert missing == []
