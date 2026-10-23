import fnmatch

from envarity.config_models import Rule


def _matches_any_rule(key: str, rules: list[Rule]) -> bool:
    return any(fnmatch.fnmatch(key, rule.key_pattern) for rule in rules)


def classify_diff(diff: dict, rules: list[Rule]) -> dict:
    expected: list[str] = []
    flagged: list[str] = []
    for key in diff["only_a"] | diff["only_b"]:
        if _matches_any_rule(key, rules):
            expected.append(key)
        else:
            flagged.append(key)
    return {"expected": sorted(expected), "flagged": sorted(flagged)}
