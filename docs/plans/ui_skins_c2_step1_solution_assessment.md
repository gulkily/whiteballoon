# UI Skins C2 (Multi-Bundle Build) — Step 1 Solution Assessment

## Problem
We now have `static/skins/base.css` and `static/skins/default.css`, but our tooling still ships a single stylesheet. To support multiple skins (Default, Terminal, Win95), we need a repeatable build process that emits one CSS bundle per skin, watches them in dev, and produces hashed assets for production.

## Option A – Simple Python build script (preferred)
- **Approach**: Extend the existing CLI with a Python command (e.g., `wb skins build`) that scans `static/skins/*.css`, concatenates `base.css` + entry file, optionally minifies using `csscompressor`, and writes `static/build/skins/<name>.css` (with optional hash). Use `watchdog` in dev to rebuild on change.
- **Pros**: Zero new runtime dependencies (no Node install), tight integration with WB CLI, straightforward to customize for future needs (e.g., injecting headers). Easy to run in CI since we already rely on Python.
- **Cons**: No autoprefixer or advanced CSS transforms; large skins might build slower in pure Python; writing a robust watcher requires care.

## Option B – Node.js/PostCSS multi-entry build
- **Approach**: Introduce a `package.json` and PostCSS pipeline to handle each skin entry.
- **Pros**: Industry-standard tooling, autoprefixer, plugin ecosystem.
- **Cons**: Adds Node dependency, complicates dev environment, more moving parts.

## Option C – Django/templated compilation on the fly
- **Approach**: Render CSS via Jinja/templating at runtime (e.g., `/skins/default.css` route), injecting base + overrides depending on query.
- **Pros**: Zero build step; skins editable without rebuild.
- **Cons**: Expensive per-request rendering, caching complexity, harder CDN integration, risk of template injection. Not ideal for static assets.

## Recommendation
Adopt **Option A**. Keeping the build tooling inside our Python CLI avoids introducing Node just for CSS, aligns with our deployment environment, and lets us tailor the watch/build commands to the upcoming skins workflow. We can revisit PostCSS later if we need advanced transforms, but a Python-based multi-bundle builder meets current requirements with less friction.
