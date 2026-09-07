from pathlib import Path
p = Path("frontend/lib/reelExport.ts")
t = p.read_text()
old = '''    const miniY = y + 6;
    const miniR = 9;
    const trackLeft = x + padX + 18;
    const trackRight = x + w - padX - 18;
    const trackW = Math.max(40, trackRight - trackLeft);

    // Track
    ctx.save();
    ctx.strokeStyle = "rgba(34,211,238,0.16)";
    ctx.lineWidth = 3;
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.moveTo(trackLeft, miniY);
    ctx.lineTo(trackRight, miniY);
    ctx.stroke();
    const drawFrac = count <= 1 ? 1 : ai / Math.max(1, count - 1);
    ctx.strokeStyle = "rgba(34,211,238,0.65)";
    ctx.shadowColor = "rgba(34,211,238,0.4)";
    ctx.shadowBlur = 8;
    ctx.beginPath();
    ctx.moveTo(trackLeft, miniY);
    ctx.lineTo(trackLeft + trackW * drawFrac, miniY);
    ctx.stroke();
    ctx.restore();

    for (let index = 0; index < count; index++) {
      const visible = index < anim.visibleCount;
      const active = index === ai && visible;
      const past = visible && index < ai;
      const cx = count <= 1 ? (trackLeft + trackRight) / 2 : trackLeft + (trackW * index) / Math.max(1, count - 1);
      ctx.beginPath();
      ctx.arc(cx, miniY, miniR, 0, Math.PI * 2);
      if (active) {
        ctx.fillStyle = "#fbbf24";
        ctx.shadowColor = "rgba(251,191,36,0.55)";
        ctx.shadowBlur = 12;
      } else if (past) {
        ctx.fillStyle = "rgba(34,211,238,0.85)";
        ctx.shadowBlur = 0;
      } else {
        ctx.fillStyle = "rgba(255,255,255,0.12)";
        ctx.shadowBlur = 0;
      }
      ctx.fill();
      ctx.shadowBlur = 0;
      ctx.fillStyle = active ? "#09090b" : past ? "#083344" : "rgba(207,250,254,0.35)";
      ctx.font = "800 10px ui-sans-serif, system-ui";
      ctx.textAlign = "center";
      ctx.fillText(String(index + 1), cx, miniY + 3);
    }
'''

new = '''    const miniY = y + 10;
    const miniR = 11;
    const trackLeft = x + padX + 22;
    const trackRight = x + w - padX - 22;
    const trackW = Math.max(40, trackRight - trackLeft);

    // Track under nodes (drawn first)
    ctx.save();
    ctx.strokeStyle = "rgba(34,211,238,0.2)";
    ctx.lineWidth = 3;
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.moveTo(trackLeft, miniY);
    ctx.lineTo(trackRight, miniY);
    ctx.stroke();
    const drawFrac = count <= 1 ? 1 : ai / Math.max(1, count - 1);
    ctx.strokeStyle = "rgba(34,211,238,0.7)";
    ctx.shadowColor = "rgba(34,211,238,0.4)";
    ctx.shadowBlur = 8;
    ctx.beginPath();
    ctx.moveTo(trackLeft, miniY);
    ctx.lineTo(trackLeft + trackW * drawFrac, miniY);
    ctx.stroke();
    ctx.restore();

    for (let index = 0; index < count; index++) {
      const visible = index < anim.visibleCount;
      const active = index === ai && visible;
      const past = visible && index < ai;
      const cx = count <= 1 ? (trackLeft + trackRight) / 2 : trackLeft + (trackW * index) / Math.max(1, count - 1);
      // Opaque board-colored halo so the connector never bleeds through the circle
      ctx.beginPath();
      ctx.arc(cx, miniY, miniR + 5, 0, Math.PI * 2);
      ctx.fillStyle = "#031018";
      ctx.fill();
      ctx.beginPath();
      ctx.arc(cx, miniY, miniR, 0, Math.PI * 2);
      if (active) {
        ctx.fillStyle = "#3b2a0a";
        ctx.shadowColor = "rgba(251,191,36,0.55)";
        ctx.shadowBlur = 12;
      } else if (past) {
        ctx.fillStyle = "#0a3a45";
        ctx.shadowBlur = 0;
      } else {
        ctx.fillStyle = "#0a1c24";
        ctx.shadowBlur = 0;
      }
      ctx.fill();
      ctx.shadowBlur = 0;
      ctx.lineWidth = 2;
      ctx.strokeStyle = active ? "#fcd34d" : past ? "#67e8f9" : "rgba(255,255,255,0.22)";
      ctx.stroke();
      ctx.fillStyle = active ? "#fef3c7" : past ? "#ecfeff" : "rgba(207,250,254,0.55)";
      ctx.font = "800 11px ui-sans-serif, system-ui";
      ctx.textAlign = "center";
      ctx.fillText(String(index + 1), cx, miniY + 4);
    }
'''

if old not in t:
    raise SystemExit('export block missing')
t = t.replace(old, new, 1)
t = t.replace('const cardTop = miniY + 28;', 'const cardTop = miniY + 40;', 1)
p.write_text(t)
print('export ok')
