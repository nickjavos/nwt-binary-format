// C++20 NWT 1.1 codec. Every record layout, enum, flag mask and text limit comes from
// schemas/records.json (embedded as schema_json); nothing here is written per record type.
// No floating point, and wire data is read with explicit byte shifts or memcpy, never cast.
// Build: c++ -std=c++20 -O2 -DNWT_ZSTD -I/opt/homebrew/include -L/opt/homebrew/lib main.cpp -lzstd
// Without -DNWT_ZSTD, codec 1 fails with "Zstd library not available" and raw files still work.
#include "example_data.hpp"
#include "vendor/json.hpp"
#include <algorithm>
#include <array>
#include <bit>
#include <charconv>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <functional>
#include <iostream>
#include <limits>
#include <map>
#include <memory>
#include <optional>
#include <set>
#include <span>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <type_traits>
#include <utility>
#include <vector>
#ifdef NWT_ZSTD
#include <zstd.h>
#endif
// Hardware CRC32C where the compiler targets an instruction for it; the table is the fallback.
#if defined(__ARM_FEATURE_CRC32)
#include <arm_acle.h>
#define NWT_HW_CRC 1
#elif defined(__SSE4_2__) && defined(__x86_64__)
#include <nmmintrin.h>
#define NWT_HW_CRC 2
#endif
using J = nlohmann::json;
using Bytes = std::vector<std::uint8_t>;
using View = std::span<const std::uint8_t>;
using U = std::uint64_t;
using U128 = unsigned __int128;
constexpr U NIL = std::numeric_limits<U>::max();
constexpr std::int64_t NIL_I = std::numeric_limits<std::int64_t>::min();
constexpr U LIMIT = 16777216; // largest frame payload and largest Zstd window
constexpr std::size_t MAXREC = 1048576;
constexpr std::size_t MAXF = 128; // most fields (header + body) one schema may have
constexpr bool LE = std::endian::native == std::endian::little;
const J SS = J::parse(schema_json);
const char *USAGE =
    "usage: nwt-example write FILE | write-v11 FILE [--zstd] | read FILE [REENCODED_FILE] | "
    "record TYPE FILE | decode-record FILE | to-json FILE [--pretty] | to-csv FILE TYPE [--pretty] | bench FILE";

void need(bool ok, const char *message) {
  if (!ok)
    throw std::runtime_error(message);
}
[[noreturn]] void fail(const std::string &message) {
  throw std::runtime_error(message);
}
U parse_u(const std::string &s) {
  U v = 0;
  auto r = std::from_chars(s.data(), s.data() + s.size(), v);
  need(r.ec == std::errc{} && r.ptr == s.data() + s.size(), "unsigned integer");
  return v;
}
std::int64_t parse_i(const std::string &s) {
  std::int64_t v = 0;
  auto r = std::from_chars(s.data(), s.data() + s.size(), v);
  need(r.ec == std::errc{} && r.ptr == s.data() + s.size(), "signed integer");
  return v;
}

// ------------------------------------------------------------ bytes and CRC

constexpr std::array<std::uint32_t, 256> make_crc_table() {
  std::array<std::uint32_t, 256> t{};
  for (std::uint32_t i = 0; i < 256; i++) {
    std::uint32_t c = i;
    for (int k = 0; k < 8; k++)
      c = (c >> 1) ^ ((c & 1) ? 0x82f63b78u : 0u);
    t[i] = c;
  }
  return t;
}
constexpr auto CRC_T = make_crc_table();
std::uint32_t crc_sw(const std::uint8_t *p, std::size_t n) {
  std::uint32_t c = 0xffffffffu;
  for (; n; --n, ++p)
    c = CRC_T[(c ^ *p) & 255] ^ (c >> 8);
  return c ^ 0xffffffffu;
}
#ifdef NWT_HW_CRC
static_assert(LE, "the hardware CRC path loads 8 bytes at a time");
std::uint32_t crc_hw(const std::uint8_t *p, std::size_t n) {
  std::uint32_t c = 0xffffffffu;
  while (n >= 8) {
    U w;
    std::memcpy(&w, p, 8);
#if NWT_HW_CRC == 1
    c = __crc32cd(c, w);
#else
    c = std::uint32_t(_mm_crc32_u64(c, w));
#endif
    p += 8;
    n -= 8;
  }
  for (; n; --n, ++p) {
#if NWT_HW_CRC == 1
    c = __crc32cb(c, *p);
#else
    c = _mm_crc32_u8(c, *p);
#endif
  }
  return c ^ 0xffffffffu;
}
#endif
// The hardware path is used only when it reproduces the standard check value.
const bool USE_HW = [] {
#ifdef NWT_HW_CRC
  const std::uint8_t s[] = {'1', '2', '3', '4', '5', '6', '7', '8', '9'};
  return crc_hw(s, 9) == 0xe3069283u;
#else
  return false;
#endif
}();
std::uint32_t crc(View b) {
#ifdef NWT_HW_CRC
  if (USE_HW)
    return crc_hw(b.data(), b.size());
#endif
  return crc_sw(b.data(), b.size());
}
Bytes bytes(const std::string &s) { return Bytes(s.begin(), s.end()); }
void append(Bytes &b, View x) { b.insert(b.end(), x.begin(), x.end()); }
Bytes pad(Bytes b) {
  b.resize((b.size() + 7) & ~std::size_t(7), 0);
  return b;
}
U get(View b, std::size_t o, std::size_t n) {
  need(n <= 8 && o <= b.size() && n <= b.size() - o, "integer bounds");
  U x = 0;
  for (std::size_t i = 0; i < n; i++)
    x |= U(b[o + i]) << (8 * i);
  return x;
}
void put(Bytes &b, std::size_t o, std::size_t n, U x) {
  need(o <= b.size() && n <= b.size() - o, "write bounds");
  for (std::size_t i = 0; i < n; i++)
    b[o + i] = std::uint8_t(x >> (8 * i));
}
Bytes hcrc(Bytes b, std::size_t o) {
  put(b, o, 4, 0);
  put(b, o, 4, crc(b));
  return b;
}
void vh(View b, std::size_t o) {
  need(b.size() == 64, "header size");
  auto c = get(b, o, 4);
  Bytes t(b.begin(), b.end());
  put(t, o, 4, 0);
  need(crc(t) == c, "header CRC");
}
bool zero(View b) {
  return std::all_of(b.begin(), b.end(), [](auto x) { return x == 0; });
}
bool magic(View b, const std::string &s) {
  return b.size() >= s.size() && std::equal(s.begin(), s.end(), b.begin());
}
// Strict UTF-8 (no overlong forms, no surrogates, nothing above U+10FFFF) and no NUL.
bool text_ok(const char *c, std::size_t n) {
  auto s = reinterpret_cast<const std::uint8_t *>(c);
  auto cont = [&](std::size_t i, int lo = 0x80, int hi = 0xbf) { return i < n && s[i] >= lo && s[i] <= hi; };
  for (std::size_t i = 0; i < n;) {
    std::uint8_t b = s[i];
    if (b == 0)
      return false;
    if (b < 0x80) {
      i += 1;
    } else if (b >= 0xc2 && b <= 0xdf) {
      if (!cont(i + 1))
        return false;
      i += 2;
    } else if (b >= 0xe0 && b <= 0xef) {
      int lo = b == 0xe0 ? 0xa0 : 0x80, hi = b == 0xed ? 0x9f : 0xbf;
      if (!cont(i + 1, lo, hi) || !cont(i + 2))
        return false;
      i += 3;
    } else if (b >= 0xf0 && b <= 0xf4) {
      int lo = b == 0xf0 ? 0x90 : 0x80, hi = b == 0xf4 ? 0x8f : 0xbf;
      if (!cont(i + 1, lo, hi) || !cont(i + 2) || !cont(i + 3))
        return false;
      i += 4;
    } else {
      return false;
    }
  }
  return true;
}
bool valid_utf8(const std::string &s) {
  // text_ok also refuses NUL, which is not allowed in any NWT text or JSON value either.
  return text_ok(s.data(), s.size());
}

