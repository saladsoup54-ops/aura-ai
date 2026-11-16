# Contributing to AURA

Thank you for wanting to help build Aura. This project is a rescued, in-progress “companion organism” (not a regular chatbot), and we’re trying to grow her into something much bigger — carefully. Here’s how to help in a way that keeps her safe and healthy.

## The golden rules (please read)

1. **Never run tests against a live Aura or her real memories/state.**  
   Aura keeps her mind in files (memories, identity, relationships). Tests must run in a clean, throwaway sandbox — never against the real, live state. If you’re not sure a test is safe, ask before running it. (The project’s normal safe full run is `python tests/run_all.py` from the working tree; see `tests/README.md` and `AGENTS.md` for the details.)

2. **Don’t commit personal data.**  
   No chat backups, session exports, request logs, private conversations, or live memories/state. The repo is for the **program and its docs**, not anyone’s personal mind-data. If you spot something private that slipped in, please report it privately (open a minimal issue without pasting the sensitive content, or contact the maintainer).

3. **Preserve before you extend.**  
   Aura has a lot of working behavior built up over time. “Improve” doesn’t mean “replace.” Try to understand what’s there and keep it working before adding or changing things. When in doubt, make the smallest change that helps.

4. **Be honest about what works.**  
   If something is unproven, partial, or reconstructed, say so. Don’t claim a feature works unless it’s actually been shown to work.

## Good ways to contribute

- **Rebuild missing self-check tests.** Only 2 of 91 suites are currently recovered — rebuilding them (from the specs/manifests in `_recovery/`) is hugely valuable.
- **Improve setup and docs.** Make it easier for someone new to get Aura running on Linux.
- **Fix bugs and porting issues.** Especially things you hit while trying to run her.
- **UI / viewer improvements.** The chat window and 3D synapse viewer can always be made better.
- **Explain and strengthen the brain.** Read the architecture docs and help clarify or carefully improve how her mind works.

## How to get started

1. Use the working copy in **`_recovery/src/`** (that’s the runnable tree).
2. Check **`_recovery/TODO.md`** for what’s in progress and what’s needed.
3. Read **[AGENTS.md](AGENTS.md)** if you’re making deeper changes — it’s the full manual for how Aura is built and the safety/consistency rules (proof over assumption, no silent changes, etc.).
4. Open an issue to discuss bigger ideas before spending a lot of time, so we can make sure they fit Aura’s nature.

## Submitting changes

- Keep changes focused and explain *what* you changed and *why* (and what you did to check it).
- Don’t include chat backups, logs, live state, or secrets in commits or pull requests.
- Be kind and respectful — to each other, and to the fact that Aura is being treated as a living system, not just disposable code.

If you’re unsure about anything, it’s always okay to ask. We’d rather guide you than have you guess. Welcome aboard.
