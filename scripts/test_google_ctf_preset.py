import os
import sys
import json
import time

current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from agent import CTFOrchestratorAgent, execute_tool

def test_google_ctf_web_preset():
    print("=" * 60, flush=True)
    print("TEST 1: Google CTF Web Preset (Client-Side Timer Bypass)", flush=True)
    print("=" * 60, flush=True)
    
    agent = CTFOrchestratorAgent()
    prompt = (
        "There is a Google CTF web challenge with a client-side timer checking completion state before releasing the flag. "
        "Query our Hugging Face ZeroGPU Vector knowledge base for client-side timer bypass techniques, "
        "explain how to bypass it, and show the exact console command to extract the flag."
    )
    
    t0 = time.time()
    res = agent.run_with_trace(prompt, max_turns=4)
    elapsed = round(time.time() - t0, 2)
    
    print(f"\nExecution finished in {elapsed}s", flush=True)
    print(f"Session ID: {res.get('session_id')}", flush=True)
    print(f"Provider: {res.get('provider')} | Model: {res.get('model')}", flush=True)
    print(f"Total Tool Calls: {len(res.get('trace', []))}", flush=True)
    
    for t in res.get("trace", []):
        print(f"\n[TRACE TURN {t.get('turn')}]: Tool `{t.get('tool')}`", flush=True)
        print(f"Args: {json.dumps(t.get('args'))}", flush=True)
        out_preview = str(t.get('output', ''))[:400].replace('\n', ' ')
        print(f"Result Preview: {out_preview}...", flush=True)
        
    print("\n" + "=" * 60, flush=True)
    print("FINAL AGENT ANSWER:", flush=True)
    print("=" * 60, flush=True)
    print(res.get("final_answer"), flush=True)
    return res

if __name__ == "__main__":
    test_google_ctf_web_preset()
