from __future__ import annotations

import argparse
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path


RESTORABLE_ROOTS = {"data", "chroma_db"}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def safe_members(archive: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    members: list[zipfile.ZipInfo] = []
    for member in archive.infolist():
        name = member.filename.replace("\\", "/")
        parts = [part for part in Path(name).parts if part not in {"", "."}]
        if not parts:
            continue
        root = parts[0]
        if root not in RESTORABLE_ROOTS:
            continue
        if any(part == ".." for part in parts):
            raise ValueError(f"Unsafe archive path: {member.filename}")
        members.append(member)
    return members


def read_manifest(archive: zipfile.ZipFile) -> dict[str, object]:
    try:
        with archive.open("BACKUP_MANIFEST.json") as raw:
            return json.loads(raw.read().decode("utf-8"))
    except KeyError:
        return {"version": "unknown", "included": []}


def extract_member(
    archive: zipfile.ZipFile,
    member: zipfile.ZipInfo,
    target_root: Path,
    selected_roots: set[str],
) -> None:
    name = member.filename.replace("\\", "/")
    parts = [part for part in Path(name).parts if part not in {"", "."}]
    if not parts or parts[0] not in selected_roots:
        return

    destination = target_root.joinpath(*parts).resolve()
    target_root_resolved = target_root.resolve()
    if target_root_resolved not in destination.parents and destination != target_root_resolved:
        raise ValueError(f"Refusing to extract outside target root: {member.filename}")

    if member.is_dir():
        destination.mkdir(parents=True, exist_ok=True)
        return

    destination.parent.mkdir(parents=True, exist_ok=True)
    with archive.open(member) as source, destination.open("wb") as target:
        shutil.copyfileobj(source, target)


def move_existing_roots(
    target_root: Path,
    selected_roots: set[str],
    replace_existing: bool,
) -> Path | None:
    existing = [target_root / root for root in selected_roots if (target_root / root).exists()]
    if not existing:
        return None

    if not replace_existing:
        existing_text = ", ".join(str(path) for path in existing)
        raise FileExistsError(
            "Target data already exists. Re-run with --replace-existing to move it aside first: "
            f"{existing_text}"
        )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%SZ")
    rollback_dir = target_root / "restore_rollback" / stamp
    rollback_dir.mkdir(parents=True, exist_ok=True)
    for path in existing:
        shutil.move(str(path), str(rollback_dir / path.name))
    return rollback_dir


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Restore an AI Story Adventure local runtime backup.",
    )
    parser.add_argument("archive", help="Backup zip created by scripts/backup_local.py")
    parser.add_argument(
        "--target-root",
        default=".",
        help="Repo/runtime root to restore into. Default: current repo root",
    )
    parser.add_argument(
        "--only",
        choices=sorted(RESTORABLE_ROOTS),
        action="append",
        help="Restore only one root. Can be repeated. Default: data and chroma_db",
    )
    parser.add_argument(
        "--replace-existing",
        action="store_true",
        help="Move existing data/chroma_db into restore_rollback/ before restoring.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Inspect what would be restored without writing files.",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Required for any real restore.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    root = repo_root()
    archive_path = Path(args.archive)
    if not archive_path.is_absolute():
        archive_path = root / archive_path

    target_root = Path(args.target_root)
    if not target_root.is_absolute():
        target_root = root / target_root
    target_root = target_root.resolve()

    selected_roots = set(args.only or RESTORABLE_ROOTS)

    with zipfile.ZipFile(archive_path, "r") as archive:
        manifest = read_manifest(archive)
        members = [
            member
            for member in safe_members(archive)
            if member.filename.replace("\\", "/").split("/", 1)[0] in selected_roots
        ]

        print(f"Archive: {archive_path}")
        print(f"Manifest version: {manifest.get('version')}")
        print(f"Target root: {target_root}")
        print(f"Selected roots: {', '.join(sorted(selected_roots))}")
        print(f"Files to restore: {sum(1 for member in members if not member.is_dir())}")

        if args.dry_run:
            print("Dry run only. No files were changed.")
            return

        if not args.confirm:
            raise SystemExit("Refusing to restore without --confirm.")

        rollback_dir = move_existing_roots(target_root, selected_roots, args.replace_existing)
        for member in members:
            extract_member(archive, member, target_root, selected_roots)

    if rollback_dir:
        print(f"Existing data was moved to: {rollback_dir}")
    print("Restore complete.")


if __name__ == "__main__":
    main()
