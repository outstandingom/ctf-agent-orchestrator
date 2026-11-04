path = r"c:\Users\SGI\Downloads\ctf-agent-orchestrator\agent.py"
with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if "# Check instant diff" in line:
        start_idx = i
    if start_idx is not None and "return json.dumps({" in line and i > start_idx + 30:
        end_idx = i + 6
        break

print(f"Replacing lines {start_idx+1} to {end_idx+1}")

replacement = [
    '        # Check instant diff\n',
    '        raw_new = []\n',
    '        for cid, chal in current_snapshot.items():\n',
    '            if cid not in baseline:\n',
    '                raw_new.append((cid, dict(chal), 0))\n',
    '\n',
    '        # If user explicitly asked for a polling watch and no new challenge found yet:\n',
    '        if not raw_new and max_polls > 1:\n',
    '            for poll in range(1, max_polls):\n',
    '                time.sleep(poll_interval)\n',
    '                current_snapshot, code = fetch_challenges()\n',
    '                if current_snapshot is None:\n',
    '                    continue\n',
    '                polls_done += 1\n',
    '                for cid, chal in current_snapshot.items():\n',
    '                    if cid not in baseline:\n',
    '                        raw_new.append((cid, dict(chal), poll + 1))\n',
    '                if raw_new:\n',
    '                    break\n',
    '\n',
    '        new_challenges = []\n',
    '        for cid, chal_data, p_num in raw_new:\n',
    '            new_chal = dict(chal_data)\n',
    '            new_chal["detected_at_poll"] = p_num\n',
    '            new_chal["elapsed_seconds"] = round(time.time() - t0, 2)\n',
    '            new_chal["attachments_downloaded"] = []\n',
    '            if dl_attachments:\n',
    '                try:\n',
    '                    detail_r = session.get(f"{ctfd_url}/api/v1/challenges/{cid}", timeout=8)\n',
    '                    if detail_r.status_code == 200:\n',
    '                        detail = detail_r.json().get("data", {})\n',
    '                        for f_info in detail.get("files", []):\n',
    '                            file_url = f_info if isinstance(f_info, str) else f_info.get("location", "")\n',
    '                            if not file_url.startswith("http"):\n',
    '                                file_url = ctfd_url + "/" + file_url.lstrip("/")\n',
    '                            try:\n',
    '                                dl = session.get(file_url, timeout=15)\n',
    '                                if dl.status_code == 200:\n',
    '                                    fname = file_url.split("/")[-1].split("?")[0] or f"challenge_{cid}_file"\n',
    '                                    fpath = os.path.join(save_dir, fname)\n',
    '                                    with open(fpath, "wb") as fh:\n',
    '                                        fh.write(dl.content)\n',
    '                                    classification = classify_file(fpath, dl.content)\n',
    '                                    new_chal["attachments_downloaded"].append({\n',
    '                                        "url": file_url,\n',
    '                                        "saved_to": fpath,\n',
    '                                        "classification": classification\n',
    '                                    })\n',
    '                            except Exception as dl_err:\n',
    '                                new_chal["attachments_downloaded"].append({"url": file_url, "error": str(dl_err)})\n',
    '                except Exception:\n',
    '                    pass\n',
    '            new_challenges.append(new_chal)\n',
    '\n',
    '        return json.dumps({\n',
    '            "status": "new_challenges_found" if new_challenges else "no_new_challenges",\n',
    '            "polls_done": polls_done,\n',
    '            "total_elapsed_s": round(time.time() - t0, 2),\n',
    '            "new_challenges": new_challenges\n',
    '        }, indent=2)\n'
]

lines[start_idx:end_idx] = replacement

with open(path, "w", encoding="utf-8") as f:
    f.writelines(lines)

import ast
with open(path, "r", encoding="utf-8") as f:
    src = f.read()
ast.parse(src)
print("✅ agent.py syntax valid after clean ctfd poller fix")
