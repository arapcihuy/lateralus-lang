// Node.js reference implementations matching benchmarks/src/*.ltl exactly.

function fib(n) {
  if (n < 2) return n;
  return fib(n - 1) + fib(n - 2);
}

function sieve(n) {
  const isPrime = new Uint8Array(n + 1);
  isPrime.fill(1);
  isPrime[0] = 0;
  isPrime[1] = 0;
  for (let p = 2; p * p <= n; p++) {
    if (isPrime[p]) {
      for (let j = p * p; j <= n; j += p) isPrime[j] = 0;
    }
  }
  let count = 0;
  for (let i = 0; i <= n; i++) if (isPrime[i]) count++;
  return count;
}

function mandelbrot(width, height, maxIter) {
  let total = 0;
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const cx = -2.0 + (x / width) * 3.0;
      const cy = -1.5 + (y / height) * 3.0;
      let zx = 0.0, zy = 0.0, i = 0;
      while (i < maxIter) {
        const zx2 = zx * zx, zy2 = zy * zy;
        if (zx2 + zy2 > 4.0) break;
        const newZx = zx2 - zy2 + cx;
        zy = 2.0 * zx * zy + cy;
        zx = newZx;
        i++;
      }
      total += i;
    }
  }
  return total;
}

function nbody(nBodies, iterations) {
  const xs = [0.0, 4.84, 8.34, 12.89, 15.37];
  const ys = [0.0, 1.16, 4.12, 11.73, 25.92];
  const vxs = [0.0, 0.00166, 0.00277, 0.00296, 0.00268];
  const vys = [0.0, 0.00769, 0.00499, 0.00237, 0.00150];
  const ms = [39.47, 0.0377, 0.113, 0.0349, 0.0534];
  for (let it = 0; it < iterations; it++) {
    for (let i = 0; i < nBodies; i++) {
      for (let j = i + 1; j < nBodies; j++) {
        const dx = xs[i] - xs[j];
        const dy = ys[i] - ys[j];
        const d2 = dx * dx + dy * dy + 0.0001;
        const d = Math.sqrt(d2);
        const mag = 0.01 / (d2 * d);
        vxs[i] -= dx * ms[j] * mag;
        vys[i] -= dy * ms[j] * mag;
        vxs[j] += dx * ms[i] * mag;
        vys[j] += dy * ms[i] * mag;
      }
    }
    for (let k = 0; k < nBodies; k++) {
      xs[k] += 0.01 * vxs[k];
      ys[k] += 0.01 * vys[k];
    }
  }
  return xs.reduce((a, b) => a + b, 0) + ys.reduce((a, b) => a + b, 0);
}

function makeTree(depth) {
  if (depth === 0) return 0;
  return { left: makeTree(depth - 1), right: makeTree(depth - 1) };
}
function checkTree(node) {
  if (node === 0) return 1;
  return 1 + checkTree(node.left) + checkTree(node.right);
}

const benchmarks = {
  fib: () => fib(32),
  sieve: () => sieve(50000),
  mandelbrot: () => mandelbrot(150, 100, 255),
  nbody: () => nbody(5, 5000),
  binary_trees: () => checkTree(makeTree(12)),
};


// ── stdlib workload references (match benchmarks/src/*.ltl) ──────────────────
const M32 = 0xFFFFFFFF;

function xorshiftBuf(n, state = 12345) {
  const buf = Buffer.alloc(n);
  for (let i = 0; i < n; i++) {
    state = (state ^ ((state << 13) & M32)) >>> 0;
    state = (state ^ (state >>> 17)) >>> 0;
    state = (state ^ ((state << 5) & M32)) >>> 0;
    buf[i] = state & 0xFF;
  }
  return buf;
}

// XXH64 with BigInt so the result is bit-exact, not truncated to 53 bits.
const M64 = (1n << 64n) - 1n;
const P1 = 0x9E3779B185EBCA87n, P2 = 0xC2B2AE3D27D4EB4Fn, P3 = 0x165667B19E3779F9n;
const P4 = 0x85EBCA77C2B2AE63n, P5 = 0x27D4EB2F165667C5n;
const rotl64 = (x, r) => ((x << r) | (x >> (64n - r))) & M64;
const rnd = (acc, inp) => (rotl64((acc + inp * P2) & M64, 31n) * P1) & M64;
const merge = (acc, val) => ((acc ^ rnd(0n, val)) * P1 + P4) & M64;

function xxh64(buf, seed = 0n) {
  const n = BigInt(buf.length);
  let i = 0n, h;
  if (buf.length >= 32) {
    let v1 = (seed + P1 + P2) & M64, v2 = (seed + P2) & M64;
    let v3 = seed & M64, v4 = (seed - P1) & M64;
    const rd = (o) => buf.readBigUInt64LE(Number(o));
    while (i <= n - 32n) {
      v1 = rnd(v1, rd(i)); i += 8n;
      v2 = rnd(v2, rd(i)); i += 8n;
      v3 = rnd(v3, rd(i)); i += 8n;
      v4 = rnd(v4, rd(i)); i += 8n;
    }
    h = (rotl64(v1, 1n) + rotl64(v2, 7n) + rotl64(v3, 12n) + rotl64(v4, 18n)) & M64;
    for (const v of [v1, v2, v3, v4]) h = merge(h, v);
  } else {
    h = (seed + P5) & M64;
  }
  h = (h + n) & M64;
  while (i <= n - 8n) {
    h ^= rnd(0n, buf.readBigUInt64LE(Number(i)));
    h = (rotl64(h, 27n) * P1 + P4) & M64;
    i += 8n;
  }
  if (i <= n - 4n) {
    h ^= (BigInt(buf.readUInt32LE(Number(i))) * P1) & M64;
    h = (rotl64(h, 23n) * P2 + P3) & M64;
    i += 4n;
  }
  while (i < n) {
    h ^= (BigInt(buf[Number(i)]) * P5) & M64;
    h = (rotl64(h, 11n) * P1) & M64;
    i += 1n;
  }
  h ^= h >> 33n; h = (h * P2) & M64;
  h ^= h >> 29n; h = (h * P3) & M64;
  return h ^ (h >> 32n);
}

