#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
5c_generate_manuscript_skeleton.py

Andromeda Nowicka v0.5-pre
Generate manuscript skeleton from publication review artifacts.

Purpose
-------
5a created publication-oriented tables and figures.
5b created captions, claims matrix, figure recommendations, and a core results narrative.
5c generates a manuscript skeleton in Markdown.

This script does NOT write the final article. It prepares an auditable drafting
structure with:

- proposed title variants,
- abstract placeholders,
- section-by-section manuscript outline,
- claims linked to tables/figures,
- recommended figure/table placement,
- methods skeleton,
- results skeleton,
- discussion skeleton,
- limitations,
- contribution/acknowledgment language.

Inputs
------
From 5b:
    ../data/title_abstract/publication_outputs_review/publication_results_claims_matrix.csv
    ../data/title_abstract/publication_outputs_review/publication_figure_caption_sheet.csv
    ../data/title_abstract/publication_outputs_review/publication_table_caption_sheet.csv
    ../data/title_abstract/publication_outputs_review/publication_figure_selection_recommendations.csv
    ../data/title_abstract/publication_outputs_review/publication_core_results_narrative.md

From 5a:
    ../data/title_abstract/publication_outputs/publication_outputs_summary.json

Outputs
-------
../reports/manuscript_drafts/
    psychoanalytic_core_manuscript_skeleton_v0_1.md

../data/title_abstract/publication_outputs_review/
    publication_manuscript_skeleton_summary.json

Run
---
Put this file in:

    data_psychoanalytic_core/scripts/

Run:

    cd data_psychoanalytic_core/scripts
    python 5c_generate_manuscript_skeleton.py
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Dict

import pandas as pd


SCRIPT_VERSION = "v0.1.0"


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def get_paths() -> Dict[str, Path]:
    scripts_dir = Path(__file__).resolve().parent
    project_root = scripts_dir.parent
    repo_root = project_root.parent
    title_root = project_root / "data" / "title_abstract"
    return {
        "scripts_dir": scripts_dir,
        "project_root": project_root,
        "repo_root": repo_root,
        "title_root": title_root,
        "publication_outputs": title_root / "publication_outputs",
        "publication_review": title_root / "publication_outputs_review",
        "reports": project_root / "reports",
        "manuscript_drafts": project_root / "reports" / "manuscript_drafts",
    }


