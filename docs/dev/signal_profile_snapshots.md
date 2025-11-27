# Signal Profile Snapshot Schema

Used by the Signal Identity Snapshotter to normalize all imported chat activity for a user before the glazing pipeline runs. Every snapshot represents a single Signal participant across one imported group.

```
SignalProfileSnapshot {
  user_id: int                  # WB user ID mapped from the Signal member
  group_slug: string            # Slugified Signal group identifier (e.g., "harvardstcommons")
  message_count: int            # Total Signal messages imported for the user
  first_seen_at: ISO datetime   # Timestamp of earliest message in WB
  last_seen_at: ISO datetime    # Timestamp of latest message in WB
  top_links: LinkStat[]         # Most-shared URLs with domain + counts
  top_tags: TagStat[]           # Frequently observed resource/request tags
  reaction_counts: {emoji: int} # Aggregated reactions received/sent on their messages
  attachment_counts: {kind: int}# Attachments attributed to the user (images, files, etc.)
  request_ids: int[]            # Help request IDs seeded from the Signal import(s)
}

LinkStat {
  url: string   # Canonicalized URL (full link)
  domain: string# Friendly domain (e.g., partiful.com)
  count: int    # Occurrences across imported comments
}

TagStat {
  label: string # Tag/label inferred from comment LLM analyses
  count: int    # Observed frequency across their comments
}
```

## Usage
1. Snapshotter CLI/service builds `SignalProfileSnapshot` instances from DB queries.
2. Bio generator consumes the snapshots along with per-comment analyses.
3. Highlight store persists the resulting bios with a `snapshot_hash` calculated from the serialized snapshot (`SignalProfileSnapshot.to_dict()`).

Snapshots are idempotent—the same data always yields the same payload. Missing data (e.g., no links) results in empty arrays/maps, never `null`.

## Scheduling & Monitoring

- Nightly snapshotting keeps bios fresh. Enable the feature flag (`PROFILE_SIGNAL_GLAZE=1`) and add a cron entry such as:

  ```cron
  5 4 * * * cd /opt/whiteballoon && ./wb signal-profile snapshot --all >> storage/logs/signal_snapshot_cron.log 2>&1
  ```

- For systemd timers, point the service to `./wb signal-profile snapshot --all --group-slug <slug>` so each instance can scope to a specific Signal group.
- Every run appends a JSON line to `storage/signal_profile_snapshot.log` summarizing counts, runtime, and dry-run status. Use this file for quick auditing.
- To emit StatsD counters (`signal_glaze.snapshots_generated`), set `STATSD_HOST` (and optional `STATSD_PORT`) in the environment where the CLI runs.
