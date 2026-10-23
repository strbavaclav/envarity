import yaml


def extract_placeholder_names(yaml_text: str) -> set[str]:
    data = yaml.safe_load(yaml_text)
    return {item["name"] for item in data.get("placeholders", [])}


def diff_keys(keys_a: set[str], keys_b: set[str]) -> dict:
    return {
        "only_a": keys_a - keys_b,
        "only_b": keys_b - keys_a,
        "both": keys_a & keys_b,
    }
