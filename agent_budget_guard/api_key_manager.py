import os
import random
import json # Added json import

class APIKeyManager:
    """
    Manages rotation and fallback for multiple API keys.
    API keys are loaded from config.json under the "api_keys" section.
    """
    def __init__(self, service_name="GEMINI", config_path="projects/agent_budget_guard/config.json"): # Modified init
        self.service_name = service_name
        self.config_path = config_path
        self.api_keys = self._load_api_keys()
        self.current_key_index = 0
        if not self.api_keys:
            print(f"Warning: No API keys found for {service_name} in {config_path}. Operations might fail.")

    def _load_api_keys(self):
        keys = []
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            if "api_keys" in config and self.service_name in config["api_keys"]:
                keys = config["api_keys"][self.service_name]
        except FileNotFoundError:
            print(f"Error: Config file not found at {self.config_path}")
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in config file at {self.config_path}")
        
        random.shuffle(keys) # Shuffle to distribute usage
        return keys

    def get_key(self):
        if not self.api_keys:
            return None
        return self.api_keys[self.current_key_index]

    def rotate_key(self):
        if not self.api_keys:
            return False
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        print(f"API key rotated for {self.service_name}. New index: {self.current_key_index}")
        return True

    def get_all_keys(self):
        return self.api_keys

# Example Usage (conceptual, assuming actual API calls are made elsewhere)
if __name__ == "__main__":
    # Ensure config.json exists with dummy keys for testing
    dummy_config_content = {
        "api_keys": {
            "GEMINI": [
                "dummy_gemini_key_1",
                "dummy_gemini_key_2"
            ]
        }
    }
    config_test_path = "projects/agent_budget_guard/test_config.json"
    with open(config_test_path, 'w') as f:
        json.dump(dummy_config_content, f, indent=4)

    manager = APIKeyManager(service_name="GEMINI", config_path=config_test_path)
    print(f"Initial Key: {manager.get_key()}")
    manager.rotate_key()
    print(f"Rotated Key: {manager.get_key()}")
    manager.rotate_key()
    print(f"Rotated Key: {manager.get_key()}")
    
    # Test with no keys for a service
    manager_no_keys = APIKeyManager(service_name="ANTHROPIC", config_path=config_test_path)
    print(f"Key (no keys for ANTHROPIC): {manager_no_keys.get_key()}")

    # Clean up dummy config
    os.remove(config_test_path)
