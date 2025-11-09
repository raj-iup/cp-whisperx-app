# Frequently Asked Questions

**Common questions and answers**

## General

**Q: How long does processing take?**
A: ~10 hours for a 2.5-hour movie with GPU, much longer with CPU.

**Q: What GPU do I need?**
A: Apple M1/M2/M3 (MPS) or NVIDIA with 8GB+ VRAM recommended.

**Q: Can I run without GPU?**
A: Yes, but processing will be much slower (150+ hours for a movie).

## Troubleshooting

**Q: Why does it show CPU when I have a GPU?**
A: Check `out/hardware_cache.json`. Delete it and re-run bootstrap.

**Q: Models fail to download?**
A: Verify HuggingFace token in `config/secrets.json`.

_More FAQs to be added_

Return to [Documentation Index](INDEX.md)
