"""
Abstract LLM client interface for Ojas.

All LLM back-ends (llama.cpp, future OpenAI-compatible servers, etc.) must
implement this interface so the rest of the codebase stays back-end agnostic.
"""

from abc import ABC, abstractmethod
from typing import Iterator


class LLMClient(ABC):
    """
    Abstract base class for language-model clients.

    Every concrete implementation must provide:
    - generate()   — blocking full-response generation
    - stream()     — token-by-token streaming generator
    - is_loaded()  — health probe (False means the model is unavailable)
    - get_info()   — metadata dict for the health endpoint
    """

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    @abstractmethod
    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.2,
        stop: list[str] | None = None,
    ) -> str:
        """
        Generate a completion for *prompt* and return the full response text.

        Parameters
        ----------
        prompt:      The user / system prompt string.
        max_tokens:  Maximum number of tokens to generate.
        temperature: Sampling temperature (0 = deterministic, 1 = creative).
        stop:        Optional list of stop sequences.

        Returns
        -------
        The generated text as a plain string (stripped of leading/trailing
        whitespace).  Returns an empty string on error.
        """

    @abstractmethod
    def stream(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.2,
        stop: list[str] | None = None,
    ) -> Iterator[str]:
        """
        Stream the completion for *prompt*, yielding one token string at a
        time as they are produced by the model.

        Parameters
        ----------
        Same as generate().

        Yields
        ------
        Individual token strings.  The caller is responsible for joining them.
        """

    @abstractmethod
    def is_loaded(self) -> bool:
        """
        Return True if the model is loaded and ready to generate.
        Return False if the model failed to load or has not been initialised.
        This method must never raise — it is used as a health probe.
        """

    @abstractmethod
    def get_info(self) -> dict:
        """
        Return a metadata dict for the health / status endpoint.

        Expected keys (all optional but recommended):
          model_name       (str)   — filename or display name of the model
          model_path       (str)   — resolved path used at load time
          load_time_seconds (float) — seconds taken to load the model
          context_size     (int)   — context window in tokens
          last_error       (str | None) — last exception message, if any
          backend          (str)   — e.g. "llama_cpp"
        """

    # ------------------------------------------------------------------
    # Convenience helpers (concrete, non-abstract)
    # ------------------------------------------------------------------

    def generate_with_system(
        self,
        system: str,
        user: str,
        max_tokens: int = 512,
        temperature: float = 0.2,
        stop: list[str] | None = None,
    ) -> str:
        """
        Convenience wrapper: format a system + user message pair into a
        simple prompt string and call generate().

        Concrete implementations that use a native chat API (e.g.
        create_chat_completion) can override this to pass the messages
        directly instead of building a string.
        """
        prompt = f"<|system|>\n{system}\n<|user|>\n{user}\n<|assistant|>\n"
        return self.generate(prompt, max_tokens=max_tokens,
                             temperature=temperature, stop=stop)

