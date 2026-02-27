import re

class TokenOptimizer:
    """
    Utility to optimize token usage in AI agent prompts.
    Includes logic for message condensation and redundant data removal.
    """
    
    @staticmethod
    def condense_messages(messages, max_history=10):
        """
        Retains the system message, the last N messages, and summarizes the rest.
        (Placeholder logic for now).
        """
        if len(messages) <= max_history:
            return messages
        
        system_msg = [m for m in messages if m.get("role") == "system"]
        recent_msgs = messages[-max_history:]
        
        # In a real scenario, we would use a low-cost model to summarize intermediate messages.
        return system_msg + recent_msgs

    @staticmethod
    def strip_redundant_whitespace(text):
        """
        Removes extra whitespaces and newlines to save tokens.
        """
        return re.sub(r'\n+', '\n', text).strip()

if __name__ == "__main__":
    optimizer = TokenOptimizer()
    sample_text = "Hello    world! \n\n This is   a test.\n\n\nNew line."
    optimized = optimizer.strip_redundant_whitespace(sample_text)
    print(f"Original length: {len(sample_text)}, Optimized length: {len(optimized)}")
    print(f"Result: {optimized}")