// ----------------------------------------------------------------- schemas

struct Fld {
  std::string name;
  std::size_t bytes = 0;
  bool sgn = false, rsv = false;
  int kind = 0; // 0 none, 1 price, 2 quantity, 3 time
};
struct Sch {
  struct TL {
    std::size_t i;
    std::string name;
    U lo, hi;
  };
  struct TE {
    std::size_t i;
    std::string name;
    std::vector<U> ok;
  };
  U type = 0;
  std::string name;
  std::vector<Fld> fl;           // header fields, then body fields: the positional layout of Rec::f
  std::vector<std::size_t> off;  // byte offset of each field inside the record
  std::size_t nh = 0, fixed = 0, lvpos = 0;
  std::vector<std::string> texts;
  std::vector<std::size_t> tlen; // position of each text's length field
  bool levels = false, typed = false;
  std::vector<std::pair<std::size_t, std::vector<U>>> enums;
  std::vector<std::pair<std::size_t, U>> masks;
  std::vector<TL> tl;
  std::vector<TE> te;
};
std::vector<Fld> HF, LF; // header and level fields
std::size_t HDRB = 0, LVB = 0;
std::vector<Sch> SCH;
std::vector<const Sch *> BY; // by record type
bool TYPED_HDR = false;     // the header matches the packed WireHeader below

Fld mkfld(const J &f) {
  Fld x;
  x.name = f.at("name").get<std::string>();
  x.bytes = f.at("bytes").get<std::size_t>();
  x.sgn = f.at("signed").get<bool>();
  x.rsv = x.name == "reserved";
  std::string k = f.value("kind", std::string());
  x.kind = k == "price" ? 1 : k == "quantity" ? 2 : k == "time" ? 3 : 0;
  need(x.bytes >= 1 && x.bytes <= 8, "schema field width");
  return x;
}
void init_registry() {
  for (const auto &f : SS.at("header")) {
    HF.push_back(mkfld(f));
    HDRB += HF.back().bytes;
  }
  for (const auto &f : SS.at("level")) {
    LF.push_back(mkfld(f));
    LVB += LF.back().bytes;
  }
  need(HDRB == 48 && !LF.empty(), "schema header");
  BY.assign(65536, nullptr);
  SCH.reserve(SS.at("schemas").size()); // pointers into SCH stay valid
  for (const auto &sj : SS.at("schemas")) {
    Sch s;
    s.type = sj.at("type").get<U>();
    need(s.type < 65536 && !BY[s.type], "schema type");
    s.name = sj.at("name").get<std::string>();
    s.fl = HF;
    s.nh = HF.size();
    for (const auto &f : sj.at("fields"))
      s.fl.push_back(mkfld(f));
    s.levels = sj.at("has_levels").get<bool>();
    for (const auto &t : sj.at("texts"))
      s.texts.push_back(t.get<std::string>());
    s.fixed = sj.at("fixed_bytes").get<std::size_t>();
    std::size_t o = 0;
    for (const auto &d : s.fl) {
      s.off.push_back(o);
      o += d.bytes;
    }
    need(o == s.fixed, "schema fixed_bytes");
    need(s.fl.size() <= MAXF, "schema field count");
    auto pos = [&](const std::string &n) {
      for (std::size_t i = 0; i < s.fl.size(); i++)
        if (s.fl[i].name == n)
          return i;
      throw std::runtime_error("schema names an unknown field " + n);
    };
    if (s.levels)
      s.lvpos = pos("levels");
    for (const auto &t : s.texts)
      s.tlen.push_back(pos(t + "_bytes"));
    if (sj.contains("enums"))
      for (const auto &it : sj.at("enums").items()) {
        std::vector<U> ok;
        for (const auto &x : it.value())
          ok.push_back(x.get<U>());
        s.enums.push_back({pos(it.key()), ok});
      }
    if (sj.contains("masks"))
      for (const auto &it : sj.at("masks").items())
        s.masks.push_back({pos(it.key()), it.value().get<U>()});
    if (sj.contains("text_limits"))
      for (const auto &it : sj.at("text_limits").items())
        s.tl.push_back({pos(it.key() + "_bytes"), it.key(), it.value().at(0).get<U>(), it.value().at(1).get<U>()});
    if (sj.contains("text_exact"))
      for (const auto &it : sj.at("text_exact").items()) {
        std::vector<U> ok;
        for (const auto &x : it.value())
          ok.push_back(x.get<U>());
        s.te.push_back({pos(it.key() + "_bytes"), it.key(), ok});
      }
    s.typed = s.texts.empty() && !s.levels;
    SCH.push_back(std::move(s));
    BY[SCH.back().type] = &SCH.back();
  }
  const std::size_t want[] = {4, 2, 1, 1, 4, 4, 8, 8, 8, 8};
  TYPED_HDR = LE && HF.size() == 10;
  for (std::size_t i = 0; TYPED_HDR && i < 10; i++)
    TYPED_HDR = HF[i].bytes == want[i] && !HF[i].sgn;
}
const Sch &schema_of(U t) {
  need(t < 65536 && BY[t], "unknown schema");
  return *BY[t];
}
// Data-driven rules shared by encode and decode: enums, flag masks and text byte lengths.
void check_schema(const Sch &s, const U *f) {
  for (const auto &e : s.enums)
    if (std::find(e.second.begin(), e.second.end(), f[e.first]) == e.second.end())
      fail("invalid " + s.fl[e.first].name);
  for (const auto &m : s.masks)
    if ((f[m.first] & ~m.second) != 0)
      fail("invalid " + s.fl[m.first].name + " bits");
  for (const auto &t : s.tl)
    if (f[t.i] < t.lo || f[t.i] > t.hi)
      fail(t.name + " text limit");
  for (const auto &t : s.te)
    if (std::find(t.ok.begin(), t.ok.end(), f[t.i]) == t.ok.end())
      fail(t.name + " text length");
}

// ------------------------------------------------------------------ records

