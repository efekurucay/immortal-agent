from .ollama import OllamaWrapper
from .groq import GroqWrapper
from .cerebras import CerebrasWrapper
from .sambanova import SambanovaWrapper
from .fireworks import FireworksWrapper
from .lepton import LeptonWrapper
from .openrouter import OpenRouterWrapper
from .deepinfra import DeepInfraWrapper
from .novita import NovitaWrapper
from .naga import NagaWrapper
from .huggingface import HuggingFaceWrapper
from .together import TogetherWrapper
from .mistral import MistralWrapper
from .cohere import CohereWrapper
from .grok import GrokWrapper
from .gemini import GeminiWrapper
from .chatgpt import ChatGPTWrapper
from .claude import ClaudeWrapper
from .perplexity import PerplexityWrapper

# Priority: local → fastest inference → aggregators → sdk-based → cookie-based
# Wrappers without a key return None immediately and get skipped by the pool.
ALL_WRAPPERS = [
    OllamaWrapper,       # local, zero limits, zero latency
    GroqWrapper,         # fastest cloud inference, generous free tier
    CerebrasWrapper,     # ultra-fast, generous free tier
    SambanovaWrapper,    # fast, free tier
    FireworksWrapper,    # fast inference, free trial credits
    LeptonWrapper,       # serverless Llama, free tier
    OpenRouterWrapper,   # aggregator — many free models
    DeepInfraWrapper,    # aggregator — cheapest paid, free trial
    NovitaWrapper,       # aggregator — free trial credits
    NagaWrapper,         # community free-tier proxy
    HuggingFaceWrapper,  # free serverless inference API
    TogetherWrapper,     # free credits on sign-up
    MistralWrapper,      # free tier (mistral-small)
    CohereWrapper,       # free tier (command-r)
    GrokWrapper,         # xAI free tier
    GeminiWrapper,       # Google — key-based
    ChatGPTWrapper,      # cookie-based (no official key path)
    ClaudeWrapper,       # cookie-based
    PerplexityWrapper,   # cookie-based
]
