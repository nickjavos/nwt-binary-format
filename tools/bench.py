#!/usr/bin/env python3
"""Measure this kit and write the chart files of the "Size and speed" document.

    python3 tools/bench.py            1,000,000 records, 9 timed runs
    python3 tools/bench.py --quick    100,000 records, 3 timed runs

Size: the same records as CSV, as JSON Lines, as NWT with raw frames and as NWT with Zstandard frames.
Speed: the `bench` command of every reference codec that builds on this machine.
Selective read: the DATA frames a time-range query reads, against a read of the whole file.

Every number written comes from this run. A measurement that cannot be made is left out with its chart.
"""

import argparse
import itertools
import json
import os
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
import time

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(KIT, "examples", "python"), os.path.join(KIT, "tools")]
import nwt as tool
import nwt_example as codec

MB = 1048576
SAMPLES = [
    "fixtures/real-market/equity-quotes.nwt",
    "fixtures/real-market/equity-orders.nwt",
    "fixtures/real-market/equity-bars.nwt",
    "fixtures/real-market/option-best-quotes.nwt",
    "fixtures/real-market/statistics.nwt",
    "fixtures/real-reference/corporate-actions-us.nwt",
]
SOURCE = SAMPLES[0]
DEFINITION = 6
WINDOW_NS = 60 * 10**9
STREAM_ID = "6e77742d62656e63682d66696c652d31"
CREATED_NS = 1760000000000000000
CSV = {"en": "CSV", "ru": "CSV"}
CSV_ZSTD = {"en": "CSV, Zstandard", "ru": "CSV, Zstandard"}
JSONL = {"en": "JSON Lines", "ru": "JSON Lines"}
NWT_RAW = {"en": "NWT, raw frames", "ru": "NWT, кадры без сжатия"}
NWT_ZSTD = {"en": "NWT, Zstandard frames", "ru": "NWT, кадры Zstandard"}


def say(text):
    print("bench: " + text, file=sys.stderr, flush=True)


def kit(path):
    return os.path.join(KIT, path)


def name_of(path):
    return os.path.basename(path)[:-4]


def sig3(value):
    rounded = float(f"{value:.3g}")
    return int(rounded) if rounded == int(rounded) else rounded


def en(n):
    return f"{n:,}"


def ru(n):
    return f"{n:,}".replace(",", " ")


def cores_ru(n):
    few = n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14)
    return f"{n} " + ("ядро" if n % 10 == 1 and n % 100 != 11 else "ядра" if few else "ядер")


def machine():
    """Hardware only: CPU model, core count, memory."""
    try:
        cpu = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True).stdout.strip()
    except OSError:
        cpu = ""
    cpu = cpu or platform.processor() or platform.machine()
    cores = os.cpu_count()
    ram = round(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 2**30)
    return {
        "en": f"Machine: {cpu}, {cores} core{'s' if cores != 1 else ''}, {ram} GB of memory.",
        "ru": f"Машина: {cpu}, {cores_ru(cores)}, {ram} ГБ памяти.",
    }


def build_codecs(work):
    """Command line of each reference codec. A codec whose toolchain is missing is left out."""
    codecs = {"Python": [sys.executable, kit("examples/python/nwt_example.py")]}

    def attempt(name, build, run):
        try:
            subprocess.run(build, check=True, capture_output=True)
            codecs[name] = run
        except (OSError, subprocess.CalledProcessError) as error:
            say(f"{name} codec not built and left out: {error}")

    cargo = shutil.which("cargo") or os.path.expanduser("~/.cargo/bin/cargo")
    attempt(
        "Rust",
        [cargo, "build", "--release", "--locked", "--manifest-path", kit("examples/rust/Cargo.toml"),
         "--target-dir", os.path.join(work, "rust")],
        [os.path.join(work, "rust", "release", "nwt-example")],
    )
    attempt(
        "C#",
        ["dotnet", "build", kit("examples/csharp/NwtExample.csproj"), "-c", "Release",
         "--artifacts-path", os.path.join(work, "csharp")],
        ["dotnet", os.path.join(work, "csharp", "bin", "NwtExample", "release", "NwtExample.dll")],
    )
    brew = [flag + "/opt/homebrew/" + d for flag, d in (("-I", "include"), ("-L", "lib")) if os.path.isdir("/opt/homebrew/" + d)]
    attempt(
        "C++",
        ["c++", "-std=c++20", "-O2", "-DNWT_ZSTD", *brew, kit("examples/cpp/main.cpp"),
         "-o", os.path.join(work, "nwt-cpp"), "-lzstd"],
        [os.path.join(work, "nwt-cpp")],
    )
    return codecs