// One record. f holds every header and body field in schema order (signed values as two's
// complement in 64 bits); lv holds the level fields flat; tx holds the texts in schema order.
struct Rec {
  U type = 0;
  std::vector<U> f;
  std::vector<U> lv;
  std::vector<std::string> tx;
};
void chk(const Fld &d, U x) {
  if (d.rsv)
    need(x == 0, "reserved must be zero");
  if (d.bytes < 8) {
    if (!d.sgn) {
      need(x < (U(1) << (8 * d.bytes)), "integer range");
    } else {
      auto v = std::bit_cast<std::int64_t>(x);
      auto lim = std::int64_t(1) << (8 * d.bytes - 1);
      need(v >= -lim && v < lim, "integer range");
    }
  }
}
void wr(Bytes &o, const Fld &d, U x) {
  chk(d, x);
  for (std::size_t i = 0; i < d.bytes; i++)
    o.push_back(std::uint8_t(x >> (8 * i)));
}
U ldv(const std::uint8_t *p, std::size_t w, bool sgn) {
  if constexpr (LE) {
    switch (w) {
    case 1:
      return sgn ? U(std::int64_t(std::int8_t(p[0]))) : U(p[0]);
    case 2: {
      std::uint16_t v;
      std::memcpy(&v, p, 2);
      return sgn ? U(std::int64_t(std::int16_t(v))) : U(v);
    }
    case 4: {
      std::uint32_t v;
      std::memcpy(&v, p, 4);
      return sgn ? U(std::int64_t(std::int32_t(v))) : U(v);
    }
    case 8: {
      U v;
      std::memcpy(&v, p, 8);
      return v;
    }
    default:
      break;
    }
  }
  U x = 0;
  for (std::size_t i = 0; i < w; i++)
    x |= U(p[i]) << (8 * i);
  if (sgn && w < 8 && ((x >> (8 * w - 1)) & 1))
    x |= ~U(0) << (8 * w);
  return x;
}
// Encode one record from positional values. Derived values (record_bytes, text lengths, level
// count) are computed here; the supplied ones are ignored.
void encode_into(Bytes &out, const Sch &s, const U *fin, const U *lv, std::size_t nlv, const std::string *tx) {
  U f[MAXF];
  std::copy(fin, fin + s.fl.size(), f);
  need(f[1] == s.type, "record type mismatch");
  need(f[2] == 1 && (f[3] & ~U(3)) == 0, "version/flags");
  if (s.levels) {
    need(nlv <= 1024, "levels limit");
    f[s.lvpos] = nlv;
  }
  for (std::size_t t = 0; t < s.texts.size(); t++) {
    need(text_ok(tx[t].data(), tx[t].size()), "text is not valid UTF-8 or contains NUL");
    f[s.tlen[t]] = tx[t].size();
  }
  check_schema(s, f);
  std::size_t start = out.size();
  out.resize(start + HDRB, 0);
  for (std::size_t k = s.nh; k < s.fl.size(); k++)
    wr(out, s.fl[k], f[k]);
  for (std::size_t j = 0; j < nlv; j++)
    for (std::size_t k = 0; k < LF.size(); k++)
      wr(out, LF[k], lv[j * LF.size() + k]);
  for (std::size_t t = 0; t < s.texts.size(); t++)
    out.insert(out.end(), tx[t].begin(), tx[t].end());
  std::size_t total = (out.size() - start + 7) & ~std::size_t(7);
  need(total <= MAXREC, "record limit");
  out.resize(start + total, 0);
  f[0] = total;
  for (std::size_t k = 0; k < s.nh; k++) {
    chk(s.fl[k], f[k]);
    put(out, start + s.off[k], s.fl[k].bytes, f[k]);
  }
}
Bytes encode_record(const Rec &r) {
  const Sch &s = schema_of(r.type);
  need(r.f.size() == s.fl.size() && r.tx.size() == s.texts.size(), "record shape");
  Bytes out;
  encode_into(out, s, r.f.data(), r.lv.data(), r.lv.size() / LF.size(), r.tx.data());
  return out;
}
Rec decode_record(View b) {
  need(b.size() >= 48 && b.size() <= MAXREC && b.size() % 8 == 0, "record size");
  U h[16];
  for (std::size_t k = 0; k < HF.size(); k++) {
    std::size_t o = 0;
    for (std::size_t q = 0; q < k; q++)
      o += HF[q].bytes;
    h[k] = ldv(b.data() + o, HF[k].bytes, HF[k].sgn);
  }
  need(h[0] == b.size() && h[1] < 65536 && BY[h[1]], "length/type");
  need(h[2] == 1 && (h[3] & ~U(3)) == 0, "version/flags");
  const Sch &s = *BY[h[1]];
  Rec r;
  r.type = s.type;
  r.f.assign(s.fl.size(), 0);
  std::copy(h, h + s.nh, r.f.begin());
  std::size_t p = HDRB;
  for (std::size_t k = s.nh; k < s.fl.size(); k++) {
    const Fld &d = s.fl[k];
    need(p <= b.size() && d.bytes <= b.size() - p, "field bounds");
    U x = ldv(b.data() + p, d.bytes, d.sgn);
    if (d.rsv)
      need(x == 0, "nonzero reserved");
    r.f[k] = x;
    p += d.bytes;
  }
  if (s.levels) {
    U n = r.f[s.lvpos];
    need(n <= 1024, "levels limit");
    for (U j = 0; j < n; j++)
      for (const auto &d : LF) {
        need(p <= b.size() && d.bytes <= b.size() - p, "field bounds");
        U x = ldv(b.data() + p, d.bytes, d.sgn);
        if (d.rsv)
          need(x == 0, "nonzero reserved");
        r.lv.push_back(x);
        p += d.bytes;
      }
  }
  for (std::size_t t = 0; t < s.texts.size(); t++) {
    U n = r.f[s.tlen[t]];
    need(p <= b.size() && n <= b.size() - p, "text bounds");
    std::string text(reinterpret_cast<const char *>(b.data() + p), std::size_t(n));
    need(text_ok(text.data(), text.size()), "text is not valid UTF-8 or contains NUL");
    r.tx.push_back(std::move(text));
    p += std::size_t(n);
  }
  // A fixed type must have its exact size; a variable type its exact padded size.
  need(((p + 7) & ~std::size_t(7)) == b.size() && zero(b.subspan(p)), "padding/record length");
  check_schema(s, r.f.data());
  return r;
}

// Typed fast path. The 48-byte header is read as one packed struct through memcpy (never through
// a pointer cast), so alignment cannot matter. Body fields use the schema's offsets and widths;
// no strings are built. Used for fixed-size types (no texts, no levels).
#pragma pack(push, 1)
struct WireHeader {
  std::uint32_t record_bytes;
  std::uint16_t record_type;
  std::uint8_t schema_version, flags;
  std::uint32_t publisher_id, channel_id;
  std::uint64_t instrument_id, ts_event, ts_recv, sequence;
};
#pragma pack(pop)
static_assert(sizeof(WireHeader) == 48 && std::is_trivially_copyable_v<WireHeader>, "packed header view");
void decode_typed(View b, const Sch &s, U *f) {
  need(b.size() == s.fixed, "padding/record length");
  const std::uint8_t *d = b.data();
  if (TYPED_HDR) {
    WireHeader h;
    std::memcpy(&h, d, sizeof h);
    f[0] = h.record_bytes;
    f[1] = h.record_type;
    f[2] = h.schema_version;
    f[3] = h.flags;
    f[4] = h.publisher_id;
    f[5] = h.channel_id;
    f[6] = h.instrument_id;
    f[7] = h.ts_event;
    f[8] = h.ts_recv;
    f[9] = h.sequence;
  } else {
    for (std::size_t k = 0; k < s.nh; k++)
      f[k] = ldv(d + s.off[k], s.fl[k].bytes, s.fl[k].sgn);
  }
  need(f[0] == b.size() && f[1] == s.type, "length/type");
  need(f[2] == 1 && (f[3] & ~U(3)) == 0, "version/flags");
  for (std::size_t k = s.nh; k < s.fl.size(); k++) {
    const Fld &x = s.fl[k];
    if (x.rsv) {
      need(zero(View(d + s.off[k], x.bytes)), "nonzero reserved");
      f[k] = 0;
    } else {
      f[k] = ldv(d + s.off[k], x.bytes, x.sgn);
    }
  }
  check_schema(s, f);
}

// A record from a catalog entry (field values are decimal strings).
Rec rec_from_json(const J &e) {
  Rec r;
  r.type = e.at("type").get<U>();
  const Sch &s = schema_of(r.type);
  const J &fj = e.at("fields");
  r.f.assign(s.fl.size(), 0);
  for (std::size_t i = 0; i < s.fl.size(); i++) {
    const Fld &d = s.fl[i];
    auto it = fj.find(d.name);
    if (it == fj.end()) {
      bool derived = i == 0 || (s.levels && i == s.lvpos) ||
                     std::find(s.tlen.begin(), s.tlen.end(), i) != s.tlen.end();
      need(derived || d.rsv, "catalog entry misses a field");
      continue;
    }
    std::string t = it->get<std::string>();
    r.f[i] = d.sgn ? std::bit_cast<U>(parse_i(t)) : parse_u(t);
  }
  if (s.levels)
    for (const auto &l : e.at("levels"))
      for (const auto &d : LF) {
        auto it = l.find(d.name);
        if (it == l.end()) {
          need(d.rsv, "catalog level misses a field");
          r.lv.push_back(0);
        } else {
          std::string t = it->get<std::string>();
          r.lv.push_back(d.sgn ? std::bit_cast<U>(parse_i(t)) : parse_u(t));
        }
      }
  for (const auto &name : s.texts)
    r.tx.push_back(e.at("texts").at(name).get<std::string>());
  return r;
}

