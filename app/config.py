import os
from typing import Optional

class Config:
    def __init__(self):
        # Modal settings
        self.modal_token: Optional[str] = os.getenv("MODAL_TOKEN")
        self.modal_project: Optional[str] = os.getenv("MODAL_PROJECT")

        # Hyperbolic settings
        self.hyperbolic_api_key: Optional[str] = os.getenv("HYPERBOLIC_API_KEY")
        self.hyperbolic_endpoint: str = os.getenv("HYPERBOLIC_ENDPOINT", "https://api.hyperbolic.xyz/v1")

        # Blaxel settings
        self.blaxel_api_key: Optional[str] = os.getenv("BLAXEL_API_KEY")
        self.blaxel_endpoint: str = os.getenv("BLAXEL_ENDPOINT", "https://api.blaxel.ai/v1")

        # LLM settings
        self.sambanova_api_key: Optional[str] = os.getenv("SAMBANOVA_API_KEY")
        self.sambanova_endpoint: str = os.getenv("SAMBANOVA_ENDPOINT", "https://api.sambanova.ai/v1")
        self.hf_token: Optional[str] = os.getenv("HF_TOKEN")
        self.hf_model: str = os.getenv("HF_MODEL", "microsoft/DialoGPT-medium")

        # App settings
        self.debug: bool = os.getenv("DEBUG", "false").lower() == "true"
        self.host: str = os.getenv("HOST", "0.0.0.0")
        self.port: int = int(os.getenv("PORT", "7860"))

    def is_modal_available(self) -> bool:
        return bool(self.modal_token and self.modal_project)

    def is_hyperbolic_available(self) -> bool:
        return bool(self.hyperbolic_api_key)

    def is_blaxel_available(self) -> bool:
        return bool(self.blaxel_api_key)

    def is_sambanova_available(self) -> bool:
        return bool(self.sambanova_api_key)

    def is_hf_available(self) -> bool:
        return bool(self.hf_token)

    def get_llm_config(self) -> dict:
        if self.is_sambanova_available():
            return {
                "provider": "sambanova",
                "api_key": self.sambanova_api_key,
                "endpoint": self.sambanova_endpoint
            }
        elif self.is_hf_available():
            return {
                "provider": "hf",
                "token": self.hf_token,
                "model": self.hf_model
            }
        else:
            return {"provider": "simulation"}

# Global config instance
config = Config()