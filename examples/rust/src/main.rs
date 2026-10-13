// NWT teaching codec for all 22 record types. All integers use explicit little-endian byte operations.
// Validation and output are driven by schemas/records.json. No floating point is used anywhere.
use serde::Deserialize;
use std::{
    collections::{BTreeMap, HashMap, HashSet},
    error::Error,
    fs::{self, File},
    io::{BufReader, BufWriter, Cursor, Read, Write},
    sync::OnceLock,
    time::Instant,
};

type R<T> = Result<T, Box<dyn Error>>;
type Values = BTreeMap<String, String>;
const NULL: u64 = u64::MAX;
const LIMIT: usize = 16_777_216; // largest frame payload and largest Zstd window
const RECORD_LIMIT: usize = 1_048_576;
const MANIFEST: &str = include_str!("../../../fixtures/manifest.json");
const MANIFEST_V11: &str = include_str!("../../../fixtures/manifest-v1.1.json");
const CATALOG: &str = include_str!("../../../fixtures/catalog.json");
const CATALOG_V11: &str = include_str!("../../../fixtures/catalog-v1.1.json");
const SCHEMA: &str = include_str!("../../../schemas/records.json");
const LEGACY_ID: [u8; 16] = [
    0x10, 0x21, 0x32, 0x43, 0x54, 0x65, 0x76, 0x87, 0x98, 0xa9, 0xba, 0xcb, 0xdc, 0xed, 0xfe, 0x0f,
];
const V11_ID: [u8; 16] = [
    0xa1, 0xb2, 0xc3, 0xd4, 0xe5, 0xf6, 0x07, 0x18, 0x29, 0x3a, 0x4b, 0x5c, 0x6d, 0x7e, 0x8f, 0x90,
];
const USAGE: &str = "usage: nwt-example write FILE | write-v11 FILE [--zstd] | read FILE [REENCODED_FILE] | \
record TYPE FILE | decode-record FILE | to-json FILE [--pretty] | to-csv FILE TYPE [--pretty] | bench FILE";

// ------------------------------------------------------------------ schema

#[derive(Deserialize)]
struct Field {
    name: String,
    bytes: usize,
    signed: bool,
    kind: Option<String>,
}
#[derive(Deserialize)]
struct Schema {
    r#type: u16,
    name: String,
    fixed_bytes: usize,
    fields: Vec<Field>,
    texts: Vec<String>,
    has_levels: bool,
    #[serde(default)]
    enums: BTreeMap<String, Vec<u64>>,
    #[serde(default)]
    masks: BTreeMap<String, u64>,
    #[serde(default)]
    text_limits: BTreeMap<String, (u64, u64)>,
    #[serde(default)]
    text_exact: BTreeMap<String, Vec<u64>>,
}
#[derive(Deserialize)]
struct Schemas {
    header: Vec<Field>,
    level: Vec<Field>,
    schemas: Vec<Schema>,
}
#[derive(Clone, Deserialize)]
struct Record {
    r#type: u16,
    fields: Values,
    texts: Values,
    levels: Vec<Values>,
    #[serde(default)]
    standalone: bool,
}

fn need(ok: bool, msg: &str) -> R<()> {
    if ok {
        Ok(())
    } else {
        Err(msg.into())
    }
}
fn number(v: &Values, k: &str) -> R<u64> {
    Ok(v.get(k).ok_or("missing field")?.parse()?)
}
fn schema(s: &Schemas, t: u16) -> R<&Schema> {
    s.schemas
        .iter()
        .find(|x| x.r#type == t)
        .ok_or_else(|| "unknown schema".into())
}

// ------------------------------------------------------------ bytes and CRC

/// Eight lookup tables for slicing-by-8 CRC-32C (reflected polynomial 0x82f63b78).
fn crc_tables() -> &'static [[u32; 256]; 8] {
    static TABLES: OnceLock<[[u32; 256]; 8]> = OnceLock::new();
    TABLES.get_or_init(|| {
        let mut t = [[0u32; 256]; 8];
        for i in 0..256 {
            let mut c = i as u32;
            for _ in 0..8 {
                c = (c >> 1) ^ if c & 1 != 0 { 0x82f63b78 } else { 0 };
            }
            t[0][i] = c;
        }
        for i in 0..256 {
            for k in 1..8 {
                let p = t[k - 1][i];
                t[k][i] = (p >> 8) ^ t[0][(p & 0xff) as usize];
            }
        }
        t
    })
}
fn crc(b: &[u8]) -> u32 {
    let t = crc_tables();
    let mut c = 0xffff_ffffu32;
    let mut chunks = b.chunks_exact(8);
    for ch in &mut chunks {
        let lo = u32::from_le_bytes([ch[0], ch[1], ch[2], ch[3]]) ^ c;
        let hi = u32::from_le_bytes([ch[4], ch[5], ch[6], ch[7]]);
        c = t[7][(lo & 0xff) as usize]
            ^ t[6][((lo >> 8) & 0xff) as usize]
            ^ t[5][((lo >> 16) & 0xff) as usize]
            ^ t[4][(lo >> 24) as usize]
            ^ t[3][(hi & 0xff) as usize]
            ^ t[2][((hi >> 8) & 0xff) as usize]
            ^ t[1][((hi >> 16) & 0xff) as usize]
            ^ t[0][(hi >> 24) as usize];
    }
    for x in chunks.remainder() {
        c = t[0][((c ^ *x as u32) & 0xff) as usize] ^ (c >> 8);
    }
    c ^ 0xffff_ffff
}
fn pad(mut b: Vec<u8>) -> Vec<u8> {
    b.resize((b.len() + 7) & !7, 0);
    b
}
fn get(b: &[u8], o: usize, n: usize) -> R<u64> {
    need(n <= 8 && o <= b.len() && n <= b.len() - o, "integer bounds")?;
    let mut a = [0; 8];
    a[..n].copy_from_slice(&b[o..o + n]);
    Ok(u64::from_le_bytes(a))
}
fn put(b: &mut [u8], o: usize, n: usize, v: u64) {
    b[o..o + n].copy_from_slice(&v.to_le_bytes()[..n]);
}
// Unchecked readers for callers that already know the bytes are there.
fn le16(b: &[u8], o: usize) -> u16 {
    u16::from_le_bytes([b[o], b[o + 1]])
}
fn le32(b: &[u8], o: usize) -> u32 {
    u32::from_le_bytes([b[o], b[o + 1], b[o + 2], b[o + 3]])
}
fn le64(b: &[u8], o: usize) -> u64 {
    u64::from_le_bytes([
        b[o],
        b[o + 1],
        b[o + 2],
        b[o + 3],
        b[o + 4],
        b[o + 5],
        b[o + 6],
        b[o + 7],
    ])
}
/// A little-endian unsigned integer of 1 to 8 bytes (the schema has 3-, 6- and 7-byte reserved blocks).
fn uint(b: &[u8], o: usize, n: usize) -> u64 {
    match n {
        1 => b[o] as u64,
        2 => le16(b, o) as u64,
        4 => le32(b, o) as u64,
        8 => le64(b, o),
        _ => b[o..o + n].iter().rev().fold(0u64, |a, x| (a << 8) | *x as u64),
    }
}
fn hcrc(mut b: Vec<u8>, o: usize) -> Vec<u8> {
    put(&mut b, o, 4, 0);
    let c = crc(&b);
    put(&mut b, o, 4, c as u64);
    b
}
fn vh(b: &[u8], o: usize) -> R<()> {
    need(b.len() == 64, "header size")?;
    let c = get(b, o, 4)?;
    let mut t = b.to_vec();
    put(&mut t, o, 4, 0);
    need(crc(&t) as u64 == c, "header CRC")
}
/// Reads until `buf` is full or the input ends; returns how many bytes arrived.
fn fill<T: Read>(r: &mut T, buf: &mut [u8]) -> R<usize> {
    let mut n = 0;
    while n < buf.len() {
        match r.read(&mut buf[n..]) {
            Ok(0) => break,
            Ok(k) => n += k,
            Err(e) if e.kind() == std::io::ErrorKind::Interrupted => {}
            Err(e) => return Err(e.into()),
        }
    }
    Ok(n)
}

