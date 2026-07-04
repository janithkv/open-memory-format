# Open Memory Format (OMF) — 0.1 (DRAFT)

> **Status: draft / unstable.** OMF is the open vault format that the Orma app
> reads and writes. This 0.1 documents the format *as currently implemented* and
> flags the decisions that must be settled before a stable 1.0. Do not treat
> 0.x as a stability guarantee.

## 0. What OMF is

A **memory vault** is a plain folder of **Markdown** files (plus a few binaries
and one JSON settings file) that records a person's life: journal entries and
linked entities — people, places, projects, and more — connected by wikilinks.

OMF is a *profile* of three things developers already know:

- **CommonMark** Markdown for bodies,
- **YAML** frontmatter for structured fields,
- `[[wikilinks]]` and `![[embeds]]` for cross-references (Obsidian-compatible).

A vault is portable by construction: it is just files in a folder, in any
storage the user controls (local disk, Google Drive, Dropbox, …). Any app that
follows this spec can read and write the same vault.

Files come in three **kinds** (§4.3): **entity** (one subject per file),
**metric** (a dated numeric table), and **log** (a timeline of dated sections).
All three are plain Markdown with YAML frontmatter; they differ only in body
shape.

UTF-8, LF line endings throughout.

### 0.1 Scope & non-goals

OMF is a **portability / migration** format: it guarantees that a vault written
by one OMF app can be fully read (and taken over) by another. It is **not** a
concurrent multi-writer protocol — two apps editing the same vault at the same
time is out of scope, so OMF does **not** define merge/conflict semantics
(writers may assume last-write-wins). This keeps the format simple: your data is
portable, without the complexity of real-time co-editing.

## 1. Vault layout

```
<vault root>/
  Journals/                 # dated entries
    YYYY/MM/YYYY-MM-DD.md
  People/<slug>.md          # entity folders (one entity per file)
  Places/<slug>.md
  Projects/<slug>.md
  Dreams/<slug>.md          # apps MAY define further entity folders
  Movies/<slug>.md
  Health/…                  # app-defined sub-layout
  Photos/                   # binary attachments (images, …)
  orma_settings.json        # vault settings + identity (see §6)
```

- Top-level folder name = the **entity collection** (singular `type` in §4).
- One entity per file; the file's **slug** (filename without `.md`) is its
  identity within the collection.
- Folders an app doesn't recognize MUST be preserved untouched (forward-compat).

## 2. Slugs

A slug is the stable file identity. Canonical slugify:

1. lowercase, 2. collapse whitespace runs to `-`, 3. remove anything outside
`[a-z0-9-]`, 4. trim leading/trailing `-`. Empty result → a folder-defined
fallback (`entry`; `me` for an empty self).

Slugs are **case-sensitive and lowercase**. A wikilink's slug MUST match the
target filename exactly (`People/jane-doe`, never `People/Jane-Doe`).

## 3. Journal entries

Path: `Journals/YYYY/MM/YYYY-MM-DD.md` (hierarchical). Readers SHOULD also
accept a flat `Journals/YYYY-MM-DD.md`; writers SHOULD use the hierarchical form.

Content is Markdown with **no frontmatter**. An optional leading
`# Heading` is the entry title; everything after is the body:

```markdown
# A good day

Had coffee with [[People/jane-doe|@Jane]]. Felt @grateful.
```

The **date is carried by the filename**, not the body.

## 4. Entity files

An entity file is YAML frontmatter + an optional Markdown body (free-text
"notes").

```markdown
---
name: Jane's Place
type: place
address: 1 Example Street, Anytown
people:
  - "[[People/jane-doe|Jane (home)]]"
---

Optional free-text notes go here.
```

### 4.1 Frontmatter fields

- **`name`** (string, required) — display name.
- **`type`** (string, required) — the entity type. The **folder is the primary
  type** (`People`→`person`, `Places`→`place`, …). `type` MAY deviate to mark a
  variant within a folder:
  - `self` — the user's own person (exactly one per vault; see §6).
  - `series` — a TV series in `Movies/` (vs. the default `movie`).
- **scalar fields** (string) — app/collection-specific, e.g. `birthday`,
  `address`, `kind`, `city`. Unknown scalars MUST be preserved.
- **link blocks** (`relations`, `places`, `people`) — see §5.

### 4.2 Bodies