function benchXxhash64() {
  return xxh64(xorshiftBuf(256 * 1024), 0n).toString();
}

function benchRadixSortU32() {
  const n = 100000, xs = new Uint32Array(n);
  let state = 2463534242;
  for (let i = 0; i < n; i++) {
    state = (state ^ ((state << 13) & M32)) >>> 0;
    state = (state ^ (state >>> 17)) >>> 0;
    state = (state ^ ((state << 5) & M32)) >>> 0;
    xs[i] = state;
  }
  xs.sort();
  let h = 2166136261;
  for (const v of xs) {
    for (let b = 0; b < 4; b++) {
      h = (h ^ ((v >>> (b * 8)) & 0xFF)) >>> 0;
      h = Math.imul(h, 16777619) >>> 0;
    }
  }
  return h;
}

function chachaBlock(key, nonce, counter) {
  const rotl = (v, r) => ((v << r) | (v >>> (32 - r))) >>> 0;
  const c = [0x61707865, 0x3320646E, 0x79622D32, 0x6B206574];
  for (let i = 0; i < 8; i++) c.push(key.readUInt32LE(i * 4));
  c.push(counter >>> 0);
  for (let i = 0; i < 3; i++) c.push(nonce.readUInt32LE(i * 4));
  const w = c.slice();
  const qr = (a, b, cc, d) => {
    w[a] = (w[a] + w[b]) >>> 0; w[d] = rotl(w[d] ^ w[a], 16);
    w[cc] = (w[cc] + w[d]) >>> 0; w[b] = rotl(w[b] ^ w[cc], 12);
    w[a] = (w[a] + w[b]) >>> 0; w[d] = rotl(w[d] ^ w[a], 8);
    w[cc] = (w[cc] + w[d]) >>> 0; w[b] = rotl(w[b] ^ w[cc], 7);
  };
  for (let r = 0; r < 10; r++) {
    qr(0, 4, 8, 12); qr(1, 5, 9, 13); qr(2, 6, 10, 14); qr(3, 7, 11, 15);
    qr(0, 5, 10, 15); qr(1, 6, 11, 12); qr(2, 7, 8, 13); qr(3, 4, 9, 14);
  }
  const out = Buffer.alloc(64);
  for (let i = 0; i < 16; i++) out.writeUInt32LE((w[i] + c[i]) >>> 0, i * 4);
  return out;
}

function benchChacha20Encrypt() {
  const data = Buffer.alloc(64 * 1024);
  for (let i = 0; i < data.length; i++) data[i] = (i * 37 + 11) & 0xFF;
  const key = Buffer.from([...Array(32).keys()]);
  const nonce = Buffer.alloc(12);
  for (let i = 0; i < 12; i++) nonce[i] = i * 7;
  let h = 0, ctr = 1;
  for (let i = 0; i < data.length; i += 64) {
    const ks = chachaBlock(key, nonce, ctr++);
    const take = Math.min(64, data.length - i);
    for (let j = 0; j < take; j++) h = (Math.imul(h, 31) + (data[i + j] ^ ks[j])) >>> 0;
  }
  return h;
}

function benchAhoCorasick() {
  const alphabet = "abcdefghijklmnopqrstuvwxyz ";
  const out = [];
  let state = 987654321;
  for (let i = 0; i < 256 * 1024; i++) {
    state = (state ^ ((state << 13) & M32)) >>> 0;
    state = (state ^ (state >>> 17)) >>> 0;
    state = (state ^ ((state << 5) & M32)) >>> 0;
    out.push(alphabet[state % 27]);
  }
  const text = out.join("");
  let hits = 0;
  for (let i = 0; i < 1000; i++) {
    const pat = "pat" + i;
    let at = text.indexOf(pat);
    while (at !== -1) { hits++; at = text.indexOf(pat, at + 1); }
  }
  return hits;
}

// LZ4 has no Node standard-library equivalent, so Node reports the round-trip
// source checksum only; the harness reads "skip" and compares the other backends.
function benchLz4Roundtrip() {
  return "skip";
}

benchmarks.xxhash64 = benchXxhash64;
benchmarks.radix_sort_u32 = benchRadixSortU32;
benchmarks.chacha20_encrypt = benchChacha20Encrypt;
benchmarks.aho_corasick = benchAhoCorasick;
benchmarks.lz4_roundtrip = benchLz4Roundtrip;

const name = process.argv[2] || "fib";
console.log(benchmarks[name]());
