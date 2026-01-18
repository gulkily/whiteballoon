# CLI Aliases for Comment/Chat Commands — Step 1 Solution Assessment

**Problem**: Operators keep forgetting verbose CLI entry points (`./wb comment-llm`, `./wb chat-index`, etc.), slowing down workflows when they need quick access to comment/chat indexing utilities.

## Option A – Add direct `wb` subcommands (aliases)
- Pros: Zero learning curve — type `wb comment-llm`/`wb chat-index` exactly as written; mirrors the mental model users already have; no additional tooling.
- Cons: Slightly increases CLI help text; need to ensure alias commands stay in sync with existing implementations.

## Option B – Ship shell functions in docs (manual aliases)
- Pros: No code changes; users add their own `alias wbc='./wb comment-llm'` entries; flexible per environment.
- Cons: Not portable (each developer must copy/paste); easy to drift or typo; doesn’t help non-shell users (e.g., Windows `wb.bat`).

## Option C – Wrapper script (`wb-comment`, `wb-chat`)
- Pros: Mirrors git-style plumbing/porcelain; can keep specialized behavior per command.
- Cons: Adds more executables to maintain; still requires mental mapping from `comment-llm`→`wb-comment`; Windows support is extra work.

## Recommendation
Option A. Add friendly aliases within the existing `wb` Click group so `wb comment-llm`, `wb chat-index`, and `wb chat-embed` simply forward to the established commands. This keeps documentation simple, works cross-platform (including `wb.bat`), and requires minimal maintenance beyond wiring the new command names to the existing handlers.
