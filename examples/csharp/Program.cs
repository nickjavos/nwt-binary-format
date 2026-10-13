// NWT .NET 10 codec for all 22 record types. Integers are exact; the general path has no native-structure
// marshaling. Raw and Zstd frames, streaming reader and writer, typed fast path (span casts) for benchmarks.
// Validation and output are driven by schemas/records.json; see fixtures/v1.1/FORMAT-NOTES.md.
using System.Buffers.Binary;
using System.Diagnostics;
using System.Globalization;
using System.Numerics;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.Json;
using V = System.Collections.Generic.Dictionary<string, string>;

sealed class Field
{
    public string name { get; set; } = "";
    public int bytes { get; set; }
    public bool signed { get; set; }
    public string? kind { get; set; }
}
sealed class Schema
{
    public int type { get; set; }
    public string name { get; set; } = "";
    public int fixed_bytes { get; set; }
    public bool has_levels { get; set; }
    public List<Field> fields { get; set; } = [];
    public List<string> texts { get; set; } = [];
    public Dictionary<string, List<ulong>> enums { get; set; } = new();
    public Dictionary<string, ulong> masks { get; set; } = new();
    public Dictionary<string, List<ulong>> text_limits { get; set; } = new();
    public Dictionary<string, List<ulong>> text_exact { get; set; } = new();
}
sealed class Schemas
{
    public List<Field> header { get; set; } = [];
    public List<Field> level { get; set; } = [];
    public List<Schema> schemas { get; set; } = [];
}
sealed class Record
{
    public int type { get; set; }
    public bool standalone { get; set; }
    public V fields { get; set; } = [];
    public V texts { get; set; } = [];
    public List<V> levels { get; set; } = [];
}

// ---- Typed fast path: packed structs read with MemoryMarshal.Cast. Sizes are checked against the schema at run time.
[StructLayout(LayoutKind.Sequential, Pack = 1)] struct Hdr { public uint Bytes; public ushort Type; public byte Version, Flags; public uint Publisher, Channel; public ulong Instrument, TsEvent, TsRecv, Sequence; }
[StructLayout(LayoutKind.Sequential, Pack = 1)] struct P1 { public byte A; }
[StructLayout(LayoutKind.Sequential, Pack = 1)] struct P2 { public ushort A; }
[StructLayout(LayoutKind.Sequential, Pack = 1)] struct P4 { public uint A; }
[StructLayout(LayoutKind.Sequential, Pack = 1)] struct P6 { public uint A; public ushort B; }
[StructLayout(LayoutKind.Sequential, Pack = 1)] struct P8 { public ulong A; }
[StructLayout(LayoutKind.Sequential, Pack = 1)] struct S01 { public Hdr H; public long Price; public ulong Quantity, TradeId, OriginalSequence; public byte Action, Aggressor; public ushort Conditions; public P4 R; }
[StructLayout(LayoutKind.Sequential, Pack = 1)] struct S02 { public Hdr H; public long BidPrice, AskPrice; public ulong BidQty, AskQty; public uint BidOrders, AskOrders, QuoteFlags; public P4 R; }
[StructLayout(LayoutKind.Sequential, Pack = 1)] struct S03 { public Hdr H; public ulong Start, End; public long Open, High, Low, Close; public ulong Volume; public uint TradeCount, BarFlags; }
[StructLayout(LayoutKind.Sequential, Pack = 1)] struct S04 { public Hdr H; public ulong OrderId; public long Price; public ulong Quantity, Priority; public byte Action, Side; public ushort MboFlags; public P4 R; }
[StructLayout(LayoutKind.Sequential, Pack = 1)] struct S07 { public Hdr H; public ushort Status, Reason; public uint StatusFlags; public P8 R; }
[StructLayout(LayoutKind.Sequential, Pack = 1)] struct S08 { public Hdr H; public ulong FirstMissing, LastMissing; public uint Reason; public P4 R; public ulong RecoveryId; }
[StructLayout(LayoutKind.Sequential, Pack = 1)] struct S13 { public Hdr H; public ulong TsRef; public long Price; public ulong Quantity; public ushort StatType; public byte Action, StatFlags; public P4 R; }
[StructLayout(LayoutKind.Sequential, Pack = 1)] struct S14 { public Hdr H; public long Iv, Delta, Gamma, Theta, Vega, Rho, UnderlyingPrice, TheoPrice; public byte Basis, Model; public P6 R; }
[StructLayout(LayoutKind.Sequential, Pack = 1)] struct S15 { public Hdr H; public long Price; public ulong Quantity; public uint OrderCount; public byte Action, Side, DeltaFlags; public P1 R; }
[StructLayout(LayoutKind.Sequential, Pack = 1)] struct S16 { public Hdr H; public ulong AuctionNs; public long RefPrice, NearPrice, FarPrice; public ulong Paired, Imbalance; public byte Side, AuctionType; public P6 R; }
[StructLayout(LayoutKind.Sequential, Pack = 1)] struct S18 { public Hdr H; public long Price; public ulong Quantity, TradeId; public long BidPrice, AskPrice; public ulong BidQty, AskQty; public uint BidOrders, AskOrders; public byte Aggressor; public P1 R1; public ushort Conditions; public P4 R2; }
[StructLayout(LayoutKind.Sequential, Pack = 1)] struct S19 { public Hdr H; public long BidPrice, AskPrice; public ulong BidQty, AskQty; public uint BidOrders, AskOrders, QuoteFlags, BidPub, AskPub; public P4 R; public ulong IntervalNs; }
[StructLayout(LayoutKind.Sequential, Pack = 1)] struct S20 { public Hdr H; public ulong FrameSeq, FrameOffset; public uint StoredBytes; public byte Codec, Flags; public P2 R1; public ulong TypeMask, MinInstrument, MaxInstrument; public P8 R2; }

interface ITyped
{
    int Size { get; }
    void Decode(byte[] raw);
    void EncodeAll(byte[] scratch);
}
sealed class Typed<T> : ITyped where T : unmanaged
{
    readonly List<T> items = [];
    public int Size => Unsafe.SizeOf<T>();
    public void Decode(byte[] raw) => items.Add(MemoryMarshal.Cast<byte, T>(raw.AsSpan())[0]);
    public void EncodeAll(byte[] scratch)
    {
        foreach (var x in items)
            Unsafe.WriteUnaligned(ref scratch[0], x);
    }
}

// ---- Zstd: P/Invoke into the system libzstd, bound by Program.ZstdLoad through SetDllImportResolver.
static class Zs
{
    [DllImport("zstd")] public static extern nuint ZSTD_compressBound(nuint n);
    [DllImport("zstd")] public static extern nuint ZSTD_compress(ref byte dst, nuint cap, ref byte src, nuint n, int level);
    [DllImport("zstd")] public static extern nuint ZSTD_decompress(ref byte dst, nuint cap, ref byte src, nuint n);
    [DllImport("zstd")] public static extern nuint ZSTD_findFrameCompressedSize(ref byte src, nuint n);
    [DllImport("zstd")] public static extern uint ZSTD_isError(nuint code);
}

