from .ollama import OllamaWrapper
from .groq import GroqWrapper
from .cerebras import CerebrasWrapper
from .sambanova import SambanovaWrapper
from .openrouter import OpenRouterWrapper
from .huggingface import HuggingFaceWrapper
from .together import TogetherWrapper
from .mistral import MistralWrapper
from .cohere import CohereWrapper
from .grok import GrokWrapper
from .gemini import GeminiWrapper
from .chatgpt import ChatGPTWrapper
from .claude import ClaudeWrapper
from .perplexity import PerplexityWrapper

# Priority: local → fastest free APIs → cookie-based last
ALL_WRAPPERS = [
    OllamaWrapper,       # local, zero limits
    GroqWrapper,         # fastest inference
    CerebrasWrapper,     # very fast, generous free tier
    SambanovaWrapper,    # fast, free tier
    OpenRouterWrapper,   # aggregator, many free models
    HuggingFaceWrapper,  # free inference API
    TogetherWrapper,     # free credits
    MistralWrapper,      # free tier
    CohereWrapper,       # free tier
    GrokWrapper,         # xAI free tier
    GeminiWrapper,       # cookie-based
    ChatGPTWrapper,      # cookie-based
    ClaudeWrapper,       # cookie-based
    PerplexityWrapper,   # cookie-based
]
