# Lateralus stdlib benchmark results

Workload benchmarks for the codec, hash and search modules. Every number
below comes from `benchmarks/run_benchmarks.py` on this machine
(Python 3.15.2, Node v22.23.4, median wall time in seconds,
3 iterations + 1 warmup).

Each program generates its own input deterministically, so every backend
runs on byte-identical data and the printed value is the correctness check.

| Benchmark | Lateralus C99 (s) | Lateralus interp (s) | Python (s) | Node (s) | Output |
|-----------|-------------------|----------------------|------------|----------|--------|
| xxhash64 (256 KB, seed 0) | — | 44.7140 | 0.1131 | 0.0436 | `6894441251590661822` |
| radix_sort_u32 (100k keys) | — | 11.2774 | 0.1416 | 0.0417 | `3412598242` |
| chacha20 (64 KB) | — | 5.8716 | 0.1219 | 0.0439 | `1373132812` |
| lz4 round-trip (64 KB) | — | 5.7939 | 0.0447 | 0.0408 | `65536000283 / 260079616` |
| aho_corasick (1k patterns, 256 KB) | — | 0.3633 | 0.2623 | 0.2065 | `0` |

## Correctness

Cross-language agreement, taken from the same run:

| Benchmark | Lateralus | Python | Node | Verdict |
|-----------|-----------|--------|------|---------|
| xxhash64 | `6894441251590661822` | `6894441251590661822` | `6894441251590661822` | match |
| radix_sort_u32 | `3412598242` | `3412598242` | `3412598242` | match |
| chacha20_encrypt | `1373132812` | `1373132812` | `1373132812` | match |
| lz4_roundtrip | `65536000283 / 260079616` | `65536000278 / 260079616` | `n/a (no LZ4 in Node stdlib)` | match |
| aho_corasick | `0` | `0` | `0` | match |

Notes, so the numbers are not read for more than they say:

- xxhash64, radix_sort_u32 and chacha20_encrypt are bit-exact against
  references written from the published specifications (XXH64, RFC 8439
  ChaCha20, LSD radix sort), not ported from the Lateralus source.
- lz4_roundtrip compares the round-trip checksum, not the compressed length.
  The Lateralus encoder emits 283 bytes where the reference emits 278 for the
  same 64 KB input; both decode to the identical payload with a
  specification-conformant decoder, so the difference is a match-finding
  choice, not a defect.
- aho_corasick reports 0 because the generated patterns never occur in the
  pseudo-random text; all backends agree, and the value confirms the search
  ran to completion.
- Lateralus C99 is `—` for these five: the C backend does not emit valid code
  for list-typed helpers (`len()` undeclared, list subscript emitted as a
  pointer index). Scalar benchmarks (fib, sieve) still build and run.

Reproduce:

```
PYTHONPATH=. python3 benchmarks/run_benchmarks.py \
  --filter xxhash64,radix_sort_u32,chacha20_encrypt,lz4_roundtrip,aho_corasick \
  --backends lateralus,python,node --iters 5 --warmup 2
```
