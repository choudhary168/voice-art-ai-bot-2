import pytest
from backend.config import Settings


def test_default_config():
    cfg = Settings(
        gemini_model="gemini-3.8-live",
        voice_name="Puck",
        input_sample_rate=16000,
        output_sample_rate=24000,
        cors_origins=["http://localhost:5173"]
    )
    assert cfg.gemini_model == "gemini-3.8-live"
    assert cfg.voice_name == "Puck"
    assert cfg.input_sample_rate == 16000
    assert cfg.output_sample_rate == 24000
    assert "http://localhost:5173" in cfg.cors_origins_list


def test_cors_origins_parsing():
    cfg = Settings(cors_origins="http://example.com, https://app.example.com")
    assert cfg.cors_origins_list == ["http://example.com", "https://app.example.com"]
