# Zetalvx-ComfyUI-XTTS

Local XTTS v2 integration for ComfyUI with:

- Voice cloning
- Built-in XTTS speakers
- Random male/female speaker selection
- Direct ComfyUI AUDIO support
- Local generation
- CUDA support
- External isolated Python environment

This project allows XTTS v2 to be used inside ComfyUI workflows through a custom node and an external wrapper script.

---

# Features

## XTTS v2 Integration
- Local XTTS v2 generation
- Multilingual support
- CUDA support
- External venv isolation

## Voice Cloning
Supports:
- Reference `.wav` files from a folder
- Connected ComfyUI `AUDIO` input

## Built-in Speakers
Supports:
- Specific speaker selection
- Random male speaker
- Random female speaker

## ComfyUI Audio Output
Outputs:
- Generated audio path
- Selected speaker
- ComfyUI `AUDIO` object

---

# Repository Structure

```text
Zetalvx-ComfyUI-XTTS/
├── README.md
├── LICENSE
├── scripts/
│   └── xtts_generate.py
├── custom_nodes/
│   └── ComfyUI-Zetalvx-XTTS/
│       ├── __init__.py
│       └── zetalvx_xtts_node.py
└── examples/
    └── workflows
```

---

# Requirements

- Ubuntu Linux
- Python 3.11
- CUDA-compatible GPU recommended
- ComfyUI installed

---

# XTTS Environment Setup

## Create environment

```bash
mkdir -p /path/xtts-test
cd /path/xtts-test

python3.11 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip setuptools wheel
```

---

## Install PyTorch

Example CUDA 12.6 build:

```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu126
```

---

## Install Coqui TTS

```bash
pip install coqui-tts
```

If audio codec support is required:

```bash
pip install "coqui-tts[codec]"
```

---

## Transformers compatibility

If required:

```bash
pip install "transformers>=4.57,<5" --upgrade
```

---

# Test XTTS

## List speakers

```bash
tts --model_name tts_models/multilingual/multi-dataset/xtts_v2 --list_speaker_idxs
```

---

## Built-in speaker example

```bash
tts --model_name tts_models/multilingual/multi-dataset/xtts_v2 \
  --text "Hello, this is a test with XTTS." \
  --speaker_idx "Andrew Chipper" \
  --language_idx en \
  --use_cuda \
  --out_path xtts_test.wav
```

---

# Voice Cloning Setup

## Create reference folder

```bash
mkdir -p /path/xtts-test/samples_clean
```

Put reference `.wav` files inside.

---

## Voice cloning example

```bash
tts --model_name tts_models/multilingual/multi-dataset/xtts_v2 \
  --text "Hello, this is a cloned voice test." \
  --speaker_wav /path/xtts-test/samples_clean/*.wav \
  --language_idx en \
  --use_cuda \
  --out_path xtts_clone.wav
```

---

# External Wrapper Script

Create:

```bash
/path/xtts-test/xtts_generate.py
```

This wrapper:
- isolates XTTS from ComfyUI
- allows external execution
- supports cloning and built-in speakers
- keeps environments separated

---

# Wrapper Script Test

## Built-in speaker

```bash
/path/xtts-test/.venv/bin/python \
/path/xtts-test/xtts_generate.py \
  --mode builtin \
  --speaker_idx "Andrew Chipper" \
  --text "Hello, this is an XTTS wrapper test." \
  --language en \
  --out /path/ComfyUI/output/xtts_test.wav \
  --cuda
```

---

## Voice cloning

```bash
/path/xtts-test/.venv/bin/python \
/path/xtts-test/xtts_generate.py \
  --mode clone \
  --voice_dir /path//xtts-test/samples_clean \
  --text "Hello, this is a cloned XTTS voice." \
  --language en \
  --out /path/ComfyUI/output/xtts_clone.wav \
  --cuda
```

---

# ComfyUI Installation

## Create custom node folder

```bash
cd /path/ComfyUI/custom_nodes

mkdir -p ComfyUI-Zetalvx-XTTS
cd ComfyUI-Zetalvx-XTTS
```

Copy:

```text
__init__.py
zetalvx_xtts_node.py
```

into the folder.

---

# Restart ComfyUI

After restarting ComfyUI, search for:

```text
Zetalvx XTTS Generate Audio
```

Category:

```text
ZetaLvx/Audio
```

---

# Node Features

## Voice Modes

### clone
Uses:
- voice_dir
- or connected AUDIO reference

### builtin_selected
Uses selected XTTS speaker.

### male_random
Random male speaker.

### female_random
Random female speaker.

---

# AUDIO Input Support

The node supports direct ComfyUI AUDIO input.

Connected audio is automatically:
- converted to WAV
- stored temporarily
- used as XTTS cloning reference

---

# Outputs

| Output | Description |
|---|---|
| audio_path | Generated WAV file path |
| selected_speaker | Speaker used |
| audio | ComfyUI AUDIO output |

---

# Notes

## XTTS Licensing

XTTS v2 model weights are licensed separately by Coqui.

Please check the official XTTS v2 license before commercial usage.

This repository only contains:
- wrapper scripts
- integration code
- ComfyUI custom nodes

---

# Credits

## XTTS v2
https://huggingface.co/coqui/XTTS-v2

## Coqui TTS
https://github.com/coqui-ai/TTS

## ComfyUI
https://github.com/comfyanonymous/ComfyUI
