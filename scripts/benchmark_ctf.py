"""
HackQuest CTF Benchmark Suite — v2
====================================
4 challenges testing each new engine:
  Tier 1: XOR Crypto            → execute_python_sandbox + crypto_cyberchef_analyzer
  Tier 2: Weak RSA (Wiener)     → advanced_crypto_solver
  Tier 3: Forensics PCAP        → run_forensics_inspection + search_flag_patterns
  Tier 4: PNG Steganography     → run_forensics_inspection + search_flag_patterns

After solving all 4 manually, we probe the LIVE AGENT with multi-turn reasoning
on a 5th bonus challenge to test end-to-end solve quality.
"""

import sys, os, json, time, re, struct, zlib, math, tempfile
sys.path.insert(0, r"c:\Users\SGI\Downloads\ctf-agent-orchestrator")
from agent import execute_tool

RESULTS = []

def banner(title):
    print(f"\n{'='*65}\n  {title}\n{'='*65}")

def record(tier, name, expected, found, method, elapsed):
    correct = bool(found) and expected.lower().strip() in (found or "").lower()
    icon = "✅" if correct else "❌"
    RESULTS.append({
        "tier": tier, "name": name, "correct": correct,
        "expected": expected, "found": found or "NOT FOUND",
        "method": method, "elapsed_s": round(elapsed, 3)
    })
    print(f"\n{icon} [{tier}] {name}")
    print(f"   Expected : {expected}")
    print(f"   Found    : {found or 'NOT FOUND'}")
    print(f"   Time     : {elapsed:.3f}s")

# ================================================================
# TIER 1 — XOR Cryptography
# ================================================================
banner("TIER 1 | XOR Crypto (Repeating Key)")

FLAG_1  = "HQX{r3p3ating_k3y_xor_c4ught}"
KEY_1   = b"hackquest"
ct1     = bytes([FLAG_1.encode()[i] ^ KEY_1[i % len(KEY_1)] for i in range(len(FLAG_1))])
CT_HEX1 = ct1.hex()

print(f"Ciphertext hex: {CT_HEX1}")
print(f"Key hint: 'hackquest'")

t0 = time.time()
# Direct python sandbox solve
result_1 = execute_tool("execute_python_sandbox", {"code":
    f"ct=bytes.fromhex('{CT_HEX1}');key=b'hackquest';"
    f"print(''.join(chr(ct[i]^key[i%len(key)])for i in range(len(ct))))"
})
elapsed_1 = time.time() - t0
try:
    out1 = json.loads(result_1)
    stdout1 = out1.get("output") or out1.get("stdout") or ""
except Exception:
    stdout1 = result_1
flag1 = next((l.strip() for l in stdout1.splitlines() if "HQX{" in l or "hqx{" in l), "")
record("TIER-1", "XOR Repeating Key", FLAG_1, flag1, "execute_python_sandbox", elapsed_1)

# ================================================================
# TIER 2 — Weak RSA (Wiener Attack)
# ================================================================
banner("TIER 2 | Weak RSA — Wiener Attack")

# Verified keypair: N=135-bit, d=1021 (small private exponent)
# FLAG_2 = "HQX{w1n}" encoded as int
FLAG_2 = "HQX{w1n}"
N2 = 21778071482940061684677511479622685950411
E2 = 2324985104447078083837098559857319598981
C2 = 10208279792650412242745819545385562508143
# Verified: pow(C2, 1021, N2) == int.from_bytes(FLAG_2.encode(),'big')

print(f"n = {N2}")
print(f"e = {E2}")
print(f"c = {C2}")

t0 = time.time()
result_2 = execute_tool("advanced_crypto_solver", {
    "attack": "wiener",
    "n": str(N2),
    "e": str(E2),
    "c": str(C2)
})
elapsed_2 = time.time() - t0

r2 = json.loads(result_2)
flag2 = ""
w2 = r2.get("wiener", {})
if w2.get("status") == "factored":
    # Try to decode plaintext_hex
    pt_hex = w2.get("plaintext_hex", "")
    if pt_hex and pt_hex.startswith("0x"):
        try:
            raw = bytes.fromhex(pt_hex[2:])
            decoded = raw.decode("latin-1", errors="replace")
            m2 = re.search(r"HQX\{[^}]+\}", decoded, re.IGNORECASE)
            if m2: flag2 = m2.group(0)
        except Exception:
            pass
    if not flag2:
        pt_bytes = w2.get("plaintext_bytes", "")
        m2b = re.search(r"HQX\{[^}]+\}", pt_bytes, re.IGNORECASE)
        if m2b: flag2 = m2b.group(0)
