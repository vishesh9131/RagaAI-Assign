"""language_agent.py
Provides LanguageAgent capable of summarizing and explaining text.
Primary path uses Mistral AI Nemo model. If no API key or internet, falls back to 
a lightweight local transformers pipeline (DistilBART).
"""
from __future__ import annotations

import os
from typing import Optional, List, Dict

# Prevent transformers from attempting to import TensorFlow / Keras (avoids Keras 3 incompat error)
os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
os.environ.setdefault("TRANSFORMERS_NO_JAX", "1")

from transformers import pipeline, Pipeline

# Try importing Mistral AI client
try:
    from mistralai import Mistral
except ImportError:
    Mistral = None  # type: ignore


def _has_mistral_key() -> bool:
    return bool(os.getenv("MISTRAL_API_KEY"))


class LanguageAgent:
    """Agent to summarise and explain text blocks using Mistral AI or local model."""

    def __init__(self, model_name: str = "open-mistral-nemo", api_key: str = None):
        self.model_name = model_name
        # Set the API key from parameter or environment variable
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY") or "NxdIH9V8xm8eldEGZrKvC1M1ziS1jHal"
        # "NxdIH9V8xm8eldEGZrKvC1M1ziS1jHal"
        self.client, self.backend = self._init_client()
        
        # Initialize local fallback model
        self.local_model = None

    # ------------------------------------------------------------------
    # Initialisation helpers
    # ------------------------------------------------------------------
    def _init_client(self):
        """Attempt to initialise Mistral AI client; fall back to local pipeline."""
        # Always initialize local model for fallback
        print("[LanguageAgent] Initializing local fallback model...")
        try:
            self.local_model = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6", framework="pt")
            print("[LanguageAgent] Local DistilBART model loaded successfully.")
        except Exception as e:
            # Attempt small t5 model if distilbart fails
            print(f"[LanguageAgent] DistilBART load failed ({e}). Trying t5-small summarizer.")
            try:
                self.local_model = pipeline("summarization", model="t5-small", framework="pt")
                print("[LanguageAgent] Local T5-small model loaded successfully.")
            except Exception as e2:
                print(f"[LanguageAgent] T5-small also failed ({e2}). No local fallback available.")
                self.local_model = None
        
        if Mistral and self.api_key:
            try:
                client = Mistral(api_key=self.api_key)
                # Test the connection with a simple request
                print("[LanguageAgent] Successfully initialized Mistral AI client.")
                return client, "mistral"
            except Exception as e:
                print(f"[LanguageAgent] Failed to initialise Mistral AI client: {e}. Falling back to local summariser.")

        # Local fallback – transformers summarisation pipeline
        print("[LanguageAgent] Using local transformers summarisation pipeline as fallback.")
        if self.local_model is None:
            # If we couldn't initialize any local model above, try one more time
            try:
                self.local_model = pipeline("summarization", model="t5-small", framework="pt")
            except Exception as e:
                print(f"[LanguageAgent] Final attempt to load local model failed: {e}")
                self.local_model = None
        
        return self.local_model, "local"

    def _call_mistral(self, prompt: str, max_tokens: int = 512) -> str:
        """Make a call to Mistral AI API."""
        try:
            response = self.client.chat.complete(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=max_tokens,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[LanguageAgent] Mistral API call failed: {e}")
            raise

    # ------------------------------------------------------------------
    # Core public methods
    # ------------------------------------------------------------------
    def summarize(self, text: str, max_words: int = 150) -> str:
        text = text.strip()
        if not text:
            return ""
            
        if self.backend == "mistral":
            prompt = f"""Summarize the following text in a concise paragraph (maximum {max_words} words):

{text}

CONCISE SUMMARY:"""
            try:
                result = self._call_mistral(prompt, max_tokens=200)
                return result
            except Exception as e:
                print(f"[LanguageAgent] Mistral summarization failed: {e}. Falling back to local model.")
                # Fall back to local model
                if self.local_model:
                    max_length = int(max_words * 1.3)
                    summary = self.local_model(text, max_length=max_length, min_length=20, do_sample=False)
                    return summary[0]["summary_text"].strip()
                else:
                    return "Unable to summarize due to API limitations and missing local model."
        else:
            # transformers pipeline expects max_length tokens, approximate tokens ~ words*1.3
            max_length = int(max_words * 1.3)
            summary = self.client(text, max_length=max_length, min_length=20, do_sample=False)
            return summary[0]["summary_text"].strip()

    def explain(self, text: str, target_audience: str = "non-expert") -> str:
        text = text.strip()
        if not text:
            return ""
            
        if self.backend == "mistral":
            prompt = f"""Explain the following text to a {target_audience} in simple, clear language (maximum 200 words):

{text}

EXPLANATION:"""
            try:
                result = self._call_mistral(prompt, max_tokens=300)
                return result
            except Exception as e:
                print(f"[LanguageAgent] Mistral explanation failed: {e}. Falling back to local model.")
                # Fall back to local model
                if self.local_model:
                    try:
                        summary = self.local_model(text, max_length=200, min_length=30, do_sample=False)
                        return f"Explanation for {target_audience}: {summary[0]['summary_text'].strip()}"
                    except Exception as fallback_error:
                        print(f"[LanguageAgent] Local model fallback also failed: {fallback_error}")
                        return f"Explanation for {target_audience}: Error occurred during both API and local processing."
                else:
                    return f"Explanation for {target_audience}: Unable to process due to API limitations and missing local model."
        else:
            # crude fallback: summarizer followed by simple prefix
            summary = self.client(text, max_length=200, min_length=30, do_sample=False)
            return f"Explanation for {target_audience}: {summary[0]['summary_text'].strip()}"


# Quick CLI test
if __name__ == "__main__":
    agent = LanguageAgent()
    sample_text = (
        "Mistral AI is a French artificial intelligence company founded in 2023. The company focuses on "
        "developing open-source and commercial large language models. Their models are designed to be "
        "efficient and capable, offering alternatives to other major language models in the market."
    )
    print("--- SUMMARY ---")
    print(agent.summarize(sample_text))
    print("\n--- EXPLANATION ---")
    print(agent.explain(sample_text)) 