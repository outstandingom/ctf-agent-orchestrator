import os
import sys
import json
import time

current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from agent import CTFOrchestratorAgent, execute_tool

def test_google_ctf_crypto_preset():
    print("=" * 60, flush=True)
    print("TEST 2: Google CTF Cryptography Preset (PRNG Time-Seeded XOR)", flush=True)
    print("=" * 60, flush=True)
    
    agent = CTFOrchestratorAgent()
    prompt = (
        "I have a Google CTF cryptography challenge where the flag was XOR encrypted using Python "
        "random.seed(int(time.time())) from approx timestamp 1700000000. "
        "Search our Hugging Face ZeroGPU Vector knowledge base for the PRNG time seeding pattern, "
        "and generate a Python solver script to verify it in the sandbox."
    )
    
    t0 = time.time()
    res = agent.run_with_trace(prompt, max_turns=4)
    elapsed = round(time.time() - t0, 2)
    
    print(f"\nExecution finished in {elapsed}s", flush=True)
    print(f"Session ID: {res.get('session_id')}", flush=True)
    print(f"Total Tool Calls: {len(res.get('trace', []))}", flush=True)
    
    for t in res.get("trace", []):
        print(f"\n[TRACE TURN {t.get('turn')}]: Tool `{t.get('tool')}`", flush=True)
        print(f"Args: {json.dumps(t.get('args'))}", flush=True)
        out_preview = str(t.get('output', ''))[:300].replace('\n', ' ')
        print(f"Result Preview: {out_preview}...", flush=True)
        
    print("\n" + "=" * 60, flush=True)
    print("FINAL AGENT ANSWER:", flush=True)
    print("=" * 60, flush=True)
    print(res.get("final_answer"), flush=True)
    return res

if __name__ == "__main__":
    test_google_ctf_crypto_preset()