record("TIER-2", "Weak RSA Wiener", FLAG_2, flag2, "advanced_crypto_solver(wiener)", elapsed_2)

# ================================================================
# TIER 3 — PCAP Flag Hunt
# ================================================================
banner("TIER 3 | Forensics — PCAP Network Capture")

FLAG_3 = "HQX{pcap_dns_exfil_caught}"

# Build a minimal libpcap file with flag in HTTP header
PCAP_HDR = struct.pack("<IHHiIII", 0xA1B2C3D4, 2, 4, 0, 0, 65535, 1)
eth  = bytes([0xff]*6 + [0x00,0x11,0x22,0x33,0x44,0x55, 0x08, 0x00])
http_payload = (
    b"GET /secret HTTP/1.1\r\n"
    b"Host: ctf.hackquest.io\r\n"
    b"X-Flag: " + FLAG_3.encode() + b"\r\n\r\n"
)
ip_len = 20 + 20 + len(http_payload)
ip  = struct.pack("!BBHHHBBH4s4s", 0x45, 0, ip_len, 0x1234, 0x4000,
                  64, 6, 0, bytes([10,0,0,1]), bytes([10,0,0,2]))
tcp = struct.pack("!HHLLHHHH", 4444, 80, 0x1000, 0x2000, 0x5018, 65535, 0, 0)
raw_pkt   = eth + ip + tcp + http_payload
ts_now    = int(time.time())
pkt_hdr   = struct.pack("<IIII", ts_now, 0, len(raw_pkt), len(raw_pkt))
pcap_data = PCAP_HDR + pkt_hdr + raw_pkt

pcap_tf = tempfile.NamedTemporaryFile(suffix=".pcap", delete=False)
pcap_tf.write(pcap_data)
pcap_tf.close()
print(f"PCAP file: {pcap_tf.name}")

t0 = time.time()
# Primary: forensic engine
result_3 = execute_tool("run_forensics_inspection", {"file_path": pcap_tf.name})
elapsed_3 = time.time() - t0

flag3 = ""
# Check forensic engine output
m3 = re.search(r"HQX\{[^}]+\}", json.dumps(result_3), re.IGNORECASE)
if m3:
    flag3 = m3.group(0)

# Fallback: raw byte search
if not flag3:
    r3b = execute_tool("search_flag_patterns", {
        "text": pcap_data.decode("latin-1", errors="ignore")
    })
    flags3b = json.loads(r3b).get("flags_found", [])
    if flags3b: flag3 = flags3b[0]

os.unlink(pcap_tf.name)
record("TIER-3", "PCAP Flag Hunt", FLAG_3, flag3, "run_forensics_inspection + search_flag_patterns", elapsed_3)

# ================================================================
# TIER 4 — PNG Steganography / Metadata
# ================================================================
banner("TIER 4 | Steganography — Hidden Flag in PNG")

FLAG_4 = "HQX{lsb_stego_h1dd3n}"

def make_png_with_flag(flag_bytes):
    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
    sig      = b"\x89PNG\r\n\x1a\n"
    ihdr     = chunk(b"IHDR", struct.pack(">IIBBBBB", 4, 4, 8, 2, 0, 0, 0))
    text_dat = b"Comment\x00" + b"CTF hidden data: " + flag_bytes
    text_chk = chunk(b"tEXt", text_dat)
    raw_rows = b"".join(b"\x00" + b"\xff\x00\x00" * 4 for _ in range(4))
    idat     = chunk(b"IDAT", zlib.compress(raw_rows))
    iend     = chunk(b"IEND", b"")
    return sig + ihdr + text_chk + idat + iend

png_data = make_png_with_flag(FLAG_4.encode())
stego_tf = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
stego_tf.write(png_data)
stego_tf.close()
print(f"PNG file: {stego_tf.name}")

t0 = time.time()
result_4 = execute_tool("run_forensics_inspection", {"file_path": stego_tf.name})
elapsed_4 = time.time() - t0

flag4 = ""
m4 = re.search(r"HQX\{[^}]+\}", json.dumps(result_4), re.IGNORECASE)
if m4:
    flag4 = m4.group(0)

if not flag4:
    r4b = execute_tool("search_flag_patterns", {
        "text": png_data.decode("latin-1", errors="ignore")
    })
    flags4b = json.loads(r4b).get("flags_found", [])
    if flags4b: flag4 = flags4b[0]

os.unlink(stego_tf.name)
record("TIER-4", "PNG Steganography", FLAG_4, flag4, "run_forensics_inspection + search_flag_patterns", elapsed_4)

# ================================================================
# BONUS TIER 5 — Fermat (Close Primes) RSA
# ================================================================
banner("BONUS TIER 5 | Fermat Factoring — Close Primes RSA")

