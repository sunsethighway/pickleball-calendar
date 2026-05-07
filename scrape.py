#!/usr/bin/env python3
"""
scrape.py — Pickleball England Tournament Calendar Scraper
Fetches https://www.pickleballengland.org/tournaments/, parses all tournament
tables, and writes calendar.ics to the repo root.

Run locally:  python scrape.py
GitHub Actions runs this daily and commits the result.
"""

import re
import sys
import hashlib
import datetime
import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
URL = "https://www.pickleballengland.org/tournaments/"
OUTPUT_FILE = "calendar.ics"
CALENDAR_NAME = "Pickleball England Tournaments"
CALENDAR_DESCRIPTION = "Auto-updated tournament calendar from pickleballengland.org"

MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
}


# ---------------------------------------------------------------------------
# Date parsing
# ---------------------------------------------------------------------------

def strip_ordinal(s):
    """Remove ordinal suffixes: 1st -> 1, 22nd -> 22, 3rd -> 3, 4th -> 4."""
    return re.sub(r"(\d+)(st|nd|rd|th)", r"\1", s, flags=re.IGNORECASE)


def month_num(name):
    return MONTHS.get(name.strip().lower())


def parse_date_range(raw):
    """
    Parse the freeform date strings used on pickleballengland.org into
    (start_date, end_date) as datetime.date objects.

    Handles formats including:
      "May 30th 2026"                      -> single day
      "May 22nd-24th 2026"                 -> same-month range
      "August 11th-16th 2026"              -> same-month range
      "October 29th-November 1st 2026"     -> cross-month range
      "June 6th & 7th 2026"               -> two-day (& separator)
      "November 3rd-8th 2026"              -> same-month range
    """
    raw = strip_ordinal(raw.strip())

    # Normalise "&" between days to a hyphen so we can use one code path
    raw = re.sub(r"\s*&\s*", "-", raw)

    # --- Cross-month range: "October 29-November 1 2026" ---
    cross = re.match(
        r"([A-Za-z]+)\s+(\d+)\s*-\s*([A-Za-z]+)\s+(\d+)\s+(\d{4})",
        raw, re.IGNORECASE,
    )
    if cross:
        m1, d1, m2, d2, yr = cross.groups()
        start = datetime.date(int(yr), month_num(m1), int(d1))
        end   = datetime.date(int(yr), month_num(m2), int(d2))
        return start, end

    # --- Same-month range: "May 22-24 2026" ---
    same = re.match(
        r"([A-Za-z]+)\s+(\d+)\s*-\s*(\d+)\s+(\d{4})",
        raw, re.IGNORECASE,
    )
    if same:
        month_name, d1, d2, yr = same.groups()
        m = month_num(month_name)
        start = datetime.date(int(yr), m, int(d1))
        end   = datetime.date(int(yr), m, int(d2))
        return start, end

    # --- Single day: "May 30 2026" ---
    single = re.match(
        r"([A-Za-z]+)\s+(\d+)\s+(\d{4})",
        raw, re.IGNORECASE,
    )
    if single:
        month_name, day, yr = single.groups()
        d = datetime.date(int(yr), month_num(month_name), int(day))
        return d, d

    print(f"  [WARN] Could not parse date: '{raw}'", file=sys.stderr)
    return None, None


# ---------------------------------------------------------------------------
# Scraping
# ---------------------------------------------------------------------------

def fetch_tournaments():
    """Return a list of dicts, one per tournament row."""
    resp = requests.get(URL, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    events = []
    tables = soup.find_all("table")

    for table in tables:
        # Identify the section name from the nearest preceding heading
        section = "Pickleball England"
        for sib in table.find_all_previous(["h1", "h2", "h3", "h4", "h5", "strong"]):
            text = sib.get_text(strip=True)
            if text:
                section = text
                break

        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all(["td", "th"])
            if not cells or len(cells) < 2:
                continue

            # Skip header rows
            first_cell_text = cells[0].get_text(strip=True)
            if first_cell_text.upper() in ("DATES", "DATE"):
                continue

            date_raw  = cells[0].get_text(" ", strip=True) if len(cells) > 0 else ""
            name      = cells[1].get_text(" ", strip=True) if len(cells) > 1 else ""
            venue     = cells[2].get_text(" ", strip=True) if len(cells) > 2 else ""
            organiser = cells[3].get_text(" ", strip=True) if len(cells) > 3 else ""
            dupr      = cells[4].get_text(" ", strip=True) if len(cells) > 4 else ""
            more_cell = cells[5] if len(cells) > 5 else None

            # Grab link from "More Information" column
            link = ""
            if more_cell:
                a = more_cell.find("a", href=True)
                if a:
                    href = a["href"]
                    link = href if href.startswith("http") else f"https://www.pickleballengland.org{href}"

            if not date_raw or not name:
                continue

            events.append({
                "date_raw":  date_raw,
                "name":      name,
                "venue":     venue,
                "organiser": organiser,
                "dupr":      dupr,
                "link":      link,
                "section":   section,
            })

    return events


# ---------------------------------------------------------------------------
# .ics generation
# ---------------------------------------------------------------------------

def ics_escape(s):
    """Escape special characters for .ics text fields."""
    return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def make_uid(name, start):
    """Generate a stable UID from event name + start date (stable across re-runs)."""
    raw = f"{name}-{start}".encode()
    return hashlib.md5(raw).hexdigest() + "@pickleballengland.org"


def format_date(d):
    return d.strftime("%Y%m%d")


def build_ics(events):
    now = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Suffolk Pickleball Co//Pickleball England Calendar//EN",
        f"X-WR-CALNAME:{CALENDAR_NAME}",
        f"X-WR-CALDESC:{CALENDAR_DESCRIPTION}",
        "X-WR-TIMEZONE:Europe/London",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]

    skipped = 0
    added = 0

    for ev in events:
        start, end = parse_date_range(ev["date_raw"])
        if start is None:
            skipped += 1
            continue

        # DTEND in iCal for all-day events is exclusive (day after last day)
        dtend = end + datetime.timedelta(days=1)

        description_parts = []
        if ev["organiser"]:
            description_parts.append(f"Organiser: {ev['organiser']}")
        if ev["dupr"]:
            description_parts.append(f"DUPR Results: {ev['dupr']}")
        if ev["section"]:
            description_parts.append(f"Category: {ev['section']}")
        if ev["link"]:
            description_parts.append(f"More info: {ev['link']}")
        description = "\\n".join(description_parts)

        uid = make_uid(ev["name"], start)

        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{now}",
            f"DTSTART;VALUE=DATE:{format_date(start)}",
            f"DTEND;VALUE=DATE:{format_date(dtend)}",
            f"SUMMARY:{ics_escape(ev['name'])}",
            f"LOCATION:{ics_escape(ev['venue'])}",
            f"DESCRIPTION:{description}",
        ]
        if ev["link"]:
            lines.append(f"URL:{ev['link']}")
        lines.append("END:VEVENT")
        added += 1

    lines.append("END:VCALENDAR")

    print(f"  {added} events written, {skipped} skipped (unparseable dates)")
    return "\r\n".join(lines) + "\r\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"Fetching {URL} ...")
    events = fetch_tournaments()
    print(f"Found {len(events)} tournament rows across all tables.")

    ics_content = build_ics(events)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(ics_content)

    print(f"Written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
