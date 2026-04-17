import pytest
from context_engine.compression.quality import QualityChecker

@pytest.fixture
def checker():
    return QualityChecker()

def test_passes_when_identifiers_preserved(checker):
    original = "def calculate_total(items, tax_rate): return sum(items) * (1 + tax_rate)"
    summary = "calculate_total takes items and tax_rate, returns the sum of items with tax applied."
    assert checker.check(original, summary) is True

def test_fails_when_identifiers_missing(checker):
    original = "def calculate_total(items, tax_rate): return sum(items) * (1 + tax_rate)"
    summary = "A function that computes a value."
    assert checker.check(original, summary) is False

def test_extracts_identifiers_from_code(checker):
    code = "class UserService:\n    def get_user(self, user_id): pass"
    identifiers = checker.extract_identifiers(code)
    assert "UserService" in identifiers
    assert "get_user" in identifiers
    assert "user_id" in identifiers
