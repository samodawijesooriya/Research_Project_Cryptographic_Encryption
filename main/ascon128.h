// main/ascon128.h
#ifndef ASCON128_H
#define ASCON128_H

#include <stdint.h>
#include <stddef.h>

// ASCON-128 AEAD, no associated data (matches this benchmark's ENCRYPT_AND_MEASURE
// usage — payload only, no AD stream). Per thesis 3.2.2/3.3.3:
//   key   : 16 bytes (128-bit)
//   nonce : 16 bytes (128-bit)
//   tag   : 16 bytes (128-bit), appended after the ciphertext
//
// out_ciphertext must have room for (payload_len + 16) bytes.
// Returns ciphertext length including the appended tag, i.e. payload_len + 16.
size_t ascon128_encrypt(const uint8_t *key,
                         const uint8_t *nonce,
                         const uint8_t *payload, size_t payload_len,
                         uint8_t *out_ciphertext);

#endif // ASCON128_H