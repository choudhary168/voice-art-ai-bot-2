import os
from pathlib import Path
from typing import List, Optional, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    """Application settings with environment validation."""
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Gemini API Settings
    gemini_api_key: Optional[str] = Field(default="", validation_alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-3.8-live", validation_alias="GEMINI_MODEL")
    voice_name: str = Field(default="Puck", validation_alias="VOICE_NAME")

    # Server Settings
    host: str = Field(default="0.0.0.0", validation_alias="HOST")
    port: int = Field(default=8000, validation_alias="PORT")
    cors_origins: Union[str, List[str]] = Field(
        default="http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173",
        validation_alias="CORS_ORIGINS"
    )

    # Audio Settings (Gemini Live standard: input 16kHz PCM, output 24kHz PCM)
    input_sample_rate: int = Field(default=16000, validation_alias="INPUT_SAMPLE_RATE")
    output_sample_rate: int = Field(default=24000, validation_alias="OUTPUT_SAMPLE_RATE")
    audio_chunk_duration_ms: int = Field(default=100, validation_alias="AUDIO_CHUNK_DURATION_MS")

    # Security & Performance Limits
    max_ws_message_size_bytes: int = Field(default=5242880, validation_alias="MAX_WS_MESSAGE_SIZE_BYTES")
    diagnostic_mode: bool = Field(default=True, validation_alias="DIAGNOSTIC_MODE")

    # System Instruction
    default_system_instruction: str = Field(
        default=(
            "You are a helpful, responsive, and articulate real-time AI voice assistant powered by Gemini Live. "
            "Keep your answers concise, natural, and conversational by default. "
            "You can understand and converse fluently in English, Hindi, and Hinglish based on the user's preference and tone. "
            "Never invent personal information about the user. "
            "When answering, speak directly without unnecessary filler."
        ),
        validation_alias="DEFAULT_SYSTEM_INSTRUCTION"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        if isinstance(self.cors_origins, list):
            return self.cors_origins
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def has_api_key(self) -> bool:
        return bool(self.gemini_api_key and self.gemini_api_key.strip() and not self.gemini_api_key.startswith("your_"))


settings = Settings()
