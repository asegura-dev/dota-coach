"""Loads and validates the application configuration from the .env file."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Read the .env file (if present) and load its values into the environment.
load_dotenv()


@dataclass(frozen=True)
class Config:
    """Immutable application configuration."""

    auth_token: str
    host: str
    port: int

    @classmethod
    def load(cls) -> "Config":
        """Build the configuration from environment variables."""
        token = os.getenv("GSI_AUTH_TOKEN")
        if not token:
            raise RuntimeError(
                "GSI_AUTH_TOKEN is missing. "
                "Copy .env.example to .env and define the token."
            )

        return cls(
            auth_token=token,
            host=os.getenv("SERVER_HOST", "127.0.0.1"),
            port=int(os.getenv("SERVER_PORT", "4000")),
        )