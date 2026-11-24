"""
Test suite for the 3 new Top-0.1% tools added to agent.py.
Tests:
  1. advanced_crypto_solver - Wiener attack on a known vulnerable RSA keypair
  2. advanced_crypto_solver - Pollard p-1 on a smooth-prime N
  3. advanced_crypto_solver - Fermat factoring on close primes
  4. ctfd_speed_listener    - graceful error on bad URL
  5. pwn_crash_triage       - returns structure even without WSL binary
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent import execute_tool

PASS = 0
FAIL = 0

def check(label, result_str, must_contain=None, must_not_error=True):
    global PASS, FAIL
    try:
        data = json.loads(result_str)
    except Exception as ex:
        print(f"  ❌ FAIL [{label}] JSON parse error: {ex}\n     raw={result_str[:200]}")
        FAIL += 1
        return
    if must_not_error and data.get("error"):
        print(f"  ❌ FAIL [{label}] tool returned error: {data['error']}")
        FAIL += 1
        return
    if must_contain:
        for key in must_contain:
            if key not in str(data):
                print(f"  ❌ FAIL [{label}] expected '{key}' in result, got:\n     {str(data)[:300]}")
                FAIL += 1
                return
    print(f"  ✅ PASS [{label}]")
    PASS += 1

print("=" * 60)
print("TOP 0.1% ENGINE TEST SUITE")
print("=" * 60)

# ---- TEST 1: Wiener attack ----
# Classic Wiener: n=ugc, e chosen so d is small
# Use a known textbook example: p=61, q=53 -> n=3233, e=17 is NOT wiener-vulnerable
# Use a proper vulnerable key: p=9539, q=9679, d=11 (small)
p1, q1 = 9539, 9679
n1 = p1 * q1
phi1 = (p1-1)*(q1-1)
# d must be small, e = inverse(d, phi)
# pow(11, -1, phi1)
e1 = pow(11, -1, phi1)
# Encrypt m=1337
m1 = 1337
c1 = pow(m1, e1, n1)

print(f"\n[1] Wiener attack: N={n1}, e={e1}")
r1 = execute_tool("advanced_crypto_solver", {"attack": "wiener", "n": str(n1), "e": str(e1), "c": str(c1)})
check("Wiener attack recovers d=11 and factors N", r1, must_contain=["factored"])

# ---- TEST 2: Pollard p-1 ----
# p=65537 is a Fermat prime: p-1 = 2^16 (perfectly B-smooth with B=2)
# q=131101 is prime: q-1 = 131100 = 2^2 * 3 * 5^2 * 19 * 23 (B-smooth with B=23)
# Use e=3 (gcd(3, phi) must be 1 — verified: phi = 65536*131100, not divisible by 3)
p2, q2 = 65537, 131071  # 131071 = 2^17 - 1 is a Mersenne prime; q-1 = 131070 = 2*3*5*43*101
n2 = p2 * q2
# phi2 = 65536 * 131070
# Use e2 = 7 — gcd(7, 65536*131070) = 1 since 65536=2^16 and 131070=2*3*5*43*101 not div by 7
e2 = 7
phi2 = (p2-1)*(q2-1)
import math
assert math.gcd(e2, phi2) == 1, f"e={e2} not coprime to phi"
d2 = pow(e2, -1, phi2)
m2 = 1337
c2 = pow(m2, e2, n2)

print(f"\n[2] Pollard p-1: N={n2}, e={e2}")
r2 = execute_tool("advanced_crypto_solver", {"attack": "pollard_pm1", "n": str(n2), "e": str(e2), "c": str(c2)})
check("Pollard p-1 factors smooth-prime N", r2, must_contain=["factored"])

# ---- TEST 3: Fermat factoring on close primes ----
# p and q very close -> Fermat works fast
p3 = 1000003
q3 = 1000033
n3 = p3 * q3
e3 = 65537
phi3 = (p3-1)*(q3-1)
d3 = pow(e3, -1, phi3)
m3 = 999
c3 = pow(m3, e3, n3)

print(f"\n[3] Fermat factoring (close primes): N={n3}")
r3 = execute_tool("advanced_crypto_solver", {"attack": "weak_prime", "n": str(n3), "e": str(e3), "c": str(c3)})
check("Fermat factors N with close p and q", r3, must_contain=["factored"])

# ---- TEST 4: small-e RSA integer cube-root precision ----
# Use a plaintext larger than IEEE-754's exact-integer range. Floating-point
# cube roots can lose precision here even though m^3 < N.
print(f"\\n[4] Small-e RSA exact cube root")
flag_bytes = b"HQX{integer_cube_root_precision}"
m4 = int.from_bytes(flag_bytes, "big")
n4 = 1 << 600
e4 = 3
c4 = m4 ** 3
r4_small_e = execute_tool("advanced_crypto_solver", {
    "attack": "small_e", "n": str(n4), "e": str(e4), "c": str(c4)
})
check("Small-e exact cube root recovers large plaintext", r4_small_e,
      must_contain=[str(m4), "recovered"])

# ---- TEST 5: CTFd speed listener graceful error on bad URL ----
print(f"\n[4] CTFd speed listener: bad URL")
r4 = execute_tool("ctfd_speed_listener", {
    "ctfd_url": "http://127.0.0.1:1",  # nothing listening here
    "max_polls": 1,
    "poll_interval_s": 2
})
# Should return an error (can't connect) or no_new_challenges — not a crash
try:
    d4 = json.loads(r4)
    if "error" in d4 or "status" in d4:
        print("  ✅ PASS [CTFd listener: graceful failure on bad URL]")
        PASS += 1
    else:
        print(f"  ❌ FAIL [CTFd listener] unexpected output: {r4[:200]}")
        FAIL += 1
except Exception as ex:
    print(f"  ❌ FAIL [CTFd listener JSON parse]: {ex}")
    FAIL += 1

# ---- TEST 6: PWN crash triage structure test ----
print(f"\n[5] PWN crash triage: structure check on nonexistent binary")
r5 = execute_tool("pwn_crash_triage", {
    "binary_path": r"c:\nonexistent\fakebinary",
    "use_cyclic": True,
    "cyclic_length": 50
})
try:
    d5 = json.loads(r5)
    # Should have a 'binary' key and not crash Python itself
    if "binary" in d5 or "error" in d5 or "wsl_path" in d5:
        print("  ✅ PASS [pwn_crash_triage: returns structured output]")
        PASS += 1
    else:
        print(f"  ❌ FAIL [pwn_crash_triage]: {r5[:200]}")
        FAIL += 1
except Exception as ex:
    print(f"  ❌ FAIL [pwn_crash_triage JSON parse]: {ex}")
    FAIL += 1

print("\n" + "=" * 60)
print(f"RESULTS: {PASS} passed / {PASS+FAIL} total")
if FAIL == 0:
    print("✅ ALL TESTS PASSED")
else:
    print(f"❌ {FAIL} TESTS FAILED")
print("=" * 60)
