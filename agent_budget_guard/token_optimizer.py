import re
import tiktoken

class TokenOptimizer:
    """
    Module to reduce token usage by stripping redundant information
    and compressing context before sending to LLM.
    """
    def __init__(self, max_history=10, max_tokens=4000, encoding_name="cl100k_base"):
        self.max_history = max_history
        self.max_tokens = max_tokens
        try:
            self.encoding = tiktoken.get_encoding(encoding_name)
        except ValueError:
            print(f"Warning: Encoding '{encoding_name}' not found. Using 'cl100k_base'.")
            self.encoding = tiktoken.get_encoding("cl100k_base")

    def estimate_tokens(self, text):
        return len(self.encoding.encode(text))

    def strip_redundant_whitespace(self, text):
        return re.sub(r'\s+', ' ', text).strip()

    def summarize_context(self, history_messages):
        """
        Optimizes a list of message dictionaries (e.g., from a conversation history)
        to fit within max_tokens, prioritizing recent messages.
        """
        if not history_messages: # Handle empty history
            return []

        current_token_count = 0
        optimized_messages = []

        # Process messages in reverse to prioritize most recent
        for msg in reversed(history_messages):
            content = msg.get("content", "")
            clean_content = self.strip_redundant_whitespace(content)
            msg_tokens = self.estimate_tokens(clean_content)

            if current_token_count + msg_tokens <= self.max_tokens:
                optimized_messages.insert(0, {**msg, "content": clean_content})
                current_token_count += msg_tokens
            else:
                # If adding the whole message exceeds limit, try truncating
                remaining_tokens = self.max_tokens - current_token_count
                if remaining_tokens > 0:
                    truncated_content = self.truncate_text_by_tokens(clean_content, remaining_tokens)
                    if truncated_content:
                        optimized_messages.insert(0, {**msg, "content": truncated_content})
                        current_token_count += self.estimate_tokens(truncated_content)
                break # Stop adding messages once limit is hit
        
        return optimized_messages

    def truncate_text_by_tokens(self, text, max_tokens):
        """
        Truncates text to fit within max_tokens using tiktoken.
        """
        tokens = self.encoding.encode(text)
        if len(tokens) <= max_tokens:
            return text
        
        return self.encoding.decode(tokens[:max_tokens])

    def optimize_payload(self, messages):
        """
        Main entry point for optimizing the entire payload (list of messages).
        This will use summarize_context to manage overall token count.
        """
        return self.summarize_context(messages)

if __name__ == "__main__":
    optimizer = TokenOptimizer(max_tokens=50)

    # Test strip_redundant_whitespace
    sample_text = "   This    is a     very    redundant    message.   "
    print(f"Original: '{sample_text}'")
    print(f"Optimized (whitespace): '{optimizer.strip_redundant_whitespace(sample_text)}'")

    # Test estimate_tokens
    test_sentence = "Hello, how are you today? This is a test sentence."
    print(f"Sentence: '{test_sentence}' -> Tokens: {optimizer.estimate_tokens(test_sentence)}")

    # Test summarize_context (prioritizing recent messages)
    history = [
        {"role": "user", "content": "This is a very long message that should definitely be truncated if the token limit is small. It contains many words and will exceed the limit easily." * 5},
        {"role": "assistant", "content": "Okay, I understand. Let me try to respond concisely."},
        {"role": "user", "content": "What is the capital of France?"},
        {"role": "assistant", "content": "The capital of France is Paris."},
        {"role": "user", "content": "Can you tell me more about its history?"},
    ]

    print("\n--- Original History ---")
    for i, msg in enumerate(history):
        print(f"Msg {i+1} ({optimizer.estimate_tokens(msg["content"])} tokens): {msg["content"][:50]}...")

    optimized_history = optimizer.optimize_payload(history)
    print("\n--- Optimized History (Max 50 tokens) ---")
    for i, msg in enumerate(optimized_history):
        print(f"Msg {i+1} ({optimizer.estimate_tokens(msg["content"])} tokens): {msg["content"][:50]}...")

    # Test with a very long single message to see truncation
    print("\n--- Very Long Single Message Test ---")
    long_message_history = [
        {"role": "user", "content": "This is an extremely long message that should be truncated because it exceeds the maximum token limit by a significant margin. We want to ensure that even a single very long message doesn't break the system, but rather gets cut down to size. It must be short enough to fit. This is an extremely long message that should be truncated because it exceeds the maximum token limit by a significant margin. We want to ensure that even a single very long message doesn't break the system, but rather gets cut down to size. It must be short enough to fit."}
    ]
    optimized_long_message = optimizer.optimize_payload(long_message_history)
    print("Optimized single message:")
    for msg in optimized_long_message:
        print(f"({optimizer.estimate_tokens(msg["content"])} tokens): {msg["content"][:100]}...")