Everything after the closing `---` is the notes body (Markdown). Apps SHOULD
preserve it verbatim.

### 4.3 File kinds

A collection's files are one of three kinds. All share YAML frontmatter, real
YAML, lowercase slugs, and Markdown bodies — they differ only in **body shape**
and so in how they're surfaced (§5.6):

| Kind | Frontmatter | Body | Used by | One file = |
|---|---|---|---|---|
| **entity** | `name`, `type`, fields, link blocks | free-text notes | People, Places, Movies, Dreams, Projects | one subject |
| **metric** | `metric`, `unit` | a dated table | Health | one measured quantity |
| **log** | `name`, `type` | a sequence of dated `##` sections | F1, any timeline | one timeline (e.g. a season) |

`type`/`metric` identify the collection. The kind is given by an optional
**`kind: entity|metric|log`** frontmatter field; when absent it is inferred — a
file with a `metric:` key is a metric, otherwise it is an entity. Because an
entity's notes may legitimately contain a `## YYYY-MM-DD` heading, **log files
MUST declare `kind: log`** (it cannot be safely inferred); `kind` is optional for
entity and metric files.

The **journal** (§3) is itself a per-date log-like file, but path-addressed by
date rather than section-addressed.

## 5. Links

### 5.1 Wikilink grammar

```
[[<Folder>/<slug>|<display>]]
```

- `<Folder>/<slug>` resolves to the file `<Folder>/<slug>.md`.
- `<display>` is human text, optionally carrying a **relation label** in
  trailing parentheses: `Name` or `Name (label)`.

Examples: `[[People/jane-doe|Jane]]`, `[[People/john-doe|John (home)]]`.

### 5.2 Link blocks (relations)

A link block is a frontmatter key whose value is a YAML **list of wikilink
strings**. The **relation label is encoded in the wikilink display** (the
`(label)` suffix), not as a YAML sub-key:

```yaml
relations:
  - "[[People/jaswan|Jaswanth (brother)]]"
  - "[[People/kimi|Kimi (friend)]]"
places:
  - "[[Places/berlin|Berlin (home)]]"
```

Defined blocks: `relations` (→ People), `places` (→ Places), `people`
(→ People, used on non-person entities). Apps MAY define more.

**Reciprocity is a within-app convention:** when an app records "X relates to
Y", it SHOULD also record the inverse on Y — *except* links to the `self` entity
(§6), which are intentionally one-directional to avoid an unbounded hub file.
Because OMF is a migration format (§0.1), an importing app simply reads whatever
links exist; it need not reconcile or merge them.

### 5.3 Mention shorthand

In journal/body text, `@<slug>` is a lightweight mention of an entity by slug
(default collection: People). It is equivalent, for indexing/backlink purposes,
to a wikilink to that slug.

### 5.4 Attachments / photos

Binary attachments live under `Photos/`. They are embedded in Markdown using
**standard CommonMark reference-style image links** with a matching link
reference definition, e.g.:

```markdown
![alt text][photo-1]

[photo-1]: Photos/2026-06-27-river.jpg
```

This is ordinary CommonMark — it renders in Obsidian and any compliant Markdown
engine, so attachments are portable with no OMF-specific extension. A
reference-style image MAY be wrapped in a reference-style link
(`[![alt][photo-1]][open-1]`) to make the image clickable; this is also standard
CommonMark.

### 5.5 Transclusion (section embeds)

A `!`-prefixed wikilink **embeds** the target rather than linking to it:

```
![[<Folder>/<file>#<heading>]]
```

This transcludes the section under `<heading>` from `<Folder>/<file>.md` — used
to surface a **log** entry (§4.3) inside another file (notably the journal,
§5.6). Example, embedding one race from a season log:

```
![[F1/2026-season#2026-06-29 — Austin Grand Prix]]
```

- The anchor is the **heading text**, so headings must be unique within the
  file; date-led headings (`## YYYY-MM-DD — Title`) are naturally unique and are
  REQUIRED for log sections. If a logged heading changes, the writing app MUST
  rewrite the corresponding journal embed so it doesn't dangle (rewrite-on-
  rename). (A future version MAY anchor on a stable block id instead.)
- Transclusion is the **Obsidian** embed convention, not CommonMark. It renders
  in Obsidian and OMF apps; a bare CommonMark engine shows it literally. (This
  is the one place OMF leans on an Obsidian extension rather than pure
  CommonMark — the same family as `[[wikilinks]]`.)