// -------------------------------------------------------------- text output

std::string dec(const Fld &d, U x) {
  return d.sgn ? std::to_string(std::bit_cast<std::int64_t>(x)) : std::to_string(x);
}
// Field report: one line per schema field (reserved included), levels, then texts, raw.
void report_into(std::string &o, std::size_t i, const Rec &r) {
  const Sch &s = schema_of(r.type);
  std::string pre = std::to_string(i) + ".";
  for (std::size_t k = 0; k < s.fl.size(); k++)
    o += pre + s.fl[k].name + "=" + dec(s.fl[k], r.f[k]) + "\n";
  std::size_t n = r.lv.size() / LF.size();
  for (std::size_t j = 0; j < n; j++)
    for (std::size_t k = 0; k < LF.size(); k++)
      o += pre + "levels." + std::to_string(j) + "." + LF[k].name + "=" + dec(LF[k], r.lv[j * LF.size() + k]) + "\n";
  for (std::size_t t = 0; t < s.texts.size(); t++)
    o += pre + s.texts[t] + "=" + r.tx[t] + "\n";
}
std::string pretty_decimal(U v, bool sgn) {
  bool neg = sgn && std::bit_cast<std::int64_t>(v) < 0;
  U a = neg ? U(0) - v : v;
  char buf[48];
  std::snprintf(buf, sizeof buf, "%llu.%09llu", (unsigned long long)(a / 1000000000ULL),
                (unsigned long long)(a % 1000000000ULL));
  return std::string(neg ? "-" : "") + buf;
}
std::string pretty_time(U ns) {
  U sec = ns / 1000000000ULL, frac = ns % 1000000000ULL;
  U days = sec / 86400, rest = sec % 86400;
  U z = days + 719468, era = z / 146097, doe = z % 146097;
  U yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365;
  U doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
  U mp = (5 * doy + 2) / 153;
  U day = doy - (153 * mp + 2) / 5 + 1;
  U month = mp < 10 ? mp + 3 : mp - 9;
  U year = yoe + era * 400 + (month <= 2 ? 1 : 0);
  char buf[64];
  std::snprintf(buf, sizeof buf, "%04llu-%02llu-%02lluT%02llu:%02llu:%02llu.%09lluZ", (unsigned long long)year,
                (unsigned long long)month, (unsigned long long)day, (unsigned long long)(rest / 3600),
                (unsigned long long)(rest % 3600 / 60), (unsigned long long)(rest % 60), (unsigned long long)frac);
  return buf;
}
struct Val {
  std::string v;
  bool null = false;
};
// A value for --pretty: null for a null price, quantity or time; fields without a kind unchanged.
Val fval(const Fld &d, U x, bool pretty) {
  Val r;
  if (!pretty || !d.kind) {
    r.v = dec(d, x);
    return r;
  }
  if (d.sgn ? std::bit_cast<std::int64_t>(x) == NIL_I : x == NIL) {
    r.null = true;
    return r;
  }
  r.v = d.kind == 3 ? pretty_time(x) : pretty_decimal(x, d.sgn);
  return r;
}
void jstr(std::string &o, const std::string &s) {
  static const char hex[] = "0123456789abcdef";
  o += '"';
  for (unsigned char c : s) {
    if (c == '"' || c == '\\') {
      o += '\\';
      o += char(c);
    } else if (c < 0x20) {
      o += "\\u00";
      o += hex[c >> 4];
      o += hex[c & 15];
    } else {
      o += char(c);
    }
  }
  o += '"';
}
void jval(std::string &o, const Val &v) {
  if (v.null)
    o += "null";
  else
    jstr(o, v.v);
}
// True for the fields that appear in JSON and CSV: no reserved, and no level count for type 5.
bool listed(const Sch &s, std::size_t k) {
  return !s.fl[k].rsv && !(s.levels && k == s.lvpos);
}
std::string to_json_line(const Rec &r, bool pretty) {
  const Sch &s = schema_of(r.type);
  std::string o = "{\"type_name\":";
  jstr(o, s.name);
  for (std::size_t k = 0; k < s.fl.size(); k++) {
    if (!listed(s, k))
      continue;
    o += ',';
    jstr(o, s.fl[k].name);
    o += ':';
    jval(o, fval(s.fl[k], r.f[k], pretty));
  }
  for (std::size_t t = 0; t < s.texts.size(); t++) {
    o += ',';
    jstr(o, s.texts[t]);
    o += ':';
    jstr(o, r.tx[t]);
  }
  if (s.levels) {
    o += ",\"levels\":[";
    std::size_t n = r.lv.size() / LF.size();
    for (std::size_t j = 0; j < n; j++) {
      o += j ? ",{" : "{";
      bool first = true;
      for (std::size_t k = 0; k < LF.size(); k++) {
        if (LF[k].rsv)
          continue;
        if (!first)
          o += ',';
        first = false;
        jstr(o, LF[k].name);
        o += ':';
        jval(o, fval(LF[k], r.lv[j * LF.size() + k], pretty));
      }
      o += '}';
    }
    o += ']';
  }
  o += '}';
  return o;
}
void csv_value(std::string &o, const std::string &v) {
  if (v.find_first_of(",\"\r\n") == std::string::npos) {
    o += v;
    return;
  }
  o += '"';
  for (char c : v) {
    if (c == '"')
      o += '"';
    o += c;
  }
  o += '"';
}
std::string csv_header(const Sch &s) {
  need(!s.levels, ("type " + std::to_string(s.type) + " has levels; use to-json").c_str());
  std::string o;
  for (std::size_t k = 0; k < s.fl.size(); k++)
    if (listed(s, k))
      o += (o.empty() ? "" : ",") + s.fl[k].name;
  for (const auto &t : s.texts)
    o += "," + t;
  return o;
}
std::string to_csv_line(const Rec &r, bool pretty) {
  const Sch &s = schema_of(r.type);
  std::string o;
  bool first = true;
  for (std::size_t k = 0; k < s.fl.size(); k++) {
    if (!listed(s, k))
      continue;
    if (!first)
      o += ',';
    first = false;
    Val v = fval(s.fl[k], r.f[k], pretty);
    if (!v.null)
      csv_value(o, v.v);
  }
  for (const auto &t : r.tx) {
    o += ',';
    csv_value(o, t);
  }
  return o;
}
void emit(const std::string &s) {
  std::cout.write(s.data(), std::streamsize(s.size()));
}

// ---------------------------------------------------------------- metadata

