"""Quick SambaNova connectivity smoke test.

Reads the API key from the environment — never hardcode credentials.
    OPENAI_API_KEY=<key> python test_samba.py
"""
import os

from openai import OpenAI

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise SystemExit("Set OPENAI_API_KEY in your environment before running this smoke test.")

client = OpenAI(
    api_key=api_key,
    base_url=os.getenv("AI_BASE_URL", "https://api.sambanova.ai/v1"),
)
response = client.chat.completions.create(
    model=os.getenv("AI_MODEL", "Meta-Llama-3.3-70B-Instruct"),
    messages=[{"role": "user", "content": "Say hello!"}],
)
print(response.choices[0].message.content)
