# Example vault

A tiny vault that follows [OMF 0.2](../spec/0.2/OMF-0.2-draft.md). Read it top
to bottom to see the format in practice.

```
example-vault/
  .orma/orma_settings.json         # omf_version + who the vault owner is
  Journals/2026/07/2026-07-03.md   # a journal day
  Notes/Trip ideas.md              # an undated note
  People/jordan-doe.md             # the vault owner (type: self)
  People/jane-doe.md               # a person
  People/hiking-club.md            # a group (type: group)
  Places/anytown.md                # a place
  Todos/book-train-tickets.md      # a to-do
  Calendar/series--events--janes-birthday--65fc.md   # a yearly event
```

All names and places are fictional.

Things to notice:

- **The day's date is its filename.** Its frontmatter only records where it
  was written; `# A good day` is the title, and `## Evening` starts a note
  inside the day.
- **`[[People/jane-doe|@jane-doe]]` is a mention:** a wikilink with the folder,
  the slug, and `@slug` as its display text.
- **Labels sit in the link text.** `Jane Doe (friend)` on Jordan's side, and
  every link has its partner on the other file. The one exception is the
  vault owner's file, which never collects back-links.
- **Tags are inline:** `#grateful` tags the whole day, `#outdoors` only the
  Evening note.
- **To-dos and events use `title`, not `name`.** An event's filename is only a
  hint; its frontmatter is the truth.
- **Wikilinks in frontmatter are quoted**, because YAML would otherwise read
  `[[…]]` as a list.
