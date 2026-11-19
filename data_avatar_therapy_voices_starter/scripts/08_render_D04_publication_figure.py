#!/usr/bin/env python3
"""Render D04 publication AVATAR ego figure from its audited CSV edge table.
Only standard library; outputs SVG; no external graphics dependencies.
From data_avatar_therapy_voices_starter:
python scripts/08_render_D04_publication_figure.py \
  --edges outputs/analyses/avatar_discourse_D04_anchor_maps_v01/strict_ego_edges.csv \
  --output outputs/analyses/avatar_discourse_D04_publication_reproduced_v01/FIGURE_1_AVATAR.svg
"""
import argparse
import csv
from pathlib import Path
from xml.sax.saxutils import escape

LABELS = {
    "VOICE_AUDITORY_HALLUCINATIONS": "Omamy słuchowe",
    "VOICE_DISTRESS": "Dystres związany z głosami",
    "VOICE_HEARING": "Słyszenie głosów",
    "CONTROLLED_TRIAL": "Badania kontrolowane",
    "VOICE_POWER": "Władza i kontrola głosów",
    "PEER_SUPPORT": "Wsparcie rówieśnicze",
    "LIVED_EXPERIENCE": "Doświadczenie przeżywane",
}

def build_svg(edges):
    # Layout designed for the seven approved, strictly matched D03 AVATAR edges.
    ordering = list(LABELS)
    absent = set(ordering) - set(edges)
    extra = set(edges) - set(ordering)
    if absent or extra:
        raise ValueError(f"Unexpected AVATAR ego network: missing={sorted(absent)}, new={sorted(extra)}")
    ys = [115, 180, 245, 310, 375, 440, 505]
    strokes = []
    nodes = []
    for concept, y in zip(ordering, ys):
        count = edges[concept]
        strokes.append(f'<path d="M 280 310 Q 330 {y} 400 {y}" stroke="#707999" stroke-width="{1.5 + count}" fill="none" opacity="0.74"/>')
        nodes.append(
            f'<rect x="400" y="{y-23}" width="480" height="46" rx="12" fill="#f6f8fb" stroke="#c4cbda"/>'
            f'<text x="421" y="{y+6}" font-family="Arial, sans-serif" font-size="18" fill="#1d2738">{escape(LABELS[concept])}</text>'
            f'<text x="852" y="{y+6}" font-family="Arial, sans-serif" font-size="18" text-anchor="end" font-weight="bold" fill="#34405a">n={count}</text>'
        )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="650" viewBox="0 0 1000 650">\n'
        '<rect width="1000" height="650" fill="#ffffff"/>\n'
        '<text x="52" y="52" font-family="Arial,sans-serif" font-size="25" fill="#192438" font-weight="700">Terapia AVATAR — współobecność pojęć</text>\n'
        '<text x="52" y="76" font-family="Arial,sans-serif" font-size="14" fill="#586478">7 publikacji · tytuły i dostępne abstrakty · wszystkie połączenia, łącznie z n=1</text>\n'
        + "\n".join(strokes) + "\n" + "\n".join(nodes) + "\n"
        '<rect x="74" y="274" width="206" height="73" rx="17" fill="#2b435f"/>'
        '<text x="177" y="306" text-anchor="middle" font-family="Arial,sans-serif" fill="#fff" font-size="22" font-weight="bold">AVATAR</text>'
        '<text x="177" y="327" text-anchor="middle" font-family="Arial,sans-serif" fill="#e6eef7" font-size="15">therapy · n=7</text>'
        '<text x="52" y="602" font-family="Arial,sans-serif" font-size="14" fill="#5a6677">Linie: współobecność terminów w tej samej publikacji; grubość zależna od liczby publikacji.</text>'
        '<text x="52" y="626" font-family="Arial,sans-serif" font-size="13" fill="#6b7483">Źródło: Andromeda Nowicka v0.5 / D03–D04. Nie jest to mapa zależności przyczynowych.</text>'
        '</svg>\n'
    )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--edges", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    with open(args.edges, newline="", encoding="utf-8-sig") as f:
        records = list(csv.DictReader(f))
    edges = {}
    for r in records:
        if r["anchor"] != "AVATAR_THERAPY":
            continue
        key = r["co_present_concept"]
        if key in edges:
            raise ValueError(f"Duplicated edge: {key}")
        edges[key] = int(r["n_articles"])
    if not edges:
        raise ValueError("No AVATAR_THERAPY edges found")
    output = Path(args.output)
    if output.exists():
        raise FileExistsError(f"Will not overwrite existing figure: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_svg(edges), encoding="utf-8")
    print(f"Saved {output} with {len(edges)} edges, including n=1")

if __name__ == "__main__":
    main()
