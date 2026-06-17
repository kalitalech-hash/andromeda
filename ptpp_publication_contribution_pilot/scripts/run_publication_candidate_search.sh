#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

python scripts/search_ptpp_publication_candidates.py \
  --members-csv data_raw/ptpp_members_snapshot_reconstructed_2026-06-17.csv \
  --output-dir . \
  --email "${ANDROMEDA_CONTACT_EMAIL:-}" \
  --sources crossref openalex pubmed \
  --max-results-per-source "${MAX_RESULTS_PER_SOURCE:-20}" \
  --sleep "${ANDROMEDA_SLEEP:-0.35}"
