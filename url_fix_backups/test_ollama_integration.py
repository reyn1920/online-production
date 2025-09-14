#!/usr / bin / env python3
"""
Test script to verify Ollama + Trae.ai integration on MacBook Air M1.

Steps:
1. Ensure Ollama is running: `ollama serve`
2. Ensure Trae.ai backend config points to http://localhost:11434
3. Run this script: `python test_ollama_integration.py`
"""

import json

import requests

OLLAMA_ENDPOINT = "http://localhost:11434"


def test_ollama_tags():
    """Check if Ollama is running and list models."""
    url = f"{OLLAMA_ENDPOINT}/api / tags"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        models = resp.json().get("models", [])
        print("✅ Ollama is live:", [m["name"] for m in models])
        return True
    except Exception as e:
        print("❌ Ollama not reachable:", e)
        return False


def test_ollama_generate():
    """Ask Ollama to debug a snippet of Python code."""
    url = f"{OLLAMA_ENDPOINT}/api / generate"
    payload = {
        "model": "codellama",  # change this if you pulled another model
        "prompt": "Find the bug in this Python code:\\n\\nfor i in range(5)\\n    print(i)",
    }

    try:
        with requests.post(url, json=payload, stream=True, timeout=30) as resp:
            resp.raise_for_status()
            print("✅ Debugging response from Ollama:\\n")
            for line in resp.iter_lines():
                if line:
                    data = json.loads(line.decode("utf - 8"))
                    if "response" in data:
                        print(data["response"], end="", flush=True)
            print("\\n")
        return True
    except Exception as e:
        print("❌ Error generating from Ollama:", e)
        return False


def main():
    print("🔍 Testing Ollama + Trae.ai integration...")
    print("=" * 50)

    ok_tags = test_ollama_tags()
    if ok_tags:
        test_ollama_generate()

    print("\\n🎯 Done. If you saw responses, Trae.ai can now use Ollama for debugging & fixes.")


if __name__ == "__main__":
    main()
