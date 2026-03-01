import os
import time
from api_key_manager import APIKeyManager
import json # Added json import for test config setup

class LLMClient:
    def __init__(self, service_name="GEMINI", config_path="projects/agent_budget_guard/config.json"): # Modified init
        self.api_key_manager = APIKeyManager(service_name=service_name, config_path=config_path)
        self.service_name = service_name
        # Internal counter for simulation to ensure rate limit triggers for the first key
        self._simulate_call_count = 0

    def make_api_call(self, prompt, model="default", max_retries=3):
        """
        Simulates an API call to an LLM with API key rotation on failure.
        """
        for retry_count in range(max_retries):
            current_key = self.api_key_manager.get_key()
            if not current_key:
                print(f"Error: No API keys available for {self.service_name}.")
                return {"status": "error", "message": "No API keys available"}

            print(f"Attempting API call with key (index {self.api_key_manager.current_key_index}) for {self.service_name}...")
            # Simulate API call
            try:
                response = self._simulate_api_request(prompt, model, current_key)
                if response.get("status") == "success":
                    print("API call successful.")
                    return response
                elif response.get("status") == "rate_limited":
                    print(f"Rate limit encountered with key (index {self.api_key_manager.current_key_index}). Rotating key.")
                    self.api_key_manager.rotate_key()
                    time.sleep(1) # Wait a bit before retrying with a new key
                else:
                    print(f"API error: {response.get('message')}. Retrying with same key.") # Other errors might not need key rotation
            except Exception as e:
                print(f"An unexpected error occurred: {e}. Retrying.")
            
        print(f"Failed to make API call after {max_retries} retries.")
        return {"status": "error", "message": "Failed after multiple retries"}

    def _simulate_api_request(self, prompt, model, api_key):
        """
        Internal function to simulate an actual API request to an LLM.
        In a real scenario, this would use a library like google.generativeai or openai.
        Simulates a rate limit for the first key used to demonstrate rotation.
        """
        self._simulate_call_count += 1
        # Simulate rate limit on the first call to the first key, then succeed
        if self.api_key_manager.current_key_index == 0 and self._simulate_call_count == 1:
            return {"status": "rate_limited", "message": "Simulated rate limit"}
        else:
            return {"status": "success", "response": f"Generated text for '{prompt}' using {model} with key {api_key[-4:]}"}


if __name__ == "__main__":
    # Setup dummy API keys in a test config for demonstration
    dummy_config_content = {
        "api_keys": {
            "GEMINI": [
                "test_key_abc1",
                "test_key_def2",
                "test_key_ghi3"
            ]
        }
    }
    config_test_path = "projects/agent_budget_guard/test_config.json"
    with open(config_test_path, 'w') as f:
        json.dump(dummy_config_content, f, indent=4)

    client = LLMClient(service_name="GEMINI", config_path=config_test_path)
    
    print("\n--- First API Call (should trigger rate limit and rotate) ---")
    result1 = client.make_api_call("Tell me a story about a brave knight.", model="gemini-flash")
    print(result1)

    print("\n--- Second API Call (should use rotated key and succeed) ---")
    result2 = client.make_api_call("Write a poem about the sea.", model="gemini-pro")
    print(result2)

    print("\n--- Third API Call (should use next rotated key and succeed) ---")
    result3 = client.make_api_call("Describe a futuristic city.", model="gemini-ultra")
    print(result3)

    # Clean up test config file
    os.remove(config_test_path)
