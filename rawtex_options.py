texture_type = [
    "unknown",
    "r32g32b32a32_typeless",
    "r32g32b32a32_float",
    "r32g32b32a32_uint",
    "r32g32b32a32_sint",
    "r32g32b32_typeless",
    "r32g32b32_float",
    "r32g32b32_uint",
    "r32g32b32_sint",
    "r16g16b16a16_typeless",
    "r16g16b16a16_float",
    "r16g16b16a16_unorm",
    "r16g16b16a16_uint",
    "r16g16b16a16_snorm",
    "r16g16b16a16_sint",
    "r32g32_typeless",
    "r32g32_float",
    "r32g32_uint",
    "r32g32_sint",
    "r32g8x24_typeless",
    "d32_float_s8x24_uint",
    "r32_float_x8x24_typeless",
    "x32_typeless_g8x24_uint",
    "r10g10b10a2_typeless",
    "r10g10b10a2_unorm",
    "r10g10b10a2_uint",
    "r11g11b10_float",
    "r8g8b8a8_typeless",
    "r8g8b8a8_unorm",
    "r8g8b8a8_unorm_srgb",
    "r8g8b8a8_uint",
    "r8g8b8a8_snorm",
    "r8g8b8a8_sint",
    "r16g16_typeless",
    "r16g16_float",
    "r16g16_unorm",
    "r16g16_uint",
    "r16g16_snorm",
    "r16g16_sint",
    "r32_typeless",
    "d32_float",
    "r32_float",
    "r32_uint",
    "r32_sint",
    "r24g8_typeless",
    "d24_unorm_s8_uint",
    "r24_unorm_x8_typeless",
    "x24_typeless_g8_uint",
    "r8g8_typeless",
    "r8g8_unorm",
    "r8g8_uint",
    "r8g8_snorm",
    "r8g8_sint",
    "r16_typeless",
    "r16_float",
    "d16_unorm",
    "r16_unorm",
    "r16_uint",
    "r16_snorm",
    "r16_sint",
    "r8_typeless",
    "r8_unorm",
    "r8_uint",
    "r8_snorm",
    "r8_sint",
    "a8_unorm",
    "r1_unorm",
    "r9g9b9e5_sharedexp",
    "r8g8_b8g8_unorm",
    "g8r8_g8b8_unorm",
    "bc1_typeless",
    "bc1_unorm",
    "bc1_unorm_srgb",
    "bc2_typeless",
    "bc2_unorm",
    "bc2_unorm_srgb",
    "bc3_typeless",
    "bc3_unorm",
    "bc3_unorm_srgb",
    "bc4_typeless",
    "bc4_unorm",
    "bc4_snorm",
    "bc5_typeless",
    "bc5_unorm",
    "bc5_snorm",
    "b5g6r5_unorm",
    "b5g5r5a1_unorm",
    "b8g8r8a8_unorm",
    "b8g8r8x8_unorm",
    "r10g10b10_xr_bias_a2_unorm",
    "b8g8r8a8_typeless",
    "b8g8r8a8_unorm_srgb",
    "b8g8r8x8_typeless",
    "b8g8r8x8_unorm_srgb",
    "bc6h_typeless",
    "bc6h_uf16",
    "bc6h_sf16",
    "bc7_typeless",
    "bc7_unorm",
    "bc7_unorm_srgb",
    "ayuv",
    "y410",
    "y416",
    "nv12",
    "p010",
    "p016",
    "420_opaque",
    "yuy2",
    "y210",
    "y216",
    "nv11",
    "ai44",
    "ia44",
    "p8",
    "a8p8",
    "b4g4r4a4_unorm",
    "p208",
    "v208",
    "v408"
]

pixbl = [1]*278
for i in range(70, 85):
    pixbl[i] = 4
for i in range(94, 100):
    pixbl[i] = 4

bpp = [
    0,
    128,
    128,
    128,
    128,
    96,
    96,
    96,
    96,
    64,
    64,
    64,
    64,
    64,
    64,
    64,
    64,
    64,
    64,
    64,
    64,
    64,
    64,
    32,
    32,
    32,
    32,
    32,
    32,
    32,
    32,
    32,
    32,
    32,
    32,
    32,
    32,
    32,
    32,
    32,
    32,
    32,
    32,
    32,
    32,
    32,
    32,
    32,
    16,
    16,
    16,
    16,
    16,
    16,
    16,
    16,
    16,
    16,
    16,
    16,
    8,
    8,
    8,
    8,
    8,
    8,
    1,
    32,
    32,
    32,
    4,
    4,
    4,
    8,
    8,
    8,
    8,
    8,
    8,
    4,
    4,
    4,
    8,
    8,
    8,
    16,
    16,
    32,
    32,
    32,
    32,
    32,
    32,
    32,
    8,
    8,
    8,
    8,
    8,
    8,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    16
]
