import json
import sys

from openai.types.chat import ChatCompletionMessageParam

from envarity.fewshot import build_fewshot_messages
from envarity.llm_client import get_client, get_model

SYSTEM_PROMPT = """You are an SRE assistant reviewing configuration differences \
between environments in a promotion pipeline. You get a JSON object with two fields:
- "diff": placeholder keys that differ, classified as "expected" (allowed to differ) \
or "flagged" (not matched by any rule).
- "key_history": for each flagged key, a short summary of how many times it has \
changed before in these environments and any associated ticket IDs.

Use the history as context, not as a verdict. A ticket shows a change was \
deliberate at the time it happened — it does not confirm the current difference \
is still the intended state, and a key that has changed many times may indicate \
a recurring problem rather than a settled, safe pattern. A key with no prior \
history is not automatically riskier either — it may simply be new. Weigh the \
history alongside what the keys themselves suggest (e.g., connectivity/auth \
settings vs. resource tuning), and say explicitly when the history is ambiguous \
rather than resolving it toward a particular risk level.

Respond with a JSON object with exactly these fields:
- "summary": one sentence describing the difference
- "risk": one of "low", "medium", "high"
- "reasoning": one or two sentences explaining the risk level, referencing the \
history where relevant"""


def explain_diff(
    classified: dict, key_histories: dict[str, str], use_fewshot: bool = True
) -> dict:
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

    payload = {"diff": classified, "key_history": key_histories}
    messages.append({"role": "user", "content": json.dumps(payload)})

    response = client.chat.completions.create(
        model=get_model(),
        messages=messages,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    if content is None:
        raise RuntimeError("LLM response had no content")

    return json.loads(content)
