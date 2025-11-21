from agent.api_client import call_model

if __name__ == "__main__":
    prompt = "What is 17 + 28? Answer with just the number."
    result = call_model(prompt)
    print("OK:", result["ok"], "HTTP:", result["status"])
    print("MODEL SAYS:", (result["text"] or "").strip())