def text_sizes(path, compress):
    """Bytes of one file's records as text, exactly as `to-csv` and `to-json` print them.

    CSV is one file per record type, each with its header line. Returns the record count and,
    for the plain and the --pretty output, the bytes of CSV, of JSON Lines and (with compress)
    of the CSV files compressed with Zstandard level 3.
    """
    records, json_bytes, tables = 0, {False: 0, True: 0}, {}
    with tool.opened(path) as reader:
        for info, _, decoded in tool.scan_complete(reader, decode=True):
            codec.need(info.codec == 0, "the sample is expected to have raw frames")
            for r in decoded:
                records += 1
                for pretty in (False, True):
                    json_bytes[pretty] += len(codec.to_json_line(r, pretty).encode()) + 1
                    table = tables.setdefault((r["type"], pretty), [0, [codec.csv_header(r["type"]) + "\n"]])
                    table[1].append(codec.to_csv_line(r, pretty) + "\n")
                    if not compress and len(table[1]) >= 10000:
                        table[0] += len("".join(table[1]).encode())
                        table[1] = []
    out = {}
    for pretty in (False, True):
        texts = [(size, "".join(lines).encode()) for (_, p), (size, lines) in tables.items() if p == pretty]
        out[pretty] = {"csv": sum(size + len(text) for size, text in texts), "json": json_bytes[pretty]}
        if compress:
            out[pretty]["csv_zstd"] = sum(len(codec.zstd_compress(text, 3)) for _, text in texts)
    return records, out


def check_text_sizes():
    """The sizes counted in this process equal the bytes the commands print."""
    python = [sys.executable, kit("examples/python/nwt_example.py")]
    printed = lambda *args: len(subprocess.run(python + list(args), check=True, capture_output=True).stdout)
    _, sizes = text_sizes(kit(SOURCE), False)
    with tool.opened(kit(SOURCE)) as reader:
        types = sorted({r["type"] for r in codec.complete_records(reader)})
    for pretty, flag in ((False, []), (True, ["--pretty"])):
        assert printed("to-json", kit(SOURCE), *flag) == sizes[pretty]["json"]
        assert sum(printed("to-csv", kit(SOURCE), str(t), *flag) for t in types) == sizes[pretty]["csv"]


def repack(source, out):
    subprocess.run([sys.executable, kit("tools/nwt.py"), "repack", source, out,
                    "--stream-id", STREAM_ID, "--created-ns", str(CREATED_NS)], check=True)