- An embed is also a reference, so it is a backlink: "open the Austin entry → see
  it was embedded in the 2026-06-29 journal."

### 5.6 Surfacing dated entries in the journal (the timeline)

An app MAY make an entry logged in another collection on date *D* appear in
*D*'s journal, turning the journal into a timeline of the day. There are two
mechanisms, chosen by the source file's kind (§4.3):

- **Log entry → embed.** Append a dated `##` section to the log file and write a
  section embed (§5.5) into *D*'s journal. This is **live** (renders the current
  section) and **portable** (Obsidian transcludes it).
- **Metric reading → snapshot line.** A table row can't be section-embedded, so
  append the row to the metric table *and* write a plain-text **snapshot** line
  into *D*'s journal, e.g. `Weight — 167 lb`. This is a **point-in-time** record,
  portable as ordinary Markdown. An app MAY additionally render the live value
  from the source table.

Both are ordinary backlinks (§5.2), so the relationship is navigable in both
directions. See Appendix D for worked examples.

## 6. Identity (the "self")

- Exactly **one** `People/<slug>.md` carries `type: self` — the vault owner.
- `orma_settings.json` → `user.person_slug` is the **authoritative pointer** to
  that slug; `user.person_name` is the display name.
- Recovery: if the pointer is missing, an app MAY scan `People/` for the single
  `type: self` file and repair the pointer.
- The self file MUST NOT accumulate auto-generated reverse links (§5.2).

## 7. Settings file

`orma_settings.json` at the vault root, plaintext JSON:

```json
{
  "omf_version": "0.1",
  "user":  { "person_slug": "jordan-doe", "person_name": "Jordan" },
  "apps":  { "<app_id>": { "enabled": true } },
  "nav_order": ["<app_id>", "..."]
}
```

- `omf_version` (string, required) — the OMF version the vault conforms to (§8).
- `user` — identity, **core to OMF**.
- `apps`, `nav_order` — UI/app state; OMF-aware but app-specific. Apps MUST
  preserve keys they don't understand.

## 8. Versioning

A vault declares its format version via `omf_version` in `orma_settings.json`.
A writer MUST set it to the version it conforms to; a reader MAY use it to
detect compatibility. Absence is treated as the earliest version (`0.1`).

## 9. Resolved decisions (0.1)

- **Strict YAML** — frontmatter MUST be valid YAML 1.x.
- **Slugs are lowercase** — writers MUST emit lowercase slugs (§2).
- **Attachments are standard CommonMark** reference-style image links (§5.4) —
  no OMF-specific embed grammar.
- **Concurrency is out of scope** (§0.1) — OMF is a migration format; no
  merge/conflict semantics. Reciprocity is a within-app convention.
- **`omf_version`** is a required settings field (§7–8).
- **File kinds** (§4.3) — entity / metric / log, with an optional `kind:` field;
  log files MUST declare `kind: log`.
- **Embed anchors** (§5.5) — date-led log headings; apps rewrite journal embeds
  on heading change.

## 10. Open questions (still to settle before 1.0)

1. **`type` redundancy.** `type` echoes the folder for the default case. Keep
   always-present (current; interop-friendly) or present-only-when-deviating?
2. **Mention resolution.** Which collection(s) `@slug` resolves against, and
   case rules.
3. **Settings scope.** Are `apps`/`nav_order` core OMF or a namespaced
   app-extension block?
4. **Metadata privacy.** Filenames/paths (`People/<name>`, dated journals) leak
   structure. How would a future encrypted profile handle names?

## 11. Conformance (planned artifacts)

A 1.0 ships with: this spec, an **example vault**, a **validator**, and a
**reference parser** library extracted from the app. The spec text is released
under an open license (e.g. CC-BY-4.0); implementing OMF requires no permission.

---

# Appendix A — Apps & collections

OMF is organized into **collections**. A collection is a top-level folder whose
files are entities of one kind (e.g. `People/`), or — for tabular data — files
of one kind (e.g. `Health/`). An **app** is a software module that owns a
collection: it defines the folder name, the `type` value, and the field set, and
provides the UI. Collections are the **extension point** — new apps add new
folders without changing the format.