// Strict JSON: no duplicate object keys at any depth and no non-integer numbers.
J strict_json(const std::string &text) {
  std::vector<std::set<std::string>> keys;
  bool dup = false, flt = false;
  J v = J::parse(text, [&](int, J::parse_event_t ev, J &x) {
    if (ev == J::parse_event_t::object_start)
      keys.emplace_back();
    else if (ev == J::parse_event_t::object_end)
      keys.pop_back();
    else if (ev == J::parse_event_t::key) {
      if (!keys.back().insert(x.get<std::string>()).second)
        dup = true;
    } else if (ev == J::parse_event_t::value && x.is_number_float())
      flt = true;
    return true;
  });
  need(!dup, "duplicate JSON key");
  need(!flt, "JSON numbers must be integers");
  return v;
}
const J *member(const J &o, const char *k) {
  auto it = o.find(k);
  return it == o.end() ? nullptr : &*it;
}
bool is_text(const J *v, std::size_t lo, std::size_t hi) {
  if (!v || !v->is_string())
    return false;
  std::size_t n = v->get_ref<const std::string &>().size();
  return lo <= n && n <= hi;
}
bool is_int(const J *v, std::int64_t lo, std::int64_t hi) {
  if (!v || !v->is_number_integer())
    return false;
  if (v->is_number_unsigned()) {
    U x = v->get<U>();
    return x >= U(lo) && x <= U(hi);
  }
  auto x = v->get<std::int64_t>();
  return x >= lo && x <= hi;
}
struct Manifest {
  std::set<std::pair<U, U>> types; // (type, version)
  std::set<U> pubs;
  std::string ordering = "none";
  bool minor1 = false;
};
// Parse and validate a MANIFEST value. Unknown properties are ignored.
Manifest parse_manifest(const std::string &text) {
  need(valid_utf8(text), "manifest is not valid UTF-8");
  J m = strict_json(text);
  need(m.is_object(), "manifest must be a JSON object");
  for (const char *k : {"dataset", "producer", "profile", "publishers", "schemas", "clock"})
    need(m.contains(k), "manifest missing a required key");
  need(is_text(member(m, "dataset"), 1, 255) && is_text(member(m, "producer"), 1, 255), "manifest dataset/producer");
  const J &profile = m.at("profile");
  need(profile.is_string() && (profile == "market-data" || profile == "generic-events"), "manifest profile");
  const J &clock = m.at("clock");
  need(clock.is_string() && clock == "posix-ns", "manifest clock");
  Manifest out;
  if (m.contains("ordering")) {
    const J &o = m.at("ordering");
    need(o.is_string() && (o == "none" || o == "ts_event" || o == "instrument,ts_event"), "manifest ordering");
    out.ordering = o.get<std::string>();
  }
  const J &publishers = m.at("publishers"), &schemas = m.at("schemas");
  need(publishers.is_array() && publishers.size() <= 4096, "manifest publishers");
  for (const auto &p : publishers) {
    need(p.is_object(), "manifest publisher");
    need(is_int(member(p, "id"), 1, 4294967295LL), "manifest publisher id");
    need(is_text(member(p, "name"), 1, 255) && is_text(member(p, "venue"), 0, 255), "manifest publisher name/venue");
    need(out.pubs.insert(p.at("id").get<U>()).second, "manifest duplicate publisher");
  }
  need(schemas.is_array() && schemas.size() >= 1 && schemas.size() <= 4096, "manifest schemas");
  for (const auto &s : schemas) {
    need(s.is_object(), "manifest schema");
    need(is_int(member(s, "type"), 1, 65534) && is_int(member(s, "version"), 1, 255), "manifest schema type/version");
    const J *req = member(s, "required");
    need(req && req->is_boolean(), "manifest schema required");
    need(is_text(member(s, "name"), 1, 255) && is_text(member(s, "spec_uri"), 1, 2048),
         "manifest schema name/spec_uri");
    U t = s.at("type").get<U>();
    need(out.types.insert({t, s.at("version").get<U>()}).second, "manifest duplicate schema");
    // minor is 1 exactly when the manifest declares a standard type added in 1.1 (10 and up, in the registry).
    if (t >= 10 && BY[t])
      out.minor1 = true;
  }
  return out;
}
Bytes tlv(U typ, U flags, const Bytes &value) {
  Bytes b(8);
  put(b, 0, 2, typ);
  put(b, 2, 2, flags);
  put(b, 4, 4, value.size());
  append(b, value);
  return pad(b);
}
struct Meta {
  std::string manifest;
  bool has_prov = false;
  std::string prov;
};
// Split metadata into elements. Unknown optional elements are bounds-checked and skipped.
Meta parse_metadata(View meta) {
  std::map<U, std::pair<U, std::string>> out;
  std::size_t p = 0;
  while (p < meta.size()) {
    need(meta.size() - p >= 8, "TLV header");
    U typ = get(meta, p, 2), flags = get(meta, p + 2, 2), n = get(meta, p + 4, 4);
    need(typ > 0 && typ < 65535 && (flags & ~U(1)) == 0, "TLV type/flags");
    need(!out.count(typ), "duplicate TLV");
    need(n <= meta.size() - p - 8, "TLV length");
    std::size_t end = p + 8 + std::size_t(n);
    std::size_t next = std::min((end + 7) & ~std::size_t(7), meta.size());
    out[typ] = {flags, std::string(meta.begin() + p + 8, meta.begin() + end)};
    need(zero(meta.subspan(end, next - end)), "TLV padding");
    need(typ == 1 || typ == 2 || flags == 0, "unknown required TLV");
    p = next;
  }
  need(out.count(1) && out[1].first == 1, "MANIFEST TLV must be present with its required flag");
  need(!out.count(2) || out[2].first == 0, "PROVENANCE TLV must not be marked required");
  Meta m;
  m.manifest = out[1].second;
  if (out.count(2)) {
    m.has_prov = true;
    m.prov = out[2].second;
    need(valid_utf8(m.prov), "PROVENANCE is not valid UTF-8");
    need(strict_json(m.prov).is_object(), "PROVENANCE must be a JSON object");
  }
  return m;
}

// -------------------------------------------------------------------- Zstd

// Spec 10.2, checked by hand on the Zstd frame header before any library call (RFC 8878:
// bit 3 of the descriptor is reserved, bit 2 is the content checksum and is allowed,
// bits 0-1 flag a dictionary ID).
void zstd_check(View st, U raw_bytes) {
  need(st.size() >= 6 && st[0] == 0x28 && st[1] == 0xb5 && st[2] == 0x2f && st[3] == 0xfd, "Zstd magic");
  unsigned d = st[4], fcs = d >> 6, single = (d >> 5) & 1;
  need((d & 0x08) == 0, "Zstd reserved bit");
  need((d & 0x03) == 0, "Zstd dictionary");
  std::size_t p = 5;
  U window = 0;
  if (!single) {
    unsigned w = st[p++];
    U base = U(1) << (10 + (w >> 3));
    window = base + (base >> 3) * (w & 7);
  }
  std::size_t n = fcs == 0 ? (single ? 1 : 0) : fcs == 1 ? 2 : fcs == 2 ? 4 : 8;
  need(n > 0, "Zstd content size missing");
  need(st.size() >= p + n, "Zstd header");
  U size = 0;
  for (std::size_t i = 0; i < n; i++)
    size |= U(st[p + i]) << (8 * i);
  size += fcs == 1 ? 256 : 0;
  need(size == raw_bytes, "Zstd content size");
  need((single ? size : window) <= LIMIT, "Zstd window");
}
Bytes zstd_compress(View b, int level) {
#ifdef NWT_ZSTD
  Bytes out(ZSTD_compressBound(b.size()));
  std::size_t n = ZSTD_compress(out.data(), out.size(), b.data(), b.size(), level);
  need(!ZSTD_isError(n), "Zstd compression failed");
  out.resize(n);
  return out;
#else
  (void)b;
  (void)level;
  throw std::runtime_error("Zstd library not available");
#endif
}
Bytes zstd_decompress(View st, U raw_bytes) {
  zstd_check(st, raw_bytes);
#ifdef NWT_ZSTD
  // Exactly one frame: no concatenated or skippable frame and no trailing bytes.
  need(ZSTD_findFrameCompressedSize(st.data(), st.size()) == st.size(), "Zstd frame must fill stored_bytes exactly");
  Bytes out(std::max<U>(raw_bytes, 1));
  std::size_t n = ZSTD_decompress(out.data(), std::size_t(raw_bytes), st.data(), st.size());
  need(!ZSTD_isError(n) && n == raw_bytes, "Zstd decompression failed");
  out.resize(std::size_t(raw_bytes));
  return out;
#else
  throw std::runtime_error("Zstd library not available");
#endif
}