static class Program
{
    const ulong NIL = ulong.MaxValue;
    const int LIMIT = 16777216; // largest frame payload and largest Zstd window
    const string Usage = "usage: NwtExample write FILE | write-v11 FILE [--zstd] | read FILE [REENCODED_FILE] | record TYPE FILE | decode-record FILE | to-json FILE [--pretty] | to-csv FILE TYPE [--pretty] | bench FILE";
    static readonly UTF8Encoding Utf8 = new(false, true);
    static readonly uint[] Tab = MakeTab();
    static string Resource(string name)
    {
        using var s = Assembly.GetExecutingAssembly().GetManifestResourceStream(name) ?? throw new Exception("missing resource");
        using var r = new StreamReader(s, Utf8);
        return r.ReadToEnd();
    }
    static readonly Schemas SS = JsonSerializer.Deserialize<Schemas>(Resource("schemas"))!;
    static readonly Dictionary<int, Schema> ByType = SS.schemas.ToDictionary(x => x.type);
    static readonly int MaxType = SS.schemas.Max(x => x.type);
    static readonly byte[] LegacyId = Convert.FromHexString("102132435465768798a9bacbdcedfe0f");
    static readonly byte[] V11Id = Convert.FromHexString("a1b2c3d4e5f60718293a4b5c6d7e8f90");
    static readonly char[] CsvSpecial = [',', '"', '\r', '\n'];
    static readonly StreamWriter Out = new(Console.OpenStandardOutput(), new UTF8Encoding(false), 1 << 16);
    static readonly StringBuilder Sb = new();
    static readonly bool FastCrc = CheckFastCrc(); // keep after Tab: it uses both CRC routines

    static void Need(bool ok, string why)
    {
        if (!ok)
            throw new InvalidDataException(why);
    }
    static ulong Num(V v, string k) => ulong.Parse(v[k], NumberStyles.None, CultureInfo.InvariantCulture);
    static string Dec(ulong n) => n.ToString(CultureInfo.InvariantCulture);
    static Schema GetSchema(int t) => ByType.TryGetValue(t, out var s) ? s : throw new InvalidDataException("unknown schema");
    static List<Record> Catalog(string resource) => JsonSerializer.Deserialize<List<Record>>(Resource(resource))!;

    // ------------------------------------------------------------ bytes and CRC

    static uint[] MakeTab()
    {
        var t = new uint[256];
        for (uint n = 0; n < 256; n++)
        {
            uint c = n;
            for (int i = 0; i < 8; i++)
                c = (c >> 1) ^ ((c & 1) != 0 ? 0x82f63b78u : 0u);
            t[n] = c;
        }
        return t;
    }
    static uint CrcTab(ReadOnlySpan<byte> b)
    {
        uint c = 0xffffffff;
        foreach (byte x in b)
            c = Tab[(c ^ x) & 255] ^ (c >> 8);
        return c ^ 0xffffffff;
    }
    static uint CrcHw(ReadOnlySpan<byte> b)
    {
        uint c = 0xffffffff;
        int i = 0;
        for (; i + 8 <= b.Length; i += 8)
            c = BitOperations.Crc32C(c, BinaryPrimitives.ReadUInt64LittleEndian(b[i..]));
        for (; i < b.Length; i++)
            c = BitOperations.Crc32C(c, b[i]);
        return c ^ 0xffffffff;
    }
    static bool CheckFastCrc()
    {
        byte[] t = new byte[1003];
        for (int i = 0; i < t.Length; i++)
            t[i] = (byte)(i * 31 + 7);
        return CrcHw("123456789"u8) == 0xe3069283 && CrcHw(t) == CrcTab(t);
    }
    static uint Crc(ReadOnlySpan<byte> b) => FastCrc ? CrcHw(b) : CrcTab(b);
    static byte[] Pad(byte[] b)
    {
        Array.Resize(ref b, (b.Length + 7) & ~7);
        return b;
    }
    static ulong Get(ReadOnlySpan<byte> b, int o, int n)
    {
        Need(n <= 8 && o >= 0 && o <= b.Length && n <= b.Length - o, "integer bounds");
        var s = b.Slice(o, n);
        return n switch
        {
            8 => BinaryPrimitives.ReadUInt64LittleEndian(s),
            4 => BinaryPrimitives.ReadUInt32LittleEndian(s),
            2 => BinaryPrimitives.ReadUInt16LittleEndian(s),
            _ => Small(s)
        };
    }
    static ulong Small(ReadOnlySpan<byte> s)
    {
        ulong x = 0;
        for (int i = 0; i < s.Length; i++)
            x |= (ulong)s[i] << (8 * i);
        return x;
    }
    static void Put(byte[] b, int o, int n, ulong v)
    {
        Need(o >= 0 && o <= b.Length && n <= b.Length - o, "write bounds");
        for (int i = 0; i < n; i++)
            b[o + i] = (byte)(v >> (8 * i));
    }
    static byte[] HCrc(byte[] b, int o)
    {
        Put(b, o, 4, 0);
        Put(b, o, 4, Crc(b));
        return b;
    }
    static void VH(ReadOnlySpan<byte> b, int o)
    {
        Need(b.Length == 64, "header size");
        ulong c = Get(b, o, 4);
        byte[] t = b.ToArray();
        Put(t, o, 4, 0);
        Need(Crc(t) == c, "header CRC");
    }
    static bool Zero(ReadOnlySpan<byte> b)
    {
        foreach (var x in b)
            if (x != 0)
                return false;
        return true;
    }

    // ------------------------------------------------------------------ records

