import base64
import math
import struct
from typing import Optional, Tuple


class AudioService:
    """Utilities for audio encoding, decoding, validation, and framing."""

    @staticmethod
    def decode_base64_pcm(base64_data: str) -> bytes:
        """Decode base64 string to raw PCM bytes."""
        try:
            return base64.b64decode(base64_data)
        except Exception as e:
            raise ValueError(f"Invalid base64 audio data: {e}")

    @staticmethod
    def encode_pcm_base64(pcm_bytes: bytes) -> str:
        """Encode raw PCM bytes to base64 string."""
        return base64.b64encode(pcm_bytes).decode("ascii")

    @staticmethod
    def calculate_pcm_duration_ms(byte_count: int, sample_rate: int = 16000, bits_per_sample: int = 16, channels: int = 1) -> float:
        """Calculate duration of PCM audio in milliseconds."""
        bytes_per_sample = bits_per_sample // 8
        bytes_per_second = sample_rate * bytes_per_sample * channels
        if bytes_per_second == 0:
            return 0.0
        return (byte_count / bytes_per_second) * 1000.0

    @staticmethod
    def calculate_rms(pcm_bytes: bytes) -> float:
        """Calculate Root Mean Square (RMS) volume of 16-bit mono PCM."""
        if len(pcm_bytes) < 2:
            return 0.0
        # Unpack 16-bit signed integers (little endian)
        count = len(pcm_bytes) // 2
        format_str = f"<{count}h"
        samples = struct.unpack(format_str, pcm_bytes[:count * 2])
        sum_squares = sum(s * s for s in samples)
        mean_square = sum_squares / count
        return math.sqrt(mean_square)

    @staticmethod
    def resample_linear(pcm_bytes: bytes, in_rate: int, out_rate: int) -> bytes:
        """Linear resampling for 16-bit mono PCM if needed when browser provides different sample rate."""
        if in_rate == out_rate or len(pcm_bytes) < 2:
            return pcm_bytes

        num_in_samples = len(pcm_bytes) // 2
        in_samples = struct.unpack(f"<{num_in_samples}h", pcm_bytes)
        num_out_samples = int(num_in_samples * out_rate / in_rate)

        if num_out_samples == 0:
            return b""

        out_samples = []
        scale = in_rate / out_rate
        for i in range(num_out_samples):
            orig_idx = i * scale
            idx0 = int(orig_idx)
            idx1 = min(idx0 + 1, num_in_samples - 1)
            frac = orig_idx - idx0
            val = int(in_samples[idx0] * (1.0 - frac) + in_samples[idx1] * frac)
            val = max(-32768, min(32767, val))
            out_samples.append(val)

        return struct.pack(f"<{len(out_samples)}h", *out_samples)


audio_service = AudioService()
