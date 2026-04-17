"""Lossy detection — verify compressed summaries preserve key identifiers."""
import re

_MIN_IDENTIFIER_RATIO = 0.4
_MIN_IDENTIFIER_LEN = 3

class QualityChecker:
    def check(self, original: str, summary: str) -> bool:
        identifiers = self.extract_identifiers(original)
        if not identifiers:
            return True
        summary_lower = summary.lower()
        preserved = sum(1 for ident in identifiers if ident.lower() in summary_lower)
        ratio = preserved / len(identifiers)
        return ratio >= _MIN_IDENTIFIER_RATIO

    def extract_identifiers(self, code: str) -> list[str]:
        patterns = [
            r"(?:def|class|function)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
            r"([a-zA-Z_][a-zA-Z0-9_]*)\s*[=:(]",
            r"self\.([a-zA-Z_][a-zA-Z0-9_]*)",
        ]
        identifiers = set()
        for pattern in patterns:
            for match in re.finditer(pattern, code):
                name = match.group(1)
                if len(name) >= _MIN_IDENTIFIER_LEN and name not in {"self", "None", "True", "False"}:
                    identifiers.add(name)
        # Extract function/method parameters
        for param_match in re.finditer(r"(?:def|function)\s+\w+\s*\(([^)]*)\)", code):
            for param in re.split(r"[,\s]+", param_match.group(1)):
                param = param.strip().split(":")[0].split("=")[0].strip()
                if len(param) >= _MIN_IDENTIFIER_LEN and param not in {"self", "cls", "None", "True", "False"}:
                    identifiers.add(param)
        for match in re.finditer(r"\b([A-Z][a-zA-Z0-9]+)\b", code):
            identifiers.add(match.group(1))
        return sorted(identifiers)