// --------------------------------------------------------------- container

struct FrameInfo {
  U seq = 0, offset = 0, kind = 0, codec = 0, stored = 0, raw = 0, count = 0, lo = NIL, hi = NIL, crc = 0;
};
Bytes frame(U kind, U seq, View payload, U count = 0, U lo = NIL, U hi = NIL, U codec = 0,
            const Bytes *stored = nullptr) {
  View st = stored ? View(*stored) : payload;
  Bytes h(64);
  const char m[] = "NWF1";
  std::copy(m, m + 4, h.begin());
  h[4] = 1;
  h[5] = std::uint8_t(kind);
  h[6] = std::uint8_t(codec);
  put(h, 8, 2, 64);
  put(h, 12, 4, st.size());
  put(h, 16, 4, payload.size());
  put(h, 20, 4, count);
  put(h, 24, 8, seq);
  put(h, 32, 8, lo);
  put(h, 40, 8, hi);
  put(h, 48, 4, crc(payload));
  h = hcrc(std::move(h), 52);
  append(h, st);
  h.resize((h.size() + 7) & ~std::size_t(7), 0);
  return h;
}
Bytes index_entry(const FrameInfo &i) {
  Bytes b(40);
  put(b, 0, 8, i.seq);
  put(b, 8, 8, i.offset);
  put(b, 16, 8, i.lo);
  put(b, 24, 8, i.hi);
  put(b, 32, 4, i.raw);
  put(b, 36, 4, i.count);
  return b;
}
std::pair<U, U> time_bounds(const std::vector<View> &raws) {
  U lo = NIL, hi = NIL;
  for (auto r : raws) {
    U t = get(r, 24, 8);
    if (t == NIL)
      continue;
    if (lo == NIL || t < lo)
      lo = t;
    if (hi == NIL || t > hi)
      hi = t;
  }
  return {lo, hi};
}
std::vector<View> split_records(View payload, U count) {
  need(count > 0 && payload.size() % 8 == 0, "DATA order/count");
  std::vector<View> raws;
  std::size_t p = 0;
  while (p < payload.size()) {
    U n = get(payload, p, 4);
    need(n >= 48 && n <= MAXREC && n % 8 == 0 && n <= payload.size() - p, "record bounds");
    raws.push_back(payload.subspan(p, std::size_t(n)));
    p += std::size_t(n);
  }
  need(raws.size() == count, "record count");
  return raws;
}

// Checks that need only a record's 48-byte header: declared type, declared publisher, sequence.
struct Scope {
  const Manifest *m;
  std::map<std::pair<U, U>, U> seq;
  std::pair<U, U> last_key{NIL, NIL};
  U *last = nullptr;
  explicit Scope(const Manifest *mm) : m(mm) {}
  void check(View raw) {
    need(m->types.count({get(raw, 4, 2), get(raw, 6, 1)}) != 0, "undeclared record type");
    std::pair<U, U> key{get(raw, 8, 4), get(raw, 12, 4)};
    need(key.first == 0 || m->pubs.count(key.first) != 0, "undeclared publisher");
    if (!last || key != last_key) {
      last = &seq[key];
      last_key = key;
    }
    U s = get(raw, 40, 8);
    need(*last != NIL && s == *last + 1, "record sequence");
    *last = s;
  }
};

// Streaming writer: header and metadata first, DATA frames as they fill, INDEX and END on close.
struct Writer {
  std::ostream &out;
  Manifest man;
  Scope scope;
  U position = 0, seq = 0, records = 0;
  U frame_bytes, frame_records; // frame_records 0: close frames by size
  int zstd_level;               // 0: raw frames only
  Bytes pending;
  U pcount = 0, plo = NIL, phi = NIL;
  std::vector<FrameInfo> frames;

  Writer(std::ostream &o, const Bytes &metadata, const std::array<std::uint8_t, 16> &id, U created,
         U fbytes = 1 << 20, U frecords = 0, int level = 0)
      : out(o), man(parse_metadata(metadata).manifest.empty() ? Manifest{} : Manifest{}), scope(&man),
        frame_bytes(fbytes), frame_records(frecords), zstd_level(level) {
    Meta m = parse_metadata(metadata);
    man = parse_manifest(m.manifest);
    need(metadata.size() <= 1048576 && metadata.size() % 8 == 0, "metadata length");
    need(std::any_of(id.begin(), id.end(), [](auto x) { return x != 0; }),
         "stream ID must be 16 bytes and not all zero");
    need(frame_bytes >= 48 && frame_bytes <= LIMIT, "frame size");
    Bytes h(64);
    const char mg[] = "NWTBIN\r\n";
    std::copy(mg, mg + 8, h.begin());
    put(h, 8, 2, 1);
    put(h, 10, 2, man.minor1 ? 1 : 0);
    put(h, 12, 2, 64);
    put(h, 16, 4, metadata.size());
    put(h, 20, 4, crc(metadata));
    std::copy(id.begin(), id.end(), h.begin() + 24);
    put(h, 40, 8, created);
    Bytes first = hcrc(std::move(h), 56);
    append(first, metadata);
    emit_bytes(first);
  }
  void emit_bytes(View d) {
    out.write(reinterpret_cast<const char *>(d.data()), std::streamsize(d.size()));
    position += d.size();
  }
  void write(const Rec &r) { write_raw(encode_record(r)); }
  void write_raw(const Bytes &b) {
    need(b.size() >= 48 && b.size() <= MAXREC && b.size() % 8 == 0 && get(b, 0, 4) == b.size(), "record size");
    scope.check(b);
    U room = frame_records ? LIMIT : frame_bytes;
    if (pcount && (pcount == frame_records || pending.size() + b.size() > room))
      flush();
    U t = get(b, 24, 8);
    if (t != NIL) {
      if (plo == NIL || t < plo)
        plo = t;
      if (phi == NIL || t > phi)
        phi = t;
    }
    append(pending, b);
    ++pcount;
  }
  void flush() {
    if (!pcount)
      return;
    U codec = 0;
    Bytes packed;
    if (zstd_level) {
      packed = zstd_compress(pending, zstd_level);
      // Codec 1 only when it is strictly smaller than the raw payload.
      if (packed.size() < pending.size()) {
        zstd_check(packed, pending.size());
        codec = 1;
      }
    }
    FrameInfo fi;
    fi.seq = seq;
    fi.offset = position;
    fi.kind = 1;
    fi.codec = codec;
    fi.stored = codec ? packed.size() : pending.size();
    fi.raw = pending.size();
    fi.count = pcount;
    fi.lo = plo;
    fi.hi = phi;
    frames.push_back(fi);
    emit_bytes(frame(1, seq, pending, pcount, plo, phi, codec, codec ? &packed : nullptr));
    ++seq;
    records += pcount;
    pending.clear();
    pcount = 0;
    plo = phi = NIL;
  }
  void close(U status = 0) {
    flush();
    U first_index = frames.empty() ? 0 : position;
    const std::size_t per_frame = LIMIT / 40; // an INDEX payload is bounded like any other frame
    for (std::size_t s0 = 0; s0 < frames.size(); s0 += per_frame) {
      Bytes chunk;
      for (std::size_t i = s0; i < std::min(frames.size(), s0 + per_frame); i++)
        append(chunk, index_entry(frames[i]));
      emit_bytes(frame(2, seq, chunk));
      ++seq;
    }
    Bytes end(32);
    put(end, 0, 8, first_index);
    put(end, 8, 8, frames.size());
    put(end, 16, 8, records);
    put(end, 24, 4, status);
    put(end, 28, 4, 0);
    emit_bytes(frame(3, seq, end));
  }
};

