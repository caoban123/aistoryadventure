# Backup + Restore

This is the first production-safe backup plan for AI Story Adventure. It protects local runtime data and documents what still needs Firebase/GCP backup in production.

## What Gets Backed Up

The local backup script includes:

- `data/`: local JSON sessions, admin state, usage logs, points ledger, audit logs when the app is using local storage.
- `chroma_db/`: ChromaDB vector memory files.
- `BACKUP_MANIFEST.json`: backup timestamp, included roots, file counts, byte counts, and excluded secret classes.

The backup intentionally excludes:

- `.env` and `.env.*`
- Firebase Admin SDK JSON files
- provider API keys
- `venv/`
- `node_modules/`

## Create A Local Backup

Run from the repo root:

```powershell
venv\Scripts\python.exe scripts\backup_local.py
```

The archive is written to `backups/` by default:

```text
backups/ai-story-backup-YYYYMMDD-HHMMSSZ.zip
```

Optional custom output:

```powershell
venv\Scripts\python.exe scripts\backup_local.py --output-dir D:\ai-story-backups --name before-public-beta
```

## Inspect A Backup Before Restore

Always dry-run first:

```powershell
venv\Scripts\python.exe scripts\restore_local.py backups\ai-story-backup-YYYYMMDD-HHMMSSZ.zip --dry-run
```

## Restore A Backup

Restore refuses to run unless `--confirm` is provided. It also refuses to overwrite existing `data/` or `chroma_db/` unless `--replace-existing` is provided.

Restore into an empty/non-production copy:

```powershell
venv\Scripts\python.exe scripts\restore_local.py backups\ai-story-backup-YYYYMMDD-HHMMSSZ.zip --confirm
```

Restore when `data/` or `chroma_db/` already exists:

```powershell
venv\Scripts\python.exe scripts\restore_local.py backups\ai-story-backup-YYYYMMDD-HHMMSSZ.zip --confirm --replace-existing
```

Existing folders are moved into `restore_rollback/<timestamp>/` instead of being deleted.

Restore only one storage root:

```powershell
venv\Scripts\python.exe scripts\restore_local.py backups\ai-story-backup-YYYYMMDD-HHMMSSZ.zip --confirm --only data
```

## Firebase / Firestore Production Backup

If production uses Firestore, the local zip is not enough. Use Firebase/GCP export for Firestore data in addition to `chroma_db/`.

Recommended production habit:

- Export Firestore daily before public beta users grow.
- Store exports in a private bucket or server backup location.
- Keep at least 7 daily backups and 4 weekly backups.
- Test restore once on a separate Firebase project or non-production environment.

Do not place Firebase export credentials, service account JSON, or bucket secrets inside the frontend or this repo.

## Restore Test Checklist

Before public beta, do this once:

- Create a backup.
- Copy the repo to a temporary folder.
- Run restore there with `--dry-run`.
- Run restore with `--confirm`.
- Start backend and frontend locally.
- Login with a test account.
- Confirm History, admin usage/audit, and Chroma memory-backed turns still load.

## Suggested Schedule

- Before every deploy: manual backup.
- Public beta: daily backup.
- After stable launch: daily backup plus weekly off-server copy.
- Before any schema/storage migration: backup and test restore first.
