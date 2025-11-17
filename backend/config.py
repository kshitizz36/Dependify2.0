"""
Configuration management for Dependify backend.
Loads environment variables and provides centralized access.
"""
import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for managing environment variables."""

    # Groq API
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

    # GitHub
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    GITHUB_CLIENT_ID: str = os.getenv("GITHUB_CLIENT_ID", "")
    GITHUB_CLIENT_SECRET: str = os.getenv("GITHUB_CLIENT_SECRET", "")

    # Anthropic (optional)
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # Server Configuration
    PORT: int = int(os.getenv("PORT", "5001"))
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")

    # API Security
    API_SECRET_KEY: str = os.getenv("API_SECRET_KEY", "")

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))
    RATE_LIMIT_PER_HOUR: int = int(os.getenv("RATE_LIMIT_PER_HOUR", "100"))

    # CORS allowed origins
    @staticmethod
    def get_allowed_origins() -> list:
        """Get CORS allowed origins."""
        frontend_url = Config.FRONTEND_URL
        origins = [frontend_url]

        # Add localhost for development
        if "localhost" not in frontend_url and "127.0.0.1" not in frontend_url:
            origins.extend([
                "http://localhost:3000",
                "http://127.0.0.1:3000"
            ])

        return origins

    @staticmethod
    def validate() -> tuple[bool, list[str]]:
        """
        Validate that all required environment variables are set.
        Returns (is_valid, list_of_missing_vars)
        """
        required_vars = {
            "GROQ_API_KEY": Config.GROQ_API_KEY,
            "SUPABASE_URL": Config.SUPABASE_URL,
            "SUPABASE_KEY": Config.SUPABASE_KEY,
            "GITHUB_TOKEN": Config.GITHUB_TOKEN,
            "API_SECRET_KEY": Config.API_SECRET_KEY,
        }

        missing = [name for name, value in required_vars.items() if not value]

        return (len(missing) == 0, missing)

# Validate configuration on import
is_valid, missing_vars = Config.validate()
if not is_valid:
    print(f"⚠️  WARNING: Missing required environment variables: {', '.join(missing_vars)}")
    print(f"Please create a .env file based on .env.example and fill in the required values.")
