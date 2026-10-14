# Open Memory Format (OMF) — 0.2 (DRAFT)

> **Status: draft / unstable.** 0.2 replaces [0.1](../0.1/OMF-0.1-draft.md) and
> describes the vault the first Orma release reads and writes.
> [Section 9](#9-changes-since-01) lists what changed. Treat 0.x as a moving
> target, not a stability guarantee.

## 1. Overview

A **memory vault** is a folder of plain Markdown files: dated journal days,
undated notes, and the people and places in them, linked together. It lives in
storage the user controls, such as a local disk, Google Drive, Dropbox or
Nextcloud. Any app that follows this spec can read the vault and take it over,
and the vault opens in Obsidian as it is.

OMF is built from formats people already use:

- **CommonMark** for text,
- **YAML** frontmatter for structured fields,
- **Obsidian conventions** for `[[wikilinks]]`, `![[embeds]]` and
  `> [!callouts]`.

Orma is the reference implementation.

**Conventions.** MUST, SHOULD and MAY are used as in RFC 2119. Files are UTF-8
with LF line endings; readers MUST also accept CRLF and a byte-order mark.
Dates are `YYYY-MM-DD`.

**The one rule above all.** An app MUST preserve everything it doesn't
understand: folders, files, frontmatter keys, settings keys and body text. It
MUST NOT rewrite a file the user didn't change.

**Out of scope:** concurrent editing (writers may assume last-write-wins),
encryption (the vault is plaintext by design), and app UI.

## 2. Vault layout

```
<vault root>/
  Journals/YYYY/MM/YYYY-MM-DD.md   # journal days (Section 4)
  Notes/<title>.md                 # undated notes
  People/<slug>.md                 # people, groups and the vault owner
  Places/<slug>.md
  Photos/…  Videos/…               # attachments
  .orma/orma_settings.json         # settings (Section 7)
```

- Each top-level folder is a **collection**, and each file in it is one record.
  Folder names are case-sensitive.
- The vault root's name isn't part of the format. Orma calls it `My Orma`.
- **Attachments** live under `Photos/` and `Videos/`. Orma names them
  `YYYY-MM-DD_<hash>.<ext>`, where `<hash>` is the first 10 hex digits of the
  file's SHA-1. Person photos go in `Photos/People/`, link thumbnails in
  `Photos/Links/`. Readers MUST accept any path a file references, and writers
  SHOULD NOT delete an attachment when its last reference goes.
- **Conflict copies.** A sync tool that keeps both sides of a conflict names
  the copy `<name> (conflict YYYY-MM-DD).md`, then ` 2`, ` 3` before the
  extension. A conflict copy is never read as a journal day.
- **Reserved names.** Later versions will specify `Todos/`, `Calendar/`,
  `Health/`, user-defined collections such as `Movies/`, and further files in
  `.orma/`. A vault may already contain them. Readers MUST preserve them, and
  SHOULD NOT use these names for anything else.
- OMF apps SHOULD NOT write inside `.obsidian/`.

## 3. Names and slugs

A record's filename without `.md` is its **slug**. In People and Places the
slug is also the record's **handle**, shown as `@slug`.

**People and Places** use the canonical slug:

1. lowercase,
2. replace each run of whitespace with `-`,
3. drop every character outside `[a-z0-9-]`,
4. trim `-` from both ends.

An empty result becomes `entry`. When a slug is taken, the next free
`<slug>-2`, `<slug>-3`, … is used. `Jane Doe` becomes `jane-doe`; letters
outside ASCII are dropped, so `José` becomes `jos`.

**Notes** keep their title as the filename. Drop `\ / : * ? " < > | # ^ [ ]`,
collapse whitespace, strip leading dots and cut to 80 characters; an empty
result becomes `Untitled`. "Trip ideas" is `Notes/Trip ideas.md`.

Rules:

- Writers MUST create People and Places files with lowercase slugs, and MUST
  NOT rename an existing file just because its name isn't canonical.
- Readers SHOULD compare slugs ignoring case. Some storage treats `Sam.md` and
  `sam.md` as one file.
- **Renaming** a record renames its file, and the writer MUST rewrite every
  wikilink to it across the vault.

## 4. Journal days

Path: `Journals/YYYY/MM/YYYY-MM-DD.md`. The filename is the date. Readers
SHOULD also accept a flat `Journals/YYYY-MM-DD.md`.

```markdown
---
location: "[[Places/anytown|Anytown]]"
---
# A good day

Coffee with [[People/jane-doe|@jane-doe]] before the train. #slow

## Lunch

Noodles with [[People/sam|@sam]]. #food
```

- **Frontmatter is optional.** Two keys are defined:
  - `tags`: tags for the whole day ([Section 6.3](#63-tags)).
  - `location`: a wikilink to the place the day was written. An empty
    `location:` means the user removed the place, and apps MUST NOT fill it in
    again.
- Frontmatter starts only on a first line that is exactly `---`. A line like
  `--- Day 2 ---` is ordinary text.
- **Title.** An optional first line `# Title`.
- **Notes inside a day.** Each `##` heading starts a section. `###` and deeper
  headings belong to the section above them.

## 5. People, places and notes

These records are YAML frontmatter followed by an optional Markdown body:

```markdown
---
name: Jane Doe
type: person
birthday: 1990-04-12
relations:
  - "[[People/john-doe|John Doe (brother)]]"
places:
  - "[[Places/anytown|Anytown (home)]]"
---

Met at university. #friends
```

- **`name`** is the display name. Readers fall back to the slug.
- **`type`** is `person`, `self` or `group` in People (no `type` means
  `person`), and `place` in Places. Notes have no `type`.
- Frontmatter MUST be valid YAML. A value that starts with `[[` MUST be
  double-quoted, or YAML reads it as a list.
- Writers leave out empty values.
- The **body** is free Markdown with the same grammar as a journal day.

Appendix A lists every field.

### 5.1 Links between records

A **link block** is a frontmatter key holding a list of wikilinks:
`relations` (person to person), `places` (person to place) and `people`
(place to person).

- A **label** goes at the end of the link's display text, in parentheses. It
  describes the linked record from this file's point of view:
  `[[People/john-doe|John Doe (brother)]]` on Jane's file means John is her
  brother.
- When X links to Y with a label, the writer SHOULD add the matching link back
  from Y to X, using the inverse label in Appendix B.
- **The vault owner** is the one People file with `type: self`. Links between
  the owner and someone else are stored only on the other person's file, so
  the owner's file never fills up with back-links.

## 6. Text grammar

### 6.1 Wikilinks and mentions

```
[[Folder/slug]]             a link
[[Folder/slug|display]]     a link with display text
```

- `Folder/slug` points at `Folder/slug.md`.
- Writers MUST include the folder. A bare `[[slug]]` is not an OMF link.
- Every wikilink counts as a **backlink**: the linked record can list the files
  that point to it.
- A **mention** is a wikilink whose display text is `@slug`:
  `[[People/jane-doe|@jane-doe]]`. That's what writers produce.
- A bare `@slug` in text is also a mention. It matches lowercase slugs only, and
  not inside an email address. It has no folder, so it can match any
  collection.

### 6.2 External links and link cards

Writers use inline links, `[text](https://example.com)`, and add `https://`
when the scheme is missing.

A link MAY carry a **preview card**, written as an Obsidian callout:

```markdown
> [!link] [Page title](https://example.com/article)
> ![[Photos/Links/2026-10-11_ab12cd34ef.jpg]]
> example.com · A one-line description of the page.
```

- Line 1 holds exactly one link. Line 2, an optional thumbnail, and line 3,
  `host` or `host · description` of at most 200 characters.
- Any other quote block is ordinary text.
- Tags inside a card don't count.

### 6.3 Tags

- A tag is `#` followed by letters, digits, `_`, `-` or `/`, at the start of a
  line or after a space. It needs at least one letter or `_`, so `#2026` isn't
  a tag.
- Tags are case-insensitive and stored lowercase. `/` nests:
  `#travel/japan` sits under `travel`.
- Tags in code are ignored.
- **Scope.** Tags before the first `##`, and frontmatter `tags:`, apply to the
  whole file. Tags under a `##` heading apply to that section.
- Writers SHOULD add new tags inline. There is no tag list file: tags exist
  only in the text.

### 6.4 Embeds

Attachments are embedded on a line of their own:

```markdown
![[Photos/2026-07-03_ab12cd34ef.jpg]]
```

A person's photo is a frontmatter field instead:
`photo: "[[Photos/People/jane-doe_ab12cd34ef.jpg]]"`.

`![[Folder/file#Heading]]` shows the section under that heading from another
file. Readers SHOULD render it; Orma doesn't write it at present.

## 7. Settings and identity

Settings live in `.orma/orma_settings.json`. Only two keys belong to OMF:

```json
{
  "omf_version": "0.2",
  "user": { "person_slug": "jordan-doe", "person_name": "Jordan" }
}
```

- `omf_version` (required) is the OMF version the vault follows.
- `user.person_slug` names the vault owner's People file, the one with
  `type: self`. If it's missing, an app MAY find that file and repair the
  pointer.
- Every other key is app state, such as Orma's `apps`, `nav_order`, `pins`,
  `nudge_state` and `location_enabled`. Readers MUST preserve all of it.

## 8. Versioning

- A writer MUST set `omf_version` to the version it follows: `"0.2"`. A
  missing value means `"0.1"`.
- A 0.2 reader MUST read a 0.1 vault, which means accepting these older forms:
  - `orma_settings.json` (and an older `apps.json`) at the vault root, not in
    `.orma/`;
  - reference-style images: `![Photo][img-1]` plus `[img-1]: Photos/…`;
  - `kind:` instead of `category:` on places;
  - a `📍 [[Places/…]]` line in a day, which Orma moves into `location:`.

## 9. Changes since 0.1

- **Simpler scope.** 0.2 covers journal days, notes, people and places. Health,
  Movies, Projects, Dreams and timeline logs are reserved for later versions.
- **Settings moved** into `.orma/`.
- **Attachments** are `![[…]]` embeds, not reference-style images.
- **Journal days** may have frontmatter: `tags` and `location`.
- **New:** notes, people groups, phones, emails and photos, inline tags,
  external links and link cards, conflict copies.
- **Mentions** are written as `[[Folder/slug|@slug]]`.

## 10. Open questions

Still to settle before 1.0:

1. Should `type` stay when it repeats the folder (`type: place`)?
2. Should writers stop producing bare `@slug` mentions? Renames don't update
   them.
3. Should Orma's app state move out of the settings file's top level?
4. Should notes use canonical slugs like everything else?
5. Should section embeds stay in the format?

1.0 will ship with this spec, an example vault, a validator and a reference
parser. The spec text is licensed CC-BY-4.0, and implementing OMF needs no
permission.

---

# Appendix A — Fields

All fields except `name` are optional. Unknown fields MUST be preserved.

## People

| Field | Meaning |
|---|---|
| `name` | display name |
| `type` | `person` (or absent), `self` for the vault owner, `group` for a group |
| `birthday` | `YYYY-MM-DD` |
| `phones` | list like `"+1 555 0100 (mobile)"` |
| `emails` | list like `"jane@example.com (work)"` |
| `photo` | `"[[Photos/People/<file>]]"` |
| `relations` | links to people |
| `places` | links to places |

A **group** is a People file with `type: group` and an optional `emoji`. It
lists members as `"[[People/sam|Sam (member)]]"` under `relations`, and each
member links back with the label `(group)`. Groups don't contain groups.

## Places

| Field | Meaning |
|---|---|
| `name` | place name |
| `type` | `place` |
| `category` | e.g. Café, Park, Home, City |
| `address` | postal address |
| `coordinates` | `"lat, long"` in decimal degrees |
| `people` | links to people |
| `unconfirmed` | `true` on a place an app captured automatically and the user hasn't reviewed |

## Notes

| Field | Meaning |
|---|---|
| `name` | the title; without it, the filename is the title |
| `tags` | tags for the whole note |

---

# Appendix B — Relation labels

When X links to Y with a label, Y links back to X with its inverse.

| Label | Inverse |
|---|---|
| parent | child |
| grandparent | grandchild |
| aunt, uncle, aunt/uncle | niece/nephew |
| manager | employee |
| mentor | mentee |
| member | group |

Each pair also works backwards, so `child` inverts to `parent`. Gendered words
invert to the neutral form: `brother` and `sister` to `sibling`, `boyfriend`
and `girlfriend` to `partner`. Any other label, such as `friend`, `spouse` or
`home`, is its own inverse.

---

# Appendix C — A complete example

`Journals/2026/10/2026-10-12.md`:

```markdown
---
location: "[[Places/anytown|Anytown]]"
---
# Long Sunday

Slow start. Coffee with [[People/jane-doe|@jane-doe]]. #slow

![[Photos/2026-10-12_ab12cd34ef.jpg]]

## Run

Down by the river with [[People/sam|@sam]]. #running

## Reading

> [!link] [The science of rest](https://example.com/rest)
> example.com · A long read about recovery.
```

- The day was written at Anytown and is titled "Long Sunday".
- It has two notes, "Run" and "Reading".
- `#slow` tags the whole day; `#running` tags only the Run note.
- `jane-doe`, `sam` and `anytown` each get a backlink to this day.
