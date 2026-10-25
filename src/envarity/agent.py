import json

from openai.types.chat import ChatCompletionMessageParam

from envarity.llm_client import get_client, get_model
from envarity.tools import TOOL_SCHEMAS, make_dispatcher

SYSTEM_PROMPT = """You are an SRE assistant investigating a config promotion diff \
between two environments. You have tools to inspect the diff and its history — \
use them as needed, then write a short markdown report for a human reviewer.

For flagged keys, use get_key_history to check for \
precedent. If a key's history is empty, you may try search_similar with a \
description of the concern instead. Don't call tools you don't need — only \
investigate flagged keys, and stop once you have enough to write the report.

Write the final report in markdown with these sections: Summary, Risk \
(low/medium/high), Flagged keys (what you found about each), Recommendation."""


def run_report_agent(
    repo,
    file_name: str,
    branch_from: str,
    branch_to: str,
    rules,
    max_iterations: int = 10,
) -> str:
    client = get_client()
    dispatch = make_dispatcher(repo, file_name, branch_from, branch_to, rules)

    messages: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Investigate the diff for {file_name} between {branch_from} and {branch_to}.",
        },
    ]

    for _ in range(max_iterations):
        response = client.chat.completions.create(
            model=get_model(), messages=messages, tools=TOOL_SCHEMAS
        )
        message = response.choices[0].message

        if not message.tool_calls:
            return message.content or ""

        tool_calls = [call for call in message.tool_calls if call.type == "function"]

        messages.append(
            {
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": c.id,
                        "type": "function",
                        "function": {
                            "name": c.function.name,
                            "arguments": c.function.arguments,
                        },
                    }
                    for c in tool_calls
                ],
            }
        )

        for call in tool_calls:
            arguments = json.loads(call.function.arguments)
            result = dispatch(call.function.name, arguments)
            messages.append(
                {"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)}
            )

    raise RuntimeError(f"agent did not finish within {max_iterations} iterations")
