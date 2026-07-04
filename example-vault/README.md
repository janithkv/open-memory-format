# Example vault

A tiny but conformant OMF 0.1 vault. Every file here is valid per the
[spec](../spec/0.1/OMF-0.1-draft.md) — read it top to bottom to see the format
in practice.

```
example-vault/
  Journals/2026/07/2026-07-03.md   # a journal entry (date in the filename, §3)
  People/jordan-doe.md             # the vault owner — type: self (§6)
  People/jane-doe.md               # an entity — type: person (§4)
  Places/anytown.md                # type: place
  Projects/learn-piano.md          # type: project
  orma_settings.json               # omf_version + identity pointer (§7)
```

All names, places and projects here are fictional placeholders.

Things to notice:

- **The journal has no frontmatter.** Its date comes from the filename; the
  leading `# heading` is the title.
- **`[[People/jane-doe|@Jane]]`** is a wikilink — `folder/slug` target, `|` alias.
- **Exactly one `People/` file is `type: self`** (`jordan-doe.md`);
  `orma_settings.json` → `user.person_slug` points at it.
- **Slugs are lowercase** and match filenames exactly.