def read_csv_safe(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    except UnicodeDecodeError:
        return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8")


def read_json_safe(path: Path) -> Dict:
    if not path.exists() or path.stat().st_size == 0:
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def read_text_safe(path: Path) -> str:
    if not path.exists() or path.stat().st_size == 0:
        return ""
    return path.read_text(encoding="utf-8")


def write_text(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(payload: Dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def md_table_from_df(df: pd.DataFrame, columns: list[str], max_rows: int | None = None) -> str:
    if df.empty:
        return "_No data available._"
    use = df[[c for c in columns if c in df.columns]].copy()
    if max_rows is not None:
        use = use.head(max_rows)
    if use.empty:
        return "_No selected columns available._"
    return use.to_markdown(index=False)


def bullet_claims(claims: pd.DataFrame) -> str:
    if claims.empty:
        return "- [ ] Claims matrix not available."
    lines = []
    for _, r in claims.iterrows():
        lines.append(
            f"- **{r.get('claim_id', '')}:** {r.get('claim_text', '')}  \n"
            f"  _Primary evidence:_ {r.get('primary_evidence', '')}.  \n"
            f"  _Caveat:_ {r.get('caveat', '')}"
        )
    return "\n".join(lines)


def figure_list(figures: pd.DataFrame) -> str:
    if figures.empty:
        return "- [ ] Figure caption sheet not available."
    lines = []
    for _, r in figures.iterrows():
        lines.append(
            f"- **{r.get('figure_id', '')}. {r.get('short_title', '')}**  \n"
            f"  File: `{r.get('file_name', '')}`  \n"
            f"  Role: `{r.get('recommended_role', '')}`  \n"
            f"  Supports: {r.get('primary_claim_ids', '')}."
        )
    return "\n".join(lines)


def table_list(tables: pd.DataFrame) -> str:
    if tables.empty:
        return "- [ ] Table caption sheet not available."
    lines = []
    for _, r in tables.iterrows():
        lines.append(
            f"- **{r.get('table_id', '')}. {r.get('short_title', '')}**  \n"
            f"  File: `{r.get('file_name', '')}`  \n"
            f"  Role: `{r.get('recommended_role', '')}`  \n"
            f"  Supports: {r.get('primary_claim_ids', '')}."
        )
    return "\n".join(lines)


def generate_skeleton(
    claims: pd.DataFrame,
    figures: pd.DataFrame,
    tables: pd.DataFrame,
    recommendations: pd.DataFrame,
    narrative: str,
    publication_summary: Dict,
) -> str:
    trend = publication_summary.get("trend_summary_from_period_indices", {})

    rel_change = trend.get("relational_shift_index_change", "[insert]")
    drive_change = trend.get("drive_conflict_defense_change", "[insert]")
    narrative_change = trend.get("narrative_reframing_index_change", "[insert]")
    context_change = trend.get("contemporary_contextualization_index_change", "[insert]")

    main_figures = recommendations[
        recommendations.get("selection_recommendation", pd.Series(dtype=str)).astype(str).eq("include_main_text")
    ] if not recommendations.empty and "selection_recommendation" in recommendations.columns else pd.DataFrame()

    skeleton = f"""# Manuscript skeleton v0.1

**Project:** Psychoanalytic core / Andromeda Nowicka  
**Generated:** {utc_now_iso()}  
**Script:** `5c_generate_manuscript_skeleton.py`  
**Status:** drafting scaffold, not final manuscript

---

## 0. Working title variants

1. **Changing Narratives of Psychoanalytic Clinical Reality: A Century of Title-and-Abstract Discourse Across Core Journals**
2. **From Drive-Conflict Narratives to Relational-Contextual Vocabularies: A Corpus Study of Psychoanalytic Journals**
3. **Regional Dialects of Psychoanalysis: Semantic Change, Pluralism, and Journal Cultures in a Century-Scale Corpus**
4. **Useful Fictions in Motion: A Bibliometric Discourse History of Psychoanalytic Concepts**
5. **The Relational-Contextual Turn in Psychoanalytic Journal Discourse: A Title-and-Abstract Corpus Analysis**

Preferred current working title:

> **Changing Narratives of Psychoanalytic Clinical Reality: A Century of Title-and-Abstract Discourse Across Core Journals**

---

## 1. Provisional abstract structure

### Background

Psychoanalysis has often been described as a pluralistic field of competing theories, regional dialects, useful fictions, and partially overlapping clinical languages. These claims are usually argued theoretically or clinically, but rarely tested through large-scale historical corpus evidence.

### Aim

This study examines whether the public discourse of core psychoanalytic journals shows measurable semantic change over the last century, especially in relation to drive/conflict/defense language, relational/intersubjective language, contextual and social-ethical vocabularies, and narrative reframing.

### Methods

We analyze an ART-only title-and-abstract corpus from five psychoanalytic journals. After metadata QA, article-type filtering, title/abstract cleaning, candidate term extraction, semantic-family mapping, marker-strength correction, and journal-balanced robustness checks, we compute semantic-change indices globally, by journal, by period, and by journal × period.

### Results

The corpus shows a substantial increase in `relational_shift_index` ({rel_change}), a decline in `drive_conflict_defense` ({drive_change}), and a strong increase in `narrative_reframing_index` ({narrative_change}) and `contemporary_contextualization_index` ({context_change}). The main direction of change is visible globally, within journals, and under equal-journal-weight and balanced-panel checks.

### Conclusions

The results support a cautious interpretation of psychoanalytic journal discourse as undergoing a century-scale semantic transformation: not the disappearance of classical language, but a loss of its monopoly and the rise of relational, contextual, trauma-regulatory, social-ethical, and narrative-redescriptive vocabularies.

---

## 2. Core claims matrix

{bullet_claims(claims)}

---

## 3. Recommended main figures and tables

### 3.1 Main-text figure candidates

{figure_list(main_figures if not main_figures.empty else figures)}

### 3.2 Table candidates

{table_list(tables)}

---

## 4. Introduction skeleton

### 4.1 Opening problem

- Psychoanalysis has never been a single unified metapsychological system.
- Its history can be read as a series of theoretical languages, clinical dialects, and redescriptions of suffering, subjectivity, conflict, relation, and meaning.
- The literature on pluralism, common ground, incommensurability, and useful fictions has conceptualized this problem, but mostly without large-scale diachronic corpus data.

### 4.2 Theoretical frame

Potential anchors:

- **Beebe and Lachmann:** relational turn, dyadic systems, self- and interactive regulation.
- **Orange:** ethical, hermeneutic, contextual, intersubjective expansion.
- **Schafer:** psychoanalysis as narrative redescription; changing ways of telling clinical reality.
- **Bernardi:** common ground, triangulation, multiple evidence sources.
- **Fulgencio:** paradigms, incommensurability, redescriptions of phenomena.
- **Karbelnig / Lament:** theoretical metaphors, useful untruths, regional dialects.

### 4.3 Gap

Existing theoretical discussions claim that psychoanalysis has become more plural, relational, contextual, and epistemologically self-aware. What is missing is a corpus-level, historical, journal-comparative test of whether these shifts are visible in published psychoanalytic discourse.

### 4.4 Research questions

1. Does psychoanalytic journal discourse show a measurable decline in drive/conflict/defense dominance?
2. Does relational/intersubjective/field language increase over time?
3. Do social-ethical, trauma-regulatory, contextual, and narrative-symbolic vocabularies increase?
4. Are the observed changes global, or driven mainly by journal composition?
5. Do journals function as distinct psychoanalytic discourse dialects?

---

## 5. Corpus and methods skeleton

### 5.1 Corpus

- Five journals:
  - IJPA
  - JAPA
  - Psychoanalytic Dialogues
  - Psychoanalytic Psychology
  - Psychoanalytic Psychotherapy
- ART-only records.
- Title and abstract metadata.
- No PDF mirroring.
- Metadata-first acquisition policy.

### 5.2 Article-type filtering

- Only article type `ART` was treated as original article material.
- Non-ART material was retained for QA/exclusion documentation but not used in the semantic core.

### 5.3 Text layer

- `title_clean`
- `abstract_clean`
- `text_for_analysis`

### 5.4 Candidate term extraction

- Title+abstract candidate terms.
- Global and journal-specific extraction.
- Stopword and artifact cleaning.
- Discriminative candidate terms.

### 5.5 Semantic-family mapping

- Initial broad semantic map.
- QA of high-risk broad markers.
- Marker-strength refinement:
  - strong
  - medium
  - weak
  - name_marker
  - unmapped

### 5.6 Refined semantic application

- Weak-only and name-only hits did not count as full family hits.
- Two or more weak markers could count as provisional.
- Refined model used for interpretation.

### 5.7 Semantic-change indices

Mention formulas or refer to table:

- `relational_shift_index`
- `classical_drive_conflict_index`
- `classical_metapsychology_index`
- `contemporary_contextualization_index`
- `narrative_reframing_index`

### 5.8 Robustness checks

- Initial vs refined comparison.
- Journal-vs-global diagnostics.
- Equal-journal-weight trajectories.
- Long-journal panel.
- Common-period panel.
- Post-1990 panel.
- Direction consistency across journals.

---

## 6. Results skeleton

### 6.1 Semantic coverage and marker-strength correction

Use:

- Table 1
- Table 2
- Table 6
- Figure 6

Claim:

> The refined semantic model preserved broad corpus coverage while reducing overconfident family assignment caused by broad weak markers and name-only markers.

### 6.2 Global semantic transformation by period

Use:

- Figure 1
- Figure 2
- Figure 3
- Table 3
- Table 8

Key numbers:

```text
relational_shift_index_change: {rel_change}
drive_conflict_defense_change: {drive_change}
narrative_reframing_index_change: {narrative_change}
contemporary_contextualization_index_change: {context_change}
```

Claim:

> The corpus shows a shift from drive/conflict/defense-centered discourse toward relational, contextual, trauma-regulatory, social-ethical, and narrative-reframing vocabularies.

### 6.3 Journal trajectories and dialects

Use:

- Figure 4
- Table 4
- Table 7

Claim:

> Journals differ in semantic profile and trajectory. Psychoanalytic Dialogues is the strongest relational-contextual pole, but long journals such as IJPA and JAPA also show the broader historical direction of change.

### 6.4 Robustness against journal composition

Use:

- Figure 5
- Table 5

Claim:

> Equal-journal-weight and balanced-panel diagnostics preserve the major directions of change, indicating that the result is not reducible to journal composition.

### 6.5 Summary of empirical pattern

Working formulation:

> Classical language remains present, but loses its earlier organizing monopoly. The later corpus is more relational, contextual, trauma-regulatory, social-ethical, and narrative-redescriptive.

---

## 7. Discussion skeleton

### 7.1 From replacement to reconfiguration

Avoid saying:

```text
drive theory disappears
```

Prefer:

```text
drive/conflict/defense language remains part of psychoanalytic discourse,
but no longer dominates the published vocabulary in the same way.
```

### 7.2 Relational-contextual transformation

Connect to Beebe and Lachmann, Orange, and relational traditions.

### 7.3 Narrative redescription

Connect to Schafer and Fulgencio:

- clinical phenomena may persist,
- theoretical languages redescribe them,
- journal cultures provide dialects of redescription.

### 7.4 Pluralism and common ground

Connect to Bernardi, Karbelnig, Lament:

- pluralism is visible not only as theoretical claim,
- journal profiles show structured dialects,
- common ground may be clinical while discourse varies.

### 7.5 Journal cultures

Interpret journals as discourse ecologies:

- IJPA: long classical archive undergoing gradual transformation.
- JAPA: American classical-to-plural shift.
- Psychoanalytic Dialogues: relational-contextual intensification.
- Psychoanalytic Psychology: relational/research/psychology-facing translation.
- Psychoanalytic Psychotherapy: clinical-practical and process/research orientation.

---

## 8. Limitations skeleton

- Title/abstract layer is not full text.
- Semantic mapping is rule-based and provisional.
- Indices are exploratory composites.
- Article abstracts and keywords vary by journal and period.
- Journal coverage is historically uneven.
- Balanced checks reduce but do not eliminate composition effects.
- Clinical continuity is inferred indirectly from discourse, not directly observed.
- The corpus maps public article self-description, not full intellectual content.

---

## 9. Conclusion skeleton

Working conclusion:

> This study provides corpus-level evidence that psychoanalytic journal discourse has undergone a broad semantic transformation over the last century. The change is visible as a decline in drive/conflict/defense dominance and an increase in relational, contextual, trauma-regulatory, social-ethical, and narrative-reframing vocabularies. The transformation is not uniform: journals function as distinct discourse dialects. However, balanced diagnostics indicate that the main direction of change is visible across journal trajectories rather than being reducible to journal composition.

---

## 10. Figure and table placement plan

### Main text, likely essential

- Figure 1: relational vs drive by period
- Figure 5: equal-weight vs article-weighted relational shift
- Table 3: semantic indices by period
- Table 4: journal trajectories
- Table 5: balanced direction consistency

### Main text or supplement

- Figure 2: narrative reframing by period
- Figure 3: contextualization vs classical metapsychology
- Figure 4: journal relational trajectories

### Methods or supplement

- Figure 6: initial vs refined family drop
- Table 1: semantic coverage
- Table 2: refined family counts
- Table 6: initial vs refined impact
- Table 7: journal distinctiveness
- Table 8: narrative table

---

## 11. Citation placeholders

Insert citations for:

- Beebe & Lachmann — relational turn / dyadic systems
- Orange — ethics, hermeneutics, contextual psychoanalysis
- Schafer — narrative psychoanalysis / action language
- Bernardi — common ground, triangulation, discipline status
- Fulgencio — paradigms and incommensurability
- Karbelnig — structured clinical pluralism
- Lament — useful untruths
- Jiménez & Altimir — empirical research paradigm

---

## 12. Acknowledgment language

Recommended acknowledgment:

> Bibliometric data preparation, semantic keyword normalization, and computational discourse-analysis support were provided by Andromeda Nowicka (v0.5-pre), a human-in-the-loop computational bibliometrics system developed under the supervision of Lech Kalita.

Alternative project-style acknowledgment:

> The computational workflow was supported by Andromeda Nowicka, a human-in-the-loop research agent for reproducible bibliometric and discourse analysis. Final scholarly interpretation remained under human supervision.

---

## 13. Andromeda / Lech contribution note for internal repo

### Lech Kalita

- Defined the psychoanalytic interpretive frame.
- Directed the shift from a narrow relational-turn focus to a broader narrative-redescription model.
- Supplied theoretical think-tank materials.
- Evaluated computational outputs against psychoanalytic meaning.
- Maintained human scholarly responsibility for interpretation.

### Andromeda Nowicka

- Generated reproducible scripts for semantic mapping, refinement, robustness, and publication outputs.
- Produced interpretive summaries and reports.
- Organized claims, figures, tables, and manuscript structure.
- Functioned as HITL computational research support, not autonomous author.

---

## 14. Immediate next tasks

1. Human review of title variants and central claim.
2. Decide journal target and required word count.
3. Add formal citations to theory section.
4. Inspect Figures 1–6 visually and choose final figure set.
5. Prepare `5d_manuscript_intro_methods_draft.py` or manually draft Introduction + Methods.
6. Consider a supplementary methods appendix for semantic-family and marker-strength rules.

"""

    if narrative:
        skeleton += "\n---\n\n## 15. Imported 5b core results narrative\n\n"
        skeleton += narrative

    return skeleton


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate manuscript skeleton from publication review artifacts.")
    parser.add_argument("--review-root", default="../data/title_abstract/publication_outputs_review")
    parser.add_argument("--publication-root", default="../data/title_abstract/publication_outputs")
    parser.add_argument("--out-dir", default="../reports/manuscript_drafts")
    args = parser.parse_args()

    paths = get_paths()

    def resolve(p: str) -> Path:
        path = Path(p)
        if not path.is_absolute():
            path = (paths["scripts_dir"] / path).resolve()
        return path

    review_root = resolve(args.review_root)
    publication_root = resolve(args.publication_root)
    out_dir = resolve(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    claims_path = review_root / "publication_results_claims_matrix.csv"
    figures_path = review_root / "publication_figure_caption_sheet.csv"
    tables_path = review_root / "publication_table_caption_sheet.csv"
    recommendations_path = review_root / "publication_figure_selection_recommendations.csv"
    narrative_path = review_root / "publication_core_results_narrative.md"
    pub_summary_path = publication_root / "publication_outputs_summary.json"

    required = [claims_path, figures_path, tables_path, recommendations_path, pub_summary_path]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise SystemExit(f"ERROR: missing required inputs: {missing}")

    claims = read_csv_safe(claims_path)
    figures = read_csv_safe(figures_path)
    tables = read_csv_safe(tables_path)
    recommendations = read_csv_safe(recommendations_path)
    narrative = read_text_safe(narrative_path)
    pub_summary = read_json_safe(pub_summary_path)

    skeleton = generate_skeleton(
        claims=claims,
        figures=figures,
        tables=tables,
        recommendations=recommendations,
        narrative=narrative,
        publication_summary=pub_summary,
    )

    manuscript_path = out_dir / "psychoanalytic_core_manuscript_skeleton_v0_1.md"
    write_text(skeleton, manuscript_path)

    summary = {
        "script_version": SCRIPT_VERSION,
        "created_at_utc": utc_now_iso(),
        "purpose": "Generate manuscript skeleton from publication captions, claims matrix, and narrative draft.",
        "inputs": {
            "claims_matrix": str(claims_path),
            "figure_caption_sheet": str(figures_path),
            "table_caption_sheet": str(tables_path),
            "figure_selection_recommendations": str(recommendations_path),
            "core_results_narrative": str(narrative_path),
            "publication_outputs_summary": str(pub_summary_path),
        },
        "outputs": {
            "manuscript_skeleton": str(manuscript_path),
        },
        "counts": {
            "n_claims": int(len(claims)),
            "n_figures": int(len(figures)),
            "n_tables": int(len(tables)),
        },
        "methodological_note": (
            "This is a drafting scaffold. It is not a final manuscript and requires human scholarly revision, "
            "citation insertion, journal-target adaptation, and substantive psychoanalytic interpretation."
        ),
    }

    summary_path = review_root / "publication_manuscript_skeleton_summary.json"
    write_json(summary, summary_path)
    summary["outputs"]["summary_json"] = str(summary_path)

    print(json.dumps({
        "status": "ok",
        "script_version": SCRIPT_VERSION,
        "n_claims": int(len(claims)),
        "n_figures": int(len(figures)),
        "n_tables": int(len(tables)),
        "manuscript_skeleton": str(manuscript_path),
        "summary_json": str(summary_path),
    }, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
