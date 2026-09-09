import re
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^]]+\]\(([^)]+)\)")


def test_relative_markdown_links_resolve():
    markdown_files = [REPOSITORY_ROOT / "README.md", REPOSITORY_ROOT / "CONTRIBUTING.md"]
    markdown_files.extend(sorted((REPOSITORY_ROOT / "docs").glob("*.md")))

    broken = []
    for document in markdown_files:
        for target in MARKDOWN_LINK.findall(document.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "#")):
                continue
            path = target.split("#", maxsplit=1)[0]
            if path and not (document.parent / path).resolve().exists():
                broken.append(f"{document.relative_to(REPOSITORY_ROOT)} -> {target}")

    assert not broken, "Broken documentation links:\n" + "\n".join(broken)


def test_required_project_documentation_exists():
    required = {
        "architecture.md",
        "api.md",
        "deployment.md",
        "operations.md",
        "security-privacy.md",
        "model-card.md",
        "testing.md",
        "production-checklist.md",
    }
    available = {path.name for path in (REPOSITORY_ROOT / "docs").glob("*.md")}
    assert required <= available