    static byte[] TextBytes(string s)
    {
        Need(!s.Contains('\0'), "NUL text");
        return Utf8.GetBytes(s);
    }
    static void EncFields(List<byte> output, V v, List<Field> fs)
    {
        foreach (var f in fs)
        {
            ulong n;
            if (f.signed)
            {
                long s = long.Parse(v[f.name], NumberStyles.AllowLeadingSign, CultureInfo.InvariantCulture);
                if (f.bytes < 8)
                    Need(s >= -(1L << (8 * f.bytes - 1)) && s < (1L << (8 * f.bytes - 1)), "integer range");
                n = unchecked((ulong)s);
            }
            else
            {
                n = Num(v, f.name);
                Need(f.bytes == 8 || n < (1UL << (8 * f.bytes)), "integer range");
            }
            if (f.name == "reserved")
                Need(n == 0, "reserved must be zero");
            for (int i = 0; i < f.bytes; i++)
                output.Add((byte)(n >> (8 * i)));
        }
    }
    static long Signed(ulong n, int bytes)
    {
        int sh = 64 - 8 * bytes;
        return unchecked((long)(n << sh)) >> sh;
    }
    static V DecFields(ReadOnlySpan<byte> b, ref int p, List<Field> fs)
    {
        V v = new();
        foreach (var f in fs)
        {
            ulong n = Get(b, p, f.bytes);
            p += f.bytes;
            if (f.name == "reserved")
                Need(n == 0, "nonzero reserved");
            v[f.name] = f.signed ? Signed(n, f.bytes).ToString(CultureInfo.InvariantCulture) : Dec(n);
        }
        return v;
    }
    // Data-driven rules shared by encode and decode: enums, flag masks and text byte lengths.
    static void CheckSchema(Schema s, V f)
    {
        foreach (var (name, allowed) in s.enums)
            Need(allowed.Contains(Num(f, name)), "invalid " + name);
        foreach (var (name, mask) in s.masks)
            Need((Num(f, name) & ~mask) == 0, "invalid " + name + " bits");
        foreach (var (name, lim) in s.text_limits)
        {
            ulong n = Num(f, name + "_bytes");
            Need(n >= lim[0] && n <= lim[1], name + " text limit");
        }
        foreach (var (name, sizes) in s.text_exact)
            Need(sizes.Contains(Num(f, name + "_bytes")), name + " text length");
    }
    static byte[] EncodeRecord(Record r)
    {
        V f = new(r.fields);
        int t = checked((int)Num(f, "record_type"));
        Need(r.type == t, "record type mismatch");
        var s = GetSchema(t);
        Need(Num(f, "schema_version") == 1 && (Num(f, "flags") & ~3UL) == 0, "version/flags");
        if (s.has_levels)
        {
            Need(r.levels.Count <= 1024, "levels limit");
            f["levels"] = Dec((ulong)r.levels.Count);
        }
        // The length of each text is checked against its limit before any length field is written.
        var texts = s.texts.Select(name => TextBytes(r.texts[name])).ToList();
        for (int i = 0; i < texts.Count; i++)
            f[s.texts[i] + "_bytes"] = Dec((ulong)texts[i].Length);
        CheckSchema(s, f);
        List<byte> body = [];
        EncFields(body, f, s.fields);
        if (s.has_levels)
            foreach (var l in r.levels)
                EncFields(body, l, SS.level);
        foreach (var b in texts)
            body.AddRange(b);
        while (body.Count % 8 != 0)
            body.Add(0);
        Need(48 + body.Count <= 1048576, "record limit");
        f["record_bytes"] = Dec((ulong)(48 + body.Count));
        List<byte> output = [];
        EncFields(output, f, SS.header);
        output.AddRange(body);
        return output.ToArray();
    }
    static Record DecodeRecord(ReadOnlySpan<byte> b)
    {
        Need(b.Length >= 48 && b.Length <= 1048576 && b.Length % 8 == 0, "record size");
        int p = 0;
        V f = DecFields(b, ref p, SS.header);
        int t = checked((int)Num(f, "record_type"));
        var s = GetSchema(t);
        Need(Num(f, "record_bytes") == (ulong)b.Length && Num(f, "schema_version") == 1 && (Num(f, "flags") & ~3UL) == 0, "record fields");
        foreach (var kv in DecFields(b, ref p, s.fields))
            f[kv.Key] = kv.Value;
        List<V> levels = [];
        V texts = new();
        if (s.has_levels)
        {
            ulong n = Num(f, "levels");
            Need(n <= 1024, "levels limit");
            for (ulong i = 0; i < n; i++)
                levels.Add(DecFields(b, ref p, SS.level));
        }
        foreach (var name in s.texts)
        {
            ulong n = Num(f, name + "_bytes");
            Need(p <= b.Length && n <= (ulong)(b.Length - p), "text bounds");
            string text = Utf8.GetString(b.Slice(p, (int)n));
            TextBytes(text);
            texts[name] = text;
            p += (int)n;
        }
        // A fixed type must have its exact size; a variable type its exact padded size.
        Need(((p + 7) & ~7) == b.Length && Zero(b[p..]), "padding/record length");
        CheckSchema(s, f);
        return new() { type = t, fields = f, texts = texts, levels = levels };
    }

    // ------------------------------------------------------------- text output

    // The field report: one line per schema field (reserved included), level fields, then the texts.
    static void ReportLines(StringBuilder b, int i, Record r)
    {
        var s = GetSchema(r.type);
        foreach (var f in SS.header.Concat(s.fields))
            b.Append(i).Append('.').Append(f.name).Append('=').Append(r.fields[f.name]).Append('\n');
        for (int j = 0; j < r.levels.Count; j++)
            foreach (var f in SS.level)
                b.Append(i).Append(".levels.").Append(j).Append('.').Append(f.name).Append('=').Append(r.levels[j][f.name]).Append('\n');
        foreach (var name in s.texts)
            b.Append(i).Append('.').Append(name).Append('=').Append(r.texts[name]).Append('\n');
    }
    static void EmitReport(int i, Record r)
    {
        Sb.Clear();
        ReportLines(Sb, i, r);
        Out.Write(Sb);
    }
    static string Scaled(bool negative, ulong abs) =>
        (negative ? "-" : "") + (abs / 1000000000UL).ToString(CultureInfo.InvariantCulture) + "." + (abs % 1000000000UL).ToString("D9", CultureInfo.InvariantCulture);
    // POSIX nanoseconds as YYYY-MM-DDTHH:MM:SS.nnnnnnnnnZ, integer arithmetic only.
    static string PrettyTime(ulong ns)
    {
        long sec = (long)(ns / 1000000000UL), fr = (long)(ns % 1000000000UL);
        long days = sec / 86400, rest = sec % 86400;
        long z = days + 719468, era = z / 146097, doe = z % 146097;
        long yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365;
        long doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
        long mp = (5 * doy + 2) / 153;
        long day = doy - (153 * mp + 2) / 5 + 1;
        long month = mp < 10 ? mp + 3 : mp - 9;
        long year = yoe + era * 400 + (month <= 2 ? 1 : 0);
        return FormattableString.Invariant($"{year:D4}-{month:D2}-{day:D2}T{rest / 3600:D2}:{rest % 3600 / 60:D2}:{rest % 60:D2}.{fr:D9}Z");
    }
    // A field value for --pretty: null for a null price, quantity or time; fields without a kind unchanged.
    static string? PrettyValue(Field f, string text)
    {
        if (f.kind == null)
            return text;
        if (f.signed)
        {
            long v = long.Parse(text, NumberStyles.AllowLeadingSign, CultureInfo.InvariantCulture);
            if (v == long.MinValue)
                return null;
            if (f.kind == "time")
            {
                Need(v >= 0, "negative time");
                return PrettyTime((ulong)v);
            }
            return Scaled(v < 0, unchecked((ulong)(v < 0 ? -v : v)));
        }
        ulong u = ulong.Parse(text, NumberStyles.None, CultureInfo.InvariantCulture);
        if (u == NIL)
            return null;
        return f.kind == "time" ? PrettyTime(u) : Scaled(false, u);
    }
    static List<(string Name, string? Value)> OutputItems(IEnumerable<Field> fields, V values, bool pretty, bool dropLevels)
    {
        List<(string, string?)> items = [];
        foreach (var f in fields)
            if (f.name != "reserved" && !(dropLevels && f.name == "levels"))
                items.Add((f.name, pretty ? PrettyValue(f, values[f.name]) : values[f.name]));
        return items;
    }
    // (name, value) in output order: header fields, body fields, texts. No reserved, no level count.
    static List<(string Name, string? Value)> RecordItems(Record r, bool pretty)
    {
        var s = GetSchema(r.type);
        var items = OutputItems(SS.header.Concat(s.fields), r.fields, pretty, s.has_levels);
        foreach (var name in s.texts)
            items.Add((name, r.texts[name]));
        return items;
    }
    static void JsonStr(StringBuilder b, string t)
    {
        b.Append('"');
        foreach (char c in t)
        {
            if (c == '"' || c == '\\')
                b.Append('\\').Append(c);
            else if (c < ' ')
                b.Append("\\u").Append(((int)c).ToString("x4", CultureInfo.InvariantCulture));
            else
                b.Append(c);
        }
        b.Append('"');
    }
    static void JsonObject(StringBuilder b, List<(string Name, string? Value)> items)
    {
        b.Append('{');
        for (int i = 0; i < items.Count; i++)
        {
            if (i > 0)
                b.Append(',');
            JsonStr(b, items[i].Name);
            b.Append(':');
            if (items[i].Value == null)
                b.Append("null");
            else
                JsonStr(b, items[i].Value!);
        }
        b.Append('}');
    }
    static void EmitJson(Record r, bool pretty)
    {
        var s = GetSchema(r.type);
        var items = RecordItems(r, pretty);
        items.Insert(0, ("type_name", s.name));
        Sb.Clear();
        JsonObject(Sb, items);
        if (s.has_levels)
        {
            Sb.Length--; // reopen the object: levels is its last key
            Sb.Append(",\"levels\":[");
            for (int j = 0; j < r.levels.Count; j++)
            {
                if (j > 0)
                    Sb.Append(',');
                JsonObject(Sb, OutputItems(SS.level, r.levels[j], pretty, false));
            }
            Sb.Append("]}");
        }
        Sb.Append('\n');
        Out.Write(Sb);
    }
    static string CsvValue(string? v) =>
        v == null ? "" : v.IndexOfAny(CsvSpecial) >= 0 ? "\"" + v.Replace("\"", "\"\"") + "\"" : v;
    static string CsvHeader(int typ)
    {
        var s = GetSchema(typ);
        Need(!s.has_levels, $"type {typ} has levels; use to-json");
        return string.Join(",", SS.header.Concat(s.fields).Where(f => f.name != "reserved").Select(f => f.name).Concat(s.texts));
    }
    static void EmitCsv(Record r, bool pretty)
    {
        Need(!GetSchema(r.type).has_levels, $"type {r.type} has levels; use to-json");
        Sb.Clear();
        Sb.Append(string.Join(",", RecordItems(r, pretty).Select(x => CsvValue(x.Value)))).Append('\n');
        Out.Write(Sb);
    }

