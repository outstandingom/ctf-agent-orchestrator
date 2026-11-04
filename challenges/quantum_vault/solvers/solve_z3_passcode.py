import z3

def solve_quantum_passcode():
    s = z3.Solver()
    b = [z3.BitVec(f"b_{i}", 8) for i in range(16)]

    # Printable ASCII range constraint (32 to 126)
    for i in range(16):
        s.add(b[i] >= 32, b[i] <= 126)

    # Challenge constraints
    s.add((b[0] ^ 0x5C) == 0x3F)
    s.add((z3.ZeroExt(8, b[1]) * 13 + z3.ZeroExt(8, b[2]) * 7) % 256 == 189)
    s.add((b[3] ^ b[4]) == 0x1B)
    s.add((z3.ZeroExt(8, b[5]) + z3.ZeroExt(8, b[6]) * 3) % 251 == 42)
    s.add((b[7] ^ 0xAA) == 0xDF)
    s.add(((b[8] << 2) | (b[9] >> 6)) & 0xFF == 0x94)
    s.add(z3.ZeroExt(8, b[10] ^ b[11]) + z3.ZeroExt(8, b[12]) == 173)
    s.add((z3.ZeroExt(8, b[13]) * z3.ZeroExt(8, b[14])) % 256 == 96)
    s.add((b[15] ^ 0x33) == 0x56)

    if s.check() == z3.sat:
        m = s.model()
        passcode = "".join(chr(m[b[i]].as_long()) for i in range(16))
        print(f"[Z3 SOLVER] Solution Found: '{passcode}' (Hex: {[hex(ord(c)) for c in passcode]})")
        return passcode
    else:
        print("[Z3 SOLVER] Unsat!")
        return None

if __name__ == "__main__":
    solve_quantum_passcode()