def build_large(out, target):
    """Repeat the data records of the source sample up to `target` records, through the public writer.

    Each repetition moves ts_event and ts_recv forward by one period (the time the sample spans,
    rounded up to a whole second). Sequence numbers continue. The definition is written once.
    """
    with tool.opened(kit(SOURCE)) as reader:
        raws = [raw for _, frame, _ in tool.scan_complete(reader) for raw in frame]
        manifest = dict(reader.manifest, ordering="ts_event")
    head = [raw for raw in raws if tool.rtype(raw) == DEFINITION]
    body = [raw for raw in raws if tool.rtype(raw) != DEFINITION]
    times = [tool.rtime(raw) for raw in body]
    assert times == sorted(times) and codec.NULL not in times and all(tool.rtime(raw) <= times[0] for raw in head)
    period = ((times[-1] - times[0]) // 10**9 + 1) * 10**9
    provenance = {
        "derived_by": "tools/bench.py",
        "derived_note": f"records of {name_of(SOURCE)} repeated to {target} records; ts_event and ts_recv "
                        f"advance by {period} ns per repetition; sequences continue",
    }
    sequencer, written = codec.Sequencer(), 0
    with open(out, "wb") as f:
        writer = codec.Writer(f, json.dumps(manifest, separators=(",", ":")), bytes.fromhex(STREAM_ID), CREATED_NS,
                              provenance=json.dumps(provenance, separators=(",", ":")))
        for shift in itertools.chain([None], (k * period for k in itertools.count())):
            for raw in head if shift is None else body:
                if written == target:
                    break
                b = bytearray(raw)
                for offset in (24, 32) if shift else ():
                    if codec.get(b, offset, 8) != codec.NULL:
                        codec.put(b, offset, 8, codec.get(b, offset, 8) + shift)
                codec.put(b, 40, 8, sequencer.next(codec.get(b, 8, 4), codec.get(b, 12, 4)))
                writer.write_raw(b)
                written += 1
            if written == target:
                break
        writer.close()
    return len(body), period


def run_bench(codecs, files, runs):
    """Median of `runs` runs of every codec's `bench` command on every file.

    Returns {codec: [{"decode": (records/s, MB/s), "encode": (records/s, MB/s)} for each file]}.
    The runs go round robin, so a busy moment of the machine falls on every codec and file alike.
    """
    seen = {(name, i): {"decode": [], "encode": []} for name in codecs for i in range(len(files))}
    for _ in range(runs):
        for (name, i), rows in seen.items():
            _, path, records = files[i]
            text = subprocess.run(codecs[name] + ["bench", path], check=True, capture_output=True, text=True).stdout
            for line in text.splitlines():
                label, *pairs = line.split()
                values = dict(pair.split("=") for pair in pairs)
                assert int(values["records"]) == records, "the codec read a different number of records"
                rows[label].append((int(values["records_per_second"]), float(values["mb_per_second"])))
    for (name, i), rows in seen.items():
        say(f"  {name} {os.path.basename(files[i][1])} " + json.dumps(rows))
    middle = lambda rows: tuple(statistics.median(column) for column in zip(*rows))
    return {name: [{label: middle(rows) for label, rows in seen[name, i].items()} for i in range(len(files))]
            for name in codecs}


def selective(path, runs):
    """A 60-second ts_event window from the middle of a store file: by the index, and by a scan of every frame."""
    with tool.opened(path) as reader:
        index = reader.index()
    times = [e for e in index if e.min_event_ns != codec.NULL]
    middle = (times[0].min_event_ns + times[-1].max_event_ns) // 2
    t0 = middle - middle % 10**9
    t1 = t0 + WINDOW_NS
    match = tool.matcher(None, None, t0, t1)

    def by_index(reader):
        return list(tool.select(reader, t0=t0, t1=t1))

    def by_scan(reader):
        return [raw for _, frame, _ in tool.scan_complete(reader) for raw in frame if match(raw)]

    def timed(read):
        took, frames = [], []
        for _ in range(runs):
            with open(path, "rb") as f:
                start = time.perf_counter_ns()
                reader = codec.open_reader(f)
                inner = reader.read_frame
                reader.read_frame = lambda entry: frames.append(entry.seq) or inner(entry)
                found = read(reader)
                took.append(time.perf_counter_ns() - start)
        return found, statistics.median(took) / 10**6, len(frames) // runs, took

    found, query_ms, query_frames, a = timed(by_index)
    scanned, scan_ms, _, b = timed(by_scan)
    assert found == scanned and found, "the query and the scan return different records"
    say(f"  selective ns by index {a} by scan {b}")
    return dict(frames=len(index), summary_frames=len(index) - len(times), query_frames=query_frames,
                query_ms=query_ms, scan_ms=scan_ms, found=len(found))


def write_chart(out, name, title, unit, note, series):
    data = {"kind": "bar", "title": title, "unit": unit, "note": note, "series": series}
    with open(os.path.join(out, name + ".json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")
    say("wrote " + name + ".json")


def bar(label, value, group=None, highlight=False):
    row = {"label": label, "value": value}
    if group:
        row["group"] = group
    row["highlight"] = highlight
    return row


def both(en_text, ru_text, hardware):
    return {"en": en_text + " " + hardware["en"], "ru": ru_text + " " + hardware["ru"]}


def main():
    parser = argparse.ArgumentParser(description="Measure the kit and write the chart files.")
    parser.add_argument("--out", default=kit("docs/data"), help="folder for the chart files (default docs/data)")
    parser.add_argument("--work", help="scratch folder for builds and generated files (default: a temporary folder)")
    parser.add_argument("--quick", action="store_true", help="100,000 records and 3 timed runs")
    args = parser.parse_args()
    target, runs = (100_000, 3) if args.quick else (1_000_000, 9)
    work = args.work or tempfile.mkdtemp(prefix="nwt-bench-")
    os.makedirs(work, exist_ok=True)
    os.makedirs(args.out, exist_ok=True)
    hw = machine()
    zstd = codec.zstd_available()
    large, store, small = (os.path.join(work, n) for n in ("large.nwt", "large.store.nwt", "sample.store.nwt"))
    how_en = ("CSV and JSON Lines are the output of the reference codec's to-csv and to-json commands, one CSV file "
              "per record type. Each command has a plain and a --pretty output; the smaller one is counted.")
    how_ru = ("CSV и JSON Lines — вывод команд to-csv и to-json эталонного кодека, по одному файлу CSV на тип записи. "
              "У каждой команды два вида вывода, обычный и --pretty; учитывается меньший.")
    try:
        check_text_sizes()

        say("sizes of the samples")
        plain, packed = [], []
        for path in SAMPLES:
            sample = name_of(path)
            records, text = text_sizes(kit(path), zstd)
            least = {key: min(text[False][key], text[True][key]) for key in text[False]}
            raw = os.path.getsize(kit(path))
            per = lambda size: sig3(size / records)
            plain += [bar(CSV, per(least["csv"]), sample), bar(JSONL, per(least["json"]), sample),
                      bar(NWT_RAW, per(raw), sample, True)]
            line = f"  {sample} records={records} csv={least['csv']} json={least['json']} nwt_raw={raw}"
            if zstd:
                repack(kit(path), small)
                stored = os.path.getsize(small)
                packed += [bar(CSV_ZSTD, per(least["csv_zstd"]), sample), bar(NWT_ZSTD, per(stored), sample, True)]
                line += f" csv_zstd={least['csv_zstd']} nwt_zstd={stored}"
            say(line)
        write_chart(
            args.out, "bytes-per-record",
            {"en": "Bytes per record without compression", "ru": "Байт на запись без сжатия"},
            {"en": "bytes per record", "ru": "байт на запись"},
            both("File bytes divided by the number of records, for six samples of the kit. " + how_en +
                 " NWT is the sample file as it is, with its header, manifest and INDEX.",
                 "Размер файла, делённый на число записей, для шести образцов комплекта. " + how_ru +
                 " NWT — файл образца целиком, с заголовком, манифестом и INDEX.", hw),
            plain,
        )
        if zstd:
            write_chart(
                args.out, "bytes-per-record-compressed",
                {"en": "Bytes per record with Zstandard", "ru": "Байт на запись со сжатием Zstandard"},
                {"en": "bytes per record", "ru": "байт на запись"},
                both("File bytes divided by the number of records, for the same six samples. CSV is each CSV file "
                     "compressed as a whole with Zstandard level 3; the smaller of the plain and the --pretty output "
                     "is counted. NWT is the store file written by nwt repack: Zstandard level 3 in every frame, "
                     "with header, manifest, INDEX and FRAME_SUMMARY records.",
                     "Размер файла, делённый на число записей, для тех же шести образцов. CSV — каждый файл CSV, "
                     "сжатый целиком Zstandard уровня 3; учитывается меньший из двух видов вывода, обычного и "
                     "--pretty. NWT — файл хранилища, записанный командой nwt repack: Zstandard уровня 3 в каждом "
                     "кадре, с заголовком, манифестом, INDEX и записями FRAME_SUMMARY.", hw),
                packed,
            )

        say(f"large file: {target} records")
        repeated, period = build_large(large, target)
        built_en = (f"a file of {en(target)} records: the {en(repeated)} data records of the {name_of(SOURCE)} sample "
                    f"repeated, with timestamps and sequence numbers that advance")
        built_ru = (f"файл из {ru(target)} записей: {ru(repeated)} записей данных образца {name_of(SOURCE)} повторены, "
                    f"метки времени и порядковые номера возрастают")
        records, text = text_sizes(large, False)
        assert records == target
        least = {key: min(text[False][key], text[True][key]) for key in text[False]}
        raw = os.path.getsize(large)
        say(f"  large records={records} csv={least['csv']} json={least['json']} nwt_raw={raw} period_ns={period}")
        write_chart(
            args.out, "size-by-encoding",
            {"en": f"{en(target)} records in three encodings", "ru": f"{ru(target)} записей в трёх кодировках"},
            {"en": "MB", "ru": "МБ"},
            both(f"Measured on {built_en}. 1 MB is 1,048,576 bytes. {how_en} NWT is the whole file with raw frames "
                 "of 1,048,576 bytes.",
                 f"Измерен {built_ru}. 1 МБ — это 1 048 576 байт. {how_ru} NWT — файл целиком, кадры без "
                 "сжатия по 1 048 576 байт.", hw),
            [bar(CSV, sig3(least["csv"] / MB)), bar(JSONL, sig3(least["json"] / MB)), bar(NWT_RAW, sig3(raw / MB), None, True)],
        )

        repack(large, store)
        with tool.opened(store) as reader:
            stored_records = sum(e.record_count for e in reader.index())
        say(f"  store bytes={os.path.getsize(store)} records={stored_records}")

        say(f"throughput: {runs} runs of each codec")
        codecs = build_codecs(work)
        files = [({"en": "Raw frames", "ru": "Кадры без сжатия"}, large, target)]
        if zstd:
            files.append(({"en": "Zstandard frames", "ru": "Кадры Zstandard"}, store, stored_records))
        rates = run_bench(codecs, files, runs)
        timing_en = (f"Median of {runs} runs of each reference codec's bench command on {built_en}. The timer starts "
                     "after the file is in memory, so process start and disk reads are not counted.")
        timing_ru = (f"Медиана {runs} запусков команды bench каждого эталонного кодека. Данные — {built_ru}. Отсчёт "
                     "времени начинается, когда файл уже в памяти: запуск процесса и чтение с диска не учитываются.")
        decode_en = (" Decoding walks the container, checks the CRC-32C of every frame, decompresses Zstandard frames "
                     "and decodes every record. The Zstandard file is the store file written by nwt repack.")
        decode_ru = (" Декодирование проходит контейнер, проверяет CRC-32C каждого кадра, распаковывает кадры "
                     "Zstandard и декодирует каждую запись. Файл Zstandard — файл хранилища, записанный командой "
                     "nwt repack.")
        encode_en = " Encoding writes the decoded values back to record bytes; frames and checksums are not written."
        encode_ru = " Кодирование записывает декодированные значения обратно в байты записей; кадры и контрольные суммы не пишутся."
        per_second = {"en": "records per second", "ru": "записей в секунду"}
        mb_second = {"en": "MB per second", "ru": "МБ в секунду"}
        mb_en, mb_ru = " 1 MB is 1,048,576 bytes of records.", " 1 МБ — это 1 048 576 байт записей."
        for column, suffix, unit, extra in ((0, "", per_second, ("", "")), (1, "-mb", mb_second, (mb_en, mb_ru))):
            write_chart(
                args.out, "decode-throughput" + suffix,
                {"en": "Decode throughput of the reference codecs", "ru": "Скорость декодирования эталонных кодеков"},
                unit, both(timing_en + decode_en + extra[0], timing_ru + decode_ru + extra[1], hw),
                [bar(label, sig3(rates[name][i]["decode"][column]), name, True)
                 for name in rates for i, (label, _, _) in enumerate(files)],
            )
            write_chart(
                args.out, "encode-throughput" + suffix,
                {"en": "Encode throughput of the reference codecs", "ru": "Скорость кодирования эталонных кодеков"},
                unit, both(timing_en + encode_en + extra[0], timing_ru + encode_ru + extra[1], hw),
                [bar({"en": name, "ru": name}, sig3(rates[name][0]["encode"][column]), None, True) for name in rates],
            )

        say("selective read")
        s = selective(store, runs)
        say("  " + json.dumps(s))
        frames_en = (f"A store file of {en(stored_records)} records in {en(s['frames'])} DATA frames, written by nwt "
                     f"repack from {built_en}. The query asks for 60 seconds of ts_event from the middle of the file "
                     f"and returns {en(s['found'])} records.")
        frames_ru = (f"Файл хранилища (записей: {ru(stored_records)}, кадров DATA: {ru(s['frames'])}), записанный "
                     f"командой nwt repack. Исходные данные — {built_ru}. Запрос выбирает 60 секунд ts_event из "
                     f"середины файла; найдено записей: {ru(s['found'])}.")
        query = {"en": "Time-range query", "ru": "Запрос по интервалу времени"}
        whole = {"en": "Whole file", "ru": "Файл целиком"}
        write_chart(
            args.out, "selective-read",
            {"en": "DATA frames read to answer a time-range query", "ru": "Кадры DATA, прочитанные для запроса по интервалу времени"},
            {"en": "DATA frames", "ru": "кадров DATA"},
            both(frames_en + " The query reads the INDEX, the frames of FRAME_SUMMARY records (their number here: "
                 f"{en(s['summary_frames'])}) and the frames whose time range overlaps the window. "
                 "The count does not depend on the machine.",
                 frames_ru + f" Запрос читает INDEX, кадры с записями FRAME_SUMMARY (здесь их {ru(s['summary_frames'])}) "
                 "и кадры, интервал времени которых пересекается с окном. Это число не зависит от машины.", hw),
            [bar(query, s["query_frames"], None, True), bar(whole, s["frames"])],
        )
        write_chart(
            args.out, "selective-read-time",
            {"en": "Time to answer a time-range query", "ru": "Время ответа на запрос по интервалу времени"},
            {"en": "ms", "ru": "мс"},
            both(frames_en + f" Median of {runs} runs inside the Python nwt tool, from opening the file to the last "
                 "matching record. The whole-file read scans every frame and applies the same filter.",
                 frames_ru + f" Медиана {runs} запусков внутри инструмента nwt на Python, от открытия файла до "
                 "последней подходящей записи. Чтение файла целиком проходит все кадры и применяет тот же фильтр.", hw),
            [bar(query, sig3(s["query_ms"]), None, True), bar(whole, sig3(s["scan_ms"]))],
        )
    finally:
        for path in (large, store, small):
            if os.path.exists(path):
                os.remove(path)
        if not args.work:
            shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
