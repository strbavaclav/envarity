from openai.types.chat import ChatCompletionToolUnionParam

from envarity.classify import classify_diff
from envarity.config_models import Rule
from envarity.embeddings import embed_texts, find_similar
from envarity.git_history import (
    changes_to_documents,
    log_all_changes,
    summarize_key_history,
)
from envarity.git_reader import read_file_at_ref
from envarity.yaml_diff import diff_keys, extract_placeholder_names

TOOL_SCHEMAS: list[ChatCompletionToolUnionParam] = [
    {
        "type": "function",
        "function": {
            "name": "get_diff",
            "description": "Get the classified placeholder key diff between the two environments. Always call this first.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_key_history",
            "description": "Get the real change history (count of changes + ticket IDs) for one specific placeholder key.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "The placeholder key name, e.g. HOST",
                    }
                },
                "required": ["key"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_similar",
            "description": "Semantic search over the file's change history, for when the exact key name is unknown or history found nothing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language description of what to search for",
                    }
                },
                "required": ["query"],
            },
        },
    },
]


def make_dispatcher(
    repo, file_name: str, branch_from: str, branch_to: str, rules: list[Rule]
):
    def dispatch(name: str, arguments: dict) -> dict:
        if name == "get_diff":
            text_from = read_file_at_ref(repo.path, f"origin/{branch_from}", file_name)
            text_to = read_file_at_ref(repo.path, f"origin/{branch_to}", file_name)
            diff = diff_keys(
                extract_placeholder_names(text_from), extract_placeholder_names(text_to)
            )
            return classify_diff(diff, rules)

        if name == "get_key_history":
            summary = summarize_key_history(
                repo.path,
                file_name,
                arguments["key"],
                branches=[branch_from, branch_to],
            )
            return {"key": arguments["key"], "history": summary}

        if name == "search_similar":
            changes = log_all_changes(
                repo.path, file_name, branches=[branch_from, branch_to]
            )
            documents = changes_to_documents(changes)
            if not documents:
                return {"results": []}
            embeddings = embed_texts(documents)
            results = find_similar(arguments["query"], documents, embeddings, top_k=3)
            return {
                "results": [{"text": doc, "score": score} for doc, score in results]
            }

        raise ValueError(f"unknown tool: {name}")

    return dispatch
