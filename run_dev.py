import json 
from agent.api_client import call_model
from agent.agent_core import CoreAgent
from evaluation import evaluate_agent

def load_dev_data(path="data/dev_data.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
    
if __name__ == "__main__":
    agent = CoreAgent()
    test_question = "What is 5 + 7? Answer with just the number."
    print("AGENT SAYS:", agent.run(test_question))
    prompt = "What is 17 + 28? Answer with just the number."
    result = call_model(prompt)
    print("OK:", result["ok"], "HTTP:", result["status"])
    print("MODEL SAYS:", (result["text"] or "").strip())
    agent = CoreAgent()
    dev_data = load_dev_data()
    evaluate_agent(agent, dev_data, max_examples=5, num_workers=10)