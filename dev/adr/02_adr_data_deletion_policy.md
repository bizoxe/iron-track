## ADR-02: Data Deletion Policy & Account Lifecycle

**Status:** Accepted

**Date:** 2026-08-27

**Relations:** Supersedes: — | Relates-to: `README.md → Database Blueprint → DELETION POLICY` (normative matrix)

---

### Description
Defines what happens to data when its owner disappears: the account lifecycle (soft delete → purge or anonymize),
the orphan zone for ownerless custom exercises, catalog soft deletes, and the scheduled jobs that are the only
exit path for PII. Cross-cutting: touches every section of the Database Blueprint.

### Glossary
* **Purge** — hard `DELETE` of an account row together with its content (JOB A Step 1).
* **Anonymize** — `UPDATE` that strips PII (email/name/password) while the row survives to keep FKs and immutable
  history valid (JOB A Step 2).
* **Orphan (zone)** — ownerless custom exercise (`created_by IS NULL`, `is_system_default = FALSE`), legalized by
  `chk_exercise_system_no_author`; invisible in listings, reaped by JOB B.

### Context
* Mixed ownership content: system exercises are global; custom exercises and templates belong to users and may be shared
  or public.
* GDPR-style right to erasure: a user must be able to leave, so any policy that makes account deletion impossible is unacceptable.
* Training history is immutable: `training_session.user_id` is `ON DELETE RESTRICT`, which blocks a raw account `DELETE` by design.
* Catalogs (`equipment`, `muscle_group`, `tag`) are referenced forever by snapshots and history; deleting them must not break references.
  Uniqueness must survive soft deletes: a deleted name may be reused.
* The jobs (`JOB A/B`) require the `training_session*` tables as their runtime prerequisite.

### Decision
1. **Catalog soft delete** (`equipment`, `muscle_group`, `tag`):
   deletion = `UPDATE ... SET deleted_at`; uniqueness among live rows only — partial unique index `WHERE deleted_at IS NULL` (`uidx_*`).
2. **System exercises are permanent catalog data:**
   they cannot be deleted through the API and may be edited only by admins/superusers. Database-level delete protection is not required; this is an application rule.
   Editing a system exercise does not rewrite existing training history: `training_session_exercise` stores snapshots of the exercise/template data
   captured at session creation, including `exercise_name_snapshot`, while `exercise_id` is only a nullable reference.
3. **Account lifecycle — two-phase purge (JOB A · daily):**
   - self-service deletion = soft delete (`deleted_at`) + deauthorization; `is_active` remains exclusively an admin ban flag;
   - **Step 1 (hard purge)** — accounts soft-deleted past `RETENTION=30d (configurable via env)` with no sessions and no
     non-private templates are purged with their content in strict order `plans → units → custom exercises → account` (RESTRICT forces the order);
   - **Step 2 (anonymize)** — everyone else: `email = 'deleted+<id>@anon.invalid'`, `name = NULL`, password sentinel, `is_active = FALSE`. Rows survive so
     immutable history stays valid and `SET NULL` ownership FKs point at a real row.
4. **Orphan zone**: `chk_exercise_system_no_author` is one-directional (`NOT is_system_default OR created_by IS NULL`), legalizing ownerless custom
   exercises produced outside JOB A (manual/DBA deletions). Orphans are invisible in listings (APP-RULE) and reaped by JOB B.
5. **Referential policy**: ownership FKs (`exercise.created_by`, `training_unit.created_by`, `training_plan.created_by`) → `SET NULL`
   (nullable ownership columns); `training_session.user_id` → `RESTRICT` (forces the anonymize path);
   `*_access` resource/user FKs (PK members) and `trainer_client` FKs → `CASCADE` (NOT NULL structural links);
   `*_access.granted_by` → `SET NULL` (provenance may legitimately vanish with its granter).
6. **JOB B · orphan GC (weekly)**: deletes ownerless custom exercises not referenced by templates or history. Source-agnostic: covers everything
   that bypassed JOB A.
7. **Provenance**: clones record `training_plan.source_plan_id` / `training_unit.source_unit_id` (informational, `ON DELETE SET NULL`).
8. **Jobs implementation deferred to post-MVP**: both jobs land in the same PR as the sessions feature (see Context).
9. **Dormant-account retention (post-MVP)**: `user_account.last_activity_at` (already in place) is updated on login (UTC), throttled to at most one
   write per ~24h to avoid write amplification. Retention ladder — warning email after ~12 months of inactivity → deletion notice → purge via JOB A;
   any login refreshes the timer. Candidates are live accounts (Appendix D). Step 1 is unchanged: login is impossible while `deleted_at` is set, so
   the `deleted_at` predicate already implies staleness.

**Alternatives rejected:**
* full `CASCADE` on ownership FKs — destroys foreign templates and history joins;
* `RESTRICT` everywhere — makes account deletion legally impossible;
* ghost-user row (permanent "Deleted User" account) — functionally equals Step 2 anonymization, minus the purge branch for clean leavers.

### Consequences
* PII leaves the system only through JOB A; there is no ad-hoc deletion path.
* `*_access.granted_by` is lost only when the grantor's row is hard-deleted (JOB A Step 1 / DBA). Anonymization (Step 2) is an `UPDATE` —
  `user_account.id` survives, no FK fires, grants keep provenance pointing at the anonymized row — accepted trade-off.
