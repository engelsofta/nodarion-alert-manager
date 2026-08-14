"""Repository-level release, HACS and privacy checks."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "nodarion_pager"
REPOSITORY = "https://github.com/engelsofta/nodarion-alert-manager"
ASSET = "nodarion-alert-manager.zip"


class ReleaseContractTests(unittest.TestCase):
    """Keep the public repository installable and free of obvious private data."""

    def test_hacs_and_manifest_metadata_match(self) -> None:
        hacs = json.loads((ROOT / "hacs.json").read_text(encoding="utf-8"))
        manifest = json.loads((COMPONENT / "manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(hacs["filename"], ASSET)
        self.assertTrue(hacs["zip_release"])
        self.assertFalse(hacs["content_in_root"])
        self.assertEqual(manifest["documentation"], REPOSITORY)
        self.assertEqual(manifest["issue_tracker"], f"{REPOSITORY}/issues")
        self.assertRegex(manifest["version"], r"^\d+\.\d+\.\d+$")
        constants = (COMPONENT / "const.py").read_text(encoding="utf-8")
        self.assertIn(f'VERSION = "{manifest["version"]}"', constants)
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn(f'## {manifest["version"]}', changelog)

    def test_readme_documents_both_languages_and_release_asset(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("## Deutsch", readme)
        self.assertIn("## English", readme)
        self.assertIn(ASSET, readme)
        self.assertIn("github/downloads/engelsofta/nodarion-alert-manager", readme)
        self.assertIn("hacs_repository", readme)

    def test_release_workflow_builds_the_hacs_asset(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn(ASSET, workflow)
        self.assertIn("softprops/action-gh-release@v2", workflow)
        self.assertIn("custom_components/nodarion_pager", workflow)

    def test_no_obvious_secrets_or_private_machine_paths(self) -> None:
        excluded = {".git", "__pycache__", ".pytest_cache", ".ruff_cache"}
        text_files = []
        for path in ROOT.rglob("*"):
            if not path.is_file() or any(part in excluded for part in path.parts):
                continue
            if path.suffix.lower() in {".pyc", ".png", ".jpg", ".jpeg", ".gif", ".zip"}:
                continue
            text_files.append(path)

        private_patterns = {
            "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
            "GitHub token": re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{20,}\b"),
            "Home Assistant token": re.compile(r"\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]+\."),
            "Windows user path": re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+", re.IGNORECASE),
            "Home directory": re.compile(r"/(?:home|Users)/[^/\s]+/"),
        }
        findings = []
        for path in text_files:
            content = path.read_text(encoding="utf-8", errors="ignore")
            for label, pattern in private_patterns.items():
                if pattern.search(content):
                    findings.append(f"{path.relative_to(ROOT)}: {label}")
        self.assertEqual(findings, [], "Potential private data found: " + ", ".join(findings))


if __name__ == "__main__":
    unittest.main()
