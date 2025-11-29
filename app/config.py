"""
Cloud Ops Sentinel Configuration
Environment variables and API availability checks for all sponsor integrations
"""

import os
from typing import Optional, Dict, List


class Config:
    """Configuration manager for Cloud Ops Sentinel."""
    
    def __init__(self):
        # Modal settings (Requirements 9.1)
        self.modal_token: Optional[str] = os.getenv("MODAL_API_TOKEN") or os.getenv("MODAL_TOKEN")
        self.modal_project: Optional[str] = os.getenv("MODAL_APP_NAME") or os.getenv("MODAL_PROJECT")

        # Hyperbolic settings (Requirements 9.2)
        self.hyperbolic_api_key: Optional[str] = os.getenv("HYPERBOLIC_API_KEY")
        self.hyperbolic_endpoint: str = os.getenv("HYPERBOLIC_ENDPOINT", "https://api.hyperbolic.xyz/v1")

        # Blaxel settings (Requirements 9.3)
        self.blaxel_api_key: Optional[str] = os.getenv("BLAXEL_API_KEY")
        self.blaxel_endpoint: str = os.getenv("BLAXEL_ENDPOINT", "https://api.blaxel.ai/v1")

        # SambaNova LLM settings (Requirements 9.5)
        self.sambanova_api_key: Optional[str] = os.getenv("SAMBANOVA_API_KEY")
        self.sambanova_endpoint: str = os.getenv("SAMBANOVA_ENDPOINT", "https://api.sambanova.ai/v1")
        
        # HuggingFace settings
        self.hf_token: Optional[str] = os.getenv("HF_API_KEY") or os.getenv("HF_TOKEN")
        self.hf_model: str = os.getenv("HF_MODEL", "microsoft/DialoGPT-medium")

        # App settings
        self.debug: bool = os.getenv("DEBUG", "false").lower() == "true"
        self.host: str = os.getenv("HOST", "0.0.0.0")
        self.port: int = int(os.getenv("PORT", "7860"))
        self.use_blaxel: bool = os.getenv("USE_BLAXEL", "false").lower() == "true"

    def is_modal_available(self) -> bool:
        """Check if Modal is configured."""
        return bool(self.modal_token)

    def is_hyperbolic_available(self) -> bool:
        """Check if Hyperbolic is configured."""
        return bool(self.hyperbolic_api_key)

    def is_blaxel_available(self) -> bool:
        """Check if Blaxel is configured."""
        return bool(self.blaxel_api_key)

    def is_sambanova_available(self) -> bool:
        """Check if SambaNova is configured."""
        return bool(self.sambanova_api_key)

    def is_hf_available(self) -> bool:
        """Check if HuggingFace is configured."""
        return bool(self.hf_token)

    def get_llm_config(self) -> Dict[str, str]:
        """Get LLM configuration with fallback chain."""
        if self.is_sambanova_available():
            return {
                "provider": "sambanova",
                "api_key": self.sambanova_api_key,
                "endpoint": self.sambanova_endpoint
            }
        elif self.is_hf_available():
            return {
                "provider": "huggingface",
                "token": self.hf_token,
                "model": self.hf_model
            }
        else:
            return {"provider": "simulation"}

    def get_compute_backend(self) -> str:
        """Get compute backend for service operations."""
        if self.use_blaxel and self.is_blaxel_available():
            return "blaxel"
        elif self.is_modal_available():
            return "modal"
        else:
            return "simulation"

    def get_available_integrations(self) -> List[str]:
        """Get list of available sponsor integrations."""
        integrations = ["MCP"]  # Always available
        if self.is_modal_available():
            integrations.append("Modal")
        if self.is_hyperbolic_available():
            integrations.append("Hyperbolic")
        if self.is_blaxel_available():
            integrations.append("Blaxel")
        if self.is_sambanova_available():
            integrations.append("SambaNova")
        if self.is_hf_available():
            integrations.append("HuggingFace")
        return integrations

    def status(self) -> Dict[str, any]:
        """Get configuration status summary."""
        return {
            "modal": self.is_modal_available(),
            "hyperbolic": self.is_hyperbolic_available(),
            "blaxel": self.is_blaxel_available(),
            "sambanova": self.is_sambanova_available(),
            "huggingface": self.is_hf_available(),
            "llm_provider": self.get_llm_config()["provider"],
            "compute_backend": self.get_compute_backend(),
            "available_integrations": self.get_available_integrations(),
            "debug": self.debug,
            "host": self.host,
            "port": self.port
        }


# Global config instance
config = Config()