    // ---------------------------------------------------------------- metadata

    // Strict JSON: no duplicate keys at any depth, no non-integer numbers, valid UTF-8.
    static JsonDocument StrictJson(byte[] bytes)
    {
        Utf8.GetString(bytes);
        var rd = new Utf8JsonReader(bytes);
        Stack<HashSet<string>?> stack = new();
        while (rd.Read())
        {
            switch (rd.TokenType)
            {
                case JsonTokenType.StartObject:
                    stack.Push(new HashSet<string>());
                    break;
                case JsonTokenType.StartArray:
                    stack.Push(null);
                    break;
                case JsonTokenType.EndObject:
                case JsonTokenType.EndArray:
                    stack.Pop();
                    break;
                case JsonTokenType.PropertyName:
                    Need(stack.Peek()!.Add(rd.GetString()!), "duplicate JSON key");
                    break;
                case JsonTokenType.Number:
                    foreach (byte x in rd.ValueSpan)
                        Need(x != '.' && x != 'e' && x != 'E', "JSON numbers must be integers");
                    break;
            }
        }
        return JsonDocument.Parse(bytes);
    }
    static string? Str(JsonElement? e) => e is { ValueKind: JsonValueKind.String } v ? v.GetString() : null;
    static JsonElement? Prop(JsonElement e, string k) => e.ValueKind == JsonValueKind.Object && e.TryGetProperty(k, out var v) ? v : null;
    static bool IsText(JsonElement? e, int lo, int hi) => Str(e) is { } t && Utf8.GetByteCount(t) >= lo && Utf8.GetByteCount(t) <= hi;
    static bool IsInt(JsonElement? e, long lo, long hi) => e is { ValueKind: JsonValueKind.Number } v && v.TryGetInt64(out long x) && x >= lo && x <= hi;

