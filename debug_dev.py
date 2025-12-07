from agent.agent_core import CoreAgent
from evaluation import grade, evaluate_agent
from run_dev import load_dev_data

def debug_run():
    agent = CoreAgent()
    data = load_dev_data()
    # Test only the first 3 examples
    subset = data[:3]
    
    print("Debugging first 3 examples...")
    for i, item in enumerate(subset):
        q = item["input"]
        expected = item["output"]
        domain = item.get("domain")
        
        print(f"\n--- Example {i+1} ---")
        print(f"Question: {q}")
        print(f"Expected: {expected}")
        print(f"Domain: {domain}")
        
        # We want to see what the agent returns
        pred = agent.run(q, domain)
        print(f"Raw Agent Output: {pred}")
        
        kind = "numeric" if domain and "math" in domain else "text"
        correct = grade(expected, pred, kind)
        print(f"Correct: {correct}")

if __name__ == "__main__":
    # Also run the simple test question from run_dev.py
    agent = CoreAgent()
    test_question = "What is 5 + 7? Answer with just the number."
    print("\n--- Simple Test Question ---")
    print(f"Question: {test_question}")
    print("AGENT SAYS:", agent.run(test_question))
    
    debug_run()
