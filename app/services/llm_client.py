from groq import Groq
from app.config import Config
import logging

logger = logging.getLogger(__name__)

# Single shared client instance
_client = None


def get_client() -> Groq:
    """Return a shared Groq client, initialising it on first call."""
    global _client
    if _client is None:
        _client = Groq(api_key=Config.GROQ_API_KEY)
    return _client


def chat_completion(messages: list, model: str = "llama-3.1-8b-instant",
                    temperature: float = 0.4, max_tokens: int = 2048) -> str | None:
    """
    Send a messages list to the Groq API and return the assistant reply text.

    Args:
        messages    (list): OpenAI-compatible list of {role, content} dicts.
        model       (str):  Groq model ID.
        temperature (float): Sampling temperature.
        max_tokens  (int):  Maximum tokens in the response.

    Returns:
        str | None: Assistant message text, or None on failure.
    """
    try:
        client = get_client()
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Groq API error: {e}")
        return None
