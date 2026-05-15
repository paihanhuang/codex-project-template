from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from argparse import Namespace
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / ".codex/tools/context_index.py"
SPEC = importlib.util.spec_from_file_location("context_index", MODULE_PATH)
context_index = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules["context_index"] = context_index
SPEC.loader.exec_module(context_index)


CONTEXT_TOML = """
[sources]
code_roots = ["."]
document_roots = []
include = []
exclude = [".git/**", "secret/**", "**/*.pem", ".codex/context/**"]
follow_symlinks = false

[retrieval]
lexical_backend = "sqlite-fts5"
vector_backend = "off"
graph_backend = "off"
rerank = "off"
top_k_initial = 80
top_k_capsule = 20

[chunking.code]
strategy = "tree-sitter-symbols-with-fallback"
max_chunk_tokens = 900
overlap_tokens = 120

[chunking.docs]
strategy = "section-aware"
max_chunk_tokens = 700
overlap_tokens = 100
contextualize_chunks = false
"""


class ContextIndexTests(unittest.TestCase):
    def make_project(self) -> tempfile.TemporaryDirectory:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        (root / ".codex").mkdir()
        (root / ".codex/context.toml").write_text(CONTEXT_TOML, encoding="utf-8")
        return temp

    def test_scan_respects_context_excludes_and_gitignore(self) -> None:
        with self.make_project() as temp:
            root = Path(temp)
            subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            (root / ".gitignore").write_text("ignored.txt\n", encoding="utf-8")
            (root / "keep.py").write_text("def keep():\n    return 'indexed'\n", encoding="utf-8")
            (root / "ignored.txt").write_text("ignored by git\n", encoding="utf-8")
            (root / "cert.pem").write_text("private key placeholder\n", encoding="utf-8")
            (root / "secret").mkdir()
            (root / "secret/data.txt").write_text("secret\n", encoding="utf-8")

            config = context_index.load_config(root)
            records = context_index.build_file_records(root, config)
            paths = {record["path"] for record in records}

            self.assertIn("keep.py", paths)
            self.assertIn(".codex/context.toml", paths)
            self.assertNotIn("ignored.txt", paths)
            self.assertNotIn("cert.pem", paths)
            self.assertNotIn("secret/data.txt", paths)

    def test_index_and_query_lexical_content(self) -> None:
        with self.make_project() as temp:
            root = Path(temp)
            (root / "docs").mkdir()
            (root / "docs/policy.md").write_text(
                "# Policy\n\nCustomer data retention obligations are reviewed yearly.\n",
                encoding="utf-8",
            )

            args = Namespace(
                root=str(root),
                config=".codex/context.toml",
                manifest=".codex/context/manifest.json",
                index=".codex/context/inventory.sqlite",
            )
            with redirect_stdout(StringIO()):
                self.assertEqual(context_index.cmd_index_lexical(args), 0)

            results = context_index.query_index(root, Path(args.index), "retention obligations", 5)
            self.assertTrue(results)
            self.assertEqual(results[0]["path"], "docs/policy.md")

            manifest = json.loads((root / args.manifest).read_text(encoding="utf-8"))
            self.assertEqual(manifest["schema_version"], "context-manifest/v1")
            self.assertTrue(any(file["path"] == "docs/policy.md" for file in manifest["files"]))

    def test_status_detects_stale_files(self) -> None:
        with self.make_project() as temp:
            root = Path(temp)
            target = root / "notes.md"
            target.write_text("alpha\n", encoding="utf-8")

            args = Namespace(
                root=str(root),
                config=".codex/context.toml",
                manifest=".codex/context/manifest.json",
            )
            with redirect_stdout(StringIO()):
                self.assertEqual(context_index.cmd_scan(args), 0)
            target.write_text("alpha beta\n", encoding="utf-8")

            config = context_index.load_config(root)
            report = context_index.status_report(root, config, Path(args.manifest))
            self.assertFalse(report["fresh"])
            self.assertIn("notes.md", report["stale_files"])


if __name__ == "__main__":
    unittest.main()