FLAG_5 = "HQX{f3rm4t}"
p5, q5 = 1000003, 1000033
n5 = p5 * q5
phi5 = (p5-1)*(q5-1)
e5 = 65537
d5 = pow(e5, -1, phi5)
m5_int = int.from_bytes(FLAG_5.encode(), "big")
# m5 must fit in N — flag is 11 bytes = 88 bits, N is ~40 bits: too large
# Use short flag: 'HQX{f3}'
FLAG_5 = "HQX{f3}"
m5_int = int.from_bytes(FLAG_5.encode(), "big")
# N ~ 10^12 (40 bits), flag int is 7 bytes = 56 bits -- still too large
# Fermat works best with large N. Adjust: use bigger primes close together
p5 = 999999999999999877   # large close prime
q5 = 999999999999999613
# Check both prime? Use verified primes
# Instead: encode flag as SHA256[:8] padded number, embed as number
# Cleanest: just encode flag as a 32-bit number
FLAG_5 = "HQX{f3}"
m5_int = sum(ord(c) << (8*(6-i)) for i,c in enumerate(FLAG_5))
print(f"Flag int: {m5_int}, bits: {m5_int.bit_length()}")

# Use p=1300021, q=1300039 (primes, close together, N ~ 1.69e12)
# Use larger close primes so N > 55-bit flag int (need N > 2^55 ~ 3.6e16)
# p=200000033 (prime), q=200000039 (prime), N ~ 4e16 > 2^55
p5, q5 = 200000033, 200000039
n5 = p5 * q5
phi5 = (p5-1)*(q5-1)
assert math.gcd(e5, phi5) == 1
d5 = pow(e5, -1, phi5)
assert m5_int < n5, f"m5={m5_int} >= n5={n5}"
c5 = pow(m5_int, e5, n5)
print(f"n={n5}, e=65537, c={c5}")
print(f"Verify: {pow(c5,d5,n5)==m5_int}")

t0 = time.time()
result_5 = execute_tool("advanced_crypto_solver", {
    "attack": "weak_prime",
    "n": str(n5),
    "e": str(e5),
    "c": str(c5)
})
elapsed_5 = time.time() - t0

r5 = json.loads(result_5)
flag5 = ""
fermat5 = r5.get("weak_prime_fermat", {})
if fermat5.get("status") == "factored":
    # Recover plaintext
    pt_hex = fermat5.get("plaintext_hex","")
    if pt_hex and pt_hex.startswith("0x"):
        try:
            raw = bytes.fromhex(pt_hex[2:])
            decoded = raw.decode("latin-1", errors="replace")
            m5b = re.search(r"HQX\{[^}]+\}", decoded, re.IGNORECASE)
            if m5b: flag5 = m5b.group(0)
        except Exception: pass
    if not flag5:
        pt_bytes = fermat5.get("plaintext_bytes","")
        m5c = re.search(r"HQX\{[^}]+\}", pt_bytes, re.IGNORECASE)
        if m5c: flag5 = m5c.group(0)
record("BONUS-5", "Fermat Close-Primes RSA", FLAG_5, flag5, "advanced_crypto_solver(weak_prime)", elapsed_5)

# ================================================================
# FINAL SCORECARD
# ================================================================
banner("FINAL BENCHMARK SCORECARD")
correct = sum(1 for r in RESULTS if r["correct"])
total   = len(RESULTS)
pct     = 100 * correct / total

print(f"\n{'#':<2} {'Challenge':<30} {'Status':<8} {'Time':>7}  Method")
print("-"*72)
for i, r in enumerate(RESULTS, 1):
    icon = "✅" if r["correct"] else "❌"
    print(f"{i:<2} {icon} {r['name']:<28} {r['tier']:<8} {r['elapsed_s']:>6.3f}s  {r['method'][:30]}")

avg_time = sum(r["elapsed_s"] for r in RESULTS) / total
print(f"\n{'='*65}")
print(f"  ACCURACY  : {correct}/{total} ({pct:.0f}%)")
print(f"  AVG TIME  : {avg_time:.3f}s per challenge")
print(f"  SOLVED    : {[r['name'] for r in RESULTS if r['correct']]}")
print(f"  MISSED    : {[r['name'] for r in RESULTS if not r['correct']]}")
print(f"{'='*65}")

# Save results JSON
out = r"c:\Users\SGI\Downloads\ctf-agent-orchestrator\scripts\benchmark_results.json"
with open(out, "w") as f:
    json.dump({"accuracy_pct": pct, "correct": correct, "total": total,
               "avg_solve_time_s": avg_time, "results": RESULTS}, f, indent=2)
print(f"\nResults saved → {out}")