- The built-in collections are listed in Appendix B.
- `orma_settings.json` → `apps` records per-app *enabled* state by `app_id`;
  `nav_order` records their display order. These are app/UI hints; a reader that
  doesn't know an `app_id` MUST preserve it (§7).
- An app encountering a **folder it doesn't recognize** MUST leave it untouched.
  This is what lets two OMF apps with different feature sets share a vault: each
  reads the collections it understands and preserves the rest.

A collection is *self-describing enough to migrate* when its files carry `name` +
`type` (entities) or a documented tabular shape (like Health). An importing app
can always fall back to showing an entity's `name`, `type`, raw frontmatter, and
Markdown body even if it doesn't model that collection.

---

# Appendix B — Built-in collection reference

Dates are ISO 8601 `YYYY-MM-DD`. "block" = a link block (§5.2). All fields other
than `name`/`type` are OPTIONAL. Unknown fields MUST be preserved.

## Journals (`Journals/`)

- **File:** `Journals/YYYY/MM/YYYY-MM-DD.md` (flat `YYYY-MM-DD.md` accepted on read).
- **No frontmatter.** The date is the filename.
- Optional leading `# Heading` = the entry title; the rest is the body (Markdown).
- Body may contain `[[Folder/slug|…]]` wikilinks, `@slug` mentions (§5.3), and
  CommonMark image embeds for attachments (§5.4).

## People (`People/`) — `type: person` (or `self`, §6)

| field | kind | meaning |
|---|---|---|
| `name` | string | display name |
| `type` | string | `person`, or `self` for the vault owner |
| `birthday` | ISO date | optional |
| `relations` | block → People | family/social links, label = relationship |
| `places` | block → Places | associated places (e.g. `home`) |
| body | Markdown | free-text notes |

## Places (`Places/`) — `type: place`

| field | kind | meaning |
|---|---|---|
| `name` | string | place name |
| `category` | string | kind of place (home, office, restaurant, …) |
| `address` | string | postal address |
| `coordinates` | string | `lat,long` |
| `people` | block → People | people associated with the place |
| body | Markdown | notes |

## Movies (`Movies/`) — `type: movie` (or `series`)

| field | kind | meaning |
|---|---|---|
| `name` | string | title |
| `type` | string | `movie` or `series` |
| `director` / `creator` | string | director (movie) / creator (series) |
| `year` | string | release year |
| `genre` | string | genre |
| `actors` | string | cast (free text) |
| `status` | string | watch status (e.g. watched, watchlist) |
| `watched_date` | ISO date | when watched |
| `rating` | string | user rating |
| `people` | block → People | people linked to this title |
| body | Markdown | notes |

## Dreams (`Dreams/`) — `type: dream`

| field | kind | meaning |
|---|---|---|
| `name` | string | dream title |
| `date` | ISO date | when dreamt |
| `dream_type` | string | e.g. lucid, nightmare |
| `mood` | string | mood/tone |
| `people` | block → People | people in the dream |
| `places` | block → Places | places in the dream |
| body | Markdown | the dream narrative |

## Projects (`Projects/`) — `type: project`

| field | kind | meaning |
|---|---|---|
| `name` | string | project name |
| `status` | string | e.g. active, done, paused |
| `start` | ISO date | start date |
| `target` | ISO date | target/deadline |
| `places` | block → Places | associated places |
| `people` | block → People | collaborators |
| body | Markdown | description; an optional `## Updates` section holds dated progress bullets, and journal entries that mention the project are surfaced as additional log items |

## Health (`Health/`) — **metric** kind (tabular)

One file **per metric**: small frontmatter + a Markdown table body.

```markdown
---
metric: weight
unit: kg
---

| date | value | unit | notes |
|------|-------|------|-------|
| 2026-06-19 | 167 | lb |  |
```

- **File:** `Health/<metric-slug>.md`.
- Frontmatter: `metric` (string), `unit` (default unit, string).
- Body: a Markdown table — header row, then one row per reading
  (`date`, `value`, `unit`, `notes`). Rows whose first cell isn't an ISO date
  are ignored.
- **Journal surfacing:** a reading is mirrored into its date's journal as a
  snapshot line (§5.6, Appendix D). The table stays the source of truth for
  charts; the journal line is a point-in-time record.

## Logs (e.g. `F1/`) — **log** kind (dated sections)

