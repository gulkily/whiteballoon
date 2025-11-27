# Positivity-Tuned Bio Generator – Step 3 Development Plan

## Stage 1 – Prompt + guardrail spec
- **Goal**: Lock the LLM contract before wiring code.
- **Dependencies**: Step 2 stories, snapshot schema.
- **Changes**: Author `docs/prompts/signal_profile_glaze_prompt.md` describing the tone rubric, length-scaling rules (longer bios for chat-heavy users), forbidden phrases, and proof-point structure. Include example inputs/outputs and guardrail checklist.
- **Verification**: Peer review of doc + prompt lint (ensure tokens < limit).
- **Risks**: Ambiguous rubric causing inconsistent tone; mitigated via examples.

## Stage 2 – Generator service API
- **Goal**: Create deterministic code surface for bios.
- **Dependencies**: Stage 1 prompt spec, snapshots, comment analysis accessors.
- **Changes**: Add `app/services/signal_profile_bio_service.py` exposing `generate_bio(snapshot: SignalProfileSnapshot, analyses: list[CommentAnalysis]) -> BioPayload`. Implement templating scaffolding, fallback phrasing for sparse data, and proof-point extraction. Define `BioPayload` dataclass.
- **Verification**: Unit tests with fixture snapshots/analyses to assert positivity, reference inclusion, and adaptive lengths.
- **Risks**: Overly long bios exceeding template; guard via length clamps per data density.

## Stage 3 – LLM client + guardrail enforcement
- **Goal**: Integrate with provider while keeping outputs safe.
- **Dependencies**: Stage 2 service.
- **Changes**: Wrap existing LLM client with prompt hashing, request/response logging, retries, and obfuscated secrets. Add guardrail filter module that checks tone (regex, sentiment heuristics) and rewrites via fallback template if violations detected.
- **Verification**: Mocked LLM tests verifying retry + logging; guardrail unit tests with intentionally negative outputs.
- **Risks**: Logging PII; mitigate by hashing prompts. Guardrail false positives causing rewrites; track metric `signal_glaze.guardrail_failures`.

## Stage 4 – Batch job + CLI integration
- **Goal**: Operationalize bios generation.
- **Dependencies**: Stage 3 client, highlight store API (for writes).
- **Changes**: Create CLI `wb signal-profile glaze` to loop snapshots, fetch recent `comment_llm_insights_db` analyses, call generator, and upsert via highlight service. Support batching, `--dry-run`, filter by user/group, and structured outcome summary.
- **Verification**: Integration test with fixture DB to ensure upserts happen; manual dry run on HarvardStCommons sample.
- **Risks**: Expensive LLM costs; mitigate with `--max-users` option + analytics.

## Stage 5 – Telemetry + failure handling
- **Goal**: Observe performance and graceful degradation.
- **Dependencies**: Stage 4 job.
- **Changes**: Emit metrics counts (bios attempted/succeeded, guardrail fallbacks, LLM errors). Add alert thresholds >10% failures. Implement resume token to skip already-fresh snapshots. Document manual rerun steps.
- **Verification**: Unit tests for metrics increments; manual chaos test simulating LLM failure.
- **Risks**: Silent failures leaving stale bios; mitigated by alerts + resume tokens.
