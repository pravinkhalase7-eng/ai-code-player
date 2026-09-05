from app.services.locale import candidate_voices, normalize_spoken_language, spoken_locale, speech_text, strip_duration_copy, tts_voice_for
from app.services.tts.google_tts import resolve_cloud_voice


def test_hindi_aliases_normalize() -> None:
    assert normalize_spoken_language("hindi") == "hi"
    assert normalize_spoken_language("हिन्दी") == "hi"
    assert normalize_spoken_language("hi-IN") == "hi"
    assert normalize_spoken_language("en-US") == "en"
    assert normalize_spoken_language("unknown") == "en"


def test_strip_duration_copy_removes_30s_branding() -> None:
    assert strip_duration_copy("30s: Java For Loop") == "Java For Loop"
    assert "30" not in strip_duration_copy("Stop scrolling. Java for loops in 30 seconds.")
    assert "30s" not in strip_duration_copy("This 30s short teaches await")


def test_strip_scroll_hook_keeps_the_question() -> None:
    from app.services.locale import hook_narration, pick_reel_hook, strip_scroll_hook

    spoken = strip_scroll_hook("स्क्रॉल करना बंद करो! Java में दो classes को एक साथ extend क्यों नहीं कर सकते?")
    assert "स्क्रॉल" not in spoken
    assert "Java में दो classes" in spoken
    assert "Stop scrolling" not in strip_scroll_hook("Stop scrolling. Why can't Java extend two classes?")
    hook = pick_reel_hook("hi", "Diamond Problem", "les_hooks")
    assert "स्क्रॉल" not in hook
    assert "Diamond Problem" in hook
    cleaned = hook_narration(
        "स्क्रॉल करना बंद करो! Java में multiple inheritance क्यों नहीं होता?",
        "hi",
        "multiple inheritance",
        "les_x",
    )
    assert cleaned.startswith("Java में")


def test_speech_text_strips_backticks() -> None:
    spoken = speech_text("लाइन 1 में `abstract class Car` बेस स्ट्रक्चर बनाती है।")
    assert "`" not in spoken
    assert "abstract class Car" in spoken
    assert spoken.startswith("लाइन 1 में abstract class Car")
    assert speech_text("Use **this** line") == "Use this line"


def test_teachable_narration_rejects_pasted_java() -> None:
    from app.services.locale import looks_like_source_code, teachable_narration

    pasted = (
        "Interface A { default void show() { System.out.println(\"A\"); } }\n"
        "interface B { default void show() { System.out.println(\"B\"); } }\n"
        "public class Main implements A, B { public void show() { A.super.show(); } }"
    )
    assert looks_like_source_code(pasted)
    spoken = teachable_narration(pasted, "hi")
    assert "{" not in spoken
    assert "प्रोग्राम" in spoken


def test_hindi_voice_stays_in_hindi() -> None:
    voice = tts_voice_for("hi")
    candidates = candidate_voices(voice)
    assert voice.startswith("hi-IN-")
    assert all(name.startswith("hi-IN-") for name in candidates)
    assert not any(name.startswith("en-") for name in candidates)
    name, language = resolve_cloud_voice(voice)
    assert language == "hi-IN"
    assert name == voice


def test_hindi_english_copy_needs_localization() -> None:
    from types import SimpleNamespace

    from app.services.locale import needs_localization

    english = SimpleNamespace(
        title="Java For Loop",
        objectives=["Understand a for loop"],
        concepts=[],
        scenes=[
            SimpleNamespace(
                narration="Stop scrolling. Here is a Java for loop in 30 seconds.",
                segments=[],
                bullets=[],
                takeaways=[],
                question="",
                options=[],
                explanation="",
            )
        ],
    )
    hindi = SimpleNamespace(
        title="जावा फॉर लूप",
        objectives=["लूप समझो"],
        concepts=[],
        scenes=[
            SimpleNamespace(
                narration="रुक जाओ। Java का for loop i को शून्य से शुरू करता है और हर बार एक बढ़ाता है।",
                segments=[],
                bullets=[],
                takeaways=[],
                question="",
                options=[],
                explanation="",
            )
        ],
    )
    assert needs_localization(english, "hi")
    assert not needs_localization(hindi, "hi")
    assert not needs_localization(english, "en")


def test_speech_text_speaks_generics() -> None:
    assert "greater" not in speech_text("Create an ArrayList<String> of names.").lower()
    assert "less" not in speech_text("Create an ArrayList<String> of names.").lower()
    assert speech_text("Use List<String> here") == "Use List of String here"
    assert speech_text("Map<String, Integer> ages") == "Map of String to Integer ages"
    assert speech_text("Python list[str] values") == "Python list of str values"
    assert speech_text("dict[str, int] ages") == "dict of str to int ages"
    assert speech_text("Promise<string> result") == "Promise of string result"
    assert speech_text("String[] names") == "String array names"
    assert "equals" in speech_text("if count == 0")
    # numeric indexes stay as brackets content is spoken normally without of-rewrite
    assert "items[0]" in speech_text("Read items[0] next") or "items" in speech_text("Read items[0] next")
