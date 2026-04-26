# Postgres Replica Lag Runbook

## When this fires

PagerDuty alert `pg-replica-lag` fires when `pg_stat_replication.lag_seconds`
exceeds 60 seconds for 5 minutes on any read replica.

## Triage (do this first)

1. Check the alert dashboard at grafana.internal/d/pg-replication.
2. Look at the `lag_seconds` graph for the affected replica. Is it climbing
   linearly (replica falling behind) or spiky (intermittent stall)?
3. Run `psql -h <replica> -c "SELECT now() - pg_last_xact_replay_timestamp();"`
   and confirm the lag is real — sometimes the metric is stale.

## Common causes

- **Long-running query on the replica.** Run
  `SELECT pid, query_start, query FROM pg_stat_activity WHERE state = 'active' ORDER BY query_start LIMIT 10;`
  on the replica. Anything older than 5 minutes is suspect.
- **Vacuum on primary blocking WAL replay.** Check
  `SELECT * FROM pg_stat_progress_vacuum;` on the primary. A vacuum on a
  10M+ row table can hold WAL for several minutes.
- **Network issue between primary and replica.** Check
  `mtr <primary-host>` from the replica box.
- **Disk I/O saturation on the replica.** Check `iostat -x 5` for `%util`
  near 100.

## Fixes

- Long query: cancel with `SELECT pg_cancel_backend(<pid>);` (graceful) or
  `pg_terminate_backend(<pid>)` (force).
- Vacuum: do not cancel a running vacuum. Wait it out, then schedule the
  next vacuum during off-hours via `crontab -e` on db-ops-host.
- Network: page network on-call, do not attempt fixes yourself.
- Disk: ssh to replica, run `iotop -ao` to find the offending process.
  If it's a backup job, kill the backup and re-run during off-hours.

## Gotchas

- The replica `db-replica-3` is on slower disks than the others. It
  routinely has 30-40 second lag during peak hours; this is expected.
  Don't escalate unless lag >120s sustained.
- `pg_stat_replication` rows are reported on the primary, not the replica.
  If you query a replica and get an empty result, that's normal.
- The `db-replica-readonly` host is shared with the analytics team and
  carries a heavier query load; expect 60-90s lag during their nightly
  ETL window (02:00-04:00 UTC).
- Cancelling an analytics query rarely helps — they retry automatically
  and faster than the replica can catch up. Coordinate with the analytics
  channel before cancelling.

## Post-incident

After any fix:

1. Comment on the PagerDuty incident with what was wrong, what you did,
   and what the lag looked like 5 minutes after the fix.
2. If you had to cancel a customer query, ping #customer-success with the
   query ID so they can reach out to the affected user.
3. If the cause was new (not in this runbook), edit this runbook and add it.
