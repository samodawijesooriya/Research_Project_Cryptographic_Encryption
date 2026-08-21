// main/ascon128.c
//
// Software reference implementation of ASCON-128 AEAD (encryption side only —
// this benchmark never decrypts on-device). Implements the standard 320-bit
// permutation-based sponge construction: 128-bit key, 128-bit nonce, 64-bit
// rate, 12-round permutation (p^a) for init/finalization, 6-round permutation
// (p^b) for absorbing data blocks. No associated data is used here, matching
// how RUN_TRIAL/ENCRYPT_AND_MEASURE call this function (payload only).
//
// IMPORTANT: validate this against the official ASCON test vectors
// (https://ascon.iaik.tugraz.at / NIST SP 800-232) before treating its timings
// as representative of an optimized implementation — see the scope note in
// Implementation_V04.md.

#include "ascon128.h"
#include <stdint.h>
#include <string.h>

typedef uint64_t u64;

#define ASCON_IV 0x80400c0600000000ULL   // k=128, r=64, a=12, b=6
#define RATE_BYTES 8
#define ROUNDS_A 12
#define ROUNDS_B 6

static const uint8_t ROUND_CONST[ROUNDS_A] = {
    0xf0, 0xe1, 0xd2, 0xc3, 0xb4, 0xa5, 0x96, 0x87, 0x78, 0x69, 0x5a, 0x4b
};

static inline u64 rotr64(u64 x, int n) {
    return (x >> n) | (x << (64 - n));
}

static inline u64 load_be64(const uint8_t *b) {
    return ((u64)b[0] << 56) | ((u64)b[1] << 48) | ((u64)b[2] << 40) | ((u64)b[3] << 32) |
           ((u64)b[4] << 24) | ((u64)b[5] << 16) | ((u64)b[6] <<  8) | ((u64)b[7]      );
}

static inline void store_be64(uint8_t *b, u64 x) {
    b[0] = (uint8_t)(x >> 56); b[1] = (uint8_t)(x >> 48);
    b[2] = (uint8_t)(x >> 40); b[3] = (uint8_t)(x >> 32);
    b[4] = (uint8_t)(x >> 24); b[5] = (uint8_t)(x >> 16);
    b[6] = (uint8_t)(x >>  8); b[7] = (uint8_t)(x      );
}

// One ASCON permutation round: add round constant, 5-bit S-box (bitsliced),
// linear diffusion layer. S[] is the 320-bit state as five 64-bit words.
static void ascon_round(u64 S[5], uint8_t rc) {
    u64 t0, t1, t2, t3, t4;

    S[2] ^= rc;

    S[0] ^= S[4];
    S[4] ^= S[3];
    S[2] ^= S[1];

    t0 = ~S[0]; t1 = ~S[1]; t2 = ~S[2]; t3 = ~S[3]; t4 = ~S[4];
    t0 &= S[1]; t1 &= S[2]; t2 &= S[3]; t3 &= S[4]; t4 &= S[0];

    S[0] ^= t1; S[1] ^= t2; S[2] ^= t3; S[3] ^= t4; S[4] ^= t0;

    S[1] ^= S[0];
    S[0] ^= S[4];
    S[3] ^= S[2];
    S[2] = ~S[2];

    S[0] ^= rotr64(S[0], 19) ^ rotr64(S[0], 28);
    S[1] ^= rotr64(S[1], 61) ^ rotr64(S[1], 39);
    S[2] ^= rotr64(S[2],  1) ^ rotr64(S[2],  6);
    S[3] ^= rotr64(S[3], 10) ^ rotr64(S[3], 17);
    S[4] ^= rotr64(S[4],  7) ^ rotr64(S[4], 41);
}

static void ascon_permute(u64 S[5], int rounds) {
    int start = ROUNDS_A - rounds;   // p^12 uses all constants, p^6 uses the last 6
    for (int i = start; i < ROUNDS_A; i++) {
        ascon_round(S, ROUND_CONST[i]);
    }
}

size_t ascon128_encrypt(const uint8_t *key,
                         const uint8_t *nonce,
                         const uint8_t *payload, size_t payload_len,
                         uint8_t *out_ciphertext) {
    u64 K0 = load_be64(key);
    u64 K1 = load_be64(key + 8);
    u64 N0 = load_be64(nonce);
    u64 N1 = load_be64(nonce + 8);

    u64 S[5];
    S[0] = ASCON_IV;
    S[1] = K0;
    S[2] = K1;
    S[3] = N0;
    S[4] = N1;

    // --- Initialization ---
    ascon_permute(S, ROUNDS_A);
    S[3] ^= K0;
    S[4] ^= K1;

    // --- Associated data: none in this benchmark, but the domain-separation
    //     bit must still be applied (per spec, even when AD is empty). ---
    S[4] ^= 0x0000000000000001ULL;

    // --- Plaintext processing (rate = 8 bytes/block) ---
    // Per spec there is always a final padding-bearing block after the last
    // real block, even when payload_len is an exact multiple of RATE_BYTES
    // (that final block then carries zero real bytes, just the pad marker).
    // So every full block processed here is followed by a permutation,
    // unconditionally — the loop never contains what will become the last block.
    size_t offset = 0;
    while (payload_len - offset >= RATE_BYTES) {
        u64 p_block = load_be64(payload + offset);
        S[0] ^= p_block;
        store_be64(out_ciphertext + offset, S[0]);
        offset += RATE_BYTES;
        ascon_permute(S, ROUNDS_B);
    }

    // Final (possibly partial, possibly zero-length) block, padded with
    // 0x80 00...00 up to 8 bytes.
    size_t rem = payload_len - offset;
    uint8_t last_block[RATE_BYTES] = {0};
    if (rem > 0) {
        memcpy(last_block, payload + offset, rem);
    }
    last_block[rem] = 0x80;   // padding start bit (valid even if rem == 7 or 0)

    u64 p_last = load_be64(last_block);
    S[0] ^= p_last;

    uint8_t c_last[RATE_BYTES];
    store_be64(c_last, S[0]);
    memcpy(out_ciphertext + offset, c_last, rem);   // only emit the real bytes
    offset += rem;

    // --- Finalization ---
    S[1] ^= K0;
    S[2] ^= K1;
    ascon_permute(S, ROUNDS_A);

    u64 T0 = S[3] ^ K0;
    u64 T1 = S[4] ^ K1;
    store_be64(out_ciphertext + offset, T0);
    store_be64(out_ciphertext + offset + 8, T1);

    return offset + 16;   // ciphertext (== payload_len bytes) + 16-byte tag
}