"""
llama-cpp-python back-end for the Ojas LLM client.

Loads a GGUF model file via llama-cpp-python, enforces one-generation-at-a-
time thread safety, and exposes the LLMClient interface.

Usage
-----
    from backend.app.llm.llama_cpp_client import LlamaCppClient
    client = LlamaCppClient()          # loads model from settings
    text   = client.generate("Hello")
    for tok in client.stream("Hello"):
        print(tok, end="", flush=True)
"""

import logging
import threading
import time
from pathlib import Path
from typing import Iterator

from backend.app.llm.client import LLMClient
from backend.app.config import get_settings

logger = logging.getLogger(__name__)

# Project root — used to resolve relative model paths
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class LlamaCppClient(LLMClient):
    """
    Concrete LLMClient that wraps llama-cpp-python's Llama class.

    Thread safety
    -------------
    llama.cpp is not thread-safe for simultaneous inferences.  A single
    threading.Lock ensures only one call to generate() or stream() runs at a
    time.  Callers that arrive while the lock is held will block until the
    current generation finishes.
    """

    def __init__(self) -> None:
        self._llm = None                  # llama_cpp.Llama instance
        self._lock = threading.Lock()     # one inference at a time
        self._model_name: str = ""
        self._model_path_used: str = ""
        self._load_time_seconds: float = 0.0
        self._last_error: str | None = None
        self._context_size: int = 0

        self._load_model()

    # ------------------------------------------------------------------
    # Model loading
    # ------------------------------------------------------------------

    def _load_model(self) -> None:
        """
        Load the GGUF model from the path specified in settings.
        On any error: log the exception, set _last_error, leave _llm = None.
        This method never raises so the app can start even without a model.
        """
        settings = get_settings()
        model_path_str = settings.model_path

        # Resolve relative paths against the project root
        model_path = Path(model_path_str)
        if not model_path.is_absolute():
            model_path = _PROJECT_ROOT / model_path

        self._model_path_used = str(model_path)
        self._model_name = model_path.name

        if not model_path.exists():
            self._last_error = f"Model file not found: {model_path}"
            logger.error(self._last_error)
            return

        try:
            # Import here so the rest of the module can be imported even if
            # llama-cpp-python is not installed (surfaces a clear ImportError).
            from llama_cpp import Llama  # type: ignore[import]

            logger.info("Loading model: %s", model_path)
            t0 = time.perf_counter()

            self._llm = Llama(
                model_path=str(model_path),
                n_ctx=settings.n_ctx,
                n_threads=settings.n_threads,
                n_batch=settings.n_batch,
                n_gpu_layers=settings.n_gpu_layers,
                verbose=False,          # suppress llama.cpp C-level logs
            )

            self._load_time_seconds = time.perf_counter() - t0
            self._context_size = settings.n_ctx
            self._last_error = None

            logger.info(
                "Model loaded in %.2f s  (ctx=%d, threads=%d, gpu_layers=%d)",
                self._load_time_seconds,
                settings.n_ctx,
                settings.n_threads,
                settings.n_gpu_layers,
            )

        except ImportError:
            self._last_error = (
                "llama-cpp-python is not installed. "
                "Run: pip install llama-cpp-python"
            )
            logger.error(self._last_error)

        except Exception as exc:
            self._last_error = f"{type(exc).__name__}: {exc}"
            logger.exception("Failed to load model from %s", model_path)

    # ------------------------------------------------------------------
    # LLMClient interface
    # ------------------------------------------------------------------

    def is_loaded(self) -> bool:
        return self._llm is not None

    def get_info(self) -> dict:
        return {
            "backend": "llama_cpp",
            "model_name": self._model_name,
            "model_path": self._model_path_used,
            "load_time_seconds": round(self._load_time_seconds, 3),
            "context_size": self._context_size,
            "last_error": self._last_error,
        }

    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.2,
        stop: list[str] | None = None,
    ) -> str:
        """
        Blocking text generation.  Acquires the inference lock, calls
        create_chat_completion, and returns the assistant reply as a string.
        Returns an empty string if the model is not loaded or an error occurs.
        """
        if not self.is_loaded():
            logger.warning("generate() called but model is not loaded.")
            return ""

        stop = stop or []

        with self._lock:
            try:
                response = self._llm.create_chat_completion(  # type: ignore[union-attr]
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stop=stop,
                    stream=False,
                )
                content: str = response["choices"][0]["message"]["content"] or ""
                return content.strip()

            except Exception as exc:
                self._last_error = f"{type(exc).__name__}: {exc}"
                logger.exception("generate() failed")
                return ""

    def stream(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.2,
        stop: list[str] | None = None,
    ) -> Iterator[str]:
        """
        Streaming token generator.  Acquires the inference lock and yields
        individual token strings as the model produces them.

        Note: the lock is held for the ENTIRE duration of streaming.  This
        means a second caller will block until the stream is exhausted or the
        generator is garbage-collected.  For Ojas's single-user, single-task
        design this is the correct behaviour.
        """
        if not self.is_loaded():
            logger.warning("stream() called but model is not loaded.")
            return

        stop = stop or []

        with self._lock:
            try:
                response_iter = self._llm.create_chat_completion(  # type: ignore[union-attr]
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stop=stop,
                    stream=True,
                )

                for chunk in response_iter:
                    delta = chunk["choices"][0].get("delta", {})
                    token = delta.get("content", "")
                    if token:
                        yield token

            except Exception as exc:
                self._last_error = f"{type(exc).__name__}: {exc}"
                logger.exception("stream() failed")
                return

    # ------------------------------------------------------------------
    # Override generate_with_system to use the native chat API
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
        Use llama.cpp's native chat-completion format with separate system
        and user message roles instead of a manually formatted string.
        """
        if not self.is_loaded():
            logger.warning("generate_with_system() called but model is not loaded.")
            return ""

        stop = stop or []

        with self._lock:
            try:
                response = self._llm.create_chat_completion(  # type: ignore[union-attr]
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user",   "content": user},
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stop=stop,
                    stream=False,
                )
                content: str = response["choices"][0]["message"]["content"] or ""
                return content.strip()

            except Exception as exc:
                self._last_error = f"{type(exc).__name__}: {exc}"
                logger.exception("generate_with_system() failed")
                return ""

