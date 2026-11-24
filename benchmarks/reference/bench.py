"""Python reference implementations matching benchmarks/src/*.ltl exactly."""
import math
import sys


def fib(n):
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)


def sieve(n):
    is_prime = [True] * (n + 1)
    is_prime[0] = False
    is_prime[1] = False
    p = 2
    while p * p <= n:
        if is_prime[p]:
            j = p * p
            while j <= n:
                is_prime[j] = False
                j += p
        p += 1
    return sum(1 for x in is_prime if x)


def mandelbrot(width, height, max_iter):
    total = 0
    for y in range(height):
        for x in range(width):
            cx = -2.0 + (x / width) * 3.0
            cy = -1.5 + (y / height) * 3.0
            zx = 0.0
            zy = 0.0
            i = 0
            while i < max_iter:
                zx2 = zx * zx
                zy2 = zy * zy
                if zx2 + zy2 > 4.0:
                    break
                new_zx = zx2 - zy2 + cx
                zy = 2.0 * zx * zy + cy
                zx = new_zx
                i += 1
            total += i
    return total


def nbody(n_bodies, iterations):
    xs = [0.0, 4.84, 8.34, 12.89, 15.37]
    ys = [0.0, 1.16, 4.12, 11.73, 25.92]
    vxs = [0.0, 0.00166, 0.00277, 0.00296, 0.00268]
    vys = [0.0, 0.00769, 0.00499, 0.00237, 0.00150]
    ms = [39.47, 0.0377, 0.113, 0.0349, 0.0534]
    for _ in range(iterations):
        for i in range(n_bodies):
            for j in range(i + 1, n_bodies):
                dx = xs[i] - xs[j]
                dy = ys[i] - ys[j]
                d2 = dx * dx + dy * dy + 0.0001
                d = math.sqrt(d2)
                mag = 0.01 / (d2 * d)
                vxs[i] -= dx * ms[j] * mag
                vys[i] -= dy * ms[j] * mag
                vxs[j] += dx * ms[i] * mag
                vys[j] += dy * ms[i] * mag
        for k in range(n_bodies):
            xs[k] += 0.01 * vxs[k]
            ys[k] += 0.01 * vys[k]
    return sum(xs) + sum(ys)


class Tree:
    __slots__ = ("left", "right")

    def __init__(self, left, right):
        self.left = left
        self.right = right


def make_tree(depth):
    if depth == 0:
        return 0
    return Tree(make_tree(depth - 1), make_tree(depth - 1))


def check_tree(node):
    if node == 0:
        return 1
    return 1 + check_tree(node.left) + check_tree(node.right)


BENCHMARKS = {
    "fib": lambda: fib(32),
    "sieve": lambda: sieve(50000),
    "mandelbrot": lambda: mandelbrot(150, 100, 255),
    "nbody": lambda: nbody(5, 5000),
    "binary_trees": lambda: check_tree(make_tree(12)),
}


# ── stdlib workload references (match benchmarks/src/*.ltl) ──────────────────
M64 = (1 << 64) - 1
M32 = 0xFFFFFFFF
_P1, _P2, _P3, _P4, _P5 = (0x9E3779B185EBCA87, 0xC2B2AE3D27D4EB4F, 0x165667B19E3779F9,
                           0x85EBCA77C2B2AE63, 0x27D4EB2F165667C5)


def _rotl64(x, r):
    return ((x << r) | (x >> (64 - r))) & M64


def _rnd(acc, inp):
    return (_rotl64((acc + inp * _P2) & M64, 31) * _P1) & M64


def _merge(acc, val):
    return ((acc ^ _rnd(0, val)) * _P1 + _P4) & M64


def xxh64(data, seed=0):
    n, i = len(data), 0
    if n >= 32:
        v1, v2, v3, v4 = (seed + _P1 + _P2) & M64, (seed + _P2) & M64, seed & M64, (seed - _P1) & M64
        while i <= n - 32:
            v1 = _rnd(v1, int.from_bytes(data[i:i + 8], "little")); i += 8
            v2 = _rnd(v2, int.from_bytes(data[i:i + 8], "little")); i += 8
            v3 = _rnd(v3, int.from_bytes(data[i:i + 8], "little")); i += 8
            v4 = _rnd(v4, int.from_bytes(data[i:i + 8], "little")); i += 8
        h = (_rotl64(v1, 1) + _rotl64(v2, 7) + _rotl64(v3, 12) + _rotl64(v4, 18)) & M64
        for v in (v1, v2, v3, v4):
            h = _merge(h, v)
    else:
        h = (seed + _P5) & M64
    h = (h + n) & M64
    while i <= n - 8:
        h ^= _rnd(0, int.from_bytes(data[i:i + 8], "little"))
        h = (_rotl64(h, 27) * _P1 + _P4) & M64
        i += 8
    if i <= n - 4:
        h ^= (int.from_bytes(data[i:i + 4], "little") * _P1) & M64
        h = (_rotl64(h, 23) * _P2 + _P3) & M64
        i += 4
    while i < n:
        h ^= (data[i] * _P5) & M64
        h = (_rotl64(h, 11) * _P1) & M64
        i += 1
    h ^= h >> 33; h = (h * _P2) & M64
    h ^= h >> 29; h = (h * _P3) & M64
    return h ^ (h >> 32)


def bench_xxhash64():
    buf, state = bytearray(), 12345
    for _ in range(256 * 1024):
        state = (state ^ ((state << 13) & M32)) & M32
        state ^= state >> 17
        state = (state ^ ((state << 5) & M32)) & M32
        buf.append(state & 0xFF)
    return xxh64(bytes(buf), 0)