// ------------------------------------------------------------------ records

fn enc_fields(v: &Values, fields: &[Field]) -> R<Vec<u8>> {
    let mut b = vec![];
    for f in fields {
        let text = v.get(&f.name).ok_or("missing field")?;
        let x = if f.signed {
            text.parse::<i64>()? as u64
        } else {
            text.parse::<u64>()?
        };
        need(f.bytes == 8 || x < (1u64 << (8 * f.bytes)), "integer range")?;
        if f.name == "reserved" {
            need(x == 0, "reserved must be zero")?;
        }
        b.extend_from_slice(&x.to_le_bytes()[..f.bytes]);
    }
    Ok(b)
}
fn dec_fields(b: &[u8], p: &mut usize, fields: &[Field]) -> R<Values> {
    let mut v = Values::new();
    for f in fields {
        let x = get(b, *p, f.bytes)?;
        *p += f.bytes;
        if f.name == "reserved" {
            need(x == 0, "nonzero reserved")?;
        }
        v.insert(
            f.name.clone(),
            if f.signed {
                (x as i64).to_string()
            } else {
                x.to_string()
            },
        );
    }
    Ok(v)
}
fn text_bytes(s: &str) -> R<&[u8]> {
    need(!s.contains('\0'), "NUL text")?;
    Ok(s.as_bytes())
}
/// Rules shared by encode and decode, all read from the schema: enums, flag masks and text byte lengths.
fn check_schema(s: &Schema, f: &Values) -> R<()> {
    for (name, allowed) in &s.enums {
        if !allowed.contains(&number(f, name)?) {
            return Err(format!("invalid {name}").into());
        }
    }
    for (name, mask) in &s.masks {
        if number(f, name)? & !*mask != 0 {
            return Err(format!("invalid {name} bits").into());
        }
    }
    for (name, (lo, hi)) in &s.text_limits {
        let n = number(f, &format!("{name}_bytes"))?;
        if n < *lo || n > *hi {
            return Err(format!("{name} text limit").into());
        }
    }
    for (name, sizes) in &s.text_exact {
        if !sizes.contains(&number(f, &format!("{name}_bytes"))?) {
            return Err(format!("{name} text length").into());
        }
    }
    Ok(())
}
fn encode_record(record: &Record, ss: &Schemas) -> R<Vec<u8>> {
    let mut r = record.clone();
    let type_number = number(&r.fields, "record_type")?;
    need(type_number <= 65535, "type range")?;
    let typ = type_number as u16;
    need(r.r#type == typ, "record type mismatch")?;
    let s = schema(ss, typ)?;
    need(
        number(&r.fields, "schema_version")? == 1 && number(&r.fields, "flags")? & !3 == 0,
        "version/flags",
    )?;
    if s.has_levels {
        need(r.levels.len() <= 1024, "level limit")?;
        r.fields.insert("levels".into(), r.levels.len().to_string());
    }
    for n in &s.texts {
        let v = text_bytes(r.texts.get(n).ok_or("missing text")?)?;
        r.fields.insert(format!("{n}_bytes"), v.len().to_string());
    }
    // The limits are checked before any length is written, so a 16-bit length can never wrap.
    check_schema(s, &r.fields)?;
    let mut body = enc_fields(&r.fields, &s.fields)?;
    if s.has_levels {
        for l in &r.levels {
            body.extend(enc_fields(l, &ss.level)?);
        }
    }
    for n in &s.texts {
        body.extend_from_slice(text_bytes(&r.texts[n])?);
    }
    body = pad(body);
    need(48 + body.len() <= RECORD_LIMIT, "record limit")?;
    r.fields
        .insert("record_bytes".into(), (48 + body.len()).to_string());
    let mut out = enc_fields(&r.fields, &ss.header)?;
    out.extend(body);
    Ok(out)
}
fn decode_record(b: &[u8], ss: &Schemas) -> R<Record> {
    need(
        b.len() >= 48 && b.len() <= RECORD_LIMIT && b.len() % 8 == 0,
        "record size",
    )?;
    let mut p = 0;
    let mut f = dec_fields(b, &mut p, &ss.header)?;
    let typ = number(&f, "record_type")? as u16;
    let s = schema(ss, typ)?;
    need(
        number(&f, "record_bytes")? == b.len() as u64
            && number(&f, "schema_version")? == 1
            && number(&f, "flags")? & !3 == 0,
        "record fields",
    )?;
    f.extend(dec_fields(b, &mut p, &s.fields)?);
    let mut levels = vec![];
    let mut texts = Values::new();
    if s.has_levels {
        let n = number(&f, "levels")?;
        need(n <= 1024, "levels limit")?;
        for _ in 0..n {
            levels.push(dec_fields(b, &mut p, &ss.level)?);
        }
    }
    for name in &s.texts {
        let n = number(&f, &format!("{name}_bytes"))? as usize;
        need(p <= b.len() && n <= b.len() - p, "text bounds")?;
        let text = std::str::from_utf8(&b[p..p + n])?;
        text_bytes(text)?;
        texts.insert(name.clone(), text.to_string());
        p += n;
    }
    // A fixed type must have its exact size; a variable type its exact padded size.
    need(
        (p + 7) & !7 == b.len() && b[p..].iter().all(|x| *x == 0),
        "padding/record length",
    )?;
    check_schema(s, &f)?;
    Ok(Record {
        r#type: typ,
        fields: f,
        texts,
        levels,
        standalone: false,
    })
}

// ------------------------------------------------------------- typed path

/// Byte layout of one fixed-size type, compiled from the schema: no strings are built when decoding.
struct Layout {
    size: usize,
    offs: Vec<(usize, usize)>, // (offset, width) of every header and body field, in schema order
    reserved: Vec<usize>,      // positions in `offs` of the fields named reserved
    version: usize,
    flags: usize,
    enums: Vec<(usize, Vec<u64>)>,
    masks: Vec<(usize, u64)>,
}
impl Layout {
    fn decode(&self, b: &[u8]) -> R<Vec<u64>> {
        need(b.len() == self.size, "record length")?;
        let mut v = Vec::with_capacity(self.offs.len());
        for &(o, n) in &self.offs {
            v.push(uint(b, o, n));
        }
        need(
            v[0] == b.len() as u64 && v[self.version] == 1 && v[self.flags] & !3 == 0,
            "record fields",
        )?;
        for &i in &self.reserved {
            need(v[i] == 0, "nonzero reserved")?;
        }
        for (i, allowed) in &self.enums {
            need(allowed.contains(&v[*i]), "invalid enum value")?;
        }
        for &(i, mask) in &self.masks {
            need(v[i] & !mask == 0, "invalid flag bits")?;
        }
        Ok(v)
    }
    fn encode(&self, v: &[u64]) -> Vec<u8> {
        let mut b = vec![0u8; self.size];
        for (k, &(o, n)) in self.offs.iter().enumerate() {
            b[o..o + n].copy_from_slice(&v[k].to_le_bytes()[..n]);
        }
        b
    }
}
fn layout_for(ss: &Schemas, s: &Schema) -> Option<Layout> {
    if !s.texts.is_empty() || s.has_levels {
        return None;
    }
    let fields: Vec<&Field> = ss.header.iter().chain(s.fields.iter()).collect();
    let mut offs = Vec::new();
    let mut end = 0usize;
    for f in &fields {
        offs.push((end, f.bytes));
        end += f.bytes;
    }
    if end != s.fixed_bytes {
        return None;
    }
    let idx = |name: &str| fields.iter().position(|f| f.name == name);
    let mut enums = Vec::new();
    for (n, a) in &s.enums {
        enums.push((idx(n)?, a.clone()));
    }
    let mut masks = Vec::new();
    for (n, m) in &s.masks {
        masks.push((idx(n)?, *m));
    }
    let reserved: Vec<usize> = fields
        .iter()
        .enumerate()
        .filter(|(_, f)| f.name == "reserved")
        .map(|(i, _)| i)
        .collect();
    Some(Layout {
        size: end,
        offs,
        reserved,
        version: idx("schema_version")?,
        flags: idx("flags")?,
        enums,
        masks,
    })
}
fn build_layouts(ss: &Schemas) -> HashMap<u16, Layout> {
    let mut m = HashMap::new();
    for s in &ss.schemas {
        if let Some(l) = layout_for(ss, s) {
            m.insert(s.r#type, l);
        }
    }
    m
}

// ------------------------------------------------------------- text output

fn write_report<W: Write>(out: &mut W, i: usize, r: &Record, ss: &Schemas) -> R<()> {
    let s = schema(ss, r.r#type)?;
    for f in ss.header.iter().chain(s.fields.iter()) {
        writeln!(out, "{}.{}={}", i, f.name, r.fields[&f.name])?;
    }
    for (j, l) in r.levels.iter().enumerate() {
        for f in &ss.level {
            writeln!(out, "{}.levels.{}.{}={}", i, j, f.name, l[&f.name])?;
        }
    }
    for n in &s.texts {
        writeln!(out, "{}.{}={}", i, n, r.texts[n])?;
    }
    Ok(())
}
/// Integer scaled by 10^9 as a decimal string with exactly nine fractional digits.
fn pretty_decimal(neg: bool, mag: u64) -> String {
    format!(
        "{}{}.{:09}",
        if neg { "-" } else { "" },
        mag / 1_000_000_000,
        mag % 1_000_000_000
    )
}
/// POSIX nanoseconds as YYYY-MM-DDTHH:MM:SS.nnnnnnnnnZ, by integer arithmetic only.
fn pretty_time(ns: u64) -> String {
    let seconds = ns / 1_000_000_000;
    let fraction = ns % 1_000_000_000;
    let days = seconds / 86_400;
    let rest = seconds % 86_400;
    let z = days + 719_468; // days since 0000-03-01
    let era = z / 146_097;
    let doe = z % 146_097;
    let yoe = (doe - doe / 1460 + doe / 36_524 - doe / 146_096) / 365;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100); // day of a year that starts on 1 March
    let mp = (5 * doy + 2) / 153;
    let day = doy - (153 * mp + 2) / 5 + 1;
    let month = if mp < 10 { mp + 3 } else { mp - 9 };
    let year = yoe + era * 400 + if month <= 2 { 1 } else { 0 };
    format!(
        "{:04}-{:02}-{:02}T{:02}:{:02}:{:02}.{:09}Z",
        year,
        month,
        day,
        rest / 3600,
        rest % 3600 / 60,
        rest % 60,
        fraction
    )
}
/// A field value for --pretty: None for a null price, quantity or time; fields without a kind unchanged.
fn pretty_value(f: &Field, text: &str) -> R<Option<String>> {
    let kind = match &f.kind {
        None => return Ok(Some(text.to_string())),
        Some(k) => k.as_str(),
    };
    let (neg, mag, null) = if f.signed {
        let v: i64 = text.parse()?;
        (v < 0, v.unsigned_abs(), v == i64::MIN)
    } else {
        let v: u64 = text.parse()?;
        (false, v, v == u64::MAX)
    };
    if null {
        return Ok(None);
    }
    if kind == "time" {
        need(!neg, "negative time")?;
        Ok(Some(pretty_time(mag)))
    } else {
        Ok(Some(pretty_decimal(neg, mag)))
    }
}
type Items = Vec<(String, Option<String>)>;
/// (name, value) for the given fields: no reserved fields, values reformatted when pretty.
fn items_of(fields: &[&Field], vals: &Values, pretty: bool) -> R<Items> {
    let mut v = Vec::new();
    for f in fields {
        if f.name == "reserved" {
            continue;
        }
        let text = vals.get(&f.name).ok_or("missing field")?;
        let value = if pretty {
            pretty_value(f, text)?
        } else {
            Some(text.clone())
        };
        v.push((f.name.clone(), value));
    }
    Ok(v)
}
/// Header and body fields in output order: no level count for a type with levels.
fn record_fields<'a>(ss: &'a Schemas, s: &'a Schema) -> Vec<&'a Field> {
    ss.header
        .iter()
        .chain(s.fields.iter())
        .filter(|f| !(s.has_levels && f.name == "levels"))
        .collect()
}
fn record_items(r: &Record, ss: &Schemas, pretty: bool) -> R<Items> {
    let s = schema(ss, r.r#type)?;
    let mut items = items_of(&record_fields(ss, s), &r.fields, pretty)?;
    for n in &s.texts {
        items.push((n.clone(), Some(r.texts.get(n).ok_or("missing text")?.clone())));
    }
    Ok(items)
}
fn json_string(out: &mut String, text: &str) {
    out.push('"');
    for ch in text.chars() {
        if ch == '"' || ch == '\\' {
            out.push('\\');
            out.push(ch);
        } else if ch < ' ' {
            out.push_str(&format!("\\u{:04x}", ch as u32));
        } else {
            out.push(ch);
        }
    }
    out.push('"');
}
fn json_object(items: &[(String, Option<String>)]) -> String {
    let mut out = String::from("{");
    for (i, (k, v)) in items.iter().enumerate() {
        if i > 0 {
            out.push(',');
        }
        json_string(&mut out, k);
        out.push(':');
        match v {
            None => out.push_str("null"),
            Some(t) => json_string(&mut out, t),
        }
    }
    out.push('}');
    out
}
fn to_json_line(r: &Record, ss: &Schemas, pretty: bool) -> R<String> {
    let s = schema(ss, r.r#type)?;
    let mut items: Items = vec![("type_name".to_string(), Some(s.name.clone()))];
    items.extend(record_items(r, ss, pretty)?);
    let mut text = json_object(&items);
    if s.has_levels {
        let level_fields: Vec<&Field> = ss.level.iter().collect();
        let mut parts = Vec::new();
        for l in &r.levels {
            parts.push(json_object(&items_of(&level_fields, l, pretty)?));
        }
        text.pop(); // the closing brace
        text.push_str(",\"levels\":[");
        text.push_str(&parts.join(","));
        text.push_str("]}");
    }
    Ok(text)
}
fn csv_value(v: &str) -> String {
    if v.contains(|c: char| c == ',' || c == '"' || c == '\r' || c == '\n') {
        format!("\"{}\"", v.replace('"', "\"\""))
    } else {
        v.to_string()
    }
}
fn csv_header(s: &Schema, ss: &Schemas) -> R<String> {
    need(
        !s.has_levels,
        &format!("type {} has levels; use to-json", s.r#type),
    )?;
    let mut names: Vec<&str> = record_fields(ss, s)
        .into_iter()
        .filter(|f| f.name != "reserved")
        .map(|f| f.name.as_str())
        .collect();
    names.extend(s.texts.iter().map(|t| t.as_str()));
    Ok(names.join(","))
}
fn to_csv_line(r: &Record, ss: &Schemas, pretty: bool) -> R<String> {
    let cells: Vec<String> = record_items(r, ss, pretty)?
        .into_iter()
        .map(|(_, v)| match v {
            None => String::new(),
            Some(t) => csv_value(&t),
        })
        .collect();
    Ok(cells.join(","))
}

// ---------------------------------------------------------------- metadata

enum Json {
    Null,
    Bool,
    Int(i128),
    Str(String),
    Arr(Vec<Json>),
    Obj(Vec<(String, Json)>),
}
/// Strict JSON reader: duplicate object keys at any depth and non-integer numbers are errors.
struct Jp<'a> {
    s: &'a [u8],
    i: usize,
}
impl<'a> Jp<'a> {
    fn peek(&self) -> Option<u8> {
        self.s.get(self.i).copied()
    }
    fn ws(&mut self) {
        while matches!(self.peek(), Some(b' ') | Some(b'\t') | Some(b'\n') | Some(b'\r')) {
            self.i += 1;
        }
    }
    fn value(&mut self, depth: usize) -> R<Json> {
        need(depth < 200, "JSON nesting")?;
        self.ws();
        match self.peek() {
            Some(b'{') => self.object(depth),
            Some(b'[') => self.array(depth),
            Some(b'"') => Ok(Json::Str(self.string()?)),
            Some(b't') => self.word("true", Json::Bool),
            Some(b'f') => self.word("false", Json::Bool),
            Some(b'n') => self.word("null", Json::Null),
            Some(b'-') | Some(b'0'..=b'9') => self.number(),
            _ => Err("JSON syntax".into()),
        }
    }
    fn word(&mut self, w: &str, v: Json) -> R<Json> {
        let s = self.s;
        need(s[self.i..].starts_with(w.as_bytes()), "JSON literal")?;
        self.i += w.len();
        Ok(v)
    }
    fn number(&mut self) -> R<Json> {
        let s = self.s;
        let neg = s[self.i] == b'-';
        if neg {
            self.i += 1;
        }
        let start = self.i;
        while self.i < s.len() && s[self.i].is_ascii_digit() {
            self.i += 1;
        }
        let digits = &s[start..self.i];
        need(
            !digits.is_empty() && (digits.len() == 1 || digits[0] != b'0'),
            "JSON number",
        )?;
        if matches!(self.peek(), Some(b'.') | Some(b'e') | Some(b'E')) {
            return Err("JSON numbers must be integers".into());
        }
        let mut v: i128 = 0;
        for d in digits {
            v = v.saturating_mul(10).saturating_add((*d - b'0') as i128);
        }
        Ok(Json::Int(if neg { -v } else { v }))
    }
    fn hex4(&mut self) -> R<u32> {
        let s = self.s;
        need(self.i + 4 <= s.len(), "JSON \\u escape")?;
        let mut v = 0u32;
        for k in 0..4 {
            let d = (s[self.i + k] as char)
                .to_digit(16)
                .ok_or("JSON \\u escape")?;
            v = v * 16 + d;
        }
        self.i += 4;
        Ok(v)
    }
    fn string(&mut self) -> R<String> {
        let s = self.s;
        self.i += 1; // the opening quote
        let mut out: Vec<u8> = Vec::new();
        loop {
            need(self.i < s.len(), "JSON string ends early")?;
            let c = s[self.i];
            self.i += 1;
            match c {
                b'"' => break,
                b'\\' => {
                    need(self.i < s.len(), "JSON escape")?;
                    let e = s[self.i];
                    self.i += 1;
                    match e {
                        b'"' => out.push(b'"'),
                        b'\\' => out.push(b'\\'),
                        b'/' => out.push(b'/'),
                        b'b' => out.push(8),
                        b'f' => out.push(12),
                        b'n' => out.push(10),
                        b'r' => out.push(13),
                        b't' => out.push(9),
                        b'u' => {
                            let mut u = self.hex4()?;
                            if (0xd800..0xdc00).contains(&u) {
                                need(s[self.i..].starts_with(b"\\u"), "JSON surrogate")?;
                                self.i += 2;
                                let low = self.hex4()?;
                                need((0xdc00..0xe000).contains(&low), "JSON surrogate")?;
                                u = 0x10000 + ((u - 0xd800) << 10) + (low - 0xdc00);
                            }
                            let ch = char::from_u32(u).ok_or("JSON surrogate")?;
                            let mut buf = [0u8; 4];
                            out.extend_from_slice(ch.encode_utf8(&mut buf).as_bytes());
                        }
                        _ => return Err("JSON escape".into()),
                    }
                }
                0..=0x1f => return Err("JSON control character in string".into()),
                _ => out.push(c),
            }
        }
        Ok(String::from_utf8(out)?)
    }
    fn array(&mut self, depth: usize) -> R<Json> {
        self.i += 1;
        let mut items = Vec::new();
        self.ws();
        if self.peek() == Some(b']') {
            self.i += 1;
            return Ok(Json::Arr(items));
        }
        loop {
            items.push(self.value(depth + 1)?);
            self.ws();
            match self.peek() {
                Some(b',') => self.i += 1,
                Some(b']') => {
                    self.i += 1;
                    break;
                }
                _ => return Err("JSON array".into()),
            }
        }
        Ok(Json::Arr(items))
    }
    fn object(&mut self, depth: usize) -> R<Json> {
        self.i += 1;
        let mut items: Vec<(String, Json)> = Vec::new();
        self.ws();
        if self.peek() == Some(b'}') {
            self.i += 1;
            return Ok(Json::Obj(items));
        }
        loop {
            self.ws();
            need(self.peek() == Some(b'"'), "JSON key")?;
            let k = self.string()?;
            need(!items.iter().any(|e| e.0 == k), "duplicate JSON key")?;
            self.ws();
            need(self.peek() == Some(b':'), "JSON colon")?;
            self.i += 1;
            let v = self.value(depth + 1)?;
            items.push((k, v));
            self.ws();
            match self.peek() {
                Some(b',') => self.i += 1,
                Some(b'}') => {
                    self.i += 1;
                    break;
                }
                _ => return Err("JSON object".into()),
            }
        }
        Ok(Json::Obj(items))
    }
}
fn parse_json(text: &str) -> R<Json> {
    let mut p = Jp {
        s: text.as_bytes(),
        i: 0,
    };
    let v = p.value(0)?;
    p.ws();
    need(p.i == p.s.len(), "JSON trailing text")?;
    Ok(v)
}
fn key<'a>(o: &'a [(String, Json)], k: &str) -> Option<&'a Json> {
    o.iter().find(|e| e.0 == k).map(|e| &e.1)
}
fn is_text(v: Option<&Json>, lo: usize, hi: usize) -> bool {
    matches!(v, Some(Json::Str(s)) if s.len() >= lo && s.len() <= hi)
}
fn int_in(v: Option<&Json>, lo: i128, hi: i128) -> Option<i128> {
    match v {
        Some(Json::Int(n)) if *n >= lo && *n <= hi => Some(*n),
        _ => None,
    }
}

/// What the scope checks need from a MANIFEST: the declared (type, version) pairs and publisher IDs.
struct Manifest {
    types: HashSet<(u16, u8)>,
    publishers: HashSet<u32>,
}
impl Manifest {
    /// Container minor: 1 exactly when a standard type above the 1.0 range (10 up to the highest in the schema) is declared.
    fn minor(&self, ss: &Schemas) -> u64 {
        let top = ss.schemas.iter().map(|s| s.r#type).max().unwrap_or(9);
        if self.types.iter().any(|&(t, _)| t >= 10 && t <= top) {
            1
        } else {
            0
        }
    }
}
/// Parse and validate a MANIFEST value. Unknown properties are ignored.
fn parse_manifest(text: &str) -> R<Manifest> {
    let m = parse_json(text)?;
    let o = match &m {
        Json::Obj(o) => o,
        _ => return Err("manifest must be a JSON object".into()),
    };
    for k in ["dataset", "producer", "profile", "publishers", "schemas", "clock"] {
        if key(o, k).is_none() {
            return Err(format!("manifest missing {k}").into());
        }
    }
    need(
        is_text(key(o, "dataset"), 1, 255) && is_text(key(o, "producer"), 1, 255),
        "manifest dataset/producer",
    )?;
    need(
        matches!(key(o, "profile"), Some(Json::Str(p)) if p == "market-data" || p == "generic-events"),
        "manifest profile",
    )?;
    need(
        matches!(key(o, "clock"), Some(Json::Str(c)) if c == "posix-ns"),
        "manifest clock",
    )?;
    let ordering_ok = match key(o, "ordering") {
        None => true,
        Some(Json::Str(p)) => p == "none" || p == "ts_event" || p == "instrument,ts_event",
        Some(_) => false,
    };
    need(ordering_ok, "manifest ordering")?;
    let pubs = match key(o, "publishers") {
        Some(Json::Arr(a)) if a.len() <= 4096 => a,
        _ => return Err("manifest publishers".into()),
    };
    let mut publishers = HashSet::new();
    for p in pubs {
        let po = match p {
            Json::Obj(po) => po,
            _ => return Err("manifest publisher".into()),
        };
        let id = int_in(key(po, "id"), 1, 4_294_967_295).ok_or("manifest publisher id")?;
        need(
            is_text(key(po, "name"), 1, 255) && is_text(key(po, "venue"), 0, 255),
            "manifest publisher name/venue",
        )?;
        need(publishers.insert(id as u32), "manifest duplicate publisher")?;
    }
    let decl = match key(o, "schemas") {
        Some(Json::Arr(a)) if !a.is_empty() && a.len() <= 4096 => a,
        _ => return Err("manifest schemas".into()),
    };
    let mut types = HashSet::new();
    for d in decl {
        let so = match d {
            Json::Obj(so) => so,
            _ => return Err("manifest schema".into()),
        };
        let t = int_in(key(so, "type"), 1, 65534);
        let v = int_in(key(so, "version"), 1, 255);
        let (t, v) = match (t, v) {
            (Some(t), Some(v)) => (t, v),
            _ => return Err("manifest schema type/version".into()),
        };
        need(
            matches!(key(so, "required"), Some(Json::Bool)),
            "manifest schema required",
        )?;
        need(
            is_text(key(so, "name"), 1, 255) && is_text(key(so, "spec_uri"), 1, 2048),
            "manifest schema name/spec_uri",
        )?;
        need(
            types.insert((t as u16, v as u8)),
            "manifest duplicate schema",
        )?;
    }
    Ok(Manifest { types, publishers })
}
fn tlv(typ: u16, flags: u16, value: &[u8]) -> Vec<u8> {
    let mut b = vec![0; 8];
    put(&mut b, 0, 2, typ as u64);
    put(&mut b, 2, 2, flags as u64);
    put(&mut b, 4, 4, value.len() as u64);
    b.extend_from_slice(value);
    pad(b)
}
/// Check the TLV elements of the metadata and return the parsed MANIFEST.
/// Unknown optional elements are bounds-checked and skipped.
fn parse_metadata(meta: &[u8]) -> R<Manifest> {
    let mut seen: Vec<u64> = Vec::new();
    let mut manifest: Option<Manifest> = None;
    let mut p = 0usize;
    while p < meta.len() {
        need(meta.len() - p >= 8, "TLV header")?;
        let typ = get(meta, p, 2)?;
        let flags = get(meta, p + 2, 2)?;
        let n = get(meta, p + 4, 4)? as usize;
        need(typ > 0 && typ < 65535 && flags & !1 == 0, "TLV type/flags")?;
        need(!seen.contains(&typ), "duplicate TLV")?;
        need(n <= meta.len() - p - 8, "TLV length")?;
        let end = p + 8 + n;
        let next = (end + 7) & !7;
        need(
            next <= meta.len() && meta[end..next].iter().all(|x| *x == 0),
            "TLV padding",
        )?;
        need(typ == 1 || typ == 2 || flags == 0, "unknown required TLV")?;
        seen.push(typ);
        if typ == 1 {
            need(
                flags == 1,
                "MANIFEST TLV must be present with its required flag",
            )?;
            manifest = Some(parse_manifest(std::str::from_utf8(&meta[p + 8..end])?)?);
        }
        if typ == 2 {
            need(flags == 0, "PROVENANCE TLV must not be marked required")?;
            let value = parse_json(std::str::from_utf8(&meta[p + 8..end])?)?;
            need(matches!(value, Json::Obj(_)), "PROVENANCE must be a JSON object")?;
        }
        p = next;
    }
    manifest.ok_or_else(|| "MANIFEST TLV must be present with its required flag".into())
}

// -------------------------------------------------------------------- Zstd

/// Spec 10.2 checked by hand on the Zstd frame header, before any library call.
/// Returns the length of the frame header.
fn zstd_check(stored: &[u8], raw_bytes: usize) -> R<usize> {
    need(
        stored.len() >= 6 && &stored[..4] == b"\x28\xb5\x2f\xfd",
        "Zstd magic",
    )?;
    let d = stored[4];
    let fcs = (d >> 6) as usize;
    let single = (d >> 5) & 1 == 1;
    // RFC 8878: bit 3 is reserved; bit 2 (content checksum) is allowed; bits 0-1 flag a dictionary ID.
    need(d & 0x08 == 0, "Zstd reserved bit")?;
    need(d & 0x03 == 0, "Zstd dictionary")?;
    let mut p = 5usize;
    let mut window = 0u64;
    if !single {
        let w = stored[p] as u64;
        p += 1;
        let base = 1u64 << (10 + (w >> 3));
        window = base + (base >> 3) * (w & 7);
    }
    let n: usize = [if single { 1 } else { 0 }, 2, 4, 8][fcs];
    need(n > 0, "Zstd content size missing")?;
    need(stored.len() >= p + n, "Zstd header")?;
    let size = get(stored, p, n)? + if fcs == 1 { 256 } else { 0 };
    need(size == raw_bytes as u64, "Zstd content size")?;
    need(
        (if single { size } else { window }) <= LIMIT as u64,
        "Zstd window",
    )?;
    Ok(p + n)
}
/// Length of the one Zstd frame at the start of `stored`, found by walking its blocks.
#[cfg(feature = "zstd")]
fn zstd_frame_len(stored: &[u8], header: usize) -> R<usize> {
    let mut p = header;
    loop {
        need(stored.len() >= p + 3, "Zstd block header")?;
        let h = get(stored, p, 3)? as usize;
        p += 3;
        let size = h >> 3;
        match (h >> 1) & 3 {
            0 | 2 => p += size,
            1 => p += 1,
            _ => return Err("Zstd block type".into()),
        }
        need(stored.len() >= p, "Zstd block")?;
        if h & 1 == 1 {
            break;
        }
    }
    if stored[4] & 0x04 != 0 {
        p += 4; // content checksum
    }
    Ok(p)
}
#[cfg(feature = "zstd")]
fn zstd_unpack(stored: &[u8], raw_bytes: usize, header: usize) -> R<Vec<u8>> {
    // Exactly one frame: no concatenated or skippable frame and no trailing bytes.
    need(
        zstd_frame_len(stored, header)? == stored.len(),
        "Zstd frame must fill stored_bytes exactly",
    )?;
    let out = zstd::bulk::decompress(stored, raw_bytes).map_err(|_| "Zstd decompression failed")?;
    need(out.len() == raw_bytes, "Zstd decompression failed")?;
    Ok(out)
}
#[cfg(not(feature = "zstd"))]
fn zstd_unpack(_stored: &[u8], _raw_bytes: usize, _header: usize) -> R<Vec<u8>> {
    Err("Zstd library not available".into())
}
#[cfg(feature = "zstd")]
fn zstd_pack(b: &[u8], level: i32) -> R<Vec<u8>> {
    Ok(zstd::bulk::compress(b, level)?)
}
#[cfg(not(feature = "zstd"))]
fn zstd_pack(_b: &[u8], _level: i32) -> R<Vec<u8>> {
    Err("Zstd library not available".into())
}
fn zstd_decompress(stored: &[u8], raw_bytes: usize) -> R<Vec<u8>> {
    let header = zstd_check(stored, raw_bytes)?;
    zstd_unpack(stored, raw_bytes, header)
}

// --------------------------------------------------------------- container

fn frame(
    kind: u8,
    seq: u64,
    payload: &[u8],
    count: u64,
    lo: u64,
    hi: u64,
    codec: u8,
    stored: &[u8],
) -> Vec<u8> {
    let mut h = vec![0; 64];
    h[..4].copy_from_slice(b"NWF1");
    h[4] = 1;
    h[5] = kind;
    h[6] = codec;
    for (o, n, v) in [
        (8, 2, 64u64),
        (12, 4, stored.len() as u64),
        (16, 4, payload.len() as u64),
        (20, 4, count),
        (24, 8, seq),
        (32, 8, lo),
        (40, 8, hi),
        (48, 4, crc(payload) as u64),
    ] {
        put(&mut h, o, n, v);
    }
    let mut out = hcrc(h, 52);
    out.extend_from_slice(stored);
    out.resize(64 + ((stored.len() + 7) & !7), 0);
    out
}
fn entry(seq: u64, offset: u64, lo: u64, hi: u64, raw: u64, count: u64) -> Vec<u8> {
    let mut b = vec![0; 40];
    for (o, n, v) in [
        (0, 8, seq),
        (8, 8, offset),
        (16, 8, lo),
        (24, 8, hi),
        (32, 4, raw),
        (36, 4, count),
    ] {
        put(&mut b, o, n, v);
    }
    b
}
/// (min, max) of the non-null ts_event values of the records in `spans`, or (NULL, NULL).
fn bounds(data: &[u8], spans: &[(usize, usize)]) -> (u64, u64) {
    let mut found: Option<(u64, u64)> = None;
    for &(a, _) in spans {
        let t = le64(data, a + 24);
        if t != NULL {
            found = Some(match found {
                None => (t, t),
                Some((lo, hi)) => (lo.min(t), hi.max(t)),
            });
        }
    }
    found.unwrap_or((NULL, NULL))
}
fn split_records(data: &[u8], count: u64) -> R<Vec<(usize, usize)>> {
    need(count > 0 && data.len() % 8 == 0, "DATA order/count")?;
    let mut spans = Vec::new();
    let mut p = 0;
    while p < data.len() {
        let n = get(data, p, 4)? as usize;
        need(
            n >= 48 && n <= RECORD_LIMIT && n % 8 == 0 && n <= data.len() - p,
            "record bounds",
        )?;
        spans.push((p, p + n));
        p += n;
    }
    need(spans.len() as u64 == count, "record count")?;
    Ok(spans)
}

/// Checks that need only a record's 48-byte header: declared type, declared publisher, sequence.
struct Scope {
    types: HashSet<(u16, u8)>,
    publishers: HashSet<u32>,
    last: HashMap<(u32, u32), u64>,
}
impl Scope {
    fn new(m: &Manifest) -> Scope {
        Scope {
            types: m.types.clone(),
            publishers: m.publishers.clone(),
            last: HashMap::new(),
        }
    }
    fn check(&mut self, raw: &[u8]) -> R<()> {
        need(
            self.types.contains(&(le16(raw, 4), raw[6])),
            "undeclared record type",
        )?;
        let k = (le32(raw, 8), le32(raw, 12));
        need(
            k.0 == 0 || self.publishers.contains(&k.0),
            "undeclared publisher",
        )?;
        let seq = le64(raw, 40);
        let last = self.last.get(&k).copied().unwrap_or(0);
        need(last.checked_add(1) == Some(seq), "record sequence")?;
        self.last.insert(k, seq);
        Ok(())
    }
}

/// Streaming container writer: header and metadata first, DATA frames as they fill, INDEX and END on close.
struct Writer<W: Write> {
    out: W,
    position: u64,
    frame_bytes: usize,
    frame_records: Option<usize>,
    zstd: Option<i32>,
    scope: Scope,
    payload: Vec<u8>,
    count: usize,
    time: Option<(u64, u64)>,
    entries: Vec<u8>,
    seq: u64,
    frames: u64,
    records: u64,
}
impl<W: Write> Writer<W> {
    #[allow(clippy::too_many_arguments)]
    fn new(
        out: W,
        metadata: Vec<u8>,
        stream_id: [u8; 16],
        created_ns: u64,
        frame_bytes: usize,
        frame_records: Option<usize>,
        zstd: Option<i32>,
        ss: &Schemas,
    ) -> R<Self> {
        let manifest = parse_metadata(&metadata)?;
        need(
            metadata.len() <= RECORD_LIMIT && metadata.len() % 8 == 0,
            "metadata length",
        )?;
        need(
            stream_id.iter().any(|x| *x != 0),
            "stream ID must not be all zero",
        )?;
        need(
            (48..=LIMIT).contains(&frame_bytes) && frame_records != Some(0),
            "frame size",
        )?;
        let mut h = vec![0; 64];
        h[..8].copy_from_slice(b"NWTBIN\r\n");
        put(&mut h, 8, 2, 1);
        put(&mut h, 10, 2, manifest.minor(ss));
        put(&mut h, 12, 2, 64);
        put(&mut h, 16, 4, metadata.len() as u64);
        put(&mut h, 20, 4, crc(&metadata) as u64);
        h[24..40].copy_from_slice(&stream_id);
        put(&mut h, 40, 8, created_ns);
        let mut head = hcrc(h, 56);
        head.extend_from_slice(&metadata);
        let mut w = Writer {
            out,
            position: 0,
            frame_bytes,
            frame_records,
            zstd,
            scope: Scope::new(&manifest),
            payload: Vec::new(),
            count: 0,
            time: None,
            entries: Vec::new(),
            seq: 0,
            frames: 0,
            records: 0,
        };
        w.emit(&head)?;
        Ok(w)
    }
    fn emit(&mut self, data: &[u8]) -> R<()> {
        self.out.write_all(data)?;
        self.position += data.len() as u64;
        Ok(())
    }
    fn write(&mut self, r: &Record, ss: &Schemas) -> R<()> {
        let b = encode_record(r, ss)?;
        self.write_raw(&b)
    }
    fn write_raw(&mut self, b: &[u8]) -> R<()> {
        need(
            b.len() >= 48 && b.len() <= RECORD_LIMIT && b.len() % 8 == 0 && le32(b, 0) as usize == b.len(),
            "record size",
        )?;
        self.scope.check(b)?;
        let room = if self.frame_records.is_none() {
            self.frame_bytes
        } else {
            LIMIT
        };
        if self.count > 0
            && (Some(self.count) == self.frame_records || self.payload.len() + b.len() > room)
        {
            self.flush()?;
        }
        self.payload.extend_from_slice(b);
        self.count += 1;
        let t = le64(b, 24);
        if t != NULL {
            self.time = Some(match self.time {
                None => (t, t),
                Some((lo, hi)) => (lo.min(t), hi.max(t)),
            });
        }
        Ok(())
    }
    /// Zstd form of one DATA payload; None (store raw) when Zstd is off or does not make it smaller.
    fn store(&self, payload: &[u8]) -> R<Option<Vec<u8>>> {
        match self.zstd {
            None => Ok(None),
            Some(level) => {
                let packed = zstd_pack(payload, level)?;
                if packed.len() >= payload.len() {
                    return Ok(None);
                }
                zstd_check(&packed, payload.len())?;
                Ok(Some(packed))
            }
        }
    }
    fn flush(&mut self) -> R<()> {
        if self.count == 0 {
            return Ok(());
        }
        let payload = std::mem::take(&mut self.payload);
        let (lo, hi) = self.time.take().unwrap_or((NULL, NULL));
        let count = self.count as u64;
        self.count = 0;
        let packed = self.store(&payload)?;
        let (codec, stored): (u8, &[u8]) = match &packed {
            Some(p) => (1, p.as_slice()),
            None => (0, payload.as_slice()),
        };
        self.entries.extend_from_slice(&entry(
            self.seq,
            self.position,
            lo,
            hi,
            payload.len() as u64,
            count,
        ));
        let bytes = frame(1, self.seq, &payload, count, lo, hi, codec, stored);
        self.emit(&bytes)?;
        self.seq += 1;
        self.frames += 1;
        self.records += count;
        Ok(())
    }
    /// Writes the last DATA frame, the INDEX and the END frame, and returns the output.
    fn close(mut self, status: u64) -> R<W> {
        self.flush()?;
        let first_index = if self.frames > 0 { self.position } else { 0 };
        let entries = std::mem::take(&mut self.entries);
        // An INDEX payload is bounded like any other frame.
        for chunk in entries.chunks(LIMIT / 40 * 40) {
            let f = frame(2, self.seq, chunk, 0, NULL, NULL, 0, chunk);
            self.emit(&f)?;
            self.seq += 1;
        }
        let mut end = vec![0; 32];
        put(&mut end, 0, 8, first_index);
        put(&mut end, 8, 8, self.frames);
        put(&mut end, 16, 8, self.records);
        put(&mut end, 24, 4, status);
        let f = frame(3, self.seq, &end, 0, NULL, NULL, 0, &end);
        self.emit(&f)?;
        Ok(self.out)
    }
}

/// One validated frame: its payload and, for a DATA frame, where each record lies in it.
struct Frame {
    payload: Vec<u8>,
    spans: Vec<(usize, usize)>,
}
/// Streaming container reader: the input is consumed one frame at a time and never held whole.
struct Reader<T: Read> {
    inp: T,
    pos: u64,
    seq: u64,
    frames: u64,
    records: u64,
    first_index: u64,
    entries: Vec<u8>,
    index: Vec<u8>,
    scope: Scope,
    end: Option<u64>, // END status, once the END frame has been read
    metadata: Vec<u8>,
    stream_id: [u8; 16],
    created_ns: u64,
}
impl<T: Read> Reader<T> {
    fn new(mut inp: T, ss: &Schemas) -> R<Self> {
        let mut h = [0u8; 64];
        need(
            fill(&mut inp, &mut h)? == 64,
            "incomplete: file ends inside the container header",
        )?;
        vh(&h, 56)?;
        need(
            &h[..8] == b"NWTBIN\r\n" && get(&h, 8, 2)? == 1 && get(&h, 12, 2)? == 64,
            "container fields",
        )?;
        let minor = get(&h, 10, 2)?;
        need(minor <= 1, "unsupported container minor")?;
        need(
            get(&h, 14, 2)? == 0
                && get(&h, 48, 8)? == 0
                && get(&h, 60, 4)? == 0
                && h[24..40].iter().any(|x| *x != 0),
            "container reserved/ID",
        )?;
        let ml = get(&h, 16, 4)? as usize;
        need(
            (8..=RECORD_LIMIT).contains(&ml) && ml % 8 == 0,
            "metadata length",
        )?;
        let mut metadata = vec![0u8; ml];
        need(
            fill(&mut inp, &mut metadata)? == ml,
            "incomplete: file ends inside the metadata",
        )?;
        need(crc(&metadata) as u64 == get(&h, 20, 4)?, "metadata CRC")?;
        let manifest = parse_metadata(&metadata)?;
        need(
            minor == manifest.minor(ss),
            "container minor does not match the declared types",
        )?;
        let mut stream_id = [0u8; 16];
        stream_id.copy_from_slice(&h[24..40]);
        Ok(Reader {
            inp,
            pos: 64 + ml as u64,
            seq: 0,
            frames: 0,
            records: 0,
            first_index: 0,
            entries: Vec::new(),
            index: Vec::new(),
            scope: Scope::new(&manifest),
            end: None,
            metadata,
            stream_id,
            created_ns: get(&h, 40, 8)?,
        })
    }
    fn take(&mut self, n: usize, what: &str) -> R<Vec<u8>> {
        let mut v = vec![0u8; n];
        if fill(&mut self.inp, &mut v)? != n {
            return Err(format!("incomplete: file ends inside {what}").into());
        }
        Ok(v)
    }
    /// The next frame after full validation, or None after END. A file that stops early is `incomplete`.
    fn next(&mut self) -> R<Option<Frame>> {
        let mut h = [0u8; 64];
        let got = fill(&mut self.inp, &mut h)?;
        if got == 0 {
            need(self.end.is_some(), "incomplete: missing END")?;
            return Ok(None);
        }
        need(self.end.is_none(), "trailing bytes")?;
        need(got == 64, "incomplete: file ends inside a frame header")?;
        vh(&h, 52)?;
        need(
            &h[..4] == b"NWF1"
                && h[4] == 1
                && h[6] <= 1
                && h[7] == 0
                && get(&h, 8, 2)? == 64
                && get(&h, 10, 2)? == 0
                && get(&h, 56, 8)? == 0,
            "frame fields/codec",
        )?;
        let kind = h[5];
        let codec = h[6];
        let stored = get(&h, 12, 4)? as usize;
        let raw = get(&h, 16, 4)? as usize;
        let count = get(&h, 20, 4)?;
        let lo = get(&h, 32, 8)?;
        let hi = get(&h, 40, 8)?;
        let seq = self.seq;
        need(
            (1..=3).contains(&kind) && get(&h, 24, 8)? == seq,
            "frame sequence/kind",
        )?;
        need(stored <= LIMIT && raw <= LIMIT, "frame size")?;
        // Raw frames store the payload as is; only DATA frames may be compressed.
        need(
            if codec == 0 { stored == raw } else { kind == 1 },
            "frame size/codec",
        )?;
        let padded = (stored + 7) & !7;
        let mut data = self.take(padded, "a frame payload")?;
        need(data[stored..].iter().all(|x| *x == 0), "frame padding")?;
        data.truncate(stored);
        if codec == 1 {
            data = zstd_decompress(&data, raw)?;
        }
        need(crc(&data) as u64 == get(&h, 48, 4)?, "payload CRC")?;
        let at = self.pos;
        self.pos += 64 + padded as u64;
        self.seq += 1;
        let mut spans = Vec::new();
        if kind == 1 {
            need(self.first_index == 0, "DATA order/count")?;
            spans = split_records(&data, count)?;
            for &(a, b) in &spans {
                self.scope.check(&data[a..b])?;
            }
            need(bounds(&data, &spans) == (lo, hi), "time bounds")?;
            self.entries
                .extend_from_slice(&entry(seq, at, lo, hi, raw as u64, count));
            self.frames += 1;
            self.records += spans.len() as u64;
        } else {
            need(count == 0 && lo == NULL && hi == NULL, "non-DATA fields")?;
            if kind == 2 {
                need(raw > 0 && raw % 40 == 0, "index size")?;
                if self.first_index == 0 {
                    self.first_index = at;
                }
                self.index.extend_from_slice(&data);
            } else {
                need(raw == 32, "END size")?;
                let status = get(&data, 24, 4)?;
                need(
                    get(&data, 0, 8)? == self.first_index
                        && get(&data, 8, 8)? == self.frames
                        && get(&data, 16, 8)? == self.records
                        && get(&data, 28, 4)? == 0
                        && status <= 1,
                    "END totals/status",
                )?;
                need(
                    self.first_index == 0 || self.index == self.entries,
                    "index mismatch",
                )?;
                self.end = Some(status);
            }
        }
        Ok(Some(Frame {
            payload: data,
            spans,
        }))
    }
}
/// Decodes the records of a normally completed container, frame by frame: every record of a frame is
/// decoded before `each` sees the first one. An aborted END is an error after the last record.
fn complete_records<T: Read>(
    reader: &mut Reader<T>,
    ss: &Schemas,
    mut each: impl FnMut(&Record) -> R<()>,
) -> R<()> {
    while let Some(fr) = reader.next()? {
        let mut records = Vec::with_capacity(fr.spans.len());
        for &(a, b) in &fr.spans {
            records.push(decode_record(&fr.payload[a..b], ss)?);
        }
        for r in &records {
            each(r)?;
        }
    }
    need(reader.end == Some(0), "aborted container")
}
/// A whole container in memory: used by `write` and `write-v11`, which have a small fixed catalog.
fn build(
    records: &[Record],
    manifest: &str,
    stream_id: [u8; 16],
    created_ns: u64,
    zstd: Option<i32>,
    ss: &Schemas,
) -> R<Vec<u8>> {
    let metadata = tlv(1, 1, manifest.trim().as_bytes());
    let mut w = Writer::new(Vec::new(), metadata, stream_id, created_ns, 1 << 20, Some(3), zstd, ss)?;
    for r in records {
        w.write(r, ss)?;
    }
    w.close(0)
}

// ------------------------------------------------------------------- bench

enum Decoded {
    Typed(u16, Vec<u64>),
    General(Record),
}
fn rate_line(label: &str, records: u64, size: u64, ns: u128) -> String {
    let ns = ns.max(1);
    let mb = size as u128 * 1_000_000_000_000 / (ns * 1_048_576); // thousandths of a MiB per second
    format!(
        "{} records={} seconds={}.{:06} records_per_second={} mb_per_second={}.{:03}\n",
        label,
        records,
        ns / 1_000_000_000,
        ns % 1_000_000_000 / 1000,
        records as u128 * 1_000_000_000 / ns,
        mb / 1000,
        mb % 1000
    )
}
/// Time a full decode (frames, CRC, decompression, typed records) and a re-encode of every record.
fn bench(path: &str, ss: &Schemas) -> R<String> {
    let data = fs::read(path)?;
    let layouts = build_layouts(ss);
    let start = Instant::now();
    let mut reader = Reader::new(Cursor::new(&data[..]), ss)?;
    let mut values: Vec<Decoded> = Vec::new();
    let mut size = 0u64;
    while let Some(fr) = reader.next()? {
        for &(a, b) in &fr.spans {
            let raw = &fr.payload[a..b];
            size += raw.len() as u64;
            let typ = le16(raw, 4);
            values.push(match layouts.get(&typ) {
                Some(l) if l.size == raw.len() => Decoded::Typed(typ, l.decode(raw)?),
                _ => Decoded::General(decode_record(raw, ss)?),
            });
        }
    }
    let decoded = start.elapsed().as_nanos();
    let again = Instant::now();
    for v in &values {
        let bytes = match v {
            Decoded::Typed(typ, vals) => match layouts.get(typ) {
                Some(l) => l.encode(vals),
                None => return Err("missing layout".into()),
            },
            Decoded::General(r) => encode_record(r, ss)?,
        };
        std::hint::black_box(&bytes);
    }
    let encoded = again.elapsed().as_nanos();
    let count = values.len() as u64;
    Ok(rate_line("decode", count, size, decoded) + &rate_line("encode", count, size, encoded))
}

// ------------------------------------------------------------ command line

fn run() -> R<()> {
    need(crc(b"123456789") == 0xe3069283, "CRC check")?;
    let ss: Schemas = serde_json::from_str(SCHEMA)?;
    let argv: Vec<String> = std::env::args().skip(1).collect();
    let pretty = argv.iter().any(|a| a == "--pretty");
    let zstd = argv.iter().any(|a| a == "--zstd");
    let args: Vec<String> = argv
        .into_iter()
        .filter(|a| a.as_str() != "--pretty" && a.as_str() != "--zstd")
        .collect();
    need(args.len() >= 2, USAGE)?;
    match args[0].as_str() {
        "write" => {
            let records: Vec<Record> = serde_json::from_str(CATALOG)?;
            let bytes = build(&records, MANIFEST, LEGACY_ID, 1_700_000_000_000_000_000, None, &ss)?;
            fs::write(&args[1], bytes)?;
        }
        "write-v11" => {
            let all: Vec<Record> = serde_json::from_str(CATALOG_V11)?;
            let records: Vec<Record> = all.into_iter().filter(|r| !r.standalone).collect();
            let level = if zstd { Some(3) } else { None };
            let bytes = build(&records, MANIFEST_V11, V11_ID, 1_760_000_000_000_000_000, level, &ss)?;
            fs::write(&args[1], bytes)?;
        }
        "record" => {
            need(args.len() == 3, USAGE)?;
            let typ: u16 = args[1].parse()?;
            let records: Vec<Record> =
                serde_json::from_str(if typ <= 9 { CATALOG } else { CATALOG_V11 })?;
            let r = records
                .iter()
                .find(|r| r.r#type == typ)
                .ok_or("no example for this record type")?;
            fs::write(&args[2], encode_record(r, &ss)?)?;
        }
        "decode-record" => {
            need(fs::metadata(&args[1])?.len() <= RECORD_LIMIT as u64, "record limit")?;
            let r = decode_record(&fs::read(&args[1])?, &ss)?;
            let so = std::io::stdout();
            let mut out = BufWriter::new(so.lock());
            write_report(&mut out, 1, &r, &ss)?;
            out.flush()?;
        }
        "read" => {
            let again = args.get(2);
            if let Some(a) = again {
                // The output is created while the input is still being read.
                if let (Ok(x), Ok(y)) = (fs::canonicalize(&args[1]), fs::canonicalize(a)) {
                    need(x != y, "REENCODED_FILE must differ from FILE")?;
                }
            }
            let mut reader = Reader::new(BufReader::new(File::open(&args[1])?), &ss)?;
            // The re-encode keeps the input's identity and metadata bytes; only the framing is rewritten.
            let mut writer = match again {
                Some(a) => Some(Writer::new(
                    BufWriter::new(File::create(a)?),
                    reader.metadata.clone(),
                    reader.stream_id,
                    reader.created_ns,
                    1 << 20,
                    Some(3),
                    None,
                    &ss,
                )?),
                None => None,
            };
            let so = std::io::stdout();
            let mut out = BufWriter::new(so.lock());
            let mut i = 0usize;
            complete_records(&mut reader, &ss, |r| {
                i += 1;
                write_report(&mut out, i, r, &ss)?;
                if let Some(w) = writer.as_mut() {
                    w.write(r, &ss)?;
                }
                Ok(())
            })?;
            out.flush()?;
            if let Some(w) = writer {
                w.close(0)?.flush()?;
            }
        }
        "to-json" => {
            let mut reader = Reader::new(BufReader::new(File::open(&args[1])?), &ss)?;
            let so = std::io::stdout();
            let mut out = BufWriter::new(so.lock());
            complete_records(&mut reader, &ss, |r| {
                out.write_all(to_json_line(r, &ss, pretty)?.as_bytes())?;
                out.write_all(b"\n")?;
                Ok(())
            })?;
            out.flush()?;
        }
        "to-csv" => {
            need(args.len() == 3, USAGE)?;
            let typ: u16 = args[2].parse()?;
            let s = schema(&ss, typ).map_err(|_| "unknown record type")?;
            let header = csv_header(s, &ss)?;
            let mut reader = Reader::new(BufReader::new(File::open(&args[1])?), &ss)?;
            let so = std::io::stdout();
            let mut out = BufWriter::new(so.lock());
            out.write_all(header.as_bytes())?;
            out.write_all(b"\n")?;
            complete_records(&mut reader, &ss, |r| {
                if r.r#type == typ {
                    out.write_all(to_csv_line(r, &ss, pretty)?.as_bytes())?;
                    out.write_all(b"\n")?;
                }
                Ok(())
            })?;
            out.flush()?;
        }
        "bench" => {
            print!("{}", bench(&args[1], &ss)?);
        }
        _ => return Err("unknown command".into()),
    };
    Ok(())
}
fn main() {
    if let Err(e) = run() {
        eprintln!("NWT error: {e}");
        std::process::exit(1);
    }
}
