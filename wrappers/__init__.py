from .gemini import GeminiWrapper
from .chatgpt import ChatGPTWrapper
from .claude import ClaudeWrapper
from .perplexity import PerplexityWrapper

ALL_WRAPPERS = [GeminiWrapper, ChatGPTWrapper, ClaudeWrapper, PerplexityWrapper]