    sealed class Manifest
    {
        public readonly HashSet<(int, int)> Declared = new();
        public readonly HashSet<ulong> Publishers = new();
        public int Minor; // 1 exactly when the manifest declares one of the 1.1 standard types (10 up to the highest in the schema)
    }
    // Parse and validate a MANIFEST value. Unknown properties are ignored.
    static Manifest ParseManifest(byte[] text)
    {
        using var doc = StrictJson(text);
        var m = doc.RootElement;
        Need(m.ValueKind == JsonValueKind.Object, "manifest must be a JSON object");
        foreach (var key in new[] { "dataset", "producer", "profile", "publishers", "schemas", "clock" })
            Need(Prop(m, key) != null, "manifest missing " + key);
        Need(IsText(Prop(m, "dataset"), 1, 255) && IsText(Prop(m, "producer"), 1, 255), "manifest dataset/producer");
        Need(Str(Prop(m, "profile")) is "market-data" or "generic-events", "manifest profile");
        Need(Str(Prop(m, "clock")) == "posix-ns", "manifest clock");
        if (Prop(m, "ordering") is { } ordering)
            Need(Str(ordering) is "none" or "ts_event" or "instrument,ts_event", "manifest ordering");
        var publishers = Prop(m, "publishers")!.Value;
        var schemas = Prop(m, "schemas")!.Value;
        Need(publishers.ValueKind == JsonValueKind.Array && publishers.GetArrayLength() <= 4096, "manifest publishers");
        var man = new Manifest();
        foreach (var p in publishers.EnumerateArray())
        {
            Need(p.ValueKind == JsonValueKind.Object, "manifest publisher");
            Need(IsInt(Prop(p, "id"), 1, uint.MaxValue), "manifest publisher id");
            Need(IsText(Prop(p, "name"), 1, 255) && IsText(Prop(p, "venue"), 0, 255), "manifest publisher name/venue");
            Need(man.Publishers.Add((ulong)Prop(p, "id")!.Value.GetInt64()), "manifest duplicate publisher");
        }
        Need(schemas.ValueKind == JsonValueKind.Array && schemas.GetArrayLength() >= 1 && schemas.GetArrayLength() <= 4096, "manifest schemas");
        foreach (var s in schemas.EnumerateArray())
        {
            Need(s.ValueKind == JsonValueKind.Object, "manifest schema");
            Need(IsInt(Prop(s, "type"), 1, 65534) && IsInt(Prop(s, "version"), 1, 255), "manifest schema type/version");
            Need(Prop(s, "required") is { ValueKind: JsonValueKind.True or JsonValueKind.False }, "manifest schema required");
            Need(IsText(Prop(s, "name"), 1, 255) && IsText(Prop(s, "spec_uri"), 1, 2048), "manifest schema name/spec_uri");
            Need(man.Declared.Add(((int)Prop(s, "type")!.Value.GetInt64(), (int)Prop(s, "version")!.Value.GetInt64())), "manifest duplicate schema");
        }
        man.Minor = man.Declared.Any(d => d.Item1 >= 10 && d.Item1 <= MaxType) ? 1 : 0;
        return man;
    }
    static byte[] Tlv(ushort typ, ushort flags, byte[] value)
    {
        byte[] b = new byte[8];
        Put(b, 0, 2, typ);
        Put(b, 2, 2, flags);
        Put(b, 4, 4, (ulong)value.Length);
        return Pad([.. b, .. value]);
    }
    // Split metadata into {type: (flags, value)}. Unknown optional elements are bounds-checked and skipped.
    static Dictionary<int, (int Flags, byte[] Value)> ParseMetadata(byte[] meta)
    {
        Dictionary<int, (int Flags, byte[] Value)> o = new();
        int p = 0;
        while (p < meta.Length)
        {
            Need(meta.Length - p >= 8, "TLV header");
            int typ = (int)Get(meta, p, 2), flags = (int)Get(meta, p + 2, 2);
            ulong n = Get(meta, p + 4, 4);
            Need(typ > 0 && typ < 65535 && (flags & ~1) == 0, "TLV type/flags");
            Need(!o.ContainsKey(typ), "duplicate TLV");
            Need(n <= (ulong)(meta.Length - p - 8), "TLV length");
            int end = p + 8 + (int)n;
            o[typ] = (flags, meta[(p + 8)..end]);
            p = (end + 7) & ~7;
            Need(p <= meta.Length && Zero(meta.AsSpan(end, p - end)), "TLV padding");
            Need(typ is 1 or 2 || flags == 0, "unknown required TLV");
        }
        Need(o.TryGetValue(1, out var mf) && mf.Flags == 1, "MANIFEST TLV must be present with its required flag");
        Need(!o.TryGetValue(2, out var pv) || pv.Flags == 0, "PROVENANCE TLV must not be marked required");
        return o;
    }
    static void ParseProvenance(Dictionary<int, (int Flags, byte[] Value)> tlvs)
    {
        if (!tlvs.TryGetValue(2, out var pv))
            return;
        using var doc = StrictJson(pv.Value);
        Need(doc.RootElement.ValueKind == JsonValueKind.Object, "PROVENANCE must be a JSON object");
    }

    // -------------------------------------------------------------------- Zstd

    static IntPtr zh;
    static int zstate; // 0 not tried, 1 loaded, 2 not available
    // NWT_ZSTD_LIB, when set, is the only library tried.
    static void ZstdLoad()
    {
        if (zstate == 0)
        {
            zstate = 2;
            string? chosen = Environment.GetEnvironmentVariable("NWT_ZSTD_LIB");
            string[] names = string.IsNullOrEmpty(chosen)
                ? ["libzstd", "/opt/homebrew/lib/libzstd.dylib", "/usr/local/lib/libzstd.dylib", "libzstd.so.1"]
                : [chosen];
            foreach (var n in names)
                if (NativeLibrary.TryLoad(n, typeof(Program).Assembly, null, out zh))
                {
                    zstate = 1;
                    break;
                }
            if (zstate == 1)
                NativeLibrary.SetDllImportResolver(typeof(Program).Assembly, (name, _, _) => name == "zstd" ? zh : IntPtr.Zero);
        }
        Need(zstate == 1, "Zstd library not available");
    }
    // Spec 10.2 checked by hand on the Zstd frame header, before any library call (FORMAT-NOTES section 7).
    static void ZstdCheck(byte[] s, int raw)
    {
        Need(s.Length >= 6 && s[0] == 0x28 && s[1] == 0xb5 && s[2] == 0x2f && s[3] == 0xfd, "Zstd magic");
        int d = s[4], fcs = d >> 6;
        bool single = ((d >> 5) & 1) != 0;
        Need((d & 0x08) == 0, "Zstd reserved bit");
        Need((d & 0x03) == 0, "Zstd dictionary");
        int p = 5;
        ulong window = 0;
        if (!single)
        {
            int w = s[p++];
            ulong b = 1UL << (10 + (w >> 3));
            window = b + (b >> 3) * (ulong)(w & 7);
        }
        int n = fcs switch { 0 => single ? 1 : 0, 1 => 2, 2 => 4, _ => 8 };
        Need(n > 0, "Zstd content size missing");
        Need(s.Length >= p + n, "Zstd header");
        ulong size = Get(s, p, n) + (fcs == 1 ? 256UL : 0UL);
        Need(size == (ulong)raw, "Zstd content size");
        Need((single ? size : window) <= LIMIT, "Zstd window");
    }
    static byte[] ZstdCompress(byte[] b, int level)
    {
        ZstdLoad();
        nuint room = Zs.ZSTD_compressBound((nuint)b.Length);
        byte[] o = new byte[(int)room];
        nuint n = Zs.ZSTD_compress(ref MemoryMarshal.GetArrayDataReference(o), room, ref MemoryMarshal.GetArrayDataReference(b), (nuint)b.Length, level);
        Need(Zs.ZSTD_isError(n) == 0, "Zstd compression failed");
        return o[..(int)n];
    }
    static byte[] ZstdDecompress(byte[] stored, int raw)
    {
        ZstdCheck(stored, raw);
        ZstdLoad();
        // Exactly one frame: no concatenated or skippable frame and no trailing bytes.
        Need((ulong)Zs.ZSTD_findFrameCompressedSize(ref MemoryMarshal.GetArrayDataReference(stored), (nuint)stored.Length) == (ulong)stored.Length, "Zstd frame must fill stored_bytes exactly");
        byte[] o = new byte[Math.Max(raw, 1)];
        nuint n = Zs.ZSTD_decompress(ref MemoryMarshal.GetArrayDataReference(o), (nuint)raw, ref MemoryMarshal.GetArrayDataReference(stored), (nuint)stored.Length);
        Need(Zs.ZSTD_isError(n) == 0 && (ulong)n == (ulong)raw, "Zstd decompression failed");
        return o.Length == raw ? o : o[..raw];
    }

    // --------------------------------------------------------------- container

