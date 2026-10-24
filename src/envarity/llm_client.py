import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def get_client() -> OpenAI:
    base_url = os.environ["ENVARITY_LLM_BASE_URL"]
    api_key = os.environ["ENVARITY_LLM_API_KEY"]
    return OpenAI(base_url=base_url, api_key=api_key)


def get_model() -> str:
    return os.environ["ENVARITY_LLM_MODEL"]
