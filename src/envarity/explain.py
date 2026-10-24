import json
import sys

from openai.types.chat import ChatCompletionMessageParam

from envarity.fewshot import build_fewshot_messages
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


def explain_diff(classified: dict, use_fewshot: bool = True) -> dict:
    client = get_client()
    messages: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    if use_fewshot:
        fewshot_messages = build_fewshot_messages()
        if not fewshot_messages:
            print(
                "Note: no few-shot examples found in config/few_shots/ — running without calibration.",
                file=sys.stderr,
            )
        messages += fewshot_messages

    messages.append({"role": "user", "content": json.dumps(classified)})

    response = client.chat.completions.create(
        model=get_model(),
        messages=messages,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    if content is None:
        raise RuntimeError("LLM response had no content")

    return json.loads(content)
