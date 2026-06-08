from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tests" / "_smoke_outputs"
if OUT.exists():
    shutil.rmtree(OUT)

commands = [
    ["scripts/1_ingest_metadata.py", "--input", "tests/fixtures/sample_articles.csv", "--output", "tests/_smoke_outputs/raw/articles_raw.csv"],
    ["scripts/1a_qa_deduplicate.py", "--input", "tests/_smoke_outputs/raw/articles_raw.csv", "--output-dir", "tests/_smoke_outputs/qa"],
    ["scripts/2_normalize_text.py", "--input", "tests/_smoke_outputs/qa/articles_deduplicated.csv", "--output-dir", "tests/_smoke_outputs/normalized"],
    ["scripts/3_extract_candidate_terms.py", "--input", "tests/_smoke_outputs/normalized/articles_text_normalized.csv", "--output-dir", "tests/_smoke_outputs/terms"],
    ["scripts/4_apply_semantic_map.py", "--terms", "tests/_smoke_outputs/terms/candidate_terms_long.csv", "--map", "templates/semantic_map_template.csv", "--output-dir", "tests/_smoke_outputs/semantic"],
    ["scripts/5_periodize.py", "--articles", "tests/_smoke_outputs/normalized/articles_text_normalized.csv", "--terms", "tests/_smoke_outputs/semantic/terms_semantic_final.csv", "--output-dir", "tests/_smoke_outputs/periodized"],
    ["scripts/6_final_analyses.py", "--articles", "tests/_smoke_outputs/periodized/articles_periodized.csv", "--terms", "tests/_smoke_outputs/periodized/terms_periodized.csv", "--output-dir", "tests/_smoke_outputs/analyses"],
    ["scripts/7_generate_methods_note.py", "--summary", "tests/_smoke_outputs/analyses/stage6_summary.json", "--output", "tests/_smoke_outputs/analyses/methods_note_draft.md"],
]

for cmd in commands:
    subprocess.check_call([sys.executable, *cmd], cwd=ROOT)

print("Smoke test completed:", OUT)
