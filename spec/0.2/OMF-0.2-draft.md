# Open Memory Format (OMF) — 0.2 (DRAFT)

> **Status: draft / unstable.** 0.2 documents the vault format that the Orma app
> reads and writes as of October 2026. It replaces [0.1](../0.1/OMF-0.1-draft.md)
> (July 2026), and several 0.1 rules were reversed. [Section 13](#13-changes-since-01)
> lists every change. Treat 0.x as a moving target, not a stability guarantee.

## 0. What OMF is

A **memory vault** is a plain folder of Markdown files, plus binary attachments
and a few JSON config files. It records a person's life: dated journal days,
undated notes, and linked entities such as people, places and anything else
the person chooses to track.

OMF is a *profile* of formats developers already know:

- **CommonMark** for bodies,
- **YAML** frontmatter for structured fields,
- **Obsidian conventions** for cross-references: `[[wikilinks]]`, `![[embeds]]`
  and `> [!callouts]`.

A vault is portable by construction. It is files in a folder, in any storage
the user controls: local disk, Google Drive, Dropbox, Nextcloud. Any app that
follows this spec can read the vault and take it over. A vault also opens in
Obsidian with no conversion.

**Orma is the reference implementation.** Where this spec describes Orma's own
app state ([Section 8](#8-the-orma-config-folder)), it does so that other apps
can preserve it, not because they must use it.

**Conventions.** MUST, SHOULD and MAY are used as in RFC 2119. Files are UTF-8.
Writers emit LF line endings; readers MUST accept CRLF and a leading byte-order
mark. Dates are ISO 8601 `YYYY-MM-DD`.

### 0.1 Scope & non-goals

OMF is a **portability / migration** format. It guarantees that a vault written
by one OMF app can be fully read, and taken over, by another.

Out of scope:

- **Concurrent multi-writer editing.** OMF defines no merge semantics; writers
  may assume last-write-wins. Sync engines can still produce conflict copies,
  and [Section 1.3](#13-conflict-copies) says how they are named.
- **Encryption.** The vault is plaintext by design. Protecting it is the job of
  the storage it lives in.
- **App UI.** Labels such as "note", "pin" or "tracker" describe on-disk shapes
  here; how an app presents them is its own business.

## 1. Vault layout

```
<vault root>/
  .orma/                          # app config (Section 8)
    orma_settings.json
    orma_types.json
    orma_metrics.json
  Journals/YYYY/MM/YYYY-MM-DD.md  # dated days (Section 3)
  Notes/<title>.md                # undated notes (Appendix A)
  People/<slug>.md                # people, the self, groups
  Places/<slug>.md
  Todos/<slug>.md
  Calendar/<event-file>.md
  Health/<metric>.md              # built-in metric collection
  <Tracker>/<metric>.md           # user-defined metric collections
  <Collection>/<slug>.md          # user-defined entity collections
  Photos/<date>_<hash>.<ext>      # attachments (Section 1.2)
  Photos/People/<slug>_<hash>.<ext>
  Photos/Links/<date>_<hash>.jpg
  Videos/<date>_<hash>.mp4
```

### 1.1 Collections

- A top-level folder is a **collection**. Folder names are case-sensitive.
- The vault root's own name is not part of the format. Orma names it `My Orma`.
- One file is one record. A record's filename without `.md` is its **slug**
  ([Section 2](#2-names-slugs-and-handles)).
- Users can define their own collections: entity collections such as `Movies/`
  ([Section 8.2](#82-collection-types-orma_typesjson)) and metric collections such
  as `Exercise/` ([Section 8.3](#83-metric-collections-orma_metricsjson)).
- These names are **reserved** and MUST NOT be used for a user collection:
  `People`, `Places`, `Notes`, `Todos`, `Calendar`, `Health`, `Tags`, `Journals`
  and `Journal`.
- A collection name MUST NOT start with `.` or contain any of
  `/ \ # ? % : * " < > |`.
- Folders and files an app doesn't recognise MUST be preserved untouched. OMF
  apps SHOULD NOT write inside `.obsidian/`.

### 1.2 Attachments

Binary files live under `Photos/` and `Videos/`. Orma names them like this:

| File | Path |
|---|---|
| journal photo | `Photos/YYYY-MM-DD_<hash>.jpg` (or `.png`) |
| person photo | `Photos/People/<slug>_<hash>.jpg`, a 512×512 JPEG |
| link-preview thumbnail | `Photos/Links/YYYY-MM-DD_<hash>.jpg`, at most 600 px |
| video | `Videos/YYYY-MM-DD_<hash>.mp4` |
| video poster | `Videos/YYYY-MM-DD_<hash>.jpg`, same base name as the video |

- The date is the day of the entry the file belongs to.
- `<hash>` is the first 10 hex digits of the SHA-1 of the file's bytes, so the
  same bytes always get the same name.
- These names are a writer convention. Readers MUST resolve whatever path a
  file references.
- Writers SHOULD NOT delete an attachment when a reference to it is removed.
  Readers MUST tolerate unreferenced attachments.

### 1.3 Conflict copies

When a sync finds the remote file changed underneath a local edit, the writer
MAY keep both by writing the local version as a **conflict copy**:

```
<stem> (conflict YYYY-MM-DD).<ext>
<stem> (conflict YYYY-MM-DD) 2.<ext>     # second copy on the same day
```

A conflict copy of a journal day doesn't match the day-file pattern, so it is
never read as a day. Apps MUST preserve conflict copies and MAY show them to
the user.

## 2. Names, slugs and handles

### 2.1 Canonical slug

Used by People, Places, Todos and user-defined collections:

1. lowercase,
2. replace each run of whitespace with `-`,
3. drop every character outside `[a-z0-9-]`,
4. trim leading and trailing `-`.

An empty result becomes `entry` (`me` for the self). Letters outside ASCII are
dropped, not transliterated: `José` becomes `jos`. When a slug is taken, the
next free `<slug>-2`, `<slug>-3`, … is used.

- Writers MUST emit lowercase slugs for new files.
- Readers SHOULD compare slugs case-insensitively, because a file written by
  another tool may be `Sam.md`, and some storage backends ignore case.
- Writers MUST NOT rename an existing file just because its slug isn't
  canonical.

### 2.2 Handles and renames

An entity's slug is its **handle**, shown as `@slug`. There is no `handle:`
frontmatter key.

- Changing a handle renames the file. The writer MUST rewrite every
  `[[Folder/old…]]` link in the vault to `[[Folder/new…]]`. An alias of
  exactly `@old` becomes `@new`; other aliases are left alone.
- Renaming a user-defined collection moves its files. The writer MUST rewrite
  every `[[Old/…]]` link to `[[New/…]]`, and each file's `type:` value.

### 2.3 Note filenames

Notes keep their title as the filename, so they follow a different rule:

1. drop `\ / : * ? " < > | # ^ [ ]`,
2. collapse whitespace to single spaces, trim, and strip leading dots,
3. cut to 80 characters.

An empty result becomes `Untitled`. Spaces and case are kept: a note titled
"Trip ideas" is `Notes/Trip ideas.md`. Note slugs are compared
case-insensitively.

### 2.4 Calendar filenames

```
<YYYY-MM-DD>--<app>--<title-slug>--<hash>.md     # one-off event
series--<app>--<title-slug>--<hash>.md          # repeating event
```

- `<app>` is the owning app id with any `app_` prefix removed (`events`).
- `<title-slug>` is the canonical slug of the title, cut to 40 characters.
- `<hash>` is the first 4 hex digits of the SHA-1 of `<appId> <id>`, where
  `<id>` is the event's `id:` value.
- The filename is only a hint; the frontmatter is the truth. Retitling or
  rescheduling an event never renames its file.

### 2.5 Field keys

A user-defined field or metric gets its key from its label: lowercase, replace
each run of characters outside `[a-z0-9]` with `_`, trim `_`. The key is fixed
when the field is created, so relabelling never moves data.

## 3. Journal days

**Path:** `Journals/YYYY/MM/YYYY-MM-DD.md`. Readers SHOULD also accept a flat
`Journals/YYYY-MM-DD.md`. The date is carried by the filename only.

```markdown
---
tags: [travel]
location: "[[Places/anytown|Anytown]]"
---
# A good day

Coffee with [[People/jane-doe|@jane-doe]] before the train. #slow

## Lunch

Noodles at [[Places/lila-cafe|@lila-cafe]]. #food
```

- **Frontmatter is optional.** A day without it MUST round-trip byte for byte
  when its content is unchanged.
  - `tags` holds the day's file-level tags ([Section 7](#7-tags)).
  - `location` is a Places wikilink recording where the day was written. A
    present but empty `location:` means the user removed the place on purpose,
    and apps MUST NOT fill it in again automatically.
  - Other keys MUST be preserved.
- **Fences.** Frontmatter opens only on a first line that is exactly `---`. A
  line like `--- Day 2 ---` is body text.
- **Title.** An optional first line `# Title`, followed by a blank line.
- **Sections.** Each `##` heading starts a section, which Orma calls a note.
  `###` and deeper headings belong to the enclosing section. Text before the
  first `##` belongs to the day itself.
- **Body grammar.** Wikilinks and mentions ([Section 5](#5-links-and-mentions)),
  media embeds ([Section 6](#6-embeds-and-attachments)), tags
  ([Section 7](#7-tags)) and link-preview cards
  ([Section 5.4](#54-link-preview-cards)).

## 4. Entity files

An entity file is YAML frontmatter plus an optional Markdown body:

```markdown
---
name: Jane's Place
type: place
category: Home
address: 1 Example Street, Anytown
coordinates: "12.9716, 77.5946"
people:
  - "[[People/jane-doe|Jane Doe (home)]]"
---

Optional free-text notes.
```

### 4.1 Frontmatter rules

- Frontmatter MUST be a YAML mapping. A block that doesn't parse as a mapping
  is not frontmatter: readers treat the whole file as body, and MUST NOT drop
  it on save.
- **`name`** (string): the display name. Readers fall back to `title:`, then to
  the slug. Writers put `name` first and `type` second.
- **`type`** (string): see [Section 4.2](#42-type).
- Writers omit keys whose value is an empty string, list or map.
- Any value that starts with `[[` MUST be double-quoted. Unquoted, YAML reads
  it as a nested list.
- Writers quote any other scalar YAML would misread: values that look like
  booleans, nulls or numbers, values with a leading indicator character, and
  values containing `: ` or ` #`. Clock times such as `"09:00"` are always
  quoted, because YAML 1.1 reads an unquoted `09:00` as the number 540.
- Unknown keys MUST be preserved.

### 4.2 `type`

| Collection | `type` |
|---|---|
| People | `person` (an absent `type` also means person), `self` ([Section 9](#9-identity-the-self)), or `group` |
| Places | `place` |
| user-defined collection | the collection's folder name, exactly: `type: Movies` |
| Notes, Todos, Calendar, metric files | none |

### 4.3 Link blocks

A **link block** is a frontmatter key whose value is a YAML list of wikilink
strings. The relation **label** sits at the end of the wikilink's alias, in
parentheses:

```yaml
relations:
  - "[[People/john-doe|John Doe (brother)]]"
  - "[[People/climbing-crew|Climbing Crew (group)]]"
places:
  - "[[Places/anytown|Anytown (home)]]"
```

- Built-in blocks: `relations` (People to People), `places` (People to Places)
  and `people` (Places and user collections to People).
- Every `link` field of a user-defined collection is also a link block
  ([Section 8.2](#82-collection-types-orma_typesjson)).
- A label describes the **target** from the point of view of the file it sits
  in. `[[People/john-doe|John Doe (brother)]]` on Jane's file means John is
  Jane's brother. Unlabelled entries are allowed.
- **Reciprocity.** A writer that records a labelled link from X to Y SHOULD
  record the inverse on Y, using the table in Appendix B.
- **The self is the exception.** A relation between the self and another person
  is stored only on the other person's file. The self file MUST NOT accumulate
  back-links, so it never becomes a hub listing everyone.

### 4.4 Bodies

Everything after the closing `---` is the body. It uses the journal body
grammar ([Section 3](#3-journal-days)). Apps SHOULD preserve it verbatim.

### 4.5 File kinds

The folder decides a file's kind:

| Kind | Where | One file is |
|---|---|---|
| entity | People, Places, user-defined collections | one subject |
| note | `Notes/` | one undated note |
| metric | `Health/` and user-defined metric collections | one measured quantity, as a dated table |
| to-do | `Todos/` | one task |
| event | `Calendar/` | one event or series |

Appendix A gives each kind's fields. 0.1's `kind:` key and its **log** kind are
retired ([Section 13](#13-changes-since-01)). Readers MUST preserve a `kind:` key
when they find one.

## 5. Links and mentions

### 5.1 Wikilink grammar

```
[[Folder/slug]]
[[Folder/slug|alias]]
[[Folder/slug#Heading|alias]]
```

- `Folder` is everything before the first `/`, and may contain spaces and
  digits. `slug` runs to the first `#`, `|` or `]]`. Neither part may contain a
  bracket or a line break.
- `[[Folder/slug]]` resolves to `Folder/slug.md`. Folder names match exactly;
  slugs match case-insensitively.
- Writers MUST emit folder-qualified links and SHOULD include an alias.
- A bare `[[slug]]` with no folder is Obsidian's shortest-path link. It is not
  an OMF entity link: readers MAY resolve it but don't index it as a reference.
- Every wikilink is a **backlink**: the target can list the files that link to
  it.

Alias conventions:

| Alias | Meaning | Example |
|---|---|---|
| `Name (label)` | a relation ([Section 4.3](#43-link-blocks)) | `[[People/jane-doe\|Jane Doe (friend)]]` |
| `@slug` | a mention in prose ([Section 5.2](#52-mentions)) | `[[People/jane-doe\|@jane-doe]]` |
| `@metric value unit · note` | a logged reading ([Section 6.3](#63-metric-readings)) | `[[Health/weight\|@weight 72.5 kg · after run]]` |
| anything else | display text | `[[Places/anytown\|Anytown]]` |

### 5.2 Mentions

Writers record a mention as a folder-qualified wikilink whose alias is
`@slug`, as in `[[People/jane-doe|@jane-doe]]`.

A bare `@slug` in prose is also a mention:

```
(?<![A-Za-z0-9._%+-])@([a-z0-9][a-z0-9-]*)
```

- It is lowercase only, so `@Jane` is display text, not a mention.
- The left boundary keeps an email address like `bob@acme.com` from matching.
- A bare mention carries no folder. Readers match it against every collection
  with that slug.

`@` never marks a tag.

### 5.3 External links

- Writers use inline links: `[text](url)`. They never write reference-style
  links for external URLs.
- A URL without a scheme gets `https://`.
- A URL that contains whitespace or parentheses is wrapped as `<url>`.
- `\`, `[` and `]` in the link text are escaped with a backslash.

### 5.4 Link-preview cards

A saved web link MAY carry a preview card, written as an Obsidian callout of
type `link`:

```markdown
> [!link] [Page title](https://example.com/article)
> ![[Photos/Links/2026-10-11_ab12cd34ef.jpg]]
> example.com · A one-line description of the page.
```

- **Line 1** is `> [!link]` followed by exactly one Markdown link. The type
  token matches case-insensitively.
- **Line 2** is optional: an embed of a thumbnail under `Photos/Links/`.
- **Line 3** is `> host` or `> host · description`. The description is one
  line of at most 200 characters, cut at a word with `…`. A third line without
  the ` · ` separator is the host when it is one word, else the description.
- The card is one block with a blank line before and after it. A `>` line
  straight after the card means the block is not a card.
- Writers put the card after the paragraph that holds the link. When that
  paragraph is only the link, the card replaces it, and the card's title line
  is the link. Writers write at most one card per URL per file.
- Any other blockquote, or a malformed card, is prose and MUST round-trip byte
  for byte.
- Text inside a card is not scanned for tags.

Obsidian renders `[!link]` as a generic callout.

## 6. Embeds and attachments

### 6.1 Media embeds

Writers embed an attachment as an Obsidian embed on its own line, with no
alias:

```markdown
![[Photos/2026-07-03_ab12cd34ef.jpg]]

![[Videos/2026-07-03_9f8e7d6c5b.mp4]]
```

- An embed with `#` or `|` in it is not a media embed, and is kept as text.
- **0.1 form.** Readers MUST still read the 0.1 reference-style form:

  ```markdown
  ![Photo][img-1]

  [img-1]: Photos/2026-06-27-river.jpg
  ```

  Writers SHOULD convert it to an embed on the next save. A photo wrapped in a
  link, `[![Photo][img-1]][link-1]`, is kept in the reference form.
- Writers MAY prune reference definitions that point into `Photos/` or
  `Videos/` and are no longer used. Other reference definitions are prose and
  MUST be kept.

Person photos are referenced from frontmatter instead:

```yaml
photo: "[[Photos/People/jane-doe_ab12cd34ef.jpg]]"
```

Readers also accept a bare path, or a wikilink with an alias.

### 6.2 Section embeds

```
![[Folder/file#Heading]]
```

A section embed transcludes the part of `Folder/file.md` under `Heading`. The
heading text is matched exactly; the section runs to the next heading of the
same or a higher level; the first match wins. An embed that doesn't resolve
renders as a placeholder. Whole-file embeds are not expanded.

Orma reads and preserves section embeds but no longer writes them
([Section 12](#12-open-questions)).

### 6.3 Metric readings

Logging a reading appends a row to the metric file (Appendix A) and writes a
wikilink into that day's journal:

```markdown
[[Health/weight|@weight 72.5 kg · after run]]
```

- The alias is fixed when the reading is logged, so the day keeps a
  point-in-time record even if the table is edited later.
- A note longer than 40 characters is cut, with `…`.
- The link is a backlink, so the metric file can list the days it was logged.

This replaces 0.1's plain-text snapshot line (`Weight — 167 lb`).

## 7. Tags

- **Inline grammar.** `#tag` at the start of a line or after whitespace,
  matching `[A-Za-z0-9_/-]+`, with at least one letter or `_`. `#2026` is not a
  tag. A line starting `# ` with a space is a heading.
- Tags are folded to lowercase.
- `/` nests: `#travel/japan` sits under `travel`. The tag is stored whole.
- Tags inside fenced code, inline code and link-preview cards are ignored.
- **Frontmatter.** `tags:` holds a YAML list, or a comma- or space-separated
  string. Values have no `#`.
- **Scope.** In a day or note file, frontmatter tags and inline tags before the
  first `##` belong to the whole file. Tags on a `##` heading line, or inside
  its section, belong to that section.
- **Writing.** Writers SHOULD add a new tag inline in the body, as `#tag `.
  Existing frontmatter tags MUST be preserved.
- **Renaming** a tag rewrites inline `#from` and `#from/…` everywhere, plus
  frontmatter entries, skipping code.
- There is no tag registry file. Tags exist only in the text.

Orma indexes tags in Journals, Notes, People and Places.

## 8. The `.orma/` config folder

Orma keeps its config in a hidden `.orma/` folder at the vault root. Obsidian
hides dot-folders, so the user sees only content.

- In 0.1 these files sat at the vault root. A reader that finds no `.orma/`
  copy MUST read the root copy. Orma moves the file into `.orma/` and deletes
  the root copy.
- An older `apps.json` at the root is merged into the settings file.
- All three files are JSON. Unknown keys MUST be preserved wherever this
  section says so.

### 8.1 Settings: `orma_settings.json`

```json
{
  "omf_version": "0.2",
  "user": { "person_slug": "jordan-doe", "person_name": "Jordan" },
  "apps": {
    "app_people": { "enabled": true },
    "type_Movies": { "enabled": true }
  },
  "nav_order": ["app_people", "type_Movies"],
  "pins": [],
  "location_enabled": false
}
```

| Key | Status | Meaning |
|---|---|---|
| `omf_version` | **core**, required | the OMF version the vault conforms to ([Section 10](#10-versioning)) |
| `user` | **core** | `person_slug` and `person_name` of the self ([Section 9](#9-identity-the-self)) |
| `apps` | app state | per-app state, by app id |
| `nav_order` | app state | app ids in display order |
| `pins` | app state | items pinned to the timeline |
| `nudge_state` | app state | dismissed and snoozed reminders |
| `location_enabled` | app state | whether new days record a location |
| `saved_searches` | legacy | read once and migrated into `pins`; never written |

Unknown top-level keys, and unknown keys inside each `apps` entry, MUST be
preserved. On a name collision, the known key wins.

**App ids.** Built-in: `app_notes`, `app_people`, `app_places`, `app_health`,
`app_todos`, `app_events`. A user-defined collection is `type_<Folder>`; a
user-defined metric collection is `metric_<Folder>`.

**`apps.<id>`** is `{ "enabled": bool, "nudges"?: {…} }`. `nudges` configures
date reminders:

```json
{ "enabled": true, "leadDays": 7, "showAnytime": false,
  "fields": { "birthday": { "on": true, "recur": "yearly" } } }
```

`recur` is `yearly` or `once`. `leadDays` and `showAnytime` are optional.

**`pins`** is an ordered list. Every pin has `id`, `kind` and `pinnedAt` (ISO
8601, UTC), plus fields by kind:

| `kind` | Fields |
|---|---|
| `note` | `path`: `"Notes/<file>.md"` |
| `dayNote` | `date`: `YYYY-MM-DD`; `heading`: the `##` text with tags removed |
| `tags` | `name`, `emoji`, `tags` (list), `view`: `day` or `note` |

Readers drop pins of an unknown kind.

**`nudge_state`** maps `<appId>:<recordPath>:<field>:<YYYY-MM-DD>` to
`{ "dismissedAt": ISO datetime }` or `{ "snoozeUntil": "YYYY-MM-DD" }`.
Entries more than 90 days past their date are pruned.

### 8.2 Collection types: `orma_types.json`

Defines the user-defined entity collections:

```json
{
  "version": 2,
  "types": [
    { "folder": "Books", "emoji": "📚", "groupBy": "status",
      "fields": [
        { "key": "author", "label": "Author", "kind": "text" },
        { "key": "status", "label": "Status", "kind": "enum",
          "options": ["To read", "Reading", "Read"] },
        { "key": "rating", "label": "Rating", "kind": "rating", "max": 5 },
        { "key": "people", "label": "People", "kind": "link",
          "targetFolder": "People", "labels": ["recommended by"] }
      ] }
  ],
  "done": ["movies-format-1"]
}
```

- A type's `folder` is its identity. `emoji` is display only.
- `groupBy` (optional) names an `enum` field to group the list by.
- `notes: false` (optional) turns off the body for the collection.
- `done` (optional) lists one-shot migrations already applied to the vault.
- A missing file, or one below version 2, gets the starter types (Appendix A).
- The field keys `name`, `type` and `notes` are reserved.
- Removing a field or a type leaves its data in the files. It is never deleted.

Field kinds and how values are stored in each file's frontmatter:

| `kind` | Extra keys | Frontmatter value |
|---|---|---|
| `text` | | string |
| `number` | | a number. Orma currently writes a quoted string, such as `"1999"`, so readers MUST accept both. |
| `rating` | `max` (default 5) | integer from 1 to `max` |
| `date` | | `YYYY-MM-DD` |
| `enum` | `options` | one of the options, as a string |
| `link` | `targetFolder` (default `People`), `labels` (offered relation labels) | a link block ([Section 4.3](#43-link-blocks)) |

Readers treat an unknown `kind` as `text`. A writer MUST keep a value it can't
display, such as a retired option or a fractional rating, unless the user edits
that field.

### 8.3 Metric collections: `orma_metrics.json`

Defines user-defined metric collections. The built-in `Health/` collection
isn't listed; its metrics are fixed (Appendix A).

```json
{
  "version": 1,
  "groups": [
    { "folder": "Exercise", "name": "Exercise", "emoji": "🏋️",
      "metrics": [
        { "key": "bench_press", "label": "Bench press", "emoji": "💪",
          "unit": "kg", "kind": "number", "direction": "higher",
          "unitOptions": ["kg", "lb"] }
      ] }
  ]
}
```

- `kind` is `number`, `scale`, `duration` or `count`. Readers treat an unknown
  kind as `number`.
- `direction` is `higher`, `lower` or `neutral`: which way counts as an
  improvement.
- A `scale` metric runs from 1 to 10 unless `scaleMin` or `scaleMax` say
  otherwise.
- `unitOptions` (optional) lists units the user can switch between.

## 9. Identity (the self)

- Exactly **one** `People/<slug>.md` carries `type: self`. It is the vault
  owner.
- `.orma/orma_settings.json`: `user.person_slug` is the authoritative pointer
  to that file; `user.person_name` is the display name.
- If the pointer is missing, an app MAY scan `People/` for the single
  `type: self` file and repair the pointer.
- The self file MUST NOT accumulate back-links ([Section 4.3](#43-link-blocks)).

## 10. Versioning

- A vault declares its version in `omf_version` ([Section 8.1](#81-settings-orma_settingsjson)).
- A writer MUST set it to the version it conforms to. A 0.2 writer writes
  `"0.2"`.
- A missing value is treated as `"0.1"`.
- A 0.2 reader MUST read a 0.1 vault. The legacy forms it has to accept are
  listed in [Section 13](#13-changes-since-01).

## 11. Resolved decisions

- **Strict YAML.** Frontmatter MUST be valid YAML.
- **Lowercase slugs** for new entity files ([Section 2.1](#21-canonical-slug)).
  Notes keep their title as the filename ([Section 2.3](#23-note-filenames)).
- **Obsidian embeds for attachments** ([Section 6.1](#61-media-embeds)). This
  reverses 0.1, which required reference-style CommonMark images.
- **Config lives in `.orma/`** ([Section 8](#8-the-orma-config-folder)).
- **Journal days may have frontmatter** ([Section 3](#3-journal-days)).
- **Labels live in the alias**: relations, phones, emails and profile links all
  use the `value (label)` form.
- **The folder decides the kind** ([Section 4.5](#45-file-kinds)). The `kind:`
  key is retired.
- **Concurrency and encryption are out of scope** ([Section 0.1](#01-scope--non-goals)).

## 12. Open questions

Still to settle before 1.0:

1. **`type` redundancy.** `type` repeats the folder for user collections, but
   marks a variant in People. Keep it always present, or only when it deviates?
2. **Bare mentions.** A bare `@slug` matches any collection, and renaming a
   handle doesn't rewrite bare mentions. Should writers stop producing them, or
   should renames rewrite them?
3. **Settings scope.** `apps`, `nav_order`, `pins` and `nudge_state` are Orma
   app state in a core file. Should they move into a namespaced block?
4. **Number fields.** Should `number` values be written as YAML numbers rather
   than quoted strings?
5. **Note filenames.** Notes are the only collection that doesn't use the
   canonical slug. Keep the exception?
6. **Section embeds and logs.** Nothing writes section embeds or log files now.
   Drop them from 1.0, or bring them back for timelines?
7. **Attachment clean-up.** Attachments are never deleted. Should the format
   define how an app may collect unreferenced files?

## 13. Changes since 0.1

**Changed:**

- Config moved from the vault root into `.orma/` ([Section 8](#8-the-orma-config-folder)).
- Attachments are written as `![[…]]` embeds, not reference-style images
  ([Section 6.1](#61-media-embeds)).
- Journal days may carry frontmatter: `tags` and `location`
  ([Section 3](#3-journal-days)).
- Movies and Projects are now starter user collections with `type: Movies` and
  `type: Projects` (Appendix A). 0.1's `type: movie` and `type: series` become
  `format: Film` and `format: Series`, and `creator` becomes `director`.
- Places use `category`, replacing 0.1's `kind`.
- Mentions are written as `[[Folder/slug|@slug]]`. A bare `@slug` matches any
  collection, not just People ([Section 5.2](#52-mentions)).
- Metric readings appear in the journal as wikilinks, not snapshot lines
  ([Section 6.3](#63-metric-readings)).

**Added:**

- Collections: `Notes/`, `Todos/`, `Calendar/`, user-defined entity
  collections and user-defined metric collections.
- People groups (`type: group`), phones, emails and person photos (Appendix A).
- Inline tags ([Section 7](#7-tags)).
- External links and link-preview cards ([Section 5.3](#53-external-links),
  [Section 5.4](#54-link-preview-cards)).
- Conflict-copy names ([Section 1.3](#13-conflict-copies)).
- `orma_types.json` and `orma_metrics.json`, and the settings keys `pins`,
  `nudge_state` and `location_enabled` ([Section 8](#8-the-orma-config-folder)).
- Note and calendar filename rules ([Section 2](#2-names-slugs-and-handles)).

**Removed:**

- The `kind:` key and the **log** kind. Dreams and F1 are no longer built-in
  collections.
- Writing section embeds. They are still read ([Section 6.2](#62-section-embeds)).
- The `## Updates` convention for Projects. Existing sections are ordinary body
  text.

**Legacy forms a 0.2 reader MUST accept:** root-level config files and
`apps.json`; reference-style photos and videos; `saved_searches`; Movies files
with `type: movie|series`; Places with `kind`; lines starting
`📍 [[Places/…]]` in a day body, which Orma moves into `location:` on save.

## 14. Conformance

A 1.0 ships with this spec, an **example vault**, a **validator** and a
**reference parser**. The spec text is licensed CC-BY-4.0; implementing OMF
needs no permission.

---

# Appendix A — Collection reference

All fields other than `name` and `type` are OPTIONAL. Unknown fields MUST be
preserved.

## People (`People/`)

| Field | Kind | Meaning |
|---|---|---|
| `name` | string | display name |
| `type` | string | `person` (or absent), `self`, or `group` |
| `birthday` | date | `YYYY-MM-DD` |
| `phones` | list | `"+1 555 0100 (mobile)"`. Labels: mobile, home, work, main, fax, pager, other |
| `emails` | list | `"jane@example.com (work)"` |
| `photo` | wikilink | `"[[Photos/People/<slug>_<hash>.jpg]]"` |
| `relations` | link block | links to People; the label says who they are to this person |
| `places` | link block | links to Places, e.g. `(home)` |
| body | Markdown | notes |

**Groups** are People files with `type: group`:

```markdown
---
name: Climbing Crew
type: group
emoji: 🧗
relations:
  - "[[People/sam|Sam (member)]]"
  - "[[People/priya|Priya (member)]]"
---
```

- `emoji` is optional; the default is 👥.
- Each member's file carries the inverse, `[[People/climbing-crew|Climbing Crew (group)]]`.
- Groups don't nest: a `(member)` link to another group is dropped on save.
- A group has no `birthday`, `phones`, `emails` or `photo`.

## Places (`Places/`) — `type: place`

| Field | Kind | Meaning |
|---|---|---|
| `category` | string | Orma offers Café, Restaurant, Bar, Park, Beach, Museum, Landmark, Hotel, Airport, City, Home, Office |
| `address` | string | postal address |
| `coordinates` | string | `"lat, long"` in decimal degrees |
| `people` | link block | people linked to the place |
| `unconfirmed` | bool | `true` on a place captured automatically and not yet reviewed. Saving the place in the editor removes it. |
| body | Markdown | notes |

## Notes (`Notes/`)

```markdown
---
name: Trip ideas
---

Kyoto in autumn. #travel
```

- `name` is the title. Without it, the filename is the title. A `# H1` in the
  body is not read as a title.
- `##` headings are sections inside the note, not separate notes.
- `tags` in frontmatter are allowed, as in [Section 7](#7-tags).

## To-dos (`Todos/`)

| Field | Kind | Meaning |
|---|---|---|
| `title` | string | the task |
| `due` | date | when it's due; absent means any time |
| `leadDays` | integer | days of warning before `due` |
| `done` | bool | `true` when finished |
| `doneAt` | datetime | local completion time, ISO 8601 |
| body | Markdown | notes |

## Calendar (`Calendar/`)

| Field | Kind | Meaning |
|---|---|---|
| `title` | string | event title |
| `app` | string | owning app id, matching the filename |
| `start` | date | the event's (first) day |
| `time` | string | `"HH:MM"` local wall-clock time, always quoted; absent means all day |
| `rrule` | string | an RFC 5545 RRULE value, kept verbatim |
| `exdate` | list of dates | skipped occurrences |
| `id` | string | a UUIDv4, stable for the event's life |
| body | Markdown | notes |

Events are single-day. `end`, `ics_uid` and `ics_source` are reserved.

## Metric files (`Health/` and user-defined metric collections)

```markdown
---
metric: weight
unit: kg
---

| date | value | unit | notes |
|------|-------|------|-------|
| 2026-10-12 | 72.5 | kg | after run |
| 2026-10-05 | 73.1 | kg |  |
```

- **Path:** `<Folder>/<metric key>.md`.
- **Frontmatter:** `metric` (the key) and `unit` (the chosen unit when the
  metric offers several). Other frontmatter lines are kept as written.
- **Rows:** rows whose first cell isn't a date are kept but not read. Writers
  keep a table's existing order, newest-first or oldest-first, and new tables
  are newest-first. A `|` inside a cell is written `\|`.
- **Values** are written as text: `number` is a decimal, `scale` and `count`
  are integers, `duration` is whole seconds.
- Surrounding prose, extra cells, CRLF line endings and a byte-order mark MUST
  survive a write.

The built-in `Health/` metrics:

| Key | Kind | Unit |
|---|---|---|
| `weight` | number | kg (or lb) |
| `sleep` | number | hr |
| `mood` | scale | |
| `steps` | count | |

## Starter collections: Movies and Projects

Orma seeds these into `orma_types.json` once. After that they are ordinary
user collections that the user can edit or delete.

**Movies** (`type: Movies`): `format` (Film, Series), `director`, `year`,
`genre`, `status` (Want to Watch, Watching, Watched), `watched_date`, `rating`
(1–5), `actors`, and `people` (labels: watched with, recommended by, starring,
directed by).

**Projects** (`type: Projects`): `status` (Planning, Active, On hold, Done),
`start`, `target`, `places` (labels: at, route, start, end, near), and `people`
(labels: with, organizer, contact).

---

# Appendix B — Relation labels and their inverses

When X's file links to Y with a label, Y's file links back to X with the
inverse label.

| Label | Inverse |
|---|---|
| parent | child |
| child | parent |
| grandparent | grandchild |
| grandchild | grandparent |
| aunt, uncle, aunt/uncle | niece/nephew |
| niece, nephew, niece/nephew | aunt/uncle |
| sibling, brother, sister | sibling |
| spouse | spouse |
| partner, boyfriend, girlfriend | partner |
| cousin | cousin |
| friend | friend |
| acquaintance | acquaintance |
| colleague | colleague |
| manager | employee |
| employee | manager |
| mentor | mentee |
| mentee | mentor |
| family | family |
| member | group |
| group | member |

A label not in this table is its own inverse. Place links use the same label in
both directions: a person's `[[Places/x|X (home)]]` pairs with the place's
`[[People/jane|Jane (home)]]`.

---

# Appendix C — Implementer guidance

- **Preserve what you don't understand.** Unknown folders, files, frontmatter
  keys, settings keys and body syntax all survive a write.
- **Don't reformat on read.** A file the user didn't change MUST NOT be
  rewritten. Orma writes `tags: [a, b]` in flow form when a day has no other
  frontmatter, so plain days stay byte-identical.
- **Assume case-insensitive storage.** Dropbox, macOS and Windows treat
  `Trip.md` and `trip.md` as one file. Check for a clash ignoring case before
  creating a file.
- **Quote for YAML 1.1.** Other tools may parse frontmatter as YAML 1.1, which
  reads `09:00`, `yes` and `no` differently from YAML 1.2.
- **Fall back gracefully.** An app that doesn't model a collection can always
  show a file's `name`, `type`, raw frontmatter and body.
- **Never delete attachments implicitly.** A removed photo leaves its file in
  place.

---

# Appendix D — A worked day

`Journals/2026/10/2026-10-12.md`:

```markdown
---
location: "[[Places/anytown|Anytown]]"
---
# Long Sunday

Slow start. Coffee with [[People/jane-doe|@jane-doe]]. #slow

![[Photos/2026-10-12_ab12cd34ef.jpg]]

## Run

Down by the river. [[Health/weight|@weight 72.5 kg · after run]] #running

## Reading

[Why we sleep](https://example.com/why-we-sleep)

> [!link] [The science of rest](https://example.com/rest)
> example.com · A long read about recovery.
```

What a reader sees:

- The day was written at Anytown. It has the title "Long Sunday" and two
  notes, "Run" and "Reading".
- `#slow` tags the whole day. `#running` tags only the Run note.
- `jane-doe`, `anytown` and `Health/weight` each get a backlink to this day.
- The photo is an attachment, and `Health/weight.md` holds the matching row
  for 2026-10-12.
- The Reading note holds a plain link and a link with a preview card.
