from backend.config import DEFAULT_LIVE_VOICE, LIVE_VOICE_NAMES, Settings, resolve_live_voice_name
from backend.providers.gemini_live import build_live_connect_config
from backend.schemas.events import SessionStartPayload


def test_voice_allowlist_and_safe_fallback():
    assert len(LIVE_VOICE_NAMES) == 30
    assert "Puck" in LIVE_VOICE_NAMES
    assert "Achird" in LIVE_VOICE_NAMES
    assert resolve_live_voice_name("Sulafat") == "Sulafat"
    assert resolve_live_voice_name("aoede") == DEFAULT_LIVE_VOICE
    assert resolve_live_voice_name("custom-voice") == DEFAULT_LIVE_VOICE
    assert resolve_live_voice_name(None) == DEFAULT_LIVE_VOICE


def test_voice_setting_default_and_environment_values_are_validated():
    assert Settings(_env_file=None).voice_name == DEFAULT_LIVE_VOICE
    assert Settings(voice_name="Aoede").voice_name == "Aoede"
    assert Settings(voice_name="not-a-live-voice").voice_name == DEFAULT_LIVE_VOICE


def test_selected_voice_is_used_in_native_audio_session_config():
    config = build_live_connect_config("Test assistant", "Achird")
    assert config.response_modalities == ["AUDIO"]
    assert config.speech_config.voice_config.prebuilt_voice_config.voice_name == "Achird"

    default_config = build_live_connect_config("Test assistant")
    assert default_config.speech_config.voice_config.prebuilt_voice_config.voice_name == "Puck"


def test_session_start_voice_is_optional_for_old_clients_and_invalid_values_fall_back():
    old_client_payload = SessionStartPayload.model_validate({"system_instruction": "Hello"})
    assert old_client_payload.voice_name is None
    assert SessionStartPayload(voice_name="unsupported").voice_name == DEFAULT_LIVE_VOICE
    assert SessionStartPayload(voice_name="Puck").voice_name == "Puck"