def bench_radix_sort_u32():
    xs, state = [], 2463534242
    for _ in range(100000):
        state = (state ^ ((state << 13) & M32)) & M32
        state ^= state >> 17
        state = (state ^ ((state << 5) & M32)) & M32
        xs.append(state)
    h = 2166136261
    for v in sorted(xs):
        for b in range(4):
            h = (h ^ ((v >> (b * 8)) & 0xFF)) & M32
            h = (h * 16777619) & M32
    return h


def _chacha_block(key, nonce, counter):
    c = [0x61707865, 0x3320646E, 0x79622D32, 0x6B206574]
    c += [int.from_bytes(bytes(key[i:i + 4]), "little") for i in range(0, 32, 4)]
    c += [counter]
    c += [int.from_bytes(bytes(nonce[i:i + 4]), "little") for i in range(0, 12, 4)]
    w = c[:]

    def rotl(v, r):
        return ((v << r) | (v >> (32 - r))) & M32

    def qr(a, b, cc, d):
        w[a] = (w[a] + w[b]) & M32; w[d] = rotl(w[d] ^ w[a], 16)
        w[cc] = (w[cc] + w[d]) & M32; w[b] = rotl(w[b] ^ w[cc], 12)
        w[a] = (w[a] + w[b]) & M32; w[d] = rotl(w[d] ^ w[a], 8)
        w[cc] = (w[cc] + w[d]) & M32; w[b] = rotl(w[b] ^ w[cc], 7)

    for _ in range(10):
        qr(0, 4, 8, 12); qr(1, 5, 9, 13); qr(2, 6, 10, 14); qr(3, 7, 11, 15)
        qr(0, 5, 10, 15); qr(1, 6, 11, 12); qr(2, 7, 8, 13); qr(3, 4, 9, 14)
    out = []
    for i in range(16):
        out += list(((w[i] + c[i]) & M32).to_bytes(4, "little"))
    return out


def bench_chacha20_encrypt():
    data = [(i * 37 + 11) & 0xFF for i in range(64 * 1024)]
    key, nonce = list(range(32)), [i * 7 for i in range(12)]
    ct, i, ctr = [], 0, 1
    while i < len(data):
        ks = _chacha_block(key, nonce, ctr)
        take = min(64, len(data) - i)
        ct += [data[i + j] ^ ks[j] for j in range(take)]
        i += take
        ctr += 1
    h = 0
    for b in ct:
        h = (h * 31 + b) & M32
    return h


def lz4_block_compress(src):
    n = len(src)
    out = bytearray()
    anchor, i = 0, 0
    while i < n:
        m, j = -1, i - 1
        while j >= 0 and j >= i - 65535:
            if src[j:j + 4] == src[i:i + 4] and i + 4 <= n:
                m = j
                break
            j -= 1
        if m < 0:
            i += 1
            continue
        lit = i - anchor
        ml = 0
        while i + 4 + ml < n and src[m + 4 + ml] == src[i + 4 + ml] and ml < 65535:
            ml += 1
        out.append((min(lit, 15) << 4) | min(ml, 15))
        if lit >= 15:
            rem = lit - 15
            while rem >= 255:
                out.append(255); rem -= 255
            out.append(rem)
        out += src[anchor:i]
        out += ((i - m) & 0xFFFF).to_bytes(2, "little")
        if ml >= 15:
            rem = ml - 15
            while rem >= 255:
                out.append(255); rem -= 255
            out.append(rem)
        i += 4 + ml
        anchor = i
    lit = n - anchor
    out.append(min(lit, 15) << 4)
    if lit >= 15:
        rem = lit - 15
        while rem >= 255:
            out.append(255); rem -= 255
        out.append(rem)
    out += src[anchor:]
    return bytes(out)


def lz4_block_decompress(packed, expected):
    out = bytearray()
    i = 0
    while i < len(packed):
        tok = packed[i]; i += 1
        lit = tok >> 4
        if lit == 15:
            while True:
                b = packed[i]; i += 1
                lit += b
                if b != 255:
                    break
        out += packed[i:i + lit]; i += lit
        if i >= len(packed):
            break
        off = int.from_bytes(packed[i:i + 2], "little"); i += 2
        ml = tok & 0x0F
        if ml == 15:
            while True:
                b = packed[i]; i += 1
                ml += b
                if b != 255:
                    break
        start = len(out) - off
        for k in range(ml + 4):
            out.append(out[start + k])
    return bytes(out)


def bench_lz4_roundtrip():
    src = bytes(i % 16 for i in range(4 * 1024 * 1024 // 64))
    packed = lz4_block_compress(src)
    back = lz4_block_decompress(packed, len(src))
    h = 0
    for b in back:
        h = (h * 31 + b) & M32
    return (len(src) * 1000000 + len(packed), h)


def bench_aho_corasick():
    alphabet = "abcdefghijklmnopqrstuvwxyz "
    out, state = [], 987654321
    for _ in range(256 * 1024):
        state = (state ^ ((state << 13) & M32)) & M32
        state ^= state >> 17
        state = (state ^ ((state << 5) & M32)) & M32
        out.append(alphabet[state % 27])
    text = "".join(out)
    return sum(text.count("pat" + str(i)) for i in range(1000))


WORKLOADS = {
    "xxhash64": bench_xxhash64,
    "radix_sort_u32": bench_radix_sort_u32,
    "chacha20_encrypt": bench_chacha20_encrypt,
    "lz4_roundtrip": bench_lz4_roundtrip,
    "aho_corasick": bench_aho_corasick,
}


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "fib"
    if name in WORKLOADS:
        result = WORKLOADS[name]()
        print("\n".join(str(x) for x in result) if isinstance(result, tuple) else result)
    else:
        print(BENCHMARKS[name]())
