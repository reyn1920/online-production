import torch
from lhotse.utils import Pathlike
from omnisense.models import OmniSenseVoiceSmall


class OmniSenseVoice:
    def __init__(self, quantize) -> None:
        self.model = OmniSenseVoiceSmall(
            "iic/SenseVoiceSmall",
            quantize=quantize,
            device_id="0" if torch.cuda.is_available() else "-1",
# BRACKET_SURGEON: disabled
#         )

    def transcribe(
        self,
        audio_path: Pathlike,
        language: str = "auto",
        textnorm: str = "woitn",  # ["withitn", "woitn"]
        timestamps: bool = False,
# BRACKET_SURGEON: disabled
#     ):
        result = self.model.transcribe(
            audio_path,
            language=language,
            textnorm=textnorm,
            batch_size=8,
            timestamps=timestamps,
# BRACKET_SURGEON: disabled
#         )
        return result[0].text


if __name__ == "__main__":
    model = OmniSenseVoice(quantize=False)
    text = model.transcribe("./audio.wav")
    print(text)