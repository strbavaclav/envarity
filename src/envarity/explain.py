import json

from envarity.llm_client import get_client, get_model

SYSTEM_PROMPT = """You are an SRE assistant reviewing configuration differences \
between environments in a promotion pipeline. You get a list of placeholder \
keys that differ, already classified as "expected" (allowed to differ) or \
"flagged" (not matched by any rule).

Respond with a JSON object with exactly these fields:
- "summary": one sentence describing the difference
- "risk": one of "low", "medium", "high"
- "reasoning": one or two sentences explaining the risk level

Only flagged keys should drive the risk level. Many flagged keys, or flagged \
keys that look like auth/URL/connectivity settings, should be rated higher."""


def explain_diff(classified: dict) -> dict:
    client = get_client()
    response = client.chat.completions.create(
        model=get_model(),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(classified)},
        ],
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    if content is None:
        raise RuntimeError("LLM response had no content")

    return json.loads(content)
