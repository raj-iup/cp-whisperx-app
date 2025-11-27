# IndicTrans2-based Hindi→English SRT Translation – Implementation Plan (Apple M1 Pro)

## 0. Goal

Set up a **fully local** pipeline on macOS (Apple M1 Pro) to:

1. Install IndicTrans2 and dependencies with GPU (MPS) support.
2. Verify Hindi → English translation works.
3. Translate a `.srt` file from Hindi to English while preserving timestamps and formatting.

---

## 1. Environment Setup

### 1.1 Create and activate a virtual environment

In Terminal:

```bash
cd /path/to/your/project

python3 -m venv indictrans2-env
source indictrans2-env/bin/activate

Upgrade pip:

pip install --upgrade pip


⸻

2. Install Dependencies

2.1 Install PyTorch (with MPS support) and Transformers

pip install "torch>=2.1" "transformers>=4.44" sentencepiece sacremoses

2.2 Install SRT helper library

pip install srt


⸻

3. Verify PyTorch + MPS on M1 Pro

Create a file check_mps.py:

import torch

print("PyTorch version:", torch.__version__)
print("MPS available:", torch.backends.mps.is_available())
print("MPS built:", torch.backends.mps.is_built())

Run:

python check_mps.py

Expected:
	•	MPS available: True
	•	MPS built: True

If False, PyTorch is not correctly installed for Apple Silicon; reinstall PyTorch with a recent version.

⸻

4. Install & Test IndicTrans2 Model

This plan uses the IndicTrans2 Indic→English 1B model from Hugging Face:
	•	Model name: ai4bharat/indictrans2-indic-en-1B
	•	Source language code: hin_Deva (Hindi, Devanagari)
	•	Target language code: eng_Latn (English, Latin)

4.1 Create a test script: test_indictrans2.py

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

# Choose device: "mps" for Apple GPU, fallback to "cpu"
device = "mps" if torch.backends.mps.is_available() else "cpu"
print("Using device:", device)

model_name = "ai4bharat/indictrans2-indic-en-1B"

print("Loading tokenizer and model...")
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name, trust_remote_code=True)
model.to(device)
model.eval()

def translate_hi_en(text: str) -> str:
    """
    Translate Hindi (Devanagari) text to English using IndicTrans2.
    """
    src = "hin_Deva"   # Hindi
    tgt = "eng_Latn"   # English

    # Target-tag prompt format used by IndicTrans2
    prompt = f"<2{tgt}> {text.strip()}"
    encoded = tokenizer(prompt, return_tensors="pt", truncation=True)
    encoded = {k: v.to(device) for k, v in encoded.items()}

    with torch.no_grad():
        output = model.generate(
            **encoded,
            max_new_tokens=128,
            num_beams=4,
        )

    decoded = tokenizer.batch_decode(output, skip_special_tokens=True)[0]
    return decoded.strip()

if __name__ == "__main__":
    sample = "मेरा नाम राज है और मैं ह्यूस्टन में रहता हूँ।"
    print("Source:", sample)
    print("Translation:", translate_hi_en(sample))

4.2 Run the test

python test_indictrans2.py

Expected:
	•	Console prints Using device: mps (or cpu if MPS not available).
	•	A reasonable English translation of the sample Hindi sentence.

If this works, IndicTrans2 is correctly installed and running.

⸻

5. SRT Translation Pipeline

5.1 Place input SRT file

In the project folder, place your Hindi subtitle file as:

input_hi.srt

(You can change the name later; just update the config in the script.)

5.2 Create translate_srt_indictrans2.py

import srt
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

# --------- Configuration ---------
MODEL_NAME = "ai4bharat/indictrans2-indic-en-1B"
SRC_LANG = "hin_Deva"  # Hindi (Devanagari)
TGT_LANG = "eng_Latn"  # English (Latin)
INPUT_SRT = "input_hi.srt"
OUTPUT_SRT = "output_en.srt"
# ----------------------------------

# Select device (M1 Pro → "mps" if available)
device = "mps" if torch.backends.mps.is_available() else "cpu"
print("Using device:", device)

print("Loading tokenizer and model...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME, trust_remote_code=True)
model.to(device)
model.eval()

def translate_hi_en(text: str) -> str:
    """
    Translate a single line of Hindi text to English using IndicTrans2.
    Empty/whitespace-only lines are returned unchanged.
    """
    text = text.strip()
    if not text:
        return text

    prompt = f"<2{TGT_LANG}> {text}"
    encoded = tokenizer(prompt, return_tensors="pt", truncation=True)
    encoded = {k: v.to(device) for k, v in encoded.items()}

    with torch.no_grad():
        output = model.generate(
            **encoded,
            max_new_tokens=128,
            num_beams=4,   # can reduce to 1 for faster, slightly worse translations
        )

    translation = tokenizer.batch_decode(output, skip_special_tokens=True)[0]
    return translation.strip()

def main():
    print(f"Reading SRT: {INPUT_SRT}")
    with open(INPUT_SRT, "r", encoding="utf-8") as f:
        subtitles = list(srt.parse(f.read()))

    print(f"Total subtitles found: {len(subtitles)}")

    for i, sub in enumerate(subtitles, start=1):
        original = sub.content

        # Preserve multi-line structure inside a single subtitle block
        lines = original.split("\n")
        translated_lines = []

        for line in lines:
            if line.strip():
                translated_lines.append(translate_hi_en(line))
            else:
                # Preserve empty lines
                translated_lines.append("")

        sub.content = "\n".join(translated_lines)

        # Progress logging
        if i % 50 == 0 or i == len(subtitles):
            print(f"Translated {i}/{len(subtitles)} subtitles...")

    print(f"Writing translated SRT to: {OUTPUT_SRT}")
    with open(OUTPUT_SRT, "w", encoding="utf-8") as f:
        f.write(srt.compose(subtitles))

    print("Done.")

if __name__ == "__main__":
    main()


⸻

6. Run the SRT Translator

From the project folder (with the virtual environment activated):

python translate_srt_indictrans2.py

Results:
	•	Input: input_hi.srt (Hindi subtitles)
	•	Output: output_en.srt (English subtitles, timestamps preserved)

⸻

7. Performance Tuning (Optional)

If translation is too slow or memory-heavy:
	1.	Reduce beam search width (faster, slightly lower quality):

output = model.generate(
    **encoded,
    max_new_tokens=128,
    num_beams=1,  # instead of 4
)


	2.	Use CPU only (if MPS causes issues):
	•	Force device to "cpu":

device = "cpu"


	3.	Batch processing (advanced):
	•	Collect multiple subtitle lines in a list and run them through the model together.
	•	This can significantly speed up translation, but requires refactoring translate_hi_en to accept a list.

⸻

8. Handling Hinglish (Optional Refinement)

If subtitles are a mix of Hindi and English:
	•	You can add a simple heuristic:
	•	If a line is already mostly ASCII/English, skip translation and keep as-is.
	•	Example (conceptual):

import re

def is_mostly_english(text: str, threshold: float = 0.7) -> bool:
    if not text.strip():
        return True
    ascii_chars = sum(c.isascii() for c in text)
    return ascii_chars / max(len(text), 1) >= threshold

Then in the SRT loop:

if is_mostly_english(line):
    translated_lines.append(line)
else:
    translated_lines.append(translate_hi_en(line))



⸻

9. File Structure Summary

Example project layout:

project-root/
├─ indictrans2-env/           # virtual environment (auto-created)
├─ input_hi.srt               # your Hindi subtitles
├─ output_en.srt              # generated English subtitles (output)
├─ check_mps.py               # optional, for verifying MPS
├─ test_indictrans2.py        # model test script
└─ translate_srt_indictrans2.py  # main translation script


⸻

10. Next Steps / Extensions

Possible future enhancements:
	•	Add a simple CLI interface with argparse:
	•	python translate_srt_indictrans2.py --input file.srt --output file_en.srt
	•	Bundle into a small desktop app (e.g., using tkinter or a simple web UI with Flask).
	•	Add logging to a file for tracking translation progress and errors.
	•	Add support for other Indic languages by changing SRC_LANG and the prompts.

