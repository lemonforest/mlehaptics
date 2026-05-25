"""R-RBS-LM-24 — Ecosystem smoke tests for the OpenAI-API endpoint.

Verifies that the RBS-LM server is reachable via the standard `base_url`
override of major LLM-orchestration frameworks. Each test does the
minimum: instantiate the framework's client with our base_url, send a
single chat completion, decode the response. Pass = no exception, content
returned.

Per `[[user_stance_ai_is_not_a_substrate]]`: these frameworks treat our
local expert as a model endpoint (callee, not orchestrator). That's
exactly what a transducer should look like in the ecosystem.

Tested frameworks:
  - openai (vanilla SDK)
  - langchain-openai (LangChain's OpenAI client)
  - autogen-ext openai (AG2's OpenAIChatCompletionClient)
  - litellm (universal LLM proxy/router)

CopilotKit (React-side) is verified via its underlying OpenAIAdapter which
delegates to the openai SDK — the openai test below covers that path.

Usage (server must be running on 127.0.0.1:8788):
    ~/.venvs/rbs-lm-research/bin/python \\
        docs/srmech/rbs_lm_research/ecosystem_smoke_tests.py
"""

import asyncio
import json
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

BASE_URL = "http://127.0.0.1:8788/v1"
MODEL_ID_DEFAULT = "rbs-lm-v18-path-c"
TEST_PROMPT = "The morning sun"
MAX_TOKENS = 8

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))


def get_model_id():
    """Discover the model_id currently served by the live server."""
    import urllib.request
    with urllib.request.urlopen(f"{BASE_URL}/models") as r:
        data = json.loads(r.read())
    return data["data"][0]["id"]


def test_openai_sdk(model_id):
    """Vanilla openai Python SDK — covers CopilotKit's OpenAIAdapter path."""
    from openai import OpenAI
    client = OpenAI(base_url=BASE_URL, api_key="not-needed")
    resp = client.chat.completions.create(
        model=model_id,
        messages=[{"role": "user", "content": TEST_PROMPT}],
        max_tokens=MAX_TOKENS,
    )
    return resp.choices[0].message.content


def test_langchain(model_id):
    """LangChain's ChatOpenAI with base_url override."""
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(
        model=model_id,
        base_url=BASE_URL,
        api_key="not-needed",
        max_tokens=MAX_TOKENS,
    )
    resp = llm.invoke(TEST_PROMPT)
    return resp.content


def test_autogen(model_id):
    """AG2 (autogen-ext) OpenAIChatCompletionClient with base_url override."""
    from autogen_core.models import UserMessage
    from autogen_ext.models.openai import OpenAIChatCompletionClient

    client = OpenAIChatCompletionClient(
        model=model_id,
        base_url=BASE_URL,
        api_key="not-needed",
        max_tokens=MAX_TOKENS,
        model_info={
            "vision": False,
            "function_calling": False,
            "json_output": False,
            "family": "unknown",
            "structured_output": False,
        },
    )

    async def _run():
        result = await client.create([UserMessage(content=TEST_PROMPT, source="user")])
        await client.close()
        return result.content

    return asyncio.run(_run())


def test_litellm(model_id):
    """LiteLLM as universal proxy/router."""
    import litellm
    resp = litellm.completion(
        model=f"openai/{model_id}",
        messages=[{"role": "user", "content": TEST_PROMPT}],
        api_base=BASE_URL,
        api_key="not-needed",
        max_tokens=MAX_TOKENS,
    )
    return resp.choices[0].message.content


TESTS = [
    ("openai (covers CopilotKit OpenAIAdapter)", test_openai_sdk),
    ("langchain-openai", test_langchain),
    ("autogen-ext (AG2)", test_autogen),
    ("litellm", test_litellm),
]


def main():
    print(f"=== R-RBS-LM-24 ecosystem smoke tests ===")
    print(f"  server: {BASE_URL}")
    print(f"  prompt: {TEST_PROMPT!r}")
    print(f"  max_tokens: {MAX_TOKENS}")

    try:
        model_id = get_model_id()
    except Exception as e:
        print(f"\nFATAL: server unreachable at {BASE_URL}: {e}")
        print(f"Start it first with: ~/.venvs/rbs-lm-research/bin/python "
              f"docs/srmech/rbs_lm_research/rbs_lm_server.py")
        sys.exit(1)
    print(f"  model_id (from /v1/models): {model_id}")

    results = []
    for label, fn in TESTS:
        print(f"\n--- {label} ---")
        t0 = time.time()
        try:
            content = fn(model_id)
            elapsed = (time.time() - t0) * 1000
            print(f"  PASS in {elapsed:.0f} ms")
            print(f"  completion: {content!r}")
            results.append({"framework": label, "status": "PASS",
                            "elapsed_ms": elapsed, "completion": content})
        except Exception as e:
            elapsed = (time.time() - t0) * 1000
            print(f"  FAIL in {elapsed:.0f} ms: {type(e).__name__}: {e}")
            results.append({"framework": label, "status": "FAIL",
                            "elapsed_ms": elapsed, "error": f"{type(e).__name__}: {e}"})

    n_pass = sum(1 for r in results if r["status"] == "PASS")
    print(f"\n=== Summary ===")
    print(f"  {n_pass}/{len(TESTS)} frameworks talked to the RBS-LM server "
          f"via standard OpenAI-API base_url override.")
    for r in results:
        print(f"  {r['status']:>4}  {r['framework']}")

    out_path = Path("docs/srmech/rbs_lm_research/ecosystem_smoke_results.json")
    out_path.write_text(json.dumps({
        "partition": "R-RBS-LM-24",
        "server_base_url": BASE_URL,
        "model_id": model_id,
        "test_prompt": TEST_PROMPT,
        "max_tokens": MAX_TOKENS,
        "results": results,
    }, indent=2))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
