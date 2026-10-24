export type SyntaxKind = "kw" | "str" | "num" | "cmt" | "fn" | "plain";

const KEYWORDS =
  /\b(and|as|assert|async|await|break|case|catch|class|const|continue|def|default|elif|else|enum|except|export|extends|False|finally|for|from|function|if|implements|import|in|instanceof|int|interface|is|lambda|let|new|None|not|null|or|pass|private|protected|public|return|static|switch|throw|True|try|typeof|undefined|var|void|while|with|yield|boolean|String|System)\b/;

export function tokenizeLine(line: string): { text: string; kind: SyntaxKind }[] {
  if (!line) return [{ text: " ", kind: "plain" }];
  const tokens: { text: string; kind: SyntaxKind }[] = [];
  const re =
    /(\/\/.*$|#.*$|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`|\b\d+(?:\.\d+)?\b|\b[A-Za-z_]\w*(?=\s*\()|\b(?:and|as|assert|async|await|break|case|catch|class|const|continue|def|default|elif|else|enum|except|export|extends|False|finally|for|from|function|if|implements|import|in|instanceof|int|interface|is|lambda|let|new|None|not|null|or|pass|private|protected|public|return|static|switch|throw|True|try|typeof|undefined|var|void|while|with|yield|boolean|String|System)\b)/g;
  let last = 0;
  let match: RegExpExecArray | null;
  while ((match = re.exec(line))) {
    if (match.index > last) tokens.push({ text: line.slice(last, match.index), kind: "plain" });
    const chunk = match[0];
    let kind: SyntaxKind = "plain";
    if (chunk.startsWith("//") || chunk.startsWith("#")) kind = "cmt";
    else if (chunk.startsWith('"') || chunk.startsWith("'") || chunk.startsWith("`")) kind = "str";
    else if (/^\d/.test(chunk)) kind = "num";
    else if (KEYWORDS.test(chunk)) kind = "kw";
    else if (/^\w+$/.test(chunk)) kind = "fn";
    tokens.push({ text: chunk, kind });
    last = match.index + chunk.length;
  }
  if (last < line.length) tokens.push({ text: line.slice(last), kind: "plain" });
  return tokens.length ? tokens : [{ text: line, kind: "plain" }];
}

export function syntaxClass(kind: SyntaxKind, vivid = false): string {
  if (vivid) {
    switch (kind) {
      case "kw":
        return "text-[#7ec8ff]";
      case "str":
        return "text-[#ffc49a]";
      case "num":
        return "text-[#d6f5b8]";
      case "cmt":
        return "text-[#9adf7a]";
      case "fn":
        return "text-[#fff3a0]";
      default:
        return "text-white";
    }
  }
  switch (kind) {
    case "kw":
      return "text-[#569cd6]";
    case "str":
      return "text-[#ce9178]";
    case "num":
      return "text-[#b5cea8]";
    case "cmt":
      return "text-[#6a9955]";
    case "fn":
      return "text-[#dcdcaa]";
    default:
      return "text-[#d4d4d4]";
  }
}

export function syntaxColor(kind: SyntaxKind, vivid = false): string {
  if (vivid) {
    switch (kind) {
      case "kw":
        return "#7ec8ff";
      case "str":
        return "#ffc49a";
      case "num":
        return "#d6f5b8";
      case "cmt":
        return "#9adf7a";
      case "fn":
        return "#fff3a0";
      default:
        return "#ffffff";
    }
  }
  switch (kind) {
    case "kw":
      return "#569cd6";
    case "str":
      return "#ce9178";
    case "num":
      return "#b5cea8";
    case "cmt":
      return "#6a9955";
    case "fn":
      return "#dcdcaa";
    default:
      return "#d4d4d4";
  }
}
