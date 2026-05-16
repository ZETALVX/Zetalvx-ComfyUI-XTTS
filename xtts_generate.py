import argparse
import glob
import os
import subprocess
import sys
from datetime import datetime


XTTS_BIN = "/home/theboss/ai/xtts-test/.venv/bin/tts"
MODEL_NAME = "tts_models/multilingual/multi-dataset/xtts_v2"


def main():
    parser = argparse.ArgumentParser(description="External XTTS v2 wrapper for ComfyUI")

    parser.add_argument("--text", required=True)
    parser.add_argument("--language", default="en")
    parser.add_argument("--out", required=True)
    parser.add_argument("--cuda", action="store_true")

    parser.add_argument("--mode", choices=["clone", "builtin"], default="clone")
    parser.add_argument("--voice_dir", default="")
    parser.add_argument("--speaker_idx", default="Andrew Chipper")

    args = parser.parse_args()

    out_path = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    cmd = [
        XTTS_BIN,
        "--model_name", MODEL_NAME,
        "--text", args.text,
        "--language_idx", args.language,
        "--out_path", out_path,
    ]

    if args.mode == "clone":
        voice_dir = os.path.abspath(args.voice_dir)

        if not os.path.isdir(voice_dir):
            print(f"ERROR: voice_dir not found: {voice_dir}", file=sys.stderr)
            sys.exit(1)

        speaker_files = sorted(glob.glob(os.path.join(voice_dir, "*.wav")))

        if not speaker_files:
            print(f"ERROR: no .wav files found in {voice_dir}", file=sys.stderr)
            sys.exit(1)

        cmd += ["--speaker_wav", *speaker_files]

    else:
        cmd += ["--speaker_idx", args.speaker_idx]

    if args.cuda:
        cmd.append("--use_cuda")

    print("XTTS wrapper started")
    print("Time:", datetime.now().isoformat())
    print("Mode:", args.mode)
    print("Language:", args.language)
    print("Speaker:", args.speaker_idx)
    print("Voice dir:", args.voice_dir)
    print("Output:", out_path)
    print("CUDA:", args.cuda)
    print("Command:")
    print(" ".join(f'"{x}"' if " " in x else x for x in cmd))

    result = subprocess.run(cmd)

    if result.returncode != 0:
        print(f"ERROR: XTTS failed with code {result.returncode}", file=sys.stderr)
        sys.exit(result.returncode)

    print(f"OK: generated {out_path}")


if __name__ == "__main__":
    main()