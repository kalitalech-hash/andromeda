# D04 — focused ego maps: AVATAR therapy and VR intervention

**Source:** approved D03 article-concept map, 209 article-labelled A/B/C records in five journals (2009–2026). Edges are publication-level **co-presence**, not intra-sentence semantic, causal or therapeutic relations. No min-edge cutoff.

## Strict approved D03 anchors
- `AVATAR_THERAPY`: n=7 publications; co-presence edges:
  - `VOICE_AUDITORY_HALLUCINATIONS` 4
  - `VOICE_DISTRESS` 3
  - `VOICE_HEARING` 3
  - `CONTROLLED_TRIAL` 2
  - `VOICE_POWER` 1
  - `PEER_SUPPORT` 1
  - `LIVED_EXPERIENCE` 1
- `VR_INTERVENTION`: n=3 publications; one D03 edge `VOICE_AUDITORY_HALLUCINATIONS` 2. Third record is about virtual reality therapy for *negative symptoms* of schizophrenia, not auditory hallucinations. No generalization to all VR work.

**Special caution:** some names represent *mentions* (controlled trial) and cannot classify an article's design. `AVATAR_THERAPY` and `VR_INTERVENTION` have no direct D03 edge under the narrow phrase dictionaries, but their conceptual domains can overlap outside those exact phrases.

## Sensitivity analysis: broad mentions (not the same as therapy)
A broad case-insensitive text-search within titles + available abstracts:
- `AVATAR_MENTION` (regex whole word `avatar` / `avatars`) n=14; co-present D03 concepts: auditory hallucinations 8, voice hearing 5, voice distress 4, controlled trial 2, lived experience 2, peer support 2; other concepts with n=1 are available in CSV.
- `VR_MENTION` (virtual reality, immersive or standalone VR expressions) n=22; co-present D03 concepts: auditory hallucinations 8, voice hearing 4, controlled trial 4, CBT 3, avatar therapy 2, lived experience 2, peer support 2, social relationships 2, plus qualitative method 1 and distress 1.
- Six publications mention both broad AVATAR and broad VR terms. These are **mentions**, not necessarily interventions specifically treating voices; several VR records concern paranoia, delusions, negative symptoms or other applications.

## Methodological claims check
- `QUALITATIVE_METHOD` narrow phrase appears in **35 / 209** articles, `CONTROLLED_TRIAL` in **18 / 209**. This supports: *qualitative-method expressions appear more often than controlled-trial expressions in the selected metadata layer*. It does **not** support: *there are more qualitative than quantitative studies*, because most quantitative designs are not RCTs; phrased trial mentions are not verified study design.
- Broad `distress` (word family) n=77 / 209, `anxiety/anxious/worry` n=30, `fear/afraid/frightened` n=24, `discomfort/uncomfortable` n=3. `distress OR anxiety OR fear` n=100 (47.8%), with overlapping sets. In contrast, explicitly `VOICE_DISTRESS` narrow D03 variants appear in **31** articles. These are mentions and may refer to phenomena beyond voice distress. Thus do not call these an unequivocal majority or a field-wide 'dominance' without a contextual audit.

## Relevance warnings and limitations
The article-type label is from OpenAlex, not an independently validated peer-review or full-research-article indicator. Some records include conference-style titles or reviews despite `article` label, warranting title-level QA. The original harvest is page capped and topic selection is strict/heuristic. Twelve records lack an abstract. All source layers preserved; no full-text or PDF acquisition.

Interpretation is bounded to the indexed metadata of this exact cohort. Sensitivity results must be treated separately from the researcher-approved concept mappings.

## Outputs
`strict_ego_edges.csv`, `broader_mention_edges.csv`, `anchor_strict_records.csv` (titles & IDs only), `focused_map.svg`, `anchor_summary.json`.
