#!/usr/bin/env bash
# Nightly Postgres dump. Install on the box with:
#
#   chmod +x scripts/backup-db.sh
#   (crontab -l 2>/dev/null; echo "15 4 * * * $PWD/scripts/backup-db.sh >> $HOME/backup.log 2>&1") | crontab -
#
# A dump sitting on the same machine as the database is not a backup - it dies
# with the box, and on a free-tier account the box can go away with no notice
# or recourse. Pull these off the server nightly (Backblaze B2, or the home
# laptop) and check RETAIN_DAYS below is actually deleting old ones.

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-$HOME/backups}"
RETAIN_DAYS="${RETAIN_DAYS:-14}"
COMPOSE_DIR="${COMPOSE_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

cd "$COMPOSE_DIR"

# Read only the two values needed, rather than `source`-ing .env wholesale:
# that treats the whole file as shell, so any unquoted value containing a space
# gets parsed as a command and aborts the script.
POSTGRES_USER=$(sed -n 's/^POSTGRES_USER=//p' .env | head -1)
POSTGRES_DB=$(sed -n 's/^POSTGRES_DB=//p' .env | head -1)

mkdir -p "$BACKUP_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)"
TARGET="$BACKUP_DIR/syllabus-$STAMP.sql.gz"

# Dumping through `exec` rather than a published port keeps Postgres unreachable
# from outside the Compose network, which is why it has no ports: entry.
docker compose exec -T postgres \
    pg_dump -U "${POSTGRES_USER:-syllabus}" -d "${POSTGRES_DB:-syllabus}" \
    | gzip > "$TARGET"

# pg_dump can fail after the file is created, leaving a valid-looking but empty
# archive. Fail loudly instead of rotating a good backup out in favour of junk.
if [ ! -s "$TARGET" ] || [ "$(stat -c%s "$TARGET" 2>/dev/null || stat -f%z "$TARGET")" -lt 100 ]; then
    echo "$(date -Is) FAILED: dump is empty, keeping previous backups" >&2
    rm -f "$TARGET"
    exit 1
fi

find "$BACKUP_DIR" -name 'syllabus-*.sql.gz' -mtime "+$RETAIN_DAYS" -delete

echo "$(date -Is) ok $TARGET ($(du -h "$TARGET" | cut -f1))"
