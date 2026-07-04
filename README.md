# Open Memory Format (OMF)

**Your memories, in files you own.** OMF is an open format for a life's
record — journals, people, places, projects and more — stored as plain
Markdown files in a folder you control. Human-readable, app-agnostic, yours
forever.

**→ [Read the 0.1 spec](https://janithkv.github.io/open-memory-format/spec/0.1/)**
 · [Website](https://janithkv.github.io/open-memory-format/)
 · [Example vault](./example-vault)

> **Status: draft / unstable.** 0.1 documents the format as currently
> implemented and flags the decisions still to settle before a stable 1.0.
> Don't treat 0.x as a stability guarantee.

## What it is

A **memory vault** is a plain folder of Markdown files (plus a few binaries and
one JSON settings file). OMF is a *profile* of three things developers already
know:

- **CommonMark** for bodies,
- **YAML** frontmatter for structured fields,
- `[[wikilinks]]` and `![[embeds]]` for cross-references (Obsidian-compatible).

A vault is portable by construction — just files in a folder, in any storage
the user controls. Any app that follows this spec can read and write the same
vault. It is a **portability / migration** format, not a concurrent
multi-writer protocol (no merge/conflict semantics; last-write-wins).

## Repository layout

```
spec/0.1/OMF-0.1-draft.md   canonical specification (source of truth)
spec/0.1/index.html         published rendering (GitHub Pages)
index.html                  landing page
example-vault/              a small, conformant vault to read
LICENSE                     CC-BY-4.0 (spec text)
LICENSE-CODE                Apache-2.0 (tooling)
```

## Roadmap to 1.0

0.1 is content-complete. Reaching a stable **1.0** means settling the open
questions in [§10](spec/0.1/OMF-0.1-draft.md) and shipping the conformance
artifacts named in [§11](spec/0.1/OMF-0.1-draft.md):

- [ ] Resolve open questions (`type` redundancy, mention resolution, settings
      scope, metadata privacy)
- [ ] **Validator** — checks a vault against the spec
- [ ] **Reference parser** — a library, extracted from the reference app
- [x] **Example vault** — see [`example-vault/`](./example-vault)

Discussion happens in [issues](https://github.com/janithkv/open-memory-format/issues).

## Licensing

The **specification text** is licensed [CC-BY-4.0](./LICENSE). Any
**tooling** in this repo (validator, parser, scripts) is licensed
[Apache-2.0](./LICENSE-CODE). Implementing OMF requires no permission.

OMF is the open format read and written by the Ōrma app; it is not tied to it.