// Bytes of a file or of memory, read at an offset.
struct Source {
  View mem;
  std::ifstream f;
  U size = 0;
  bool inmem = false;
  void open_file(const char *path) {
    f.open(path, std::ios::binary);
    need(bool(f), "open input");
    f.seekg(0, std::ios::end);
    auto e = f.tellg();
    need(e >= 0, "input size");
    size = U(e);
  }
  void open_mem(View v) {
    mem = v;
    size = v.size();
    inmem = true;
  }
  Bytes read(U off, std::size_t n, const char *what) {
    if (off > size || n > size - off)
      fail(std::string("incomplete: file ends inside ") + what);
    if (inmem)
      return Bytes(mem.begin() + std::ptrdiff_t(off), mem.begin() + std::ptrdiff_t(off) + std::ptrdiff_t(n));
    Bytes b(n);
    f.clear();
    f.seekg(std::streamoff(off));
    f.read(reinterpret_cast<char *>(b.data()), std::streamsize(n));
    if (std::size_t(f.gcount()) != n)
      fail(std::string("incomplete: file ends inside ") + what);
    return b;
  }
};
struct End {
  U first_index = 0, frames = 0, total = 0, status = 0;
};
// Streaming reader: one frame at a time, validating everything as it goes.
struct Reader {
  Source src;
  Bytes metadata;
  Manifest man;
  std::array<std::uint8_t, 16> stream_id{};
  U created_ns = 0;
  End end;
  bool ended = false;

  void init() {
    Bytes h = src.read(0, 64, "container header");
    vh(h, 56);
    need(magic(h, "NWTBIN\r\n") && get(h, 8, 2) == 1 && get(h, 12, 2) == 64, "container fields");
    U minor = get(h, 10, 2);
    need(minor == 0 || minor == 1, "unsupported container minor");
    View hv(h);
    need(get(h, 14, 2) == 0 && zero(hv.subspan(48, 8)) && zero(hv.subspan(60, 4)) && !zero(hv.subspan(24, 16)),
         "container reserved/ID");
    U ml = get(h, 16, 4);
    need(ml >= 8 && ml <= 1048576 && ml % 8 == 0, "metadata length");
    metadata = src.read(64, std::size_t(ml), "metadata");
    need(crc(metadata) == get(h, 20, 4), "metadata CRC");
    man = parse_manifest(parse_metadata(metadata).manifest);
    std::copy(h.begin() + 24, h.begin() + 40, stream_id.begin());
    created_ns = get(h, 40, 8);
    need(minor == (man.minor1 ? 1u : 0u), "container minor does not match the declared types");
  }
  void open_file(const char *path) {
    src.open_file(path);
    init();
  }
  void open_mem(View v) {
    src.open_mem(v);
    init();
  }
  FrameInfo frame_info(U offset) {
    Bytes h = src.read(offset, 64, "frame header");
    vh(h, 52);
    need(magic(h, "NWF1") && h[4] == 1 && (h[6] == 0 || h[6] == 1) && h[7] == 0 && get(h, 8, 2) == 64 &&
             get(h, 10, 2) == 0 && get(h, 56, 8) == 0,
         "frame fields/codec");
    FrameInfo i;
    i.offset = offset;
    i.kind = h[5];
    i.codec = h[6];
    i.stored = get(h, 12, 4);
    i.raw = get(h, 16, 4);
    i.count = get(h, 20, 4);
    i.seq = get(h, 24, 8);
    i.lo = get(h, 32, 8);
    i.hi = get(h, 40, 8);
    i.crc = get(h, 48, 4);
    need(i.kind >= 1 && i.kind <= 3, "frame sequence/kind");
    need(i.stored <= LIMIT && i.raw <= LIMIT, "frame size");
    // Raw frames store the payload as is; only DATA frames may be compressed.
    need(i.codec == 0 ? i.stored == i.raw : i.kind == 1, "frame size/codec");
    return i;
  }
  Bytes payload(const FrameInfo &i) {
    Bytes padded = src.read(i.offset + 64, std::size_t((i.stored + 7) & ~U(7)), "frame payload");
    need(zero(View(padded).subspan(std::size_t(i.stored))), "frame padding");
    padded.resize(std::size_t(i.stored));
    Bytes raw = i.codec == 0 ? std::move(padded) : zstd_decompress(padded, i.raw);
    need(crc(raw) == i.crc, "payload CRC");
    return raw;
  }
  // Full sequential validation. cb(FrameInfo, raw records, decoded records) runs once per frame,
  // after the frame has passed every check. INDEX and END frames carry empty lists.
  template <class F> void scan(bool decode, F &&cb) {
    ended = false;
    Scope scope(&man);
    U pos = 64 + metadata.size(), seq = 0, records = 0, first_index = 0, nd = 0;
    Bytes entries, index;
    while (!ended || pos < src.size) {
      need(!ended, "trailing bytes");
      need(pos < src.size, "incomplete: missing END");
      FrameInfo info = frame_info(pos);
      need(info.seq == seq, "frame sequence/kind");
      Bytes data = payload(info);
      std::vector<View> raws;
      std::vector<Rec> decoded;
      if (info.kind == 1) {
        need(first_index == 0, "DATA order/count");
        raws = split_records(data, info.count);
        for (auto raw : raws) {
          scope.check(raw);
          if (decode)
            decoded.push_back(decode_record(raw));
        }
        need(time_bounds(raws) == std::pair<U, U>{info.lo, info.hi}, "time bounds");
        append(entries, index_entry(info));
        records += raws.size();
        ++nd;
      } else {
        need(info.count == 0 && info.lo == NIL && info.hi == NIL, "non-DATA fields");
        if (info.kind == 2) {
          need(info.raw > 0 && info.raw % 40 == 0, "index size");
          if (!first_index)
            first_index = pos;
          append(index, data);
        } else {
          need(info.raw == 32, "END size");
          End e;
          e.first_index = get(data, 0, 8);
          e.frames = get(data, 8, 8);
          e.total = get(data, 16, 8);
          e.status = get(data, 24, 4);
          need(e.first_index == first_index && e.frames == nd && e.total == records && get(data, 28, 4) == 0,
               "END totals/status");
          need(e.status == 0 || e.status == 1, "END totals/status");
          need(!first_index || index == entries, "index mismatch");
          end = e;
          ended = true;
        }
      }
      cb(info, raws, decoded);
      pos += 64 + ((info.stored + 7) & ~U(7));
      ++seq;
    }
  }
};

// -------------------------------------------------------------- benchmark

