from pathlib import Path
root = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder")
p = root / "frontend/components/player/LessonPlayer.tsx"
text = p.read_text()
if "async function downloadReel()" not in text:
    needle = "  async function recordReelVideo(source: Lesson) {"
    insert = """  async function downloadReel() {
    if (videoBlob && !exporting) {
      downloadBlob(videoBlob, `${safeReelName(lesson.topic)}.${fileExtension(videoBlob)}`);
      setExportLabel("Downloaded — tap Download again anytime");
      return;
    }
    if (reelReview) {
      try {
        const next = scriptIsDirty() ? await persistDraft() : lesson;
        setReelReview(false);
        await recordReelVideo(next);
      } catch (err) {
        setExportLabel(err instanceof Error ? err.message : "Could not export the reel");
      }
      return;
    }
    await recordReelVideo(lesson);
  }

"""
    if needle not in text:
        raise SystemExit("needle missing")
    text = text.replace(needle, insert + needle, 1)
    p.write_text(text)
    print("inserted downloadReel")
else:
    print("downloadReel present")

studio = root / "frontend/components/player/ReelScriptStudio.tsx"
st = studio.read_text()
if "onDownload" not in st:
    st = st.replace(
        'import { Film, Play } from "lucide-react";',
        'import { Download, Film, Play } from "lucide-react";',
    )
    st = st.replace(
        "  onPlay,\n  onRecord,\n}: {",
        "  onPlay,\n  onRecord,\n  onDownload,\n  downloading,\n}: {",
    )
    st = st.replace(
        "  onPlay: () => void;\n  onRecord: () => void;\n}) {",
        "  onPlay: () => void;\n  onRecord: () => void;\n  onDownload: () => void;\n  downloading?: boolean;\n}) {",
    )
    old = """      <div className=\"flex flex-wrap justify-end gap-2 border-t border-white/10 px-5 py-4\">
        <Button type=\"button\" variant=\"outline\" onClick={onRecord} disabled={locked}>
          <Film className=\"h-4 w-4\" />
          {busy === \"save\" ? \"Saving voice…\" : busy === \"record\" ? \"Recording video…\" : \"Record video\"}
        </Button>
        <Button type=\"button\" onClick={onPlay} disabled={locked}>
          <Play className=\"h-4 w-4\" />
          {busy === \"save\" ? \"Saving voice…\" : \"Play this short\"}
        </Button>
      </div>"""
    new = """      <div className=\"flex flex-wrap justify-end gap-2 border-t border-white/10 px-5 py-4\">
        <Button type=\"button\" variant=\"outline\" onClick={onDownload} disabled={locked || downloading}>
          <Download className=\"h-4 w-4\" />
          {busy === \"record\" || downloading ? \"Exporting…\" : \"Download video\"}
        </Button>
        <Button type=\"button\" variant=\"outline\" onClick={onRecord} disabled={locked}>
          <Film className=\"h-4 w-4\" />
          {busy === \"save\" ? \"Saving voice…\" : busy === \"record\" ? \"Recording video…\" : \"Record video\"}
        </Button>
        <Button type=\"button\" onClick={onPlay} disabled={locked}>
          <Play className=\"h-4 w-4\" />
          {busy === \"save\" ? \"Saving voice…\" : \"Play this short\"}
        </Button>
      </div>"""
    if old not in st:
        raise SystemExit("studio footer missing")
    studio.write_text(st.replace(old, new, 1))
    print("studio updated")
else:
    print("studio already has onDownload")

lp = p.read_text()
if "onDownload={() => void downloadReel()}" not in lp:
    old = """          onPlay={() => void playReviewedShort()}
          onRecord={() => void confirmScriptAndRecord()}
        />"""
    new = """          onPlay={() => void playReviewedShort()}
          onRecord={() => void confirmScriptAndRecord()}
          onDownload={() => void downloadReel()}
          downloading={exporting}
        />"""
    if old not in lp:
        raise SystemExit("studio props missing")
    p.write_text(lp.replace(old, new, 1))
    print("wired studio props")
else:
    print("props already wired")
print("done")
