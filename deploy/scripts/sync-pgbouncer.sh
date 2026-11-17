#!/usr/bin/env bash
#
# deploy/scripts/sync-pgbouncer.sh — regenerate the PgBouncer auth_file (userlist.txt)
# from the PostgreSQL system catalog (pg_authid).
#
# Usage (from the repo root):
#   deploy/scripts/sync-pgbouncer.sh                  # default roles: alfacat,admin,monitor
#   deploy/scripts/sync-pgbouncer.sh "user1,user2"    # explicit list
#   SYNC_USERS="user1,user2" deploy/scripts/sync-pgbouncer.sh
#
# Every setting is overridable via environment variables (see the block below).

set -euo pipefail

# --- Configuration ---
POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-postgres_V18_iron_track}"
PGBOUNCER_CONTAINER="${PGBOUNCER_CONTAINER:-pgbouncer_iron_track}"
PGBOUNCER_USERLIST="${PGBOUNCER_USERLIST:-deploy/pgbouncer/conf/userlist.txt}"  # host path, relative to repo root
PGB_USERLIST_IN_CT="${PGB_USERLIST_IN_CT:-/etc/pgbouncer/userlist.txt}"         # path inside the pgbouncer container
DEFAULT_SYNC_USERS="alfacat,admin,monitor"   # roles created by deploy/postgres/init/init-user-db.sh

die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

SYNC_USERS="${1:-${SYNC_USERS:-$DEFAULT_SYNC_USERS}}"

# --- Check PostgreSQL Health ---
status="$(docker inspect --format '{{.State.Health.Status}}' "$POSTGRES_CONTAINER" 2>/dev/null || true)"
[ "$status" = "healthy" ] || die "container $POSTGRES_CONTAINER is not ready (status: ${status:-not found})"

# --- Validate Role Names ---
# Whitelist: letters, digits, underscore, hyphen. Catches typos, empty items
# ("a,,b", "a, b") and anything that could change the meaning of the SQL below.
# NB: grep -qvE (not $(... | sed !p)) — command substitution would swallow a
# lone empty line and let inputs like "a,,b" through.
if printf '%s\n' "$SYNC_USERS" | tr ',' '\n' | grep -qvE '^[A-Za-z0-9_-]+$'; then
  bad="$(printf '%s\n' "$SYNC_USERS" | tr ',' '\n' | grep -vE '^[A-Za-z0-9_-]+$' | sed 's/^$/<empty>/' || true)"
  die "invalid role names (empty items or bad characters):
 $bad
allowed: A-Z a-z 0-9 _ -"
fi

# --- Fetch SCRAM Verifiers ---
mkdir -p "$(dirname "$PGBOUNCER_USERLIST")"   # fresh overrides may point at a not-yet-existing dir
tmp="${PGBOUNCER_USERLIST}.tmp"
trap 'rm -f "$tmp"' EXIT

roles_csv="$(printf '%s\n' "$SYNC_USERS" | tr ',' '\n' | LC_ALL=C sort -u | paste -sd, -)"

# Role names are NOT interpolated into SQL: they travel as a psql variable;
# the whitelist above stays as the second line of defence.
docker exec -i "$POSTGRES_CONTAINER" \
  psql -U postgres -d postgres -v ON_ERROR_STOP=1 -v roles="$roles_csv" -t -q -A <<-'EOSQL' > "$tmp"
  SELECT '"' || rolname || '" "' || rolpassword || '"'
    FROM pg_authid
   WHERE rolname = ANY (string_to_array(:'roles', ','))
     AND rolpassword IS NOT NULL
   ORDER BY rolname;
EOSQL

# --- Verify Requested Roles ---
requested="$(printf '%s\n' "$roles_csv" | tr ',' '\n' | LC_ALL=C sort -u)"
found="$(cut -d'"' -f2 "$tmp" | LC_ALL=C sort -u)"
missing="$(LC_ALL=C comm -23 <(printf '%s\n' "$requested") <(printf '%s\n' "$found"))"
[ -z "$missing" ] || die "roles not found or without password (rolpassword IS NULL):
 $missing
userlist.txt was NOT updated"

[ -s "$tmp" ] || die "query returned no rows — userlist.txt was NOT updated"

# --- Publish Userlist ---
# The .tmp file sits next to the target, so mv is an atomic rename(2) within one
# filesystem. 644: the file must stay readable by the pgbouncer user inside the
# container (read-only bind mount of ./deploy/pgbouncer/conf).
chmod 644 "$tmp"
mv -f "$tmp" "$PGBOUNCER_USERLIST"

# --- Reload PgBouncer ---
if docker ps --format '{{.Names}}' | grep -qx "$PGBOUNCER_CONTAINER"; then
  docker exec --user pgbouncer "$PGBOUNCER_CONTAINER" cat "$PGB_USERLIST_IN_CT" > /dev/null \
    || die "pgbouncer cannot read $PGB_USERLIST_IN_CT (permissions/mount)"
  docker kill --signal HUP "$PGBOUNCER_CONTAINER" > /dev/null
  echo "pgbouncer: SIGHUP sent, auth_file reloaded"
else
  echo "pgbouncer: container is not running — userlist will be picked up on start"
fi

echo "userlist: $(wc -l < "$PGBOUNCER_USERLIST" | tr -d ' ') roles -> $PGBOUNCER_USERLIST ($(cut -d'"' -f2 "$PGBOUNCER_USERLIST" | paste -sd, -))"