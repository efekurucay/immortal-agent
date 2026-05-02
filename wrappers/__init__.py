"""Wrapper registry — order defines static priority (lower index = higher priority)."""
from wrappers.base import BaseWrapper

# ── Free / no-auth / local first ──────────────────────────────────────────────
from wrappers.ollama import OllamaWrapper
from wrappers.groq import GroqWrapper
from wrappers.cerebras import CerebrasWrapper
from wrappers.chutes import ChutesWrapper
from wrappers.scaleway import ScalewayWrapper
from wrappers.hyperbolic import HyperbolicWrapper
from wrappers.klusterai import KlusterAiWrapper
from wrappers.aimlapi import AimlApiWrapper

# ── Reliable free tiers ───────────────────────────────────────────────────────
from wrappers.openrouter import OpenRouterWrapper
from wrappers.huggingface import HuggingFaceWrapper
from wrappers.together import TogetherWrapper
from wrappers.deepinfra import DeepInfraWrapper
from wrappers.fireworks import FireworksWrapper
from wrappers.lepton import LeptonWrapper
from wrappers.novita import NovitaWrapper
from wrappers.naga import NagaWrapper

# ── Paid / rate-limited (used as fallback) ────────────────────────────────────
from wrappers.sambanova import SambanovaWrapper
from wrappers.mistral import MistralWrapper
from wrappers.cohere import CohereWrapper
from wrappers.gemini import GeminiWrapper
from wrappers.chatgpt import ChatGPTWrapper
from wrappers.claude import ClaudeWrapper
from wrappers.grok import GrokWrapper
from wrappers.perplexity import PerplexityWrapper

ALL_WRAPPERS = [
    OllamaWrapper,
    GroqWrapper,
    CerebrasWrapper,
    ChutesWrapper,
    ScalewayWrapper,
    HyperbolicWrapper,
    KlusterAiWrapper,
    AimlApiWrapper,
    OpenRouterWrapper,
    HuggingFaceWrapper,
    TogetherWrapper,
    DeepInfraWrapper,
    FireworksWrapper,
    LeptonWrapper,
    NovitaWrapper,
    NagaWrapper,
    SambanovaWrapper,
    MistralWrapper,
    CohereWrapper,
    GeminiWrapper,
    ChatGPTWrapper,
    ClaudeWrapper,
    GrokWrapper,
    PerplexityWrapper,
]