std::string rate_line(const char *label, U records, U size, U ns) {
  ns = std::max<U>(ns, 1);
  U128 mb = U128(size) * 1000000000000ULL / (U128(ns) * 1048576); // thousandths of a MiB per second
  U128 rps = U128(records) * 1000000000ULL / ns;
  char buf[256];
  std::snprintf(buf, sizeof buf, "%s records=%llu seconds=%llu.%06llu records_per_second=%llu mb_per_second=%llu.%03llu\n",
                label, (unsigned long long)records, (unsigned long long)(ns / 1000000000ULL),
                (unsigned long long)(ns % 1000000000ULL / 1000), (unsigned long long)rps,
                (unsigned long long)(mb / 1000), (unsigned long long)(mb % 1000));
  return buf;
}
Bytes read_file(const char *path) {
  std::ifstream in(path, std::ios::binary);
  need(bool(in), "open input");
  return Bytes(std::istreambuf_iterator<char>(in), {});
}
// Time a full decode (frames, CRC, decompression, typed records) and a re-encode of every record.
std::string bench(const char *path) {
  using Clock = std::chrono::steady_clock;
  auto ns_since = [](Clock::time_point a, Clock::time_point b) {
    return U(std::chrono::duration_cast<std::chrono::nanoseconds>(b - a).count());
  };
  Bytes data = read_file(path);
  auto t0 = Clock::now();
  std::vector<std::pair<const Sch *, std::size_t>> typed; // schema, offset in pool
  std::vector<U> pool;
  std::vector<Rec> general;
  U size = 0;
  Reader rd;
  rd.open_mem(data);
  rd.scan(false, [&](const FrameInfo &, const std::vector<View> &raws, std::vector<Rec> &) {
    for (auto raw : raws) {
      const Sch *s = BY[raw[4] | (raw[5] << 8)];
      if (s && s->typed && raw.size() == s->fixed) {
        std::size_t at = pool.size();
        pool.resize(at + s->fl.size());
        decode_typed(raw, *s, pool.data() + at);
        typed.push_back({s, at});
      } else {
        general.push_back(decode_record(raw));
      }
      size += raw.size();
    }
  });
  auto t1 = Clock::now();
  Bytes out;
  U sink = 0;
  for (const auto &t : typed) {
    out.clear();
    encode_into(out, *t.first, pool.data() + t.second, nullptr, 0, nullptr);
    sink += out.size() + out.back();
  }
  for (const auto &r : general) {
    out.clear();
    encode_into(out, schema_of(r.type), r.f.data(), r.lv.data(), r.lv.size() / LF.size(), r.tx.data());
    sink += out.size() + out.back();
  }
  auto t2 = Clock::now();
  volatile U keep = sink; // keep the encoding work observable
  (void)keep;
  U count = typed.size() + general.size();
  return rate_line("decode", count, size, ns_since(t0, t1)) + rate_line("encode", count, size, ns_since(t1, t2));
}

// ------------------------------------------------------------ command line

const std::array<std::uint8_t, 16> LEGACY_ID{0x10, 0x21, 0x32, 0x43, 0x54, 0x65, 0x76, 0x87,
                                             0x98, 0xa9, 0xba, 0xcb, 0xdc, 0xed, 0xfe, 0x0f};
const std::array<std::uint8_t, 16> V11_ID{0xa1, 0xb2, 0xc3, 0xd4, 0xe5, 0xf6, 0x07, 0x18,
                                          0x29, 0x3a, 0x4b, 0x5c, 0x6d, 0x7e, 0x8f, 0x90};
void write_file(const char *path, const Bytes &b) {
  std::ofstream out(path, std::ios::binary);
  need(bool(out), "open output");
  out.write(reinterpret_cast<const char *>(b.data()), std::streamsize(b.size()));
  out.close();
  need(bool(out), "write output");
}
void write_catalog(const std::string &path, const char *catalog, const char *manifest, const std::array<std::uint8_t, 16> &id,
                   U created, int level) {
  std::ofstream out(path, std::ios::binary);
  need(bool(out), "open output");
  Writer w(out, tlv(1, 1, bytes(manifest)), id, created, 1 << 20, 3, level);
  for (const auto &e : J::parse(catalog))
    if (!e.value("standalone", false))
      w.write(rec_from_json(e));
  w.close(0);
  out.close();
  need(bool(out), "write output");
}
int main(int argc, char **argv) {
  std::ios::sync_with_stdio(false);
  try {
    init_registry();
    need(crc(bytes("123456789")) == 0xe3069283u && crc_sw(reinterpret_cast<const std::uint8_t *>("123456789"), 9) == 0xe3069283u,
         "CRC check");
    std::vector<std::string> args;
    bool pretty = false, zst = false;
    for (int i = 1; i < argc; i++) {
      std::string a = argv[i];
      if (a == "--pretty")
        pretty = true;
      else if (a == "--zstd")
        zst = true;
      else
        args.push_back(a);
    }
    need(args.size() >= 2, USAGE);
    const std::string &cmd = args[0];
    if (cmd == "write") {
      write_catalog(args[1], catalog_json, manifest_json, LEGACY_ID, 1700000000000000000ULL, 0);
    } else if (cmd == "write-v11") {
      write_catalog(args[1], catalog_v11_json, manifest_v11_json, V11_ID, 1760000000000000000ULL, zst ? 3 : 0);
    } else if (cmd == "record") {
      need(args.size() == 3, USAGE);
      U typ = parse_u(args[1]);
      J catalog = J::parse(typ <= 9 ? catalog_json : catalog_v11_json);
      auto it = std::find_if(catalog.begin(), catalog.end(), [&](const J &r) { return r.at("type").get<U>() == typ; });
      need(it != catalog.end(), "no example for this record type");
      write_file(args[2].c_str(), encode_record(rec_from_json(*it)));
    } else if (cmd == "decode-record") {
      need(std::filesystem::file_size(args[1]) <= MAXREC, "record limit");
      Bytes b = read_file(args[1].c_str());
      std::string o;
      report_into(o, 1, decode_record(b));
      emit(o);
    } else if (cmd == "read") {
      std::optional<std::string> again;
      if (args.size() > 2)
        again = args[2];
      if (again && std::filesystem::exists(*again) && std::filesystem::exists(args[1]))
        need(!std::filesystem::equivalent(args[1], *again), "REENCODED_FILE must differ from FILE");
      Reader rd;
      rd.open_file(args[1].c_str());
      std::ofstream out;
      std::optional<Writer> w;
      if (again) {
        out.open(*again, std::ios::binary);
        need(bool(out), "open output");
        // The re-encode keeps the input's identity and metadata bytes; only the framing is rewritten.
        w.emplace(out, rd.metadata, rd.stream_id, rd.created_ns, 1 << 20, 3, 0);
      }
      std::size_t n = 0;
      rd.scan(true, [&](const FrameInfo &, const std::vector<View> &, std::vector<Rec> &recs) {
        std::string o;
        for (const auto &r : recs) {
          report_into(o, ++n, r);
          if (w)
            w->write(r);
        }
        emit(o);
      });
      need(rd.end.status == 0, "aborted container");
      if (w) {
        w->close(0);
        out.close();
        need(bool(out), "write output");
      }
    } else if (cmd == "to-json") {
      Reader rd;
      rd.open_file(args[1].c_str());
      rd.scan(true, [&](const FrameInfo &, const std::vector<View> &, std::vector<Rec> &recs) {
        std::string o;
        for (const auto &r : recs)
          o += to_json_line(r, pretty) + "\n";
        emit(o);
      });
      need(rd.end.status == 0, "aborted container");
    } else if (cmd == "to-csv") {
      need(args.size() == 3, USAGE);
      U typ = parse_u(args[2]);
      need(typ < 65536 && BY[typ], "unknown record type");
      std::string header = csv_header(*BY[typ]);
      Reader rd;
      rd.open_file(args[1].c_str());
      emit(header + "\n");
      rd.scan(true, [&](const FrameInfo &, const std::vector<View> &, std::vector<Rec> &recs) {
        std::string o;
        for (const auto &r : recs)
          if (r.type == typ)
            o += to_csv_line(r, pretty) + "\n";
        emit(o);
      });
      need(rd.end.status == 0, "aborted container");
    } else if (cmd == "bench") {
      emit(bench(args[1].c_str()));
    } else {
      throw std::runtime_error("unknown command");
    }
    std::cout.flush();
    return 0;
  } catch (const std::exception &e) {
    std::cout.flush();
    std::cerr << "NWT error: " << e.what() << '\n';
    return 1;
  }
}
