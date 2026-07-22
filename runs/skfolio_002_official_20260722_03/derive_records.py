#!/usr/bin/env python3
"""从 claude_stream.raw.jsonl 派生可读记录(原始流是唯一证据源, 派生只为便于阅读)。"""
import json, sys
from pathlib import Path

RUN = Path(sys.argv[1])
raw = (RUN / "records" / "claude_stream.raw.jsonl").read_text().splitlines()

events = []
for line in raw:
    line = line.strip()
    if not line:
        continue
    try:
        events.append(json.loads(line))
    except json.JSONDecodeError:
        pass

traj, term, final = [], [], ""
resolved_model, session_id = None, None
for ev in events:
    t = ev.get("type")
    if t == "system" and ev.get("subtype") == "init":
        session_id = ev.get("session_id")
        resolved_model = ev.get("model")
        traj.append(f"### [init] session={session_id} model={resolved_model} cwd={ev.get('cwd')}")
    elif t == "assistant":
        for b in ev.get("message", {}).get("content", []):
            bt = b.get("type")
            if bt == "text" and b.get("text", "").strip():
                traj.append(f"\n**assistant:** {b['text'].strip()}")
            elif bt == "thinking" and b.get("thinking", "").strip():
                traj.append(f"\n*(thinking… {len(b['thinking'])} chars)*")
            elif bt == "tool_use":
                name = b.get("name")
                inp = b.get("input", {})
                arg = inp.get("command") or inp.get("file_path") or inp.get("pattern") or json.dumps(inp, ensure_ascii=False)[:200]
                traj.append(f"\n`[tool] {name}` → {str(arg)[:400]}")
                if name == "Bash":
                    term.append(f"$ {inp.get('command','')}")
    elif t == "user":
        for b in ev.get("message", {}).get("content", []):
            if b.get("type") == "tool_result":
                c = b.get("content", "")
                if isinstance(c, list):
                    c = " ".join(x.get("text", "") for x in c if isinstance(x, dict))
                traj.append(f"  ↳ result: {str(c)[:300]}")
                term.append(str(c)[:2000])
    elif t == "result":
        final = ev.get("result", "") or ""

(RUN / "records" / "trajectory.md").write_text(
    f"# 正式盲测轨迹(派生自 raw stream)\n\nsession={session_id} model={resolved_model}\n\n" + "\n".join(traj), encoding="utf-8")
(RUN / "records" / "terminal.log").write_text("\n".join(term), encoding="utf-8")
(RUN / "records" / "final_answer.md").write_text(final, encoding="utf-8")
print(f"events={len(events)} traj_lines={len(traj)} resolved_model={resolved_model} session={session_id}")
print(f"final_answer chars={len(final)}")
