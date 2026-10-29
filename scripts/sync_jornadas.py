#!/usr/bin/env python3
"""Sube a Supabase la hora de inicio de cada jornada (tabla jornadas), a partir de data.json.

Si la liga ya publica la hora, se actualiza. Si no, se estima a las 17:00 y no se pisa lo que
hayas corregido a mano en Supabase. Variables: SUPABASE_URL y SUPABASE_SERVICE_KEY.
"""
import json
import os
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

URL, KEY = os.environ["SUPABASE_URL"].rstrip("/"), os.environ["SUPABASE_SERVICE_KEY"]
MADRID = ZoneInfo("Europe/Madrid")


def upsert(rows, merge):
    if not rows:
        return
    req = urllib.request.Request(
        f"{URL}/rest/v1/jornadas?on_conflict=jornada", data=json.dumps(rows).encode(), method="POST",
        headers={"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json",
                 "Prefer": "resolution=" + ("merge-duplicates" if merge else "ignore-duplicates")})
    urllib.request.urlopen(req, timeout=30).read()


def main():
    data = json.load(open("data.json", encoding="utf-8"))
    confirmed, estimated = [], []
    for m in data["partidos"]:
        if m["descansa"]:
            continue
        day = m["fecha"][:10]
        t = datetime.fromisoformat(f"{day}T{m['hora'] or '17:00:00'}").replace(tzinfo=MADRID)
        (confirmed if m["hora"] else estimated).append({"jornada": m["jornada"], "kickoff": t.isoformat()})
    upsert(estimated, merge=False)
    upsert(confirmed, merge=True)
    print(f"{len(confirmed)} jornadas con hora confirmada y {len(estimated)} estimadas")


if __name__ == "__main__":
    main()