The general timeline shape: a collection of log files, each a sequence of dated
`##` sections. F1 is one instance — one file per season:

```markdown
---
name: 2026 Season
type: f1
kind: log
---

## 2026-03-16 — Bahrain Grand Prix
Verstappen pole to flag. Norris P2.

## 2026-06-29 — Austin Grand Prix
Wet start, three safety cars. Leclerc won from P4.
```

- **File:** `<Collection>/<slug>.md` (e.g. `F1/2026-season.md`).
- Frontmatter: `name`, `type` (the collection's type), `kind: log` (required).
- Body: zero or more sections, each headed `## YYYY-MM-DD — Title` (date-led for
  stable, unique anchors). The section body is free Markdown.
- **Journal surfacing:** an entry is embedded into its date's journal via a
  section transclusion (§5.5, Appendix D), so it renders inline there and in
  Obsidian.

---

# Appendix C — Implementer guidance

**A minimal OMF reader:**

1. Read `orma_settings.json` for `omf_version` and the `user` identity.
2. Enumerate top-level folders. For each known collection, list `*.md` files.
3. Parse each entity: split the leading `---…---` frontmatter (valid YAML) from
   the Markdown body. The slug is the filename without `.md`.
4. Resolve `[[Folder/slug|Display]]` wikilinks against `Folder/slug.md`; treat
   `@slug` as a People mention. Render attachments via the CommonMark image
   links pointing into `Photos/`.
5. For an unknown collection, fall back to `name` + `type` + raw frontmatter +
   body, and preserve the files unchanged.

**Hard rules for any writer:**

- **Preserve everything you don't model** — unknown folders, files, frontmatter
  keys, and bodies. Mutate only what you change. (Frontmatter comments and key
  order are not guaranteed across a rewrite; data is.)
- **Emit valid YAML** and **lowercase slugs**.
- **Stamp `omf_version`** when you write settings.
- Use ISO `YYYY-MM-DD` dates.

**Adding a new collection (new app):**

1. Pick a folder name (the collection) and a singular `type` string.
2. Store one entity per file with at least `name` + `type`; add scalar fields
   and link blocks as needed.
3. Optionally register an `app_id` in `orma_settings.json` → `apps`.
4. That's it — existing OMF apps will preserve your folder and files, and a
   generic reader can already display them.

---

# Appendix D — Journal surfacing, worked examples

Both examples show what's on disk after logging an entry on **2026-06-29**, and
what the journal looks like for that day.

## D.1 Log entry (F1) — section embed

You log the Austin Grand Prix. Two files change:

**`F1/2026-season.md`** — the section is appended (source of truth):

```markdown
---
name: 2026 Season
type: f1
kind: log
---

## 2026-06-29 — Austin Grand Prix
Wet start, three safety cars. Leclerc won from P4.
```

**`Journals/2026/06/2026-06-29.md`** — an embed is inserted:

```markdown
Caught the race after lunch.

![[F1/2026-season#2026-06-29 — Austin Grand Prix]]
```

Rendering 2026-06-29: the journal shows your prose, then the embedded F1 section
(Orma styles it as a race widget; Obsidian transcludes the same section). Editing
the race text later updates everywhere it's embedded — one source of truth.

## D.2 Metric reading (weight) — snapshot line

You log weight 167 lb. Two files change:

**`Health/weight.md`** — a row is appended (source of truth, chartable):

```markdown
---
metric: weight
unit: kg
---

| date | value | unit | notes |
|------|-------|------|-------|
| 2026-06-29 | 167 | lb |  |
```

**`Journals/2026/06/2026-06-29.md`** — a snapshot line is inserted:

```markdown
Caught the race after lunch.

Weight — 167 lb
```

Rendering 2026-06-29: the journal shows the snapshot line (Obsidian shows it as
plain text; Orma MAY render it as a chip and/or refresh it from the live table).
Because a table row can't be section-embedded, the value is denormalized as a
point-in-time snapshot — which is the correct semantics for a journal: it records
what you logged that day.

## Why the two differ

| | Log (F1) | Metric (weight) |
|---|---|---|
| source body | dated `##` section | dated table row |
| journal carries | `![[…#section]]` embed | snapshot text line |
| live in journal? | yes (transcluded) | no (point-in-time) |
| inline in Obsidian? | yes | yes (as text) |
| best for | rich events | numeric series + charts |
