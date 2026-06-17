# PTPP members snapshot script

`build_ptpp_members_snapshot.py` creates two metadata-first source layers from public PTPP membership-related pages:

- `data_raw/ptpp_memberships_snapshot.csv` — one row per occurrence on a public list;
- `data_raw/ptpp_members_snapshot.csv` — deduplicated person table with aggregated membership categories.

Default source pages:

- certified therapists;
- extraordinary members;
- candidates.

Optional source page:

- supervisors (`--include-supervisors`) as an additional role/specialization layer, not a replacement for membership category.

The script does not download PDFs, does not log in, and does not bypass bot protection. If a PTPP page returns a verification page, use a manually saved HTML file and run with `--offline-html-dir`.

Example:

```bash
python scripts/build_ptpp_members_snapshot.py \
  --contact-email your.email@example.org \
  --output-dir . \
  --save-source-html
```

Offline example:

```bash
python scripts/build_ptpp_members_snapshot.py \
  --no-fetch \
  --offline-html-dir data_raw/ptpp_html_pages \
  --output-dir .
```

Expected offline filenames:

```text
certified_therapists.html
extraordinary_members.html
candidates.html
supervisors.html
```

Interpretive rule: this produces a public snapshot of names visible on selected PTPP pages at acquisition time. It is not yet a publication database and not an official institutional-impact measure.