    static byte[] FrameBytes(byte kind, ulong seq, byte[] payload, ulong count = 0, ulong lo = NIL, ulong hi = NIL, byte codec = 0, byte[]? stored = null)
    {
        stored ??= payload;
        byte[] h = new byte[64];
        "NWF1"u8.CopyTo(h);
        h[4] = 1;
        h[5] = kind;
        h[6] = codec;
        Put(h, 8, 2, 64);
        Put(h, 12, 4, (ulong)stored.Length);
        Put(h, 16, 4, (ulong)payload.Length);
        Put(h, 20, 4, count);
        Put(h, 24, 8, seq);
        Put(h, 32, 8, lo);
        Put(h, 40, 8, hi);
        Put(h, 48, 4, Crc(payload));
        return [.. HCrc(h, 52), .. Pad(stored)];
    }
    static byte[] Entry(ulong seq, ulong offset, ulong lo, ulong hi, ulong raw, ulong count)
    {
        byte[] b = new byte[40];
        Put(b, 0, 8, seq);
        Put(b, 8, 8, offset);
        Put(b, 16, 8, lo);
        Put(b, 24, 8, hi);
        Put(b, 32, 4, raw);
        Put(b, 36, 4, count);
        return b;
    }
    // (min, max) of the non-null ts_event values of raw records; (NIL, NIL) when there are none.
    static (ulong, ulong) Bounds(List<byte[]> raws)
    {
        ulong lo = NIL, hi = NIL;
        bool any = false;
        foreach (var raw in raws)
        {
            ulong t = Get(raw, 24, 8);
            if (t == NIL)
                continue;
            lo = any ? Math.Min(lo, t) : t;
            hi = any ? Math.Max(hi, t) : t;
            any = true;
        }
        return (lo, hi);
    }
    static List<byte[]> SplitRecords(byte[] payload, ulong count)
    {
        Need(count > 0 && payload.Length % 8 == 0, "DATA order/count");
        List<byte[]> raws = [];
        int p = 0;
        while (p < payload.Length)
        {
            ulong n = Get(payload, p, 4);
            Need(n >= 48 && n <= 1048576 && n % 8 == 0 && n <= (ulong)(payload.Length - p), "record bounds");
            raws.Add(payload[p..(p + (int)n)]);
            p += (int)n;
        }
        Need((ulong)raws.Count == count, "record count");
        return raws;
    }

    // Checks that need only a record's 48-byte header: declared type, declared publisher, sequence.
    sealed class Scope
    {
        readonly Manifest man;
        readonly Dictionary<(ulong, ulong), ulong> last = new();
        public Scope(Manifest m) => man = m;
        public void Check(byte[] raw)
        {
            Need(man.Declared.Contains(((int)Get(raw, 4, 2), (int)Get(raw, 6, 1))), "undeclared record type");
            ulong pub = Get(raw, 8, 4), ch = Get(raw, 12, 4);
            Need(pub == 0 || man.Publishers.Contains(pub), "undeclared publisher");
            last.TryGetValue((pub, ch), out ulong previous);
            Need(Get(raw, 40, 8) == previous + 1, "record sequence");
            last[(pub, ch)] = previous + 1;
        }
    }

    sealed class FInfo
    {
        public ulong Seq, Count, Lo, Hi;
        public long Offset;
        public byte Kind, Codec;
        public int Stored, Raw;
        public uint PayloadCrc;
    }

    // Streaming writer: header and metadata first, DATA frames as they fill, INDEX and END on Close.
    sealed class Writer
    {
        readonly Stream o;
        readonly int frameBytes;
        readonly int? frameRecords, level;
        readonly Scope scope;
        readonly List<(ulong Seq, long Offset, ulong Lo, ulong Hi, int Raw, int Count)> frames = [];
        List<byte[]> pending = [];
        int pendingBytes;
        long position;
        ulong seq, records;

        // metadata: the TLV bytes, written as given. level: Zstd level, or null for raw frames.
        public Writer(Stream o, byte[] metadata, byte[] streamId, ulong createdNs, int? frameRecords = null, int? level = null, int frameBytes = 1 << 20)
        {
            var tlvs = ParseMetadata(metadata);
            ParseProvenance(tlvs);
            var man = ParseManifest(tlvs[1].Value);
            Need(metadata.Length <= 1048576 && metadata.Length % 8 == 0, "metadata length");
            Need(streamId.Length == 16 && !Zero(streamId), "stream ID must be 16 bytes and not all zero");
            Need(frameBytes >= 48 && frameBytes <= LIMIT && (frameRecords == null || frameRecords > 0), "frame size");
            this.o = o;
            this.frameBytes = frameBytes;
            this.frameRecords = frameRecords;
            this.level = level;
            scope = new Scope(man);
            byte[] h = new byte[64];
            "NWTBIN\r\n"u8.CopyTo(h);
            Put(h, 8, 2, 1);
            Put(h, 10, 2, (ulong)man.Minor);
            Put(h, 12, 2, 64);
            Put(h, 16, 4, (ulong)metadata.Length);
            Put(h, 20, 4, Crc(metadata));
            streamId.CopyTo(h, 24);
            Put(h, 40, 8, createdNs);
            Emit(HCrc(h, 56));
            Emit(metadata);
        }
        void Emit(byte[] data)
        {
            o.Write(data);
            position += data.Length;
        }
        public void Write(Record r) => WriteRaw(EncodeRecord(r));
        public void WriteRaw(byte[] b)
        {
            Need(b.Length >= 48 && b.Length <= 1048576 && b.Length % 8 == 0 && Get(b, 0, 4) == (ulong)b.Length, "record size");
            scope.Check(b);
            int room = frameRecords == null ? frameBytes : LIMIT;
            if (pending.Count > 0 && (pending.Count == frameRecords || pendingBytes + b.Length > room))
                Flush();
            pending.Add(b);
            pendingBytes += b.Length;
        }
        // (codec, stored bytes) for one DATA payload: raw when Zstd is off or does not make it smaller.
        (byte, byte[]) Store(byte[] payload)
        {
            if (level == null)
                return (0, payload);
            byte[] packed = ZstdCompress(payload, level.Value);
            if (packed.Length >= payload.Length)
                return (0, payload);
            ZstdCheck(packed, payload.Length);
            return (1, packed);
        }
        public void Flush()
        {
            if (pending.Count == 0)
                return;
            byte[] payload = new byte[pendingBytes];
            int p = 0;
            foreach (var b in pending)
            {
                b.CopyTo(payload, p);
                p += b.Length;
            }
            var (lo, hi) = Bounds(pending);
            var (codec, stored) = Store(payload);
            int count = pending.Count;
            frames.Add((seq, position, lo, hi, payload.Length, count));
            Emit(FrameBytes(1, seq, payload, (ulong)count, lo, hi, codec, stored));
            seq++;
            records += (ulong)count;
            pending = [];
            pendingBytes = 0;
        }
        public void Close(ulong status = 0)
        {
            Flush();
            ulong firstIndex = frames.Count > 0 ? (ulong)position : 0;
            int perFrame = LIMIT / 40; // an INDEX payload is bounded like any other frame
            for (int start = 0; start < frames.Count; start += perFrame)
            {
                List<byte> chunk = [];
                for (int k = start; k < Math.Min(frames.Count, start + perFrame); k++)
                {
                    var f = frames[k];
                    chunk.AddRange(Entry(f.Seq, (ulong)f.Offset, f.Lo, f.Hi, (ulong)f.Raw, (ulong)f.Count));
                }
                Emit(FrameBytes(2, seq, chunk.ToArray()));
                seq++;
            }
            byte[] end = new byte[32];
            Put(end, 0, 8, firstIndex);
            Put(end, 8, 8, (ulong)frames.Count);
            Put(end, 16, 8, records);
            Put(end, 24, 4, status);
            Emit(FrameBytes(3, seq, end));
        }
    }

