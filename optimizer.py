import re

class TokenOptimizer:
    def __init__(self, max_context_tokens=4096):
        self.max_context_tokens = max_context_tokens

    def prune_whitespace(self, text):
        """Remove redundant whitespace and newlines."""
        return re.sub(r'\n+', '\n', text).strip()

    def summarize_history(self, history, keep_last=5):
        """
        Logic placeholder to keep the last N messages intact 
        and summarize older ones to save tokens.
        """
        if len(history) <= keep_last:
            return history
        
        # In a real scenario, we'd call a cheap model to summarize history[0:-keep_last]
        print(f"[OPTIMIZER] Pruning history: Keeping last {keep_last} messages.")
        return history[-keep_last:]

if __name__ == "__main__":
    optimizer = TokenOptimizer()
    sample_text = "Hello    world. \n\n\n This is   a test."
    print(f"Original: {repr(sample_text)}")
    print(f"Optimized: {repr(optimizer.prune_whitespace(sample_text))}")
