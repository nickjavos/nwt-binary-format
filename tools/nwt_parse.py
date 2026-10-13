
import re

I64_MIN, I64_MAX = -(1 << 63), (1 << 63) - 1
U64_NULL = (1 << 64) - 1
DECIMAL = re.compile(r"([+-]?)(\d*)(?:\.(\d*))?(?:[eE]([+-]?\d+))?", re.ASCII)
DATE = re.compile(r"(\d{4})-(\d{2})-(\d{2})", re.ASCII)
TIMESTAMP = re.compile(
    r"(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,9}))?(Z|[+-]\d{2}:\d{2})", re.ASCII
)
MONTH_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def need(ok, why):
    if not ok:
        raise ValueError(why)


def decimal_parts(text):
    m = DECIMAL.fullmatch(text)
    need(m and (m[2] or m[3]), f"not a decimal number: {text!r}")
    fraction = m[3] or ""
    return m[1] == "-", int(m[2] + fraction), int(m[4] or 0) - len(fraction)


def scale_decimal(text, scale, rounded):
    negative, digits, exponent = decimal_parts(text)
    shift = exponent + scale
    dropped = False
    if digits == 0:
        value = 0
    elif shift >= 0:
        need(shift <= 40, f"decimal out of range: {text!r}")
        value = digits * 10**shift
    else:
        value, rest = divmod(digits, 10**-shift) if -shift <= len(str(digits)) else (0, digits)
        dropped = rest != 0
        need(rounded or not dropped, f"more than {scale} decimal places: {text!r}")
        if -shift <= len(str(digits)):
            half = 2 * rest - 10**-shift
            if half > 0 or (half == 0 and value % 2 == 1):
                value += 1
    value = -value if negative else value
    need(I64_MIN <= value <= I64_MAX, f"decimal out of range: {text!r}")
    return value, dropped


def parse_decimal(text, scale=9):
    return scale_decimal(text, scale, False)[0]


def parse_decimal_rounded(text, scale=9):
    return scale_decimal(text, scale, True)


def days_from_civil(year, month, day):
    leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    need(1 <= month <= 12, "month out of range")
    need(1 <= day <= MONTH_DAYS[month - 1] + (leap and month == 2), "day out of range")
    year -= month <= 2
    era, yoe = divmod(year, 400)
    doy = (153 * (month - 3 if month > 2 else month + 9) + 2) // 5 + day - 1
    return era * 146097 + yoe * 365 + yoe // 4 - yoe // 100 + doy - 719468


def date_ns(text, year, month, day):
    need(year >= 1970, f"date before 1970: {text!r}")
    try:
        return days_from_civil(year, month, day) * 86400 * 10**9
    except ValueError as error:
        raise ValueError(f"{error}: {text!r}") from None


def parse_date_ns(text):
    m = DATE.fullmatch(text)
    need(m, f"not a date (YYYY-MM-DD): {text!r}")
    ns = date_ns(text, int(m[1]), int(m[2]), int(m[3]))
    need(ns < U64_NULL, f"date out of range: {text!r}")
    return ns


def parse_timestamp_ns(text):
    m = TIMESTAMP.fullmatch(text)
    need(m, f"not a timestamp: {text!r}")
    need(m[8] in ("Z", "+00:00"), f"timestamp is not UTC: {text!r}")
    hour, minute, second = int(m[4]), int(m[5]), int(m[6])
    need(hour <= 23 and minute <= 59 and second <= 59, f"time of day out of range: {text!r}")
    fraction = int((m[7] or "").ljust(9, "0"))
    ns = date_ns(text, int(m[1]), int(m[2]), int(m[3])) + (hour * 3600 + minute * 60 + second) * 10**9 + fraction
    need(ns < U64_NULL, f"timestamp out of range: {text!r}")
    return ns


def strip_id(text, prefix):
    need(text.startswith(prefix), f"expected prefix {prefix!r}: {text!r}")
    number = text[len(prefix) :]
    need(number.isascii() and number.isdigit(), f"expected digits after {prefix!r}: {text!r}")
    value = int(number)
    need(value < U64_NULL, f"identifier out of range: {text!r}")
    return value