* Orphans require GC discipline (JOB B); if volume grows, an admin orphan-review queue is added on top of the same zone.
* Deep-clone doctrine keeps recipient templates independent of originals: deleting an original never breaks a clone.
* Ownerless templates (`training_unit`/`training_plan` with `created_by IS NULL`) are accepted residue outside JOB B; JOB A Step 1 is
  the only sanctioned template-removal path.
* JOB A Step 1 correctness relies on Blueprint invariants (see Relations): custom exercises may be referenced by private/shared
  templates, but public templates may reference system exercises only.
* JOB A Step 1 does not filter by `last_activity_at`: login is impossible while `deleted_at` is set (APP-RULE, §1), 
  so staleness is implied by the `deleted_at` predicate; the column serves the dormant ladder (Decision 9).

### Artifacts
* **Planned:** `src/app/jobs/account_purge.py` (JOB A) and `src/app/jobs/orphan_gc.py` (JOB B) — batch entry points
  (`async def run() -> JobResult`), invoked by the scheduler; no business logic in CLI. Thin manual-run adapters live in `src/app/jobs/cli.py`
  (click group `jobs`), registered in `src/app/main.py` as `app jobs purge-accounts|gc-orphans` (same pattern as `app users`).
  Both commands support `--dry-run` and are idempotent — Step 2 is guarded by the `email NOT LIKE 'deleted+%'` predicate, which prevents
  re-anonymizing already anonymized accounts.
* **Soft-delete filter interplay:** the global ORM filter (`src/app/db/soft_delete.py` → `register_soft_delete_filter` — a
  `do_orm_execute` listener applying `with_loader_criteria`) intercepts ORM SELECTs only. JOB A/B intentionally bypass it: candidate scans run
  as Core SQL over `__table__` (Appendix A) — bulk `DELETE`/`UPDATE` and Core selects are not intercepted. If a job ever resolves candidates
  through ORM services instead, it must pass `execution_options(include_deleted=True)` (or use Core select), otherwise
  soft-deleted rows would be invisible to the scan.
* **Normative matrix:** `README.md → Database Blueprint → DELETION POLICY`.
* **Appendices A–D (illustrative, non-normative):** SQL excerpts below. Canonical SQL is written at implementation 
  time and follows the final schema.

#### Appendix A · JOB A — account purge (illustrative)

```sql
-- Step 1: hard purge; one transaction; the set is materialized exactly once
BEGIN;

CREATE TEMP TABLE _doomed ON COMMIT DROP AS
SELECT u.id
FROM user_account AS u
WHERE u.deleted_at < :cutoff                                 -- now() - RETENTION
  AND NOT EXISTS (SELECT 1 FROM training_session AS s
                  WHERE s.user_id = u.id)
  AND NOT EXISTS (SELECT 1 FROM training_unit AS tu
                  WHERE tu.created_by = u.id
                    AND tu.sharing_status <> 'private')
  AND NOT EXISTS (SELECT 1 FROM training_plan AS tp
                  WHERE tp.created_by = u.id
                    AND tp.sharing_status <> 'private');

DELETE FROM training_plan WHERE created_by IN (SELECT id FROM _doomed);  -- cascades plan_units
DELETE FROM training_unit WHERE created_by IN (SELECT id FROM _doomed);  -- cascades unit_exercises
DELETE FROM exercise
WHERE created_by IN (SELECT id FROM _doomed)
  AND is_system_default = FALSE;                                         -- customs only
DELETE FROM user_account WHERE id IN (SELECT id FROM _doomed);

COMMIT;

-- Step 2: anonymize survivors; idempotent via the email guard
UPDATE user_account
SET email     = 'deleted+' || id || '@anon.invalid',
    name      = NULL,
    password  = '!purged',      -- sentinel: never validates as a hash
    is_active = FALSE
WHERE deleted_at < :cutoff
  AND email NOT LIKE 'deleted+%';
```

#### Appendix B · JOB B — orphan exercise GC (illustrative)

```sql
DELETE FROM exercise AS e
WHERE e.created_by IS NULL
  AND e.is_system_default IS FALSE
  AND NOT EXISTS (SELECT 1 FROM training_unit_exercise AS tue
                  WHERE tue.exercise_id = e.id)
  AND NOT EXISTS (SELECT 1 FROM training_session_exercise AS tse
                  WHERE tse.exercise_id = e.id)
RETURNING e.id;
```

#### Appendix C — supporting indexes (already in the Blueprint)

```sql
-- JOB A/B anti-joins and SET NULL sweeps
CREATE INDEX idx_training_unit_exercise_exercise_id      ON training_unit_exercise    (exercise_id);
CREATE INDEX idx_training_session_exercise_exercise_id   ON training_session_exercise (exercise_id);

-- Owner partial unique indexes double as created_by indexes for purge sweeps;
-- *_access.user_id indexes serve "shared with me" AND the account CASCADE sweep;
-- training_session probes (JOB A anti-join) ride on idx_training_session_user_id_start_time.
```

#### Appendix D · dormant ladder candidates (illustrative, post-MVP)

```sql
-- Live accounts, long inactive (Decision 9); any login refreshes
-- last_activity_at. COALESCE covers accounts created before the column
-- existed (NULL = never logged in / unknown).
SELECT id FROM user_account
WHERE deleted_at IS NULL
  AND COALESCE(last_activity_at, created_at) < :inactivity_cutoff;
```