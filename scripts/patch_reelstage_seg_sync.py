from pathlib import Path
path = Path("frontend/components/player/ReelStage.tsx")
text = path.read_text()
old = """  const infoAnim = useMemo(
    () => (isConcept ? infoBulletAt(syncTitles, currentTime, duration) : null),
    [isConcept, syncTitles, currentTime, duration],
  );"""
new = """  const infoAnim = useMemo(() => {
    if (!isConcept) return null;
    // HashMap explainers: lock phases to narration segment clocks (not equal-split of padded audio).
    const segs = scene.segments || [];
    if (hashmapVisual && segs.length >= 2) {
      const beats = beatsFromSegments(segs, duration);
      return infoBulletAtBeats(beats, currentTime);
    }
    return infoBulletAt(syncTitles, currentTime, duration);
  }, [isConcept, hashmapVisual, scene.segments, syncTitles, currentTime, duration]);"""
if old not in text:
    raise SystemExit("infoAnim block not found")
path.write_text(text.replace(old, new, 1))
print("ReelStage synced to segments")
