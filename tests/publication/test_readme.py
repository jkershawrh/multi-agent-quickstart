"""Stage 5: Publication validation — README meets all BLOCKER requirements."""
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
DOCS_IMAGES = ROOT / "docs" / "images"

REQUIRED_SECTIONS = [
    "Table of Contents",
    "Overview",
    "Detailed description",
    "Architecture diagrams",
    "Requirements",
    "Minimum hardware requirements",
    "Minimum software requirements",
    "Required user permissions",
    "Deploy",
    "Prerequisites",
    "Delete",
    "Repository structure",
    "Tags",
]

APPROVED_INDUSTRIES = [
    "Automotive",
    "Banking and securities",
    "Broadcasting and cable",
    "Education",
    "Government",
    "Health insurance payer",
    "Healthcare provider",
    "Insurance",
    "Life sciences",
    "Manufacturing",
    "Media and IT services",
    "Retail",
    "Telecommunications",
    "Transportation",
    "Utilities",
    "Wholesale trade",
]

REQUIRED_TAG_KEYS = ["Title", "Description", "Industry", "Product", "Contributor org"]


@pytest.fixture
def readme_text():
    assert README.exists(), "README.md not found"
    return README.read_text()


@pytest.fixture
def readme_lines(readme_text):
    return readme_text.splitlines()


class TestTitleAndDescription:

    def test_h1_exists(self, readme_lines):
        h1_lines = [l for l in readme_lines if l.startswith("# ")]
        assert len(h1_lines) >= 1, "No H1 heading found"

    def test_h1_under_64_chars(self, readme_lines):
        h1 = next(l for l in readme_lines if l.startswith("# "))
        title = h1.lstrip("# ").strip()
        assert len(title) <= 64, f"H1 title is {len(title)} chars, max 64: '{title}'"

    def test_h1_starts_with_action_verb(self, readme_lines):
        h1 = next(l for l in readme_lines if l.startswith("# "))
        title = h1.lstrip("# ").strip()
        first_word = title.split()[0] if title.split() else ""
        action_verbs = [
            "Deploy", "Build", "Accelerate", "Route", "Detect", "Encrypt",
            "Govern", "Scale", "Optimize", "Orchestrate", "Automate",
            "Monitor", "Secure", "Analyze", "Create", "Run", "Serve",
            "Stream", "Transform", "Classify", "Boost", "Catch", "Certify",
            "Coordinate", "Cut", "Enforce", "Ensure", "Find", "Get", "Go",
            "Handle", "Know", "Let", "Make", "Prevent", "Protect", "Prove",
            "Reduce", "Resolve", "Solve", "Stop", "Surface",
        ]
        assert first_word in action_verbs, (
            f"H1 title should start with an action verb, got '{first_word}'"
        )

    def test_short_description_exists(self, readme_lines):
        h1_idx = next(i for i, l in enumerate(readme_lines) if l.startswith("# "))
        desc_lines = []
        for line in readme_lines[h1_idx + 1:]:
            if line.startswith(("#", "## ")):
                break
            if line.strip():
                desc_lines.append(line.strip())
        assert desc_lines, "No short description found after H1"

    def test_short_description_under_160_chars(self, readme_lines):
        h1_idx = next(i for i, l in enumerate(readme_lines) if l.startswith("# "))
        desc_lines = []
        for line in readme_lines[h1_idx + 1:]:
            if line.startswith("#"):
                break
            if line.strip():
                desc_lines.append(line.strip())
        if desc_lines:
            desc = " ".join(desc_lines)
            assert len(desc) <= 160, f"Short description is {len(desc)} chars, max 160"


class TestRequiredSections:

    def test_sections_present(self, readme_text):
        headings = re.findall(r"^#{1,4}\s+(.+)$", readme_text, re.MULTILINE)
        heading_text = [h.strip() for h in headings]
        for section in REQUIRED_SECTIONS:
            assert any(
                section.lower() in h.lower() for h in heading_text
            ), f"Missing required section: '{section}'"

    def test_architecture_diagram_exists(self):
        assert DOCS_IMAGES.exists(), "docs/images/ directory not found"
        images = list(DOCS_IMAGES.glob("*"))
        assert images, "No architecture diagram found in docs/images/"

    def test_architecture_diagram_has_alt_text(self, readme_text):
        img_refs = re.findall(r"!\[([^\]]*)\]", readme_text)
        for alt in img_refs:
            assert alt.strip(), "Image found with empty alt text"
            assert alt.lower() not in ("image", "image1", "screenshot"), (
                f"Non-descriptive alt text: '{alt}'"
            )


class TestTags:

    def test_tags_section_exists(self, readme_text):
        assert re.search(r"^##\s+Tags", readme_text, re.MULTILINE), (
            "Missing ## Tags section"
        )

    def test_required_tag_keys(self, readme_text):
        tags_match = re.search(r"^##\s+Tags\s*\n(.*?)(?=^##|\Z)", readme_text, re.MULTILINE | re.DOTALL)
        assert tags_match, "Cannot find Tags section content"
        tags_content = tags_match.group(1)
        for key in REQUIRED_TAG_KEYS:
            assert re.search(rf"\*\*{key}:\*\*", tags_content), (
                f"Missing required tag: **{key}:**"
            )

    def test_tag_format_bold_key(self, readme_text):
        tags_match = re.search(r"^##\s+Tags\s*\n(.*?)(?=^##|\Z)", readme_text, re.MULTILINE | re.DOTALL)
        if not tags_match:
            pytest.skip("No Tags section")
        tag_lines = [l.strip() for l in tags_match.group(1).splitlines() if l.strip().startswith("-")]
        for line in tag_lines:
            assert re.match(r"^-\s+\*\*\w[\w\s]*:\*\*\s+.+", line), (
                f"Tag line not in '- **Key:** value' format: '{line}'"
            )

    def test_industry_tag_valid(self, readme_text):
        tags_match = re.search(r"^##\s+Tags\s*\n(.*?)(?=^##|\Z)", readme_text, re.MULTILINE | re.DOTALL)
        if not tags_match:
            pytest.skip("No Tags section")
        industry_match = re.search(r"\*\*Industry:\*\*\s+(.+)", tags_match.group(1))
        assert industry_match, "Industry tag not found"
        industry = industry_match.group(1).strip()
        assert industry in APPROVED_INDUSTRIES, (
            f"Industry '{industry}' not in approved list"
        )


class TestNoSecrets:

    def test_no_api_keys_in_source(self):
        patterns = [
            r'api_key\s*[:=]\s*["\x27][A-Za-z0-9]',
            r'password\s*[:=]\s*["\x27][A-Za-z0-9]',
            r'secret\s*[:=]\s*["\x27][A-Za-z0-9]',
            r'sk-[A-Za-z0-9]{20,}',
        ]
        violations = []
        for ext in ("*.py", "*.yaml", "*.yml", "*.json"):
            for f in ROOT.rglob(ext):
                if ".git" in f.parts or "node_modules" in f.parts or ".venv" in f.parts or "venv" in f.parts:
                    continue
                text = f.read_text(errors="ignore")
                for pat in patterns:
                    matches = re.findall(pat, text)
                    if matches:
                        violations.append(f"{f.relative_to(ROOT)}: matches {pat}")
        assert not violations, "Potential secrets found:\n" + "\n".join(violations)


class TestLinks:

    def test_no_broken_internal_links(self, readme_text):
        internal_links = re.findall(r"\[.*?\]\((?!http)(.*?)\)", readme_text)
        for link in internal_links:
            if link.startswith("#"):
                continue
            target = ROOT / link
            assert target.exists(), f"Broken internal link: {link}"
