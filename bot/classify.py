"""Keyword-based topic tagging. No API, no cost, works offline.

RULES are checked in priority order and the first MAX_TAGS matches are shown.
Edit the word lists freely: plain words are matched as whole words
(case-insensitive); `regex` entries are used exactly as written.
"""
import re

from . import config

# (tag, emoji, plain words, extra regex)
RULES = [
    ("AI", "🤖", [
        "ai", "llm", "llms", "gpt", "chatgpt", "openai", "anthropic", "claude",
        "gemini", "deepseek", "mistral", "copilot", "chatbot", "chatbots",
        "machine learning", "deep learning", "neural network", "neural networks",
        "generative", "diffusion model", "agentic", "midjourney", "sora", "grok",
        "perplexity", "hugging face",
    ], []),
    ("Security", "🔐", [
        "security", "cybersecurity", "vulnerability", "vulnerabilities", "exploit",
        "exploits", "exploited", "zero-day", "0-day", "ransomware", "malware",
        "phishing", "breach", "breaches", "hacked", "hacker", "hackers", "backdoor",
        "botnet", "ddos", "spyware", "infostealer", "encryption", "privacy",
        "surveillance", "cve", "cyberattack", "cyberattacks", "password", "passkey",
    ], [r"\bcve-\d{4}-\d+"]),
    ("Funding", "💰", [
        "startup", "startups", "raises", "raised", "funding", "valuation", "valued",
        "series a", "series b", "series c", "series d", "seed round", "venture",
        "vc", "vcs", "ipo", "unicorn", "acquires", "acquire", "acquired",
        "acquisition", "buyout", "investors", "investment", "invests",
    ], [r"\$\d[\d.,]*\s?(?:k|m|b|bn|million|billion)\b"]),
    ("Crypto", "🪙", [
        "bitcoin", "ethereum", "crypto", "cryptocurrency", "blockchain", "stablecoin",
        "stablecoins", "nft", "nfts", "defi", "solana", "coinbase", "binance",
    ], []),
    ("Policy", "⚖️", [
        "law", "laws", "lawsuit", "lawsuits", "sues", "sued", "court", "regulation",
        "regulations", "regulator", "regulators", "ban", "bans", "banned", "antitrust",
        "ftc", "fcc", "doj", "eu", "gdpr", "congress", "senate", "tariff", "tariffs",
        "export controls", "copyright", "fined", "fines", "legislation", "government",
    ], []),
    ("Hardware", "🔌", [
        "chip", "chips", "semiconductor", "semiconductors", "cpu", "gpu", "tsmc",
        "nvidia", "intel", "amd", "qualcomm", "arm", "iphone", "ipad", "macbook",
        "laptop", "smartphone", "battery", "batteries", "processor",
        "ram", "ssd", "hardware", "raspberry pi", "robot", "robots", "robotics",
        "drone", "drones", "wearable", "headset",
    ], []),
    ("Science", "🔬", [
        "nasa", "spacex", "space", "rocket", "satellite", "satellites", "quantum",
        "physics", "biology", "climate", "fusion", "telescope", "mars", "moon",
        "astronomy", "dna", "genome", "vaccine", "scientists", "researchers",
    ], []),
    ("Dev", "💻", [
        "show hn", "open source", "open-source", "github", "gitlab", "rust", "python",
        "javascript", "typescript", "linux", "kernel", "api", "sdk", "framework",
        "compiler", "database", "sql", "postgres", "postgresql", "sqlite",
        "kubernetes", "docker", "devops", "programming", "developer", "developers",
        "golang", "java", "c++", "llvm", "npm", "pypi",
    ], []),
    ("BigTech", "🏢", [
        "apple", "google", "alphabet", "microsoft", "meta", "facebook", "instagram",
        "whatsapp", "amazon", "aws", "netflix", "tesla", "youtube",
    ], []),
]

DEFAULT = ("General", "💡")


def _compile(words, regex):
    parts = [rf"\b{re.escape(w)}\b" for w in words] + list(regex)
    return re.compile("|".join(parts), re.IGNORECASE)


_COMPILED = [(tag, emoji, _compile(words, regex)) for tag, emoji, words, regex in RULES]


def classify(title: str) -> list[tuple[str, str]]:
    """Return up to MAX_TAGS (tag, emoji) pairs for a headline."""
    found = [(tag, emoji) for tag, emoji, rx in _COMPILED if rx.search(title)]
    return found[: config.MAX_TAGS] or [DEFAULT]


def format_tags(title: str) -> str:
    """e.g. '🤖 #AI · 💰 #Funding' (hashtags are tappable in Telegram)."""
    return " · ".join(f"{emoji} #{tag}" for tag, emoji in classify(title))
