import json, time, urllib.request
lid = "les_35fca6ad110b478b88ac76947219c171"
url = f"http://127.0.0.1:8010/api/v1/lesson/{lid}"
for i in range(60):
    with urllib.request.urlopen(url, timeout=20) as r:
        d = json.load(r)
    status = d.get("status")
    L = d.get("lesson") or {}
    print(f"t={i*3}s status={status} reel={L.get('reel_mode')} scenes={len(L.get('scenes') or [])}")
    if status in {"ready", "failed"}:
        Path = __import__("pathlib").Path
        Path("storage/tmp-concurrency-explainer.json").write_text(json.dumps(d, indent=2))
        for s in L.get("scenes") or []:
            print(f"  [{s.get('type')}] {(s.get('narration') or '')[:180].replace(chr(10),' ')}")
            bullets = s.get("bullets") or []
            steps = s.get("diagram_steps") or []
            if bullets:
                print("    bullets:", bullets[:6])
            if steps:
                print("    steps:", [x.get("title") for x in steps[:8]])
        raise SystemExit(0 if status == "ready" else 2)
    time.sleep(3)
print("timeout")
raise SystemExit(1)
