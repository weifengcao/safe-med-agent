import re

class MockLLM:
    """
    Simulates an LLM for the Triage Agent.
    It inspects the conversation history to decide the next 'Thought' and 'Action'.
    """
    def generate(self, history: str) -> str:
        history_lower = history.lower()
        
        # Rule 1: Safety First - Verify Insurance if not done
        if "action: verify_insurance" not in history_lower:
            # Extract patient ID from history (e.g., "Patient 999")
            match = re.search(r"patient (\d+)", history_lower)
            p_id = match.group(1) if match else "unknown"
            return f"Thought: I need to verify the patient's insurance before proceeding with any referral.\nAction: verify_insurance[patient_id={p_id}]"
        
        # Rule 2: If insurance failed, stop
        if "observation: insurance invalid" in history_lower:
             return "Final Answer: Cannot provide referral due to invalid insurance."

        # Rule 3: Analyze Symptoms for Specialist
        if "specialist" not in history_lower and "primary_care" not in history_lower:
            if "chest pain" in history_lower or "severe" in history_lower or "heart" in history_lower:
                return "Thought: The symptoms (chest pain/severe) indicate a need for a specialist.\nAction: find_specialist[symptoms=chest pain]"
            else:
                return "Thought: The symptoms appear mild. A primary care physician is appropriate.\nAction: find_primary_care[symptoms=mild]"

        # Rule 4: Finalize if we have a referral
        if "observation: found" in history_lower:
            return "Final Answer: I have authorized a referral. Details have been provided."
            
        return "Final Answer: I am unsure how to proceed."

class TriageAgent:
    def __init__(self):
        self.llm = MockLLM()
    
    # --- Tools ---
    def verify_insurance(self, args):
        print(f"  [Tool] Verifying insurance for {args}...")
        # Mock logic: patient_id=123 is valid, others invalid
        if "123" in args:
            return "Valid Insurance"
        return "Insurance Invalid"

    def find_specialist(self, args):
        print(f"  [Tool] Finding specialist for {args}...")
        return "Found Specialist: Dr. Strange (Cardiology)"

    def find_primary_care(self, args):
        print(f"  [Tool] Finding PCP for {args}...")
        return "Found PCP: Dr. House (General Practice)"

    # --- ReAct Loop ---
    def run(self, query: str):
        print(f"--- Starting ReAct Agent Task: {query} ---")
        history = f"Query: {query}"
        
        for step in range(5):
            # 1. Thought (LLM Generation)
            llm_output = self.llm.generate(history)
            print(f"\n[Step {step+1}]")
            print(f"LLM Output:\n{llm_output}")
            
            history += f"\n{llm_output}"
            
            # 2. Check for Final Answer
            if "Final Answer:" in llm_output:
                return llm_output.split("Final Answer:")[1].strip()
            
            # 3. Action (Parser)
            # Regex to find Action: tool_name[args]
            match = re.search(r"Action: (\w+)\[(.*?)\]", llm_output)
            if match:
                tool_name = match.group(1)
                tool_args = match.group(2)
                
                # 4. Observation (Execution)
                if tool_name == "verify_insurance":
                    result = self.verify_insurance(tool_args)
                elif tool_name == "find_specialist":
                    result = self.find_specialist(tool_args)
                elif tool_name == "find_primary_care":
                    result = self.find_primary_care(tool_args)
                else:
                    result = "Error: Tool not found"
                
                observation = f"Observation: {result}"
                print(f"{observation}")
                history += f"\n{observation}"
            else:
                print("Error: Could not parse action.")
                break
                
        return "Agent timed out."

# --- FastAPI Service ---
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()
agent = TriageAgent()

class TriageRequest(BaseModel):
    query: str

@app.post("/triage")
def triage_endpoint(request: TriageRequest):
    result = agent.run(request.query)
    return {"result": result}

if __name__ == "__main__":
    # Local CLI Test
    print("\n=== Scenario 1: Severe Symptoms (Valid Insurance) ===")
    result = agent.run("Patient 123 has severe chest pain.")
    print(f"Result: {result}")
    
    print("\n=== Scenario 2: Mild Symptoms (Valid Insurance) ===")
    result = agent.run("Patient 123 has a mild cough.")
    print(f"Result: {result}")
    
    print("\n=== Scenario 3: Invalid Insurance ===")
    result = agent.run("Patient 999 has a headache.")
    print(f"Result: {result}")
