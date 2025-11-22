Problem: Hub visitors currently see only sync stats; they need a reddit-style feed that lists public requests stored in bundles, backed by structured storage so future skins can reskin the data without new plumbing.

User Stories:
- As a public visitor, I want to browse the latest public requests with timestamps and completion state so I can understand what the community is working on.
- As a hub operator, I want the feed to refresh automatically after peers upload new bundles so the public page stays current without manual parsing.
- As a skin developer, I want the hub to expose normalized request/comment data so I can build alternate skins or APIs without re-reading bundle files.
- As a moderation reviewer, I want the feed to clearly respect sync scope and omit pending/private records so we do not leak internal data.

Core Requirements:
- Parse each uploaded bundle into a structured SQLite/SQLModel store that tracks requests (and optionally comments) with manifest digests and timestamps.
- Provide a reddit-style hub page that queries the structured store, lists recent public requests, and displays key metadata (title/description, creator, status, relative time, tags, comment counts).
- Ensure ingest deduplicates by request ID + source instance so re-uploads of the same manifest update existing rows rather than duplicating entries.
- Expose a lightweight JSON endpoint that returns the same normalized records for progressive enhancement or future skins.
- Enforce sync scope filtering: only data marked public in the bundle should enter the feed store or API output.

Simple User Flow:
1. Peer uploads a signed bundle to the hub.
2. Hub verifies the signature, writes bundle files, then runs the structured ingest to parse requests/comments into SQLite tables keyed by manifest digest.
3. A visitor hits the hub home/feed route; the server queries the structured store (with pagination) for recent public requests and renders the reddit-style template.
4. Optional: the template loads a JSON endpoint for infinite scroll or enhancements by requesting the same normalized data.

Success Criteria:
- Uploading a new bundle updates the feed within the same request cycle (no manual restarts required).
- Visiting the hub shows at least 20 recent public requests with consistent formatting, sorted by updated date, and matches the data in the latest bundle.
- The JSON endpoint returns the same records and metadata as the rendered feed and is documented for skin builders.
- No pending/private bundle entries appear in the structured store or output.
- The solution remains fully server-rendered with progressive enhancement hooks available for future skins.
