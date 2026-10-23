import struct
import pytest
from backend.services.audio import audio_service


def test_encode_decode_pcm():
    # 100 samples of 16-bit PCM
    original_samples = list(range(100))
    raw_bytes = struct.pack(f"<{len(original_samples)}h", *original_samples)

    b64 = audio_service.encode_pcm_base64(raw_bytes)
    assert isinstance(b64, str)

    decoded = audio_service.decode_base64_pcm(b64)
    assert decoded == raw_bytes


def test_duration_calculation():
    # 16000 samples * 2 bytes = 32000 bytes = 1 second (1000ms)
    duration = audio_service.calculate_pcm_duration_ms(32000, sample_rate=16000)
    assert duration == 1000.0


def test_rms_calculation():
    # Silence
    silence = b"\x00" * 3200
    assert audio_service.calculate_rms(silence) == 0.0

    # Sine wave or loud values
    loud = struct.pack("<5h", 1000, -1000, 1000, -1000, 1000)
    rms = audio_service.calculate_rms(loud)
    assert rms == 1000.0


def test_resampling():
    samples = [1000, 2000, 3000, 4000]
    raw = struct.pack("<4h", *samples)
    resampled = audio_service.resample_linear(raw, in_rate=32000, out_rate=16000)
    assert len(resampled) == 4  # 2 samples * 2 bytes
