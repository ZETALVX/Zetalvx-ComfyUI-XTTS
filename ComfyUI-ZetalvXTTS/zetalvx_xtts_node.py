import os
import random
import shutil
import subprocess
import tempfile
import uuid

import torch
import torchaudio


XTTS_PYTHON = "/home/zetalvx/ai/xtts-test/.venv/bin/python"
XTTS_SCRIPT = "/home/zetalvx/ai/xtts-test/xtts_generate.py"
DEFAULT_VOICE_DIR = "/home/zetalvx/ai/xtts-test/samples_clean"
COMFY_OUTPUT_DIR = "/home/zetalvx/ai/ComfyUI/output"


MALE_SPEAKERS = [
    "Andrew Chipper",
    "Badr Odhiambo",
    "Dionisio Schuyler",
    "Royston Min",
    "Viktor Eka",
    "Abrahan Mack",
    "Adde Michal",
    "Baldur Sanjin",
    "Craig Gutsy",
    "Damien Black",
    "Gilberto Mathias",
    "Ilkin Urbano",
    "Kazuhiko Atallah",
    "Ludvig Milivoj",
    "Suad Qasim",
    "Torcull Diarmuid",
    "Viktor Menelaos",
    "Zacharie Aimilios",
    "Filip Traverse",
    "Damjan Chapman",
    "Wulf Carlevaro",
    "Aaron Dreschner",
    "Kumar Dahl",
    "Eugenio Mataracı",
    "Ferran Simen",
    "Xavier Hayasaka",
    "Luis Moray",
    "Marcos Rudaski",
]

FEMALE_SPEAKERS = [
    "Claribel Dervla",
    "Daisy Studious",
    "Gracie Wise",
    "Tammie Ema",
    "Alison Dietlinde",
    "Ana Florence",
    "Annmarie Nele",
    "Asya Anara",
    "Brenda Stern",
    "Gitta Nikolina",
    "Henriette Usha",
    "Sofia Hellen",
    "Tammy Grit",
    "Tanja Adelina",
    "Vjollca Johnnie",
    "Nova Hogarth",
    "Maja Ruoho",
    "Uta Obando",
    "Lidiya Szekeres",
    "Chandra MacFarland",
    "Szofi Granger",
    "Camilla Holmström",
    "Lilya Stainthorpe",
    "Zofija Kendrick",
    "Narelle Moon",
    "Barbora MacLean",
    "Alexandra Hisakawa",
    "Alma María",
    "Rosemary Okafor",
]

ALL_SPEAKERS = MALE_SPEAKERS + FEMALE_SPEAKERS


def _sanitize_filename(name: str) -> str:
    safe = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in name)
    return safe.strip("_") or "zetalvx_xtts_output"


def _save_comfy_audio_to_wav(audio_reference, out_wav_path: str):
    """
    ComfyUI AUDIO format is usually:
    {
        "waveform": torch.Tensor with shape [batch, channels, samples] or [channels, samples],
        "sample_rate": int
    }
    XTTS needs a real wav file, so we save a temporary reference.wav.
    """
    if not isinstance(audio_reference, dict):
        raise ValueError("audio_reference is not a valid ComfyUI AUDIO object")

    if "waveform" not in audio_reference or "sample_rate" not in audio_reference:
        raise ValueError("audio_reference must contain waveform and sample_rate")

    waveform = audio_reference["waveform"]
    sample_rate = int(audio_reference["sample_rate"])

    if not torch.is_tensor(waveform):
        waveform = torch.tensor(waveform)

    waveform = waveform.detach().cpu().float()

    # Shape handling:
    # [batch, channels, samples] -> [channels, samples]
    # [samples] -> [1, samples]
    if waveform.ndim == 3:
        waveform = waveform[0]
    elif waveform.ndim == 1:
        waveform = waveform.unsqueeze(0)

    # Ensure [channels, samples]
    if waveform.ndim != 2:
        raise ValueError(f"Unsupported waveform shape: {tuple(waveform.shape)}")

    os.makedirs(os.path.dirname(out_wav_path), exist_ok=True)
    torchaudio.save(out_wav_path, waveform, sample_rate)


def _load_wav_as_comfy_audio(wav_path: str):
    waveform, sample_rate = torchaudio.load(wav_path)

    # ComfyUI AUDIO usually expects [batch, channels, samples]
    if waveform.ndim == 2:
        waveform = waveform.unsqueeze(0)

    return {
        "waveform": waveform,
        "sample_rate": sample_rate,
    }


