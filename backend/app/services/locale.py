from __future__ import annotations

import re
from dataclasses import dataclass

_DURATION_COPY = re.compile(
    r"^\s*30s:\s*|"
    r"\b(?:in\s+)?30(?:\s*|-)?seconds?\b|"
    r"\b30s\b|"
    r"30\s*(?:सेकंड|सेकंद|வினாடிகளில்|வினாடி|సెకన్లలో|సెకన్|segundos?)\b|"
    r"३०\s*(?:सेकंड|सेकंद)|"
    r"सिर्फ\s*30|"
    r"फक्त\s*३०|"
    r"en\s*30\s*segundos",
    re.IGNORECASE,
)


def strip_duration_copy(text: str) -> str:
    cleaned = _DURATION_COPY.sub(" ", text or "")
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    cleaned = re.sub(r"\s+([,.!?।])", r"\1", cleaned).strip(" :-–—")
    if not cleaned:
        return (text or "").strip()
    return cleaned[0].upper() + cleaned[1:] if cleaned[0].islower() else cleaned

_SPANISH_HINT = re.compile(
    r"[áéíóúñ¿¡]|\b(el|la|los|las|un|una|para|esto|este|código|bucle|aquí)\b",
    re.IGNORECASE,
)
_SCRIPT_RANGES: dict[str, tuple[int, int]] = {
    "hi": (0x0900, 0x097F),
    "mr": (0x0900, 0x097F),
    "ta": (0x0B80, 0x0BFF),
    "te": (0x0C00, 0x0C7F),
}


@dataclass(frozen=True)
class SpokenLocale:
    id: str
    label: str
    native_label: str
    english_name: str
    language_code: str
    voice: str
    voice_fallbacks: tuple[str, ...]
    reel_hook: str
    reel_end: str
    compile_error: str


LOCALES: tuple[SpokenLocale, ...] = (
    SpokenLocale(
        id="en",
        label="English",
        native_label="English",
        english_name="English",
        language_code="en-US",
        voice="en-US-Chirp3-HD-Aoede",
        voice_fallbacks=(
            "en-US-Chirp3-HD-Kore",
            "en-US-Chirp3-HD-Leda",
            "en-US-Journey-F",
            "en-US-Studio-O",
        ),
        reel_hook="Stop scrolling. Here's {topic}.",
        reel_end="That's the trick. Save this and try it in your own file.",
        compile_error="Compilation Error. Let's read the compiler message together.",
    ),
    SpokenLocale(
        id="hi",
        label="Hindi",
        native_label="हिन्दी",
        english_name="Hindi",
        language_code="hi-IN",
        voice="hi-IN-Chirp3-HD-Aoede",
        voice_fallbacks=(
            "hi-IN-Chirp3-HD-Kore",
            "hi-IN-Chirp3-HD-Leda",
            "hi-IN-Neural2-A",
            "hi-IN-Wavenet-A",
        ),
        reel_hook="रुक जाओ। {topic} की असली ट्रिक ये है।",
        reel_end="यही ट्रिक है। सेव करो और अपनी फाइल में ट्राई करो।",
        compile_error="कंपाइल नहीं हुआ। चलो टर्मिनल में कंपाइलर का संदेश साथ में पढ़ते हैं।",
    ),
    SpokenLocale(
        id="ta",
        label="Tamil",
        native_label="தமிழ்",
        english_name="Tamil",
        language_code="ta-IN",
        voice="ta-IN-Chirp3-HD-Aoede",
        voice_fallbacks=("ta-IN-Chirp3-HD-Kore", "ta-IN-Neural2-A", "ta-IN-Wavenet-A"),
        reel_hook="நிறுத்து. {topic} — இதோ டிரிக்.",
        reel_end="இதுதான் டிரிக். சேமித்து உங்கள் கோப்பில் முயற்சி செய்யுங்கள்.",
        compile_error="தொகுப்பு பிழை. கம்பைலர் செய்தியை டெர்மினலில் சேர்ந்து படிப்போம்.",
    ),
    SpokenLocale(
        id="te",
        label="Telugu",
        native_label="తెలుగు",
        english_name="Telugu",
        language_code="te-IN",
        voice="te-IN-Chirp3-HD-Aoede",
        voice_fallbacks=("te-IN-Chirp3-HD-Kore", "te-IN-Standard-A", "te-IN-Standard-B"),
        reel_hook="ఆగు. {topic} — ఇదే ట్రిక్.",
        reel_end="ఇదే ట్రిక్. సేవ్ చేసి మీ ఫైల్‌లో ట్రై చేయండి.",
        compile_error="కంపైల్ కాలేదు. టెర్మినల్‌లో కంపైలర్ మెసేజ్ కలిసి చదుద్దాం.",
    ),
    SpokenLocale(
        id="mr",
        label="Marathi",
        native_label="मराठी",
        english_name="Marathi",
        language_code="mr-IN",
        voice="mr-IN-Chirp3-HD-Aoede",
        voice_fallbacks=("mr-IN-Chirp3-HD-Kore", "mr-IN-Wavenet-A", "mr-IN-Standard-A"),
        reel_hook="थांबा. {topic} ची ट्रिक ही आहे.",
        reel_end="हीच ट्रिक आहे. सेव्ह करा आणि स्वतःच्या फाइलमध्ये ट्राई करा.",
        compile_error="कंपाइल झाले नाही. टर्मिनलमधील कंपाइलर संदेश एकत्र वाचूया.",
    ),
    SpokenLocale(
        id="es",
        label="Spanish",
        native_label="Español",
        english_name="Spanish",
        language_code="es-US",
        voice="es-US-Chirp3-HD-Aoede",
        voice_fallbacks=("es-US-Chirp3-HD-Kore", "es-US-Neural2-A", "es-US-Studio-B"),
        reel_hook="Para. Aquí está el truco de {topic}.",
        reel_end="Ese es el truco. Guárdalo y pruébalo en tu archivo.",
        compile_error="Error de compilación. Leamos juntos el mensaje del compilador.",
    ),
)

