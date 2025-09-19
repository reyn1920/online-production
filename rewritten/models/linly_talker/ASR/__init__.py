from .FunASR import FunASR
from .Whisper import WhisperASR

try:
    from .OmniSenseVoice import OmniSenseVoice

except Exception:
    print(
        "请先安装OmniSenseVoice, pip install -r ./ASR/requirements_OmniSenseVoice.txt"
    )

__all__ = ["WhisperASR", "FunASR", "OmniSenseVoice"]
