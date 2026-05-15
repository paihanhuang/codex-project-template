#!/usr/bin/env python3
"""Local context inventory and lexical indexing for Codex projects."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback.
    tomllib = None


EXTRACTOR_VERSION = "context-index/0.2"
MANIFEST_VERSION = "context-manifest/v1"
DEFAULT_MANIFEST = Path(".codex/context/manifest.json")
DEFAULT_INDEX = Path(".codex/context/inventory.sqlite")
DEFAULT_CONFIG = Path(".codex/context.toml")

CODE_EXTENSIONS = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".css",
    ".go",
    ".h",
    ".hpp",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".m",
    ".mm",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".scala",
    ".sh",
    ".sql",
    ".swift",
    ".ts",
    ".tsx",
}

DOC_EXTENSIONS = {
    ".adoc",
    ".docx",
    ".html",
    ".htm",
    ".md",
    ".pdf",
    ".rst",
    ".txt",
}

CONFIG_EXTENSIONS = {
    ".cfg",
    ".conf",
    ".ini",
    ".json",
    ".lock",
    ".toml",
    ".yaml",
    ".yml",
    ".xml",
}

LANGUAGE_BY_EXTENSION = {
    ".c": "c",
    ".cc": "cpp",
    ".cpp": "cpp",
    ".cs": "csharp",
    ".css": "css",
    ".go": "go",
    ".h": "c",
    ".hpp": "cpp",
    ".html": "html",
    ".java": "java",
    ".js": "javascript",
    ".jsx": "javascript",
    ".json": "json",
    ".md": "markdown",
    ".php": "php",
    ".py": "python",
    ".rb": "ruby",
    ".rs": "rust",
    ".sh": "shell",
    ".sql": "sql",
    ".toml": "toml",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".txt": "text",
    ".yaml": "yaml",
    ".yml": "yaml",
}


@dataclass(frozen=True)
class Config:
    code_roots: list[str]
    document_roots: list[str]
    include: list[str]
    exclude: list[str]
    follow_symlinks: bool
    code_max_chunk_tokens: int
    doc_max_chunk_tokens: int


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel_path(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def load_config(root: Path, config_path: Path = DEFAULT_CONFIG) -> Config:
    path = root / config_path
    if tomllib is None:
        raise RuntimeError("Python 3.11+ is required to read TOML context config")
    with path.open("rb") as handle:
        raw = tomllib.load(handle)

    sources = raw.get("sources", {})
    chunking = raw.get("chunking", {})
    code_chunking = chunking.get("code", {})
    doc_chunking = chunking.get("docs", {})
    return Config(
        code_roots=list(sources.get("code_roots", ["."])),
        document_roots=list(sources.get("document_roots", [])),
        include=list(sources.get("include", [])),
        exclude=list(sources.get("exclude", [])),
        follow_symlinks=bool(sources.get("follow_symlinks", False)),
        code_max_chunk_tokens=int(code_chunking.get("max_chunk_tokens", 900)),
        doc_max_chunk_tokens=int(doc_chunking.get("max_chunk_tokens", 700)),
    )


def match_pattern(path: str, pattern: str) -> bool:
    normalized = path.strip("/")
    pattern = pattern.strip("/")
    if not pattern:
        return False
    if pattern.endswith("/**"):
        prefix = pattern[:-3].strip("/")
        return normalized == prefix or normalized.startswith(prefix + "/")
    return fnmatch.fnmatch(normalized, pattern) or fnmatch.fnmatch("/" + normalized, pattern)


def is_excluded(path: str, config: Config) -> tuple[bool, str | None]:
    if config.include and not any(match_pattern(path, pattern) for pattern in config.include):
        return True, "not matched by include patterns"
    for pattern in config.exclude:
        if match_pattern(path, pattern):
            return True, f"matched exclude pattern {pattern}"
    return False, None


def run_git(root: Path, args: list[str]) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def git_head(root: Path) -> str | None:
    result = run_git(root, ["rev-parse", "HEAD"])
    if result.returncode != 0:
        return None
    return result.stdout.decode("utf-8", errors="replace").strip() or None


def git_candidate_paths(root: Path) -> list[str] | None:
    result = run_git(root, ["ls-files", "-co", "--exclude-standard", "-z"])
    if result.returncode != 0:
        return None
    return sorted(path.decode("utf-8", errors="replace") for path in result.stdout.split(b"\0") if path)


def git_status_map(root: Path) -> dict[str, str]:
    result = run_git(root, ["status", "--porcelain=v1", "-z"])
    if result.returncode != 0:
        return {}
    entries = [entry for entry in result.stdout.split(b"\0") if entry]
    status: dict[str, str] = {}
    skip_next = False
    for index, entry in enumerate(entries):
        if skip_next:
            skip_next = False
            continue
        text = entry.decode("utf-8", errors="replace")
        if len(text) < 4:
            continue
        code = text[:2]
        path = text[3:]
        status[path] = code
        if code.strip().startswith("R") and index + 1 < len(entries):
            new_path = entries[index + 1].decode("utf-8", errors="replace")
            status[new_path] = code
            skip_next = True
    return status


def walk_candidate_paths(root: Path, config: Config) -> list[str]:
    roots = config.code_roots + config.document_roots
    if not roots:
        roots = ["."]
    paths: list[str] = []
    for source_root in roots:
        absolute_root = (root / source_root).resolve()
        if not absolute_root.exists():
            continue
        if absolute_root.is_file():
            paths.append(rel_path(absolute_root, root))
            continue
        for dirpath, dirnames, filenames in os.walk(absolute_root, followlinks=config.follow_symlinks):
            current = Path(dirpath)
            kept_dirs = []
            for dirname in dirnames:
                candidate = current / dirname
                try:
                    relative = rel_path(candidate, root)
                except ValueError:
                    continue
                excluded, _ = is_excluded(relative, config)
                if not excluded:
                    kept_dirs.append(dirname)
            dirnames[:] = kept_dirs
            for filename in filenames:
                candidate = current / filename
                try:
                    paths.append(rel_path(candidate, root))
                except ValueError:
                    continue
    return sorted(set(paths))


def candidate_paths(root: Path, config: Config) -> list[str]:
    git_paths = git_candidate_paths(root)
    if git_paths is not None:
        roots = [Path(item).as_posix().strip("/") for item in config.code_roots + config.document_roots]
        roots = [item for item in roots if item and item != "."]
        if roots:
            git_paths = [
                path for path in git_paths if any(path == source_root or path.startswith(source_root + "/") for source_root in roots)
            ]
        return git_paths
    return walk_candidate_paths(root, config)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def is_binary(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            sample = handle.read(8192)
    except OSError:
        return True
    return b"\0" in sample


def classify(path: Path) -> tuple[str, str | None]:
    extension = path.suffix.lower()
    language = LANGUAGE_BY_EXTENSION.get(extension)
    if is_binary(path):
        return "binary", language
    if extension in CODE_EXTENSIONS:
        return "code", language
    if extension in DOC_EXTENSIONS:
        return "document", language
    if extension in CONFIG_EXTENSIONS or path.name in {"Makefile", "Dockerfile", "AGENTS.md"}:
        return "config", language
    return "unknown", language


def mtime_utc(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_file_records(root: Path, config: Config) -> list[dict]:
    status_map = git_status_map(root)
    records: list[dict] = []
    for path_text in candidate_paths(root, config):
        excluded, reason = is_excluded(path_text, config)
        absolute = root / path_text
        if excluded or not absolute.is_file():
            continue
        kind, language = classify(absolute)
        file_hash = sha256_file(absolute)
        source_id = sha256_text(f"{path_text}\0{file_hash}")[:16]
        records.append(
            {
                "source_id": source_id,
                "path": path_text,
                "hash": file_hash,
                "size_bytes": absolute.stat().st_size,
                "mtime_utc": mtime_utc(absolute),
                "kind": kind,
                "language": language,
                "index_status": "indexed",
                "ignore_reason": reason,
                "git_status": status_map.get(path_text),
            }
        )
    return sorted(records, key=lambda item: item["path"])


def build_manifest(root: Path, config: Config, records: list[dict]) -> dict:
    context_config = (root / DEFAULT_CONFIG).read_text(encoding="utf-8")
    return {
        "schema_version": MANIFEST_VERSION,
        "generated_at": utc_now(),
        "git_head": git_head(root),
        "extractor_version": EXTRACTOR_VERSION,
        "config_hash": sha256_text(context_config),
        "files": records,
    }


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_manifest(root: Path, manifest_path: Path) -> dict | None:
    path = root / manifest_path
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_text(path: Path) -> str | None:
    if is_binary(path):
        return None
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def chunk_text(text: str, max_tokens: int) -> Iterable[tuple[int, int, str]]:
    max_chars = max(1000, max_tokens * 4)
    lines = text.splitlines()
    start_line = 1
    current: list[str] = []
    current_chars = 0
    for line_number, line in enumerate(lines, start=1):
        line_chars = len(line) + 1
        if current and current_chars + line_chars > max_chars:
            yield start_line, line_number - 1, "\n".join(current)
            start_line = line_number
            current = []
            current_chars = 0
        current.append(line)
        current_chars += line_chars
    if current:
        yield start_line, start_line + len(current) - 1, "\n".join(current)


def build_lexical_index(root: Path, manifest: dict, index_path: Path, config: Config) -> int:
    database_path = root / index_path
    database_path.parent.mkdir(parents=True, exist_ok=True)
    if database_path.exists():
        database_path.unlink()

    connection = sqlite3.connect(database_path)
    try:
        connection.executescript(
            """
            CREATE TABLE files (
              source_id TEXT PRIMARY KEY,
              path TEXT UNIQUE NOT NULL,
              hash TEXT NOT NULL,
              size_bytes INTEGER NOT NULL,
              mtime_utc TEXT NOT NULL,
              kind TEXT NOT NULL,
              language TEXT,
              git_status TEXT
            );
            CREATE TABLE chunks (
              chunk_id TEXT PRIMARY KEY,
              source_id TEXT NOT NULL,
              path TEXT NOT NULL,
              chunk_index INTEGER NOT NULL,
              start_line INTEGER NOT NULL,
              end_line INTEGER NOT NULL,
              text TEXT NOT NULL
            );
            CREATE VIRTUAL TABLE chunks_fts USING fts5(
              chunk_id UNINDEXED,
              path UNINDEXED,
              text
            );
            """
        )
    except sqlite3.OperationalError as exc:
        connection.close()
        raise RuntimeError(f"SQLite FTS5 is required for lexical indexing: {exc}") from exc

    chunk_count = 0
    for file_record in manifest["files"]:
        connection.execute(
            """
            INSERT INTO files(source_id, path, hash, size_bytes, mtime_utc, kind, language, git_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                file_record["source_id"],
                file_record["path"],
                file_record["hash"],
                file_record["size_bytes"],
                file_record["mtime_utc"],
                file_record["kind"],
                file_record.get("language"),
                file_record.get("git_status"),
            ),
        )
        if file_record["kind"] == "binary":
            continue
        text = read_text(root / file_record["path"])
        if not text:
            continue
        max_tokens = config.doc_max_chunk_tokens if file_record["kind"] == "document" else config.code_max_chunk_tokens
        for chunk_index, (start_line, end_line, chunk) in enumerate(chunk_text(text, max_tokens)):
            chunk_id = f"{file_record['source_id']}:{chunk_index}"
            connection.execute(
                """
                INSERT INTO chunks(chunk_id, source_id, path, chunk_index, start_line, end_line, text)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chunk_id,
                    file_record["source_id"],
                    file_record["path"],
                    chunk_index,
                    start_line,
                    end_line,
                    chunk,
                ),
            )
            connection.execute(
                "INSERT INTO chunks_fts(chunk_id, path, text) VALUES (?, ?, ?)",
                (chunk_id, file_record["path"], chunk),
            )
            chunk_count += 1
    connection.commit()
    connection.close()
    return chunk_count


def fts_query(query: str) -> str:
    terms = re.findall(r"[A-Za-z0-9_]+", query)
    return " OR ".join(terms)


def query_index(root: Path, index_path: Path, query: str, limit: int) -> list[dict]:
    database_path = root / index_path
    if not database_path.exists():
        raise FileNotFoundError(f"lexical index not found: {database_path}")
    match = fts_query(query)
    if not match:
        return []
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    rows = connection.execute(
        """
        SELECT
          chunks.chunk_id,
          chunks.path,
          chunks.start_line,
          chunks.end_line,
          bm25(chunks_fts) AS rank,
          snippet(chunks_fts, 2, '[', ']', '...', 24) AS snippet
        FROM chunks_fts
        JOIN chunks ON chunks.chunk_id = chunks_fts.chunk_id
        WHERE chunks_fts MATCH ?
        ORDER BY rank
        LIMIT ?
        """,
        (match, limit),
    ).fetchall()
    connection.close()
    return [dict(row) for row in rows]


def status_report(root: Path, config: Config, manifest_path: Path) -> dict:
    manifest = load_manifest(root, manifest_path)
    current_records = build_file_records(root, config)
    current_by_path = {record["path"]: record for record in current_records}
    dirty = sorted(record["path"] for record in current_records if record.get("git_status"))
    if manifest is None:
        return {
            "manifest": "missing",
            "fresh": False,
            "indexed_files": 0,
            "current_files": len(current_records),
            "new_files": sorted(current_by_path),
            "stale_files": [],
            "missing_files": [],
            "dirty_files": dirty,
        }

    indexed_by_path = {record["path"]: record for record in manifest.get("files", [])}
    stale = sorted(
        path
        for path, current in current_by_path.items()
        if path in indexed_by_path and indexed_by_path[path].get("hash") != current.get("hash")
    )
    missing = sorted(path for path in indexed_by_path if path not in current_by_path)
    new = sorted(path for path in current_by_path if path not in indexed_by_path)
    return {
        "manifest": str(manifest_path),
        "fresh": not (stale or missing or new),
        "indexed_files": len(indexed_by_path),
        "current_files": len(current_by_path),
        "new_files": new,
        "stale_files": stale,
        "missing_files": missing,
        "dirty_files": dirty,
        "generated_at": manifest.get("generated_at"),
        "git_head": manifest.get("git_head"),
    }


def cmd_scan(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    config = load_config(root, Path(args.config))
    records = build_file_records(root, config)
    manifest = build_manifest(root, config, records)
    write_json(root / args.manifest, manifest)
    print(json.dumps({"manifest": args.manifest, "files": len(records)}, indent=2))
    return 0


def cmd_index_lexical(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    config = load_config(root, Path(args.config))
    records = build_file_records(root, config)
    manifest = build_manifest(root, config, records)
    write_json(root / args.manifest, manifest)
    chunks = build_lexical_index(root, manifest, Path(args.index), config)
    print(json.dumps({"manifest": args.manifest, "index": args.index, "files": len(records), "chunks": chunks}, indent=2))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    config = load_config(root, Path(args.config))
    report = status_report(root, config, Path(args.manifest))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["fresh"] else 1


def cmd_query(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    results = query_index(root, Path(args.index), args.query, args.limit)
    print(json.dumps({"query": args.query, "results": results}, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="project root")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="context TOML path relative to root")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan", help="write a context manifest")
    scan.add_argument("--manifest", default=str(DEFAULT_MANIFEST), help="manifest path relative to root")
    scan.set_defaults(func=cmd_scan)

    lexical = subparsers.add_parser("index-lexical", help="write manifest and SQLite FTS5 lexical index")
    lexical.add_argument("--manifest", default=str(DEFAULT_MANIFEST), help="manifest path relative to root")
    lexical.add_argument("--index", default=str(DEFAULT_INDEX), help="SQLite index path relative to root")
    lexical.set_defaults(func=cmd_index_lexical)

    status = subparsers.add_parser("status", help="compare manifest with current files")
    status.add_argument("--manifest", default=str(DEFAULT_MANIFEST), help="manifest path relative to root")
    status.set_defaults(func=cmd_status)

    query = subparsers.add_parser("query", help="query the SQLite FTS5 lexical index")
    query.add_argument("query", help="query text")
    query.add_argument("--index", default=str(DEFAULT_INDEX), help="SQLite index path relative to root")
    query.add_argument("--limit", type=int, default=10)
    query.set_defaults(func=cmd_query)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:
        print(f"context-index failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