_BY_ID = {item.id: item for item in LOCALES}

_ALIASES = {
    "en": "en",
    "eng": "en",
    "english": "en",
    "en-us": "en",
    "en-in": "en",
    "hi": "hi",
    "hin": "hi",
    "hindi": "hi",
    "हिन्दी": "hi",
    "हिंदी": "hi",
    "hi-in": "hi",
    "ta": "ta",
    "tam": "ta",
    "tamil": "ta",
    "தமிழ்": "ta",
    "ta-in": "ta",
    "te": "te",
    "tel": "te",
    "telugu": "te",
    "తెలుగు": "te",
    "te-in": "te",
    "mr": "mr",
    "mar": "mr",
    "marathi": "mr",
    "मराठी": "mr",
    "mr-in": "mr",
    "es": "es",
    "spa": "es",
    "spanish": "es",
    "español": "es",
    "espanol": "es",
    "es-us": "es",
    "es-es": "es",
}


def normalize_spoken_language(value: str | None) -> str:
    raw = (value or "en").strip()
    if not raw:
        return "en"
    key = raw.lower()
    if key in _ALIASES:
        return _ALIASES[key]
    prefix = key.replace("_", "-").split("-")[0]
    return _ALIASES.get(prefix, "en")


def spoken_locale(value: str | None) -> SpokenLocale:
    return _BY_ID[normalize_spoken_language(value)]


def tts_voice_for(value: str | None) -> str:
    return spoken_locale(value).voice


def candidate_voices(voice: str) -> list[str]:
    requested = (voice or "").strip()
    locale = next((item for item in LOCALES if item.voice == requested or requested in item.voice_fallbacks), None)
    if locale is None and requested:
        lang = "-".join(requested.split("-")[:2])
        locale = next((item for item in LOCALES if item.language_code == lang), None)
    if locale is None:
        locale = _BY_ID["en"]
        requested = locale.voice
    names: list[str] = []
    for name in (requested, locale.voice, *locale.voice_fallbacks):
        if name and name not in names:
            names.append(name)
    return names


def spoken_generation_rules(value: str | None) -> str:
    locale = spoken_locale(value)
    if locale.id == "en":
        return (
            "Spoken language: English.\n"
            "Write all teaching copy in English: narration, segments, quiz, bullets, takeaways, greeting, title, objectives."
        )
    sample = {
        "hi": 'Correct Hindi: "रुक जाओ। for loop i को 0 से शुरू करता है।" Invalid: "Stop scrolling. Here is a for loop."',
        "ta": 'Correct Tamil must use தமிழ் script. Invalid: English paragraphs.',
        "te": "Correct Telugu must use తెలుగు script. Invalid: English paragraphs.",
        "mr": 'Correct Marathi: "थांबा. for loop i ला 0 पासून सुरू करतो." Invalid: English paragraphs.',
        "es": 'Correct Spanish: "Para. El for loop empieza i en 0." Invalid: English paragraphs.',
    }.get(locale.id, "")
    return (
        f"CRITICAL: Output language is {locale.english_name} ({locale.native_label}). "
        f"English teaching copy is invalid.\n"
        f"Write ALL teaching copy in {locale.english_name} using {locale.native_label} script: "
        "title, objectives, narration, segments.text, quiz question/options/explanation, bullets, takeaways.\n"
        "Keep source code, keywords, identifiers, filenames, and program output unchanged "
        f"(for, if, System.out.println may appear inside {locale.english_name} sentences).\n"
        f"Byte speaks {locale.english_name}. {sample}"
    )


def teaching_copy(lesson: object) -> str:
    parts: list[str] = [str(getattr(lesson, "title", "") or "")]
    parts.extend(str(item) for item in (getattr(lesson, "objectives", None) or []))
    parts.extend(str(item) for item in (getattr(lesson, "concepts", None) or []))
    for scene in getattr(lesson, "scenes", None) or []:
        parts.append(str(getattr(scene, "narration", "") or ""))
        for segment in getattr(scene, "segments", None) or []:
            parts.append(str(getattr(segment, "text", "") or ""))
        parts.extend(str(item) for item in (getattr(scene, "bullets", None) or []))
        parts.extend(str(item) for item in (getattr(scene, "takeaways", None) or []))
        parts.append(str(getattr(scene, "question", "") or ""))
        parts.extend(str(item) for item in (getattr(scene, "options", None) or []))
        parts.append(str(getattr(scene, "explanation", "") or ""))
    return " ".join(part for part in parts if part)


def uses_spoken_script(text: str, spoken_id: str) -> bool:
    locale_id = normalize_spoken_language(spoken_id)
    if locale_id == "en":
        return True
    if locale_id == "es":
        return bool(_SPANISH_HINT.search(text or ""))
    bounds = _SCRIPT_RANGES.get(locale_id)
    if not bounds:
        return True
    start, end = bounds
    hits = sum(1 for char in text or "" if start <= ord(char) <= end)
    return hits >= 12


def needs_localization(lesson: object, spoken_id: str | None) -> bool:
    locale_id = normalize_spoken_language(spoken_id)
    if locale_id == "en":
        return False
    return not uses_spoken_script(teaching_copy(lesson), locale_id)