class ZetalvXTTSGenerate:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "voice_mode": (["clone", "builtin_selected", "male_random", "female_random"], {
                    "default": "builtin_selected"
                }),
                "text": ("STRING", {
                    "multiline": True,
                    "default": "Hello, this is a test generated with XTTS inside ComfyUI"
                }),
                "language": ([
                    "en", "it", "fr", "es", "de", "pt", "pl", "tr",
                    "ru", "nl", "cs", "ar", "zh-cn", "ja", "ko", "hu", "hi"
                ], {
                    "default": "en"
                }),
                "speaker_idx": (ALL_SPEAKERS, {
                    "default": "Andrew Chipper"
                }),
                "voice_dir": ("STRING", {
                    "default": DEFAULT_VOICE_DIR
                }),
                "output_name": ("STRING", {
                    "default": "zetalvx_xtts_output"
                }),
                "use_cuda": ("BOOLEAN", {
                    "default": True
                }),
            },
            "optional": {
                "audio_reference": ("AUDIO",),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "AUDIO")
    RETURN_NAMES = ("audio_path", "selected_speaker", "audio")
    FUNCTION = "generate"
    CATEGORY = "ZetaLvx/Audio"
    OUTPUT_NODE = True

    def generate(
        self,
        voice_mode,
        text,
        language,
        speaker_idx,
        voice_dir,
        output_name,
        use_cuda,
        audio_reference=None
    ):
        if not os.path.exists(XTTS_PYTHON):
            raise FileNotFoundError(f"XTTS python not found: {XTTS_PYTHON}")

        if not os.path.exists(XTTS_SCRIPT):
            raise FileNotFoundError(f"XTTS script not found: {XTTS_SCRIPT}")

        safe_name = _sanitize_filename(output_name)
        unique_id = uuid.uuid4().hex[:8]
        out_path = os.path.join(COMFY_OUTPUT_DIR, f"{safe_name}_{unique_id}.wav")

        temp_dir = None

        try:
            if voice_mode == "clone":
                xtts_mode = "clone"
                selected_speaker = "cloned_voice"

                if audio_reference is not None:
                    temp_dir = tempfile.mkdtemp(prefix="zetalvx_xtts_ref_")
                    temp_ref_wav = os.path.join(temp_dir, "reference.wav")
                    _save_comfy_audio_to_wav(audio_reference, temp_ref_wav)
                    effective_voice_dir = temp_dir
                    print(f"[ZetalvxXTTS] Using connected AUDIO reference: {temp_ref_wav}")

                else:
                    effective_voice_dir = voice_dir

                    if not os.path.isdir(effective_voice_dir):
                        raise FileNotFoundError(f"Voice directory not found: {effective_voice_dir}")

                    wav_files = [
                        f for f in os.listdir(effective_voice_dir)
                        if f.lower().endswith(".wav")
                    ]

                    if not wav_files:
                        raise FileNotFoundError(f"No wav files found in voice_dir: {effective_voice_dir}")

                    print(f"[ZetalvxXTTS] Using voice_dir wav references: {effective_voice_dir}")

            elif voice_mode == "male_random":
                xtts_mode = "builtin"
                selected_speaker = random.choice(MALE_SPEAKERS)
                effective_voice_dir = ""

            elif voice_mode == "female_random":
                xtts_mode = "builtin"
                selected_speaker = random.choice(FEMALE_SPEAKERS)
                effective_voice_dir = ""

            else:
                xtts_mode = "builtin"
                selected_speaker = speaker_idx
                effective_voice_dir = ""

            cmd = [
                XTTS_PYTHON,
                XTTS_SCRIPT,
                "--mode", xtts_mode,
                "--text", text,
                "--language", language,
                "--out", out_path,
            ]

            if xtts_mode == "clone":
                cmd += ["--voice_dir", effective_voice_dir]
            else:
                cmd += ["--speaker_idx", selected_speaker]

            if use_cuda:
                cmd.append("--cuda")

            print("[ZetalvxXTTS] Running:")
            print(" ".join(f'"{x}"' if " " in x else x for x in cmd))
            print(f"[ZetalvxXTTS] voice_mode: {voice_mode}")
            print(f"[ZetalvxXTTS] selected_speaker: {selected_speaker}")

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            print("[ZetalvxXTTS STDOUT]")
            print(result.stdout)

            if result.returncode != 0:
                print("[ZetalvxXTTS STDERR]")
                print(result.stderr)
                raise RuntimeError(f"XTTS generation failed:\n{result.stderr}")

            if not os.path.exists(out_path):
                raise FileNotFoundError(f"XTTS finished but output file was not found: {out_path}")

            audio_out = _load_wav_as_comfy_audio(out_path)

            return (out_path, selected_speaker, audio_out)

        finally:
            if temp_dir and os.path.isdir(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)


NODE_CLASS_MAPPINGS = {
    "ZetalvXTTSGenerate": ZetalvXTTSGenerate
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ZetalvXTTSGenerate": "Zetalvx XTTS Generate Audio"
}