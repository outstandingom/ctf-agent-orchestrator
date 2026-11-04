"""Fix Pollard p-1 in agent.py: check gcd at each prime, not only at the end."""
AGENT_PATH = r"c:\Users\SGI\Downloads\ctf-agent-orchestrator\agent.py"

with open(AGENT_PATH, "r", encoding="utf-8") as f:
    src = f.read()

old_pollard = '''        # --- POLLARD p-1 FACTORING ---
        def pollard_pm1(n, B=1_000_000):
            if n % 2 == 0:
                return 2
            a = 2
            primes = []
            sieve = bytearray([1]) * (B + 1)
            sieve[0] = sieve[1] = 0
            for i in range(2, int(B**0.5) + 1):
                if sieve[i]:
                    for j in range(i*i, B+1, i):
                        sieve[j] = 0
            primes = [i for i in range(2, B+1) if sieve[i]]
            for p in primes:
                pk = p
                while pk <= B:
                    a = pow(a, p, n)
                    pk *= p
            g = math.gcd(a - 1, n)
            if 1 < g < n:
                return g
            return None'''

new_pollard = '''        # --- POLLARD p-1 FACTORING (Montgomery Stage 1 with per-prime gcd check) ---
        def pollard_pm1(n, B=1_000_000):
            """
            Standard Pollard p-1 Stage 1.
            For each prime p <= B, computes a = a^(p^k) mod n (p^k <= B),
            then checks gcd after each prime. This correctly factors N when
            p-1 is B-smooth (all prime power factors of p-1 are <= B).
            """
            if n % 2 == 0:
                return 2
            # Sieve primes up to B
            sieve = bytearray([1]) * (B + 1)
            sieve[0] = sieve[1] = 0
            for i in range(2, int(B**0.5) + 1):
                if sieve[i]:
                    for j in range(i*i, B+1, i):
                        sieve[j] = 0
            a = 2
            for p in range(2, B+1):
                if not sieve[p]:
                    continue
                # Raise a to p^k where p^k <= B (all prime powers of p)
                pk = p
                while pk <= B:
                    a = pow(a, p, n)
                    pk *= p
                # Check gcd after each prime — catches factor early
                g = math.gcd(a - 1, n)
                if 1 < g < n:
                    return g
                if g == n:
                    return None  # Degenerate; try with smaller B
            # Final check
            g = math.gcd(a - 1, n)
            return g if 1 < g < n else None'''

assert old_pollard in src, "Pollard pattern not found"
src = src.replace(old_pollard, new_pollard, 1)

with open(AGENT_PATH, "w", encoding="utf-8") as f:
    f.write(src)

import ast
try:
    ast.parse(src)
    print("✅ Syntax OK after Pollard p-1 fix")
except SyntaxError as e:
    print(f"❌ Syntax error: {e}")
