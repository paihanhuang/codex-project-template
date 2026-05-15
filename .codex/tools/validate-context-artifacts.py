#!/usr/bin/env python3
"""Validate context-indexing artifacts without external dependencies."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        raise AssertionError(f"missing required file: {path}") from None
    except json.JSONDecodeError as exc:
        raise AssertionError(f"invalid JSON in {path}: {exc}") from None
    if not isinstance(data, dict):
        raise AssertionError(f"{path} must contain a JSON object")
    return data


def require_keys(label: str, data: dict, keys: list[str]) -> None:
    missing = [key for key in keys if key not in data]
    if missing:
        raise AssertionError(f"{label} missing keys: {', '.join(missing)}")


def validate_schema_files() -> None:
    manifest_schema = load_json(ROOT / ".codex/context/schemas/manifest.schema.json")
    capsule_schema = load_json(ROOT / ".codex/context/schemas/capsule.schema.json")

    require_keys(
        "manifest schema",
        manifest_schema,
        ["$schema", "title", "type", "required", "properties"],
    )
    require_keys(
        "capsule schema",
        capsule_schema,
        ["$schema", "title", "type", "required", "properties", "$defs"],
    )

    if manifest_schema.get("properties", {}).get("schema_version", {}).get("const") != "context-manifest/v1":
        raise AssertionError("manifest schema_version const must be context-manifest/v1")
    if capsule_schema.get("properties", {}).get("schema_version", {}).get("const") != "context-capsule/v1":
        raise AssertionError("capsule schema_version const must be context-capsule/v1")


def validate_sample_capsule() -> None:
    capsule = load_json(ROOT / ".codex/context/capsules/sample-context-capsule.json")
    required = [
        "schema_version",
        "capsule_id",
        "created_at",
        "task",
        "token_budget",
        "freshness",
        "sources",
        "evidence",
        "gaps",
        "suggested_raw_reads",
    ]
    require_keys("sample capsule", capsule, required)

    if capsule["schema_version"] != "context-capsule/v1":
        raise AssertionError("sample capsule has wrong schema_version")
    if not isinstance(capsule["sources"], list) or not capsule["sources"]:
        raise AssertionError("sample capsule must include at least one source")
    if not isinstance(capsule["evidence"], list) or not capsule["evidence"]:
        raise AssertionError("sample capsule must include at least one evidence item")

    source_paths = {source.get("path") for source in capsule["sources"] if isinstance(source, dict)}
    for evidence in capsule["evidence"]:
        if not isinstance(evidence, dict):
            raise AssertionError("sample capsule evidence items must be objects")
        require_keys(
            "sample capsule evidence",
            evidence,
            [
                "evidence_id",
                "source_path",
                "source_anchor",
                "retrieval_layers",
                "confidence",
                "token_estimate",
                "summary",
            ],
        )
        if evidence["source_path"] not in source_paths:
            raise AssertionError(
                f"evidence {evidence['evidence_id']} references unknown source_path {evidence['source_path']}"
            )


def validate_manifest_if_present() -> None:
    manifest_path = ROOT / ".codex/context/manifest.json"
    if not manifest_path.exists():
        return
    manifest = load_json(manifest_path)
    require_keys(
        "generated manifest",
        manifest,
        ["schema_version", "generated_at", "extractor_version", "config_hash", "files"],
    )
    if manifest["schema_version"] != "context-manifest/v1":
        raise AssertionError("generated manifest has wrong schema_version")
    if not isinstance(manifest["files"], list):
        raise AssertionError("generated manifest files must be a list")
    for file_record in manifest["files"]:
        if not isinstance(file_record, dict):
            raise AssertionError("generated manifest file entries must be objects")
        require_keys(
            "generated manifest file",
            file_record,
            ["source_id", "path", "hash", "size_bytes", "mtime_utc", "kind", "index_status"],
        )


def validate_config() -> None:
    context_toml = ROOT / ".codex/context.toml"
    if not context_toml.exists():
        raise AssertionError("missing .codex/context.toml")
    text = context_toml.read_text(encoding="utf-8")
    for section in ["[sources]", "[retrieval]", "[chunking.code]", "[chunking.docs]", "[capsules]", "[privacy]"]:
        if section not in text:
            raise AssertionError(f".codex/context.toml missing {section}")
    if 'hosted_vector_store = "disabled"' not in text:
        raise AssertionError("hosted vector stores must default to disabled")


def validate_context_indexing_skill() -> None:
    skill_path = ROOT / ".agents/skills/context-indexing/SKILL.md"
    if not skill_path.exists():
        raise AssertionError("missing .agents/skills/context-indexing/SKILL.md")
    text = skill_path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise AssertionError("context-indexing skill missing YAML frontmatter")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        raise AssertionError("context-indexing skill has invalid frontmatter")
    frontmatter = match.group(1)
    if "name: context-indexing" not in frontmatter:
        raise AssertionError("context-indexing skill frontmatter has wrong name")
    if "description:" not in frontmatter:
        raise AssertionError("context-indexing skill frontmatter missing description")

    required_phrases = [
        "python3 .codex/tools/context_index.py --root . status",
        "python3 .codex/tools/context_index.py --root . index-lexical",
        'python3 .codex/tools/context_index.py --root . query "<query>" --limit 10',
        "Before implementation edits, read the raw files",
        "stale, missing, or unknown context",
        "privacy rules and excludes",
    ]
    missing = [phrase for phrase in required_phrases if phrase not in text]
    if missing:
        raise AssertionError("context-indexing skill missing required rule/command: " + missing[0])


def main() -> int:
    try:
        validate_schema_files()
        validate_sample_capsule()
        validate_manifest_if_present()
        validate_config()
        validate_context_indexing_skill()
    except AssertionError as exc:
        print(f"context artifact validation failed: {exc}", file=sys.stderr)
        return 1
    print("context artifact validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
