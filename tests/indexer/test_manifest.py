import pytest
from pathlib import Path
from context_engine.indexer.manifest import Manifest

@pytest.fixture
def manifest(tmp_path):
    return Manifest(manifest_path=tmp_path / "manifest.json")

def test_empty_manifest_has_no_entries(manifest):
    assert manifest.get_hash("anything.py") is None

def test_update_and_get(manifest):
    manifest.update("src/main.py", "abc123hash")
    assert manifest.get_hash("src/main.py") == "abc123hash"

def test_has_changed_detects_new_file(manifest):
    assert manifest.has_changed("src/main.py", "abc123") is True

def test_has_changed_detects_modification(manifest):
    manifest.update("src/main.py", "old_hash")
    assert manifest.has_changed("src/main.py", "new_hash") is True

def test_has_changed_returns_false_if_same(manifest):
    manifest.update("src/main.py", "same_hash")
    assert manifest.has_changed("src/main.py", "same_hash") is False

def test_save_and_load(tmp_path):
    path = tmp_path / "manifest.json"
    m1 = Manifest(manifest_path=path)
    m1.update("a.py", "hash_a")
    m1.save()
    m2 = Manifest(manifest_path=path)
    assert m2.get_hash("a.py") == "hash_a"

def test_remove(manifest):
    manifest.update("a.py", "hash_a")
    manifest.remove("a.py")
    assert manifest.get_hash("a.py") is None