    // Streaming reader over readAt(offset, n): one frame is held at a time, whatever the file size.
    sealed class Reader
    {
        readonly Func<long, int, byte[]> readAt;
        readonly long size;
        public readonly byte[] Metadata, StreamId;
        public readonly Manifest Man;
        public readonly ulong CreatedNs;
        public bool Ended;
        public ulong EndStatus;

        public Reader(Func<long, int, byte[]> readAt, long size)
        {
            this.readAt = readAt;
            this.size = size;
            var h = Read(0, 64, "container header");
            VH(h, 56);
            Need(h.AsSpan().StartsWith("NWTBIN\r\n"u8) && Get(h, 8, 2) == 1 && Get(h, 12, 2) == 64, "container fields");
            ulong minor = Get(h, 10, 2);
            Need(minor <= 1, "unsupported container minor");
            Need(Get(h, 14, 2) == 0 && Zero(h.AsSpan(48, 8)) && Zero(h.AsSpan(60, 4)) && !Zero(h.AsSpan(24, 16)), "container reserved/ID");
            ulong ml = Get(h, 16, 4);
            Need(ml >= 8 && ml <= 1048576 && ml % 8 == 0, "metadata length");
            Metadata = Read(64, (int)ml, "metadata");
            Need(Crc(Metadata) == Get(h, 20, 4), "metadata CRC");
            var tlvs = ParseMetadata(Metadata);
            Man = ParseManifest(tlvs[1].Value);
            ParseProvenance(tlvs);
            StreamId = h[24..40];
            CreatedNs = Get(h, 40, 8);
            Need((int)minor == Man.Minor, "container minor does not match the declared types");
        }
        byte[] Read(long offset, int n, string what)
        {
            Need(offset + n <= size, "incomplete: file ends inside " + what);
            byte[] d = readAt(offset, n);
            Need(d.Length == n, "incomplete: file ends inside " + what);
            return d;
        }
        FInfo Info(long offset)
        {
            var h = Read(offset, 64, "frame header");
            VH(h, 52);
            Need(h.AsSpan().StartsWith("NWF1"u8) && h[4] == 1 && (h[6] == 0 || h[6] == 1) && h[7] == 0
                && Get(h, 8, 2) == 64 && Get(h, 10, 2) == 0 && Get(h, 56, 8) == 0, "frame fields/codec");
            ulong stored = Get(h, 12, 4), raw = Get(h, 16, 4);
            var i = new FInfo
            {
                Seq = Get(h, 24, 8), Offset = offset, Kind = h[5], Codec = h[6], Count = Get(h, 20, 4),
                Lo = Get(h, 32, 8), Hi = Get(h, 40, 8), PayloadCrc = (uint)Get(h, 48, 4)
            };
            Need(i.Kind >= 1 && i.Kind <= 3, "frame sequence/kind");
            Need(stored <= LIMIT && raw <= LIMIT, "frame size");
            // Raw frames store the payload as is; only DATA frames may be compressed.
            Need(i.Codec == 0 ? stored == raw : i.Kind == 1, "frame size/codec");
            i.Stored = (int)stored;
            i.Raw = (int)raw;
            return i;
        }
        byte[] Payload(FInfo i)
        {
            byte[] padded = Read(i.Offset + 64, (i.Stored + 7) & ~7, "frame payload");
            Need(Zero(padded.AsSpan(i.Stored)), "frame padding");
            byte[] stored = padded.Length == i.Stored ? padded : padded[..i.Stored];
            byte[] raw = i.Codec == 0 ? stored : ZstdDecompress(stored, i.Raw);
            Need(Crc(raw) == i.PayloadCrc, "payload CRC");
            return raw;
        }
        // Full sequential validation, one frame at a time. Yields once per frame, after the frame has passed all checks.
        // A file that ends early raises "incomplete"; the caller sees the earlier frames first.
        public IEnumerable<(FInfo Info, List<byte[]> Raws, List<Record> Decoded)> Scan(bool decode = true)
        {
            Ended = false;
            var scope = new Scope(Man);
            long pos = 64 + Metadata.Length;
            ulong seq = 0, records = 0, frames = 0, firstIndex = 0;
            List<byte> entries = [], index = [];
            while (!Ended || pos < size)
            {
                Need(!Ended, "trailing bytes");
                Need(pos < size, "incomplete: missing END");
                var info = Info(pos);
                Need(info.Seq == seq, "frame sequence/kind");
                byte[] payload = Payload(info);
                List<byte[]> raws = [];
                List<Record> decoded = [];
                if (info.Kind == 1)
                {
                    Need(firstIndex == 0, "DATA order/count");
                    raws = SplitRecords(payload, info.Count);
                    foreach (var raw in raws)
                    {
                        scope.Check(raw);
                        if (decode)
                            decoded.Add(DecodeRecord(raw));
                    }
                    var (lo, hi) = Bounds(raws);
                    Need(info.Lo == lo && info.Hi == hi, "time bounds");
                    entries.AddRange(Entry(info.Seq, (ulong)pos, lo, hi, (ulong)info.Raw, info.Count));
                    records += (ulong)raws.Count;
                    frames++;
                }
                else
                {
                    Need(info.Count == 0 && info.Lo == NIL && info.Hi == NIL, "non-DATA fields");
                    if (info.Kind == 2)
                    {
                        Need(info.Raw > 0 && info.Raw % 40 == 0, "index size");
                        if (firstIndex == 0)
                            firstIndex = (ulong)pos;
                        index.AddRange(payload);
                    }
                    else
                    {
                        Need(info.Raw == 32, "END size");
                        ulong status = Get(payload, 24, 4);
                        Need(Get(payload, 0, 8) == firstIndex && Get(payload, 8, 8) == frames && Get(payload, 16, 8) == records && Get(payload, 28, 4) == 0, "END totals/status");
                        Need(status <= 1, "END totals/status");
                        Need(firstIndex == 0 || index.SequenceEqual(entries), "index mismatch");
                        Ended = true;
                        EndStatus = status;
                    }
                }
                yield return (info, raws, decoded);
                pos += 64 + ((info.Stored + 7) & ~7);
                seq++;
            }
        }
    }

    // Decoded records of a normally completed container; an aborted END is an error after the last record.
    static IEnumerable<Record> Records(Reader reader)
    {
        foreach (var frame in reader.Scan())
            foreach (var r in frame.Decoded)
                yield return r;
        Need(reader.EndStatus == 0, "aborted container");
    }
    static Reader OpenReader(FileStream f) => new((offset, n) =>
    {
        f.Seek(offset, SeekOrigin.Begin);
        byte[] b = new byte[n];
        f.ReadExactly(b);
        return b;
    }, f.Length);
    static FileStream OpenRead(string path) => new(path, FileMode.Open, FileAccess.Read, FileShare.Read, 1 << 16);
    static string Resolved(string path) => new FileInfo(path).ResolveLinkTarget(true)?.FullName ?? Path.GetFullPath(path);
    static bool Same(string a, string b) => Path.GetFullPath(a) == Path.GetFullPath(b) || (File.Exists(a) && File.Exists(b) && Resolved(a) == Resolved(b));

