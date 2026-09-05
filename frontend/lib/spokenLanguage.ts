export const SPOKEN_LANGUAGES = [
  { id: "en", label: "English" },
  { id: "hi", label: "हिन्दी" },
  { id: "ta", label: "தமிழ்" },
  { id: "te", label: "తెలుగు" },
  { id: "mr", label: "मराठी" },
  { id: "es", label: "Español" },
] as const;

export type SpokenLanguage = (typeof SPOKEN_LANGUAGES)[number]["id"];

const STORAGE_KEY = "spoken_language";

export function isSpokenLanguage(value: string): value is SpokenLanguage {
  return SPOKEN_LANGUAGES.some((item) => item.id === value);
}

export function readStoredSpokenLanguage(): SpokenLanguage {
  if (typeof window === "undefined") return "en";
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY) || "";
    return isSpokenLanguage(stored) ? stored : "en";
  } catch {
    return "en";
  }
}

export function storeSpokenLanguage(value: SpokenLanguage) {
  try {
    window.localStorage.setItem(STORAGE_KEY, value);
  } catch {
    /* ignore quota / private mode */
  }
}

const FORMAT_KEY = "lesson_format";

export type MakeMode = "lesson" | "reel" | "info";

export function readStoredFormat(): MakeMode {
  if (typeof window === "undefined") return "lesson";
  try {
    const stored = window.localStorage.getItem(FORMAT_KEY);
    if (stored === "reel" || stored === "info") return stored;
    return "lesson";
  } catch {
    return "lesson";
  }
}

export function storeFormat(value: MakeMode) {
  try {
    window.localStorage.setItem(FORMAT_KEY, value);
  } catch {
    /* ignore */
  }
}

export const REEL_DURATIONS = [
  { seconds: 30, label: "30 sec" },
  { seconds: 60, label: "60 sec" },
  { seconds: 90, label: "90 sec" },
  { seconds: 120, label: "2 min" },
] as const;

export type ReelSeconds = (typeof REEL_DURATIONS)[number]["seconds"];

const REEL_SECONDS_KEY = "reel_seconds";

export function isReelSeconds(value: number): value is ReelSeconds {
  return REEL_DURATIONS.some((item) => item.seconds === value);
}

export function readStoredReelSeconds(): ReelSeconds {
  if (typeof window === "undefined") return 30;
  try {
    const stored = Number(window.localStorage.getItem(REEL_SECONDS_KEY) || "");
    return isReelSeconds(stored) ? stored : 30;
  } catch {
    return 30;
  }
}

export function storeReelSeconds(value: ReelSeconds) {
  try {
    window.localStorage.setItem(REEL_SECONDS_KEY, String(value));
  } catch {
    /* ignore */
  }
}
