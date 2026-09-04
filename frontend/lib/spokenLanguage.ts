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

export function readStoredFormat(): "lesson" | "reel" {
  if (typeof window === "undefined") return "lesson";
  try {
    return window.localStorage.getItem(FORMAT_KEY) === "reel" ? "reel" : "lesson";
  } catch {
    return "lesson";
  }
}

export function storeFormat(value: "lesson" | "reel") {
  try {
    window.localStorage.setItem(FORMAT_KEY, value);
  } catch {
    /* ignore */
  }
}
