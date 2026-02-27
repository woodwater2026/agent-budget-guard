import re

class TokenOptimizer:
    """
    Core logic for reducing token usage by optimizing prompts and context.
    """
    def __init__(self, max_context_tokens=4000):
        self.max_context_tokens = max_context_tokens

    def clean_text(self, text):
        """
        Removes redundant whitespace, newlines, and common 'filler' phrases.
        """
        # Remove multiple spaces and newlines
        text = re.sub(r'\s+', ' ', text).strip()
        # Remove repetitive phrases common in AI responses (example)
        fillers = ["I understand that", "As an AI language model", "I'm happy to help"]
        for filler in fillers:
            text = text.replace(filler, "")
        return text

    def truncate_history(self, messages, limit=10):
        """
        Keeps only the most recent N messages to save context space.
        """
        if len(messages) <= limit:
            return messages
        return messages[-limit:]

    def estimate_token_savings(self, original_text, optimized_text):
        """
        Rough estimation of characters saved (approx 4 chars per token).
        """
        savings = len(original_text) - len(optimized_text)
        return max(0, savings // 4)

if __name__ == "__main__":
    optimizer = TokenOptimizer()
    sample = "   Hello!    I understand that you want to save   tokens. I'm happy to help.   "
    clean = optimizer.clean_text(sample)
    print(f"Original: '{sample}'")
    print(f"Cleaned: '{clean}'")
    print(f"Approx savings: {optimizer.estimate_token_savings(sample, clean)} tokens")
