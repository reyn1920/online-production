import json

import requests


def ask_ollama(model, prompt):
    """Send a prompt to Ollama and get the response."""

    Args:
        model (str): The model name to use (e.g., 'codellama:latest', 'llama2:7b')
        prompt (str): The prompt to send to the model

    Returns:
        str: The complete response from the model
    """"""
    url = "http://localhost:11434 / api / generate"
    payload = {"model": model, "prompt": prompt}
    resp = requests.post(url, json=payload, stream=True)
    answer = ""
    for line in resp.iter_lines():
        if line:
            data = json.loads(line.decode("utf - 8"))
            answer += data.get("response", "")
    return answer


# Test function
if __name__ == "__main__":
    # Test with CodeLlama model
    test_prompt = "Write a simple Python function to calculate factorial"
    response = ask_ollama("codellama:latest", test_prompt)
    print(f"Prompt: {test_prompt}")
    print(f"Response: {response}")