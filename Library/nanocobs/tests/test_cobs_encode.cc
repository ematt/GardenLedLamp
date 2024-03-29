#include "../cobs.h"
#include "catch.hpp"

#include <cstring>

using byte_vec_t = std::vector< unsigned char >;

TEST_CASE("Encoding validation", "[cobs_encode]") {
  unsigned char enc[32], dec[32];
  unsigned const enc_n = sizeof(enc);
  unsigned const dec_n = sizeof(dec);
  unsigned enc_len;

  SECTION("Null buffer pointer") {
    REQUIRE( cobs_encode(nullptr, dec_n, enc, enc_n, &enc_len) ==
             COBS_RET_ERR_BAD_ARG );
    REQUIRE( cobs_encode(dec, dec_n, nullptr, enc_n, &enc_len) ==
             COBS_RET_ERR_BAD_ARG );
    REQUIRE( cobs_encode(dec, dec_n, enc, enc_n, nullptr) ==
             COBS_RET_ERR_BAD_ARG );
  }

  SECTION("Invalid enc_max") {
    REQUIRE( cobs_encode(dec, dec_n, enc, 0, &enc_len) ==
             COBS_RET_ERR_BAD_ARG );
    REQUIRE( cobs_encode(dec, dec_n, enc, 1, &enc_len) ==
             COBS_RET_ERR_BAD_ARG );
    REQUIRE( cobs_encode(dec, dec_n, enc, dec_n - 2, &enc_len) ==
             COBS_RET_ERR_BAD_ARG );
    REQUIRE( cobs_encode(dec, dec_n, enc, dec_n - 1, &enc_len) ==
             COBS_RET_ERR_BAD_ARG );
  }
}

TEST_CASE("Simple encodings", "[cobs_encode]") {
  unsigned char dec[16];
  unsigned char enc[16];
  unsigned enc_len;

  SECTION("Empty") {
    REQUIRE( cobs_encode(&dec, 0, enc, sizeof(enc), &enc_len) ==
             COBS_RET_SUCCESS );
    REQUIRE( byte_vec_t(enc, enc + enc_len) == byte_vec_t{0x01, 0x00} );
  }

  SECTION("1 nonzero byte") {
    dec[0] = 0x34;
    REQUIRE( cobs_encode(&dec, 1, enc, sizeof(enc), &enc_len) ==
             COBS_RET_SUCCESS );
    REQUIRE( byte_vec_t(enc, enc + enc_len) == byte_vec_t{0x02, 0x34, 0x00} );
  }

  SECTION("2 nonzero bytes") {
    dec[0] = 0x34;
    dec[1] = 0x56;
    REQUIRE( cobs_encode(&dec, 2, enc, sizeof(enc), &enc_len) ==
             COBS_RET_SUCCESS );
    REQUIRE( byte_vec_t(enc, enc + enc_len) ==
             byte_vec_t{0x03, 0x34, 0x56, 0x00} );
  }

  SECTION("8 nonzero bytes") {
    dec[0] = 0x12;
    dec[1] = 0x34;
    dec[2] = 0x56;
    dec[3] = 0x78;
    dec[4] = 0x9A;
    dec[5] = 0xBC;
    dec[6] = 0xDE;
    dec[7] = 0xFF;
    REQUIRE( cobs_encode(&dec, 8, enc, sizeof(enc), &enc_len) ==
             COBS_RET_SUCCESS );
    REQUIRE( byte_vec_t(enc, enc + enc_len) ==
             byte_vec_t{0x09,0x12,0x34,0x56,0x78,0x9A,0xBC,0xDE,0xFF,0x00} );
  }

  SECTION("1 zero byte") {
    dec[0] = 0x00;
    REQUIRE( cobs_encode(&dec, 1, enc, sizeof(enc), &enc_len) ==
             COBS_RET_SUCCESS );
    REQUIRE( byte_vec_t(enc, enc + enc_len) == byte_vec_t{0x01, 0x01, 0x00} );
  }

  SECTION("2 zero bytes") {
    dec[0] = 0x00;
    dec[1] = 0x00;
    REQUIRE( cobs_encode(&dec, 2, enc, sizeof(enc), &enc_len) ==
             COBS_RET_SUCCESS );
    REQUIRE( byte_vec_t(enc, enc + enc_len) ==
             byte_vec_t{0x01, 0x01, 0x01, 0x00} );
  }

  SECTION("8 nonzero bytes") {
    memset(dec, 0, 8);
    REQUIRE( cobs_encode(&dec, 8, enc, sizeof(enc), &enc_len) ==
             COBS_RET_SUCCESS );
    REQUIRE( byte_vec_t(enc, enc + enc_len) ==
             byte_vec_t{0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x01,0x00} );
  }

  SECTION("4 alternating zero/nonzero bytes") {
    dec[0] = 0x00;
    dec[1] = 0x11;
    dec[2] = 0x00;
    dec[3] = 0x22;
    REQUIRE( cobs_encode(&dec, 4, enc, sizeof(enc), &enc_len) ==
             COBS_RET_SUCCESS );
    REQUIRE( byte_vec_t(enc, enc + enc_len) ==
             byte_vec_t{0x01, 0x02, 0x11, 0x02, 0x22, 0x00} );
  }
}

TEST_CASE("0xFF single code-block case", "[cobs_encode]") {
  byte_vec_t dec(254, 0x01);
  byte_vec_t enc( cobs_encode_max(static_cast< unsigned >(dec.size())) );
  unsigned enc_len;
  REQUIRE( cobs_encode(dec.data(),
                       static_cast< unsigned >(dec.size()),
                       enc.data(),
                       static_cast< unsigned >(enc.size()),
                       &enc_len) == COBS_RET_SUCCESS );

  byte_vec_t expected(255, 0x01);
  expected[0] = 0xFF;
  expected.push_back(0x00);
  REQUIRE ( enc == expected );
}
