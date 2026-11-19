import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(path):
 spec=importlib.util.spec_from_file_location("stage",ROOT/"scripts"/path); mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def test_doi_normalization():
 m=load("02_qa_screen.py")
 assert m.doi_key("https://doi.org/10.1234/ABC ")=="10.1234/abc"
def test_abstract_reconstruction():
 m=load("01_acquire_candidates.py")
 assert m.abstract_from_index({"voice":[1],"hearing":[0]})=="hearing voice"
def test_unapproved_source_refused():
 m=load("01_acquire_candidates.py")
 try:m.acquire({"source_ids_confirmed":False},"abc@example.org",ROOT/"dummy")
 except ValueError:pass
 else:raise AssertionError("Unapproved sources must be refused")
