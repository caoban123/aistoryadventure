from __future__ import annotations

import argparse
import json
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


BACKUP_VERSION = 1


@dataclass(frozen=True)
class BackupSource:
    label: str
    path: Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_runtime_sources(root: Path) -> list[BackupSource]:
    try:
        from app.config import get_settings

        settings = get_settings()
        local_data_dir = Path(settings.local_data_dir)
        chroma_dir = Path(settings.chroma_persist_dir)
    except Exception:
        local_data_dir = Path("data")
        chroma_dir = Path("chroma_db")

    if not local_data_dir.is_absolute():
        local_data_dir = root / local_data_dir
    if not chroma_dir.is_absolute():
        chroma_dir = root / chroma_dir

    return [
        BackupSource("data", local_data_dir),
        BackupSource("chroma_db", chroma_dir),
    ]


def iter_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    if not path.exists():
        return []
    return sorted(item for item in path.rglob("*") if item.is_file())


def add_path_to_zip(
    archive: zipfile.ZipFile,
    source: BackupSource,
) -> dict[str, object]:
    files = iter_files(source.path)
    total_bytes = 0

    for file_path in files:
        total_bytes += file_path.stat().st_size
        relative = file_path.relative_to(source.path)
        archive.write(file_path, Path(source.label) / relative)

    return {
        "label": source.label,
        "exists": source.path.exists(),
        "file_count": len(files),
        "total_bytes": total_bytes,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a local runtime backup for AI Story Adventure.",
    )
    parser.add_argument(
        "--output-dir",
        default="backups",
        help="Directory where the backup zip will be written. Default: backups",
    )
    parser.add_argument(
        "--name",
        default=None,
        help="Optional backup filename without extension.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    root = repo_root()
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = root / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    created_at = datetime.now(timezone.utc).replace(microsecond=0)
    stamp = created_at.strftime("%Y%m%d-%H%M%SZ")
    archive_name = args.name or f"ai-story-backup-{stamp}"
    archive_path = output_dir / f"{archive_name}.zip"

    sources = load_runtime_sources(root)

    manifest: dict[str, object] = {
        "version": BACKUP_VERSION,
        "created_at": created_at.isoformat(),
        "app": "AI Story Adventure",
        "included": [],
        "excluded": [
            ".env",
            ".env.*",
            "Firebase Admin SDK JSON",
            "provider API keys",
            "node_modules",
            "venv",
        ],
        "restore_note": "Use scripts/restore_local.py with --confirm on a non-production copy first.",
    }

    readme = (
        "AI Story Adventure runtime backup\n"
        f"Created at: {created_at.isoformat()}\n\n"
        "This archive includes local runtime data only: data/ and chroma_db/ when present.\n"
        "It intentionally excludes .env files, Firebase admin JSON, provider API keys, venv, and node_modules.\n"
        "For production Firestore, use Firebase/GCP export in addition to this local runtime backup.\n"
    )

    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        included: list[dict[str, object]] = []
        for source in sources:
            included.append(add_path_to_zip(archive, source))
        manifest["included"] = included
        archive.writestr("BACKUP_MANIFEST.json", json.dumps(manifest, indent=2))
        archive.writestr("README_BACKUP.txt", readme)

    print(f"Backup created: {archive_path}")
    for item in manifest["included"]:
        label = item["label"]
        exists = "yes" if item["exists"] else "no"
        print(
            f"- {label}: exists={exists}, files={item['file_count']}, bytes={item['total_bytes']}"
        )


if __name__ == "__main__":
    main()
