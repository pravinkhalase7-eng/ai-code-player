from app.services.locale import candidate_voices, normalize_spoken_language, spoken_locale, strip_duration_copy, tts_voice_for
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
