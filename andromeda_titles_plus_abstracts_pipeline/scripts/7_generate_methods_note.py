from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import argparse
import json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate a draft methods note from final summary JSON.")
    ap.add_argument("--summary", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    summary = json.loads(Path(args.summary).read_text(encoding="utf-8"))
    text = f"""# Draft methods note: title + abstract discourse mapping

The corpus was analysed with `andromeda_titles_plus_abstracts_pipeline`, a reusable Andromeda Nowicka v0.4 workflow for metadata/abstract-layer discourse mapping.

The analytical unit was the article record. Candidate terms were extracted from normalized article titles and abstracts, then mapped to auditable semantic concepts through a human-in-the-loop semantic map. Final trend analyses used article-level concept presence rather than repeated within-article mentions.

Summary of analytical layer:

- Articles: {summary.get('n_articles')}
- Article–concept pairs: {summary.get('n_article_concept_pairs')}
- Unique semantic concepts: {summary.get('n_unique_concepts')}
- Periods: {summary.get('n_periods')}
- Co-occurrence network nodes: {summary.get('network_nodes')}
- Co-occurrence network edges: {summary.get('network_edges')}
- Network communities: {summary.get('network_communities')}

Interpretive limitation: this analysis maps lexical and semantic signals available in titles and abstracts. It should not be treated as full-text analysis or as a reconstruction of complete article arguments.

Ethical acquisition note: the workflow assumes metadata-first acquisition, avoids PDF mirroring, and should store restricted source text outside public repositories unless redistribution is explicitly permitted.
"""
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
