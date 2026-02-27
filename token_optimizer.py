import re

class TokenOptimizer:
    """
    Module to reduce token usage by stripping redundant information
    and compressing context before sending to LLM.
    """
    def __init__(self, max_history=10):
        self.max_history = max_history

    def strip_redundant_whitespace(self, text):
        return re.sub(r'\s+', ' ', text).strip()

    def summarize_context(self, history):
        """
        Keep the last N turns, and summarize the earlier ones.
        (Placeholder for summarization logic)
        """
        if len(history) <= self.max_history:
            return history
        
        # Keep the latest context intact
        important_part = history[-self.max_history:]
        return important_part

    def optimize_payload(self, messages):
        optimized = []
        for msg in messages:
            content = msg.get("content", "")
            # Apply basic cleanup
            clean_content = self.strip_redundant_whitespace(content)
            optimized.append({**msg, "content": clean_content})
        return optimized

if __name__ == "__main__":
    optimizer = TokenOptimizer()
    sample_text = "   This    is a     very    redundant    message.   "
    print(f"Original: '{sample_text}'")
    print(f"Optimized: '{optimizer.strip_redundant_whitespace(sample_text)}'")
