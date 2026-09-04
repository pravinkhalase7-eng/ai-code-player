export const LANGUAGES = [
  { id: "java", label: "Java", topic: "Explain Java for loop" },
  { id: "python", label: "Python", topic: "Explain Python for loop" },
  { id: "javascript", label: "JavaScript", topic: "Explain JavaScript for loop" },
] as const;

export type LessonLanguage = (typeof LANGUAGES)[number]["id"];

export function sourceFilename(language: string): string {
  const name = language.toLowerCase();
  if (name === "python") return "main.py";
  if (name === "javascript" || name === "js") return "main.js";
  return "Main.java";
}

export function runCommand(language: string): string {
  const name = language.toLowerCase();
  if (name === "python") return "python3 main.py";
  if (name === "javascript" || name === "js") return "node main.js";
  return "javac Main.java && java Main";
}

export function defaultCode(language: string): string {
  const name = language.toLowerCase();
  if (name === "python") {
    return 'for i in range(5):\n    print(i)\n';
  }
  if (name === "javascript" || name === "js") {
    return "for (let i = 0; i < 5; i++) {\n  console.log(i);\n}\n";
  }
  return "public class Main {\n    public static void main(String[] args) {\n        System.out.println(\"Hello\");\n    }\n}\n";
}

export function topicForLanguage(language: string, current: string): string {
  const match = LANGUAGES.find((item) => item.id === language);
  const known = LANGUAGES.some((item) => item.topic === current);
  if (known && match) return match.topic;
  return current;
}