    // -------------------------------------------------------------- typed path

    static Dictionary<int, ITyped> MakeTyped()
    {
        Dictionary<int, ITyped> d = new();
        void Add<T>(int t) where T : unmanaged
        {
            var c = new Typed<T>();
            var s = GetSchema(t);
            if (s.texts.Count == 0 && !s.has_levels && c.Size == s.fixed_bytes)
                d[t] = c;
        }
        Add<S01>(1); Add<S02>(2); Add<S03>(3); Add<S04>(4); Add<S07>(7); Add<S08>(8);
        Add<S13>(13); Add<S14>(14); Add<S15>(15); Add<S16>(16); Add<S18>(18); Add<S19>(19); Add<S20>(20);
        return d;
    }
    static string RateLine(string label, int records, ulong size, long ticks)
    {
        UInt128 ns = (UInt128)(ulong)Math.Max(ticks * 100, 1L);
        ulong mb = (ulong)((UInt128)size * 1000000000000UL / (ns * 1048576UL)); // thousandths of a MiB per second
        ulong rps = (ulong)((UInt128)(ulong)records * 1000000000UL / ns);
        ulong n = (ulong)ns;
        return FormattableString.Invariant($"{label} records={records} seconds={n / 1000000000UL}.{n % 1000000000UL / 1000:D6} records_per_second={rps} mb_per_second={mb / 1000}.{mb % 1000:D3}\n");
    }
    // Time a full decode (frames, CRC, decompression, typed records) of a file held in memory, then a re-encode.
    static string Bench(string path)
    {
        byte[] data = File.ReadAllBytes(path);
        var typed = MakeTyped();
        List<Record> general = [];
        int count = 0;
        ulong size = 0;
        long t0 = Stopwatch.GetTimestamp();
        var reader = new Reader((offset, n) => data.AsSpan((int)offset, n).ToArray(), data.Length);
        foreach (var frame in reader.Scan(false))
            foreach (var raw in frame.Raws)
            {
                int t = raw[4] | raw[5] << 8;
                if (typed.TryGetValue(t, out var c) && c.Size == raw.Length)
                    c.Decode(raw);
                else
                    general.Add(DecodeRecord(raw));
                count++;
                size += (ulong)raw.Length;
            }
        long t1 = Stopwatch.GetTimestamp();
        byte[] scratch = new byte[1048576];
        foreach (var c in typed.Values)
            c.EncodeAll(scratch);
        foreach (var r in general)
            EncodeRecord(r);
        long t2 = Stopwatch.GetTimestamp();
        return RateLine("decode", count, size, Stopwatch.GetElapsedTime(t0, t1).Ticks) + RateLine("encode", count, size, Stopwatch.GetElapsedTime(t1, t2).Ticks);
    }

    // ------------------------------------------------------------ command line

    static void Flush()
    {
        try { Out.Flush(); } catch (IOException) { }
    }
    static void CmdWrite(string file, bool v11, bool zstd)
    {
        using var ms = new MemoryStream();
        byte[] metadata = Tlv(1, 1, Utf8.GetBytes(Resource(v11 ? "manifest11" : "manifest").Trim()));
        int? level = v11 && zstd ? 3 : null;
        var w = v11
            ? new Writer(ms, metadata, V11Id, 1760000000000000000UL, 3, level)
            : new Writer(ms, metadata, LegacyId, 1700000000000000000UL, 3, level);
        foreach (var r in Catalog(v11 ? "catalog11" : "catalog").Where(r => !r.standalone))
            w.Write(r);
        w.Close();
        File.WriteAllBytes(file, ms.ToArray());
    }
    static void CmdRecord(string[] args)
    {
        Need(args.Length == 3, Usage);
        int typ = int.Parse(args[1], NumberStyles.None, CultureInfo.InvariantCulture);
        var r = Catalog(typ <= 9 ? "catalog" : "catalog11").FirstOrDefault(x => x.type == typ);
        Need(r != null, "no example for this record type");
        File.WriteAllBytes(args[2], EncodeRecord(r!));
    }
    static void CmdRead(string[] args)
    {
        string? again = args.Length > 2 ? args[2] : null;
        // The output is opened for writing while the input is still being read.
        Need(again == null || !Same(args[1], again), "REENCODED_FILE must differ from FILE");
        using var input = OpenRead(args[1]);
        var reader = OpenReader(input);
        using var output = again == null ? null : new FileStream(again, FileMode.Create, FileAccess.Write, FileShare.None, 1 << 16);
        // The re-encode keeps the input's identity and metadata bytes; only the framing is rewritten.
        Writer? w = output == null ? null : new Writer(output, reader.Metadata, reader.StreamId, reader.CreatedNs, 3);
        int i = 0;
        foreach (var r in Records(reader))
        {
            EmitReport(++i, r);
            w?.Write(r);
        }
        w?.Close();
    }
    static void CmdToCsv(string[] args, bool pretty)
    {
        Need(args.Length == 3, Usage);
        int typ = int.Parse(args[2], NumberStyles.None, CultureInfo.InvariantCulture);
        Need(ByType.ContainsKey(typ), "unknown record type");
        string header = CsvHeader(typ);
        using var input = OpenRead(args[1]);
        var reader = OpenReader(input);
        Out.Write(header + "\n");
        foreach (var r in Records(reader))
            if (r.type == typ)
                EmitCsv(r, pretty);
    }
    static int Main(string[] argv)
    {
        try
        {
            Need(Crc("123456789"u8) == 0xe3069283, "CRC check");
            var args = argv.Where(a => a != "--pretty" && a != "--zstd").ToArray();
            bool pretty = argv.Contains("--pretty"), zstd = argv.Contains("--zstd");
            Need(args.Length >= 2, Usage);
            switch (args[0])
            {
                case "write": CmdWrite(args[1], false, false); break;
                case "write-v11": CmdWrite(args[1], true, zstd); break;
                case "record": CmdRecord(args); break;
                case "decode-record":
                    Need(new FileInfo(args[1]).Length <= 1048576, "record limit");
                    EmitReport(1, DecodeRecord(File.ReadAllBytes(args[1])));
                    break;
                case "read": CmdRead(args); break;
                case "to-json":
                    {
                        using var input = OpenRead(args[1]);
                        foreach (var r in Records(OpenReader(input)))
                            EmitJson(r, pretty);
                        break;
                    }
                case "to-csv": CmdToCsv(args, pretty); break;
                case "bench": Out.Write(Bench(args[1])); break;
                default: throw new InvalidDataException("unknown command");
            }
            Flush();
            return 0;
        }
        catch (Exception e)
        {
            Flush();
            Console.Error.WriteLine("NWT error: " + e.Message);
            return 1;
        }
    }
}
