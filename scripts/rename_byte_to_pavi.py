from pathlib import Path
import re

root = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder")

files = {
    root / "frontend/components/tutor/TalkingByteAvatar.tsx": [
        ('aria-label="Byte talking"', 'aria-label="Pavi talking"'),
        ("\n        Byte\n", "\n        Pavi\n"),
    ],
    root / "frontend/components/tutor/TutorAvatar.tsx": [
        (">Byte</p>", ">Pavi</p>"),
    ],
    root / "frontend/components/tutor/ByteAvatar.tsx": [
        ('alt="Byte"', 'alt="Pavi"'),
        (">Byte</p>", ">Pavi</p>"),
    ],
    root / "frontend/lib/reelExport.ts": [
        ('ctx.fillText("BYTE"', 'ctx.fillText("PAVI"'),
    ],
    root / "frontend/remotion/components/TutorAvatar.tsx": [
        (">BYTE</div>", ">PAVI</div>"),
    ],
    root / "frontend/components/player/LessonPlayer.tsx": [
        ("Tap to play Byte\u2019s voice", "Tap to play Pavi\u2019s voice"),
        ("Click to hear Byte \u2014 uses Google Cloud Chirp, not the browser voice", "Click to hear Pavi \u2014 uses Google Cloud Chirp, not the browser voice"),
        ("Preparing Byte\u2019s natural voice\u2026 playback starts as soon as the audio file is ready.", "Preparing Pavi\u2019s natural voice\u2026 playback starts as soon as the audio file is ready."),
        ("Apply Byte\u2019s fix", "Apply Pavi\u2019s fix"),
        ('item.role === "tutor" ? "Byte" : "You"', 'item.role === "tutor" ? "Pavi" : "You"'),
        # ascii apostrophe variants
        ("Tap to play Byte's voice", "Tap to play Pavi's voice"),
        ("Preparing Byte's natural voice", "Preparing Pavi's natural voice"),
        ("Apply Byte's fix", "Apply Pavi's fix"),
    ],
}

for path, pairs in files.items():
    text = path.read_text()
    for old, new in pairs:
        if old in text:
            text = text.replace(old, new)
            print(f"OK {path.name}: {old[:48]!r}")
        else:
            print(f"skip {path.name}: {old[:48]!r}")
    path.write_text(text)

# Verify display labels
for path in files:
    for line in path.read_text().splitlines():
        if re.search(r">\s*Byte\s*<|\"BYTE\"|>BYTE<|>Byte<|\bByte talking\b", line):
            if "TalkingByte" in line or "ByteAvatar" in line or "drawByte" in line:
                continue
            print("REMAINING", path, line.strip())
print("done")
