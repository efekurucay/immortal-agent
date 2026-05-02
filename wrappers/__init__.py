from .ollama import OllamaWrapper
from .groq import GroqWrapper
from .openrouter import OpenRouterWrapper
from .huggingface import HuggingFaceWrapper
from .together import TogetherWrapper
from .mistral import MistralWrapper
from .cohere import CohereWrapper
from .gemini import GeminiWrapper
from .chatgpt import ChatGPTWrapper
from .claude import ClaudeWrapper
from .perplexity import PerplexityWrapper

# Priority order: most reliable/free first, cookie-based last
ALL_WRAPPERS = [
    OllamaWrapper,       # local, no limits
    GroqWrapper,         # fastest free API
    OpenRouterWrapper,   # many free models
    HuggingFaceWrapper,  # free inference API
    TogetherWrapper,     # free credits
    MistralWrapper,      # free tier
    CohereWrapper,       # free tier
    GeminiWrapper,       # cookie-based
    ChatGPTWrapper,      # cookie-based
    ClaudeWrapper,       # cookie-based
    PerplexityWrapper,   # cookie-based
]
