#!/usr/bin/env python3
"""Extrae plantilla, calendario y estadísticas por partido del Truskulus FC desde la API pública de Liga Elite Fútbol.

No requiere credenciales: los datos de equipos, jugadores y actas son públicos.
Uso: python3 scrape.py [salida.json]
"""
import base64
import io
import json
import sys
import urllib.request
from datetime import datetime, timezone

API = "https://api.playooz.com"
TENANT = "www.ligaelitefutbol.com"
EVENT_ID = 302      # Zona Sur Domingo Tarde 2026-2027
TEAM_ID = 1092      # Truskulus FC


def get(path):
    req = urllib.request.Request(API + path, headers={"X-Tenant-Host": TENANT, "Accept-Language": "es"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r)


def image_uri(url, size):
    """Descarga una imagen, la recorta cuadrada y la devuelve como data URI (las URLs firmadas caducan a la hora)."""
    if not url:
        return None
    from PIL import Image
    try:
        with urllib.request.urlopen(url, timeout=40) as r:
            im = Image.open(io.BytesIO(r.read())).convert("RGBA")
    except OSError as e:
        print("imagen no descargada:", e, file=sys.stderr)
        return None
    w, h = im.size
    side = min(w, h)
    im = im.crop(((w - side) // 2, (h - side) // 2, (w - side) // 2 + side, (h - side) // 2 + side)).resize((size, size))
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=82)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()


def logo_uri(url, size=128):
    """Como image_uri, pero sin recortar para conservar la proporción del escudo."""
    if not url:
        return None
    from PIL import Image
    try:
        with urllib.request.urlopen(url, timeout=40) as r:
            im = Image.open(io.BytesIO(r.read())).convert("RGBA")
    except OSError as e:
        print("imagen no descargada:", e, file=sys.stderr)
        return None
    im.thumbnail((size, size))
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=85)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()


def match_row(m):
    return {
        "matchId": m["matchId"], "jornada": m["fixtureNumber"], "fecha": m["date"], "hora": m["start"],
        "campo": m["fieldName"], "local": m["homeName"], "visitante": m["awayName"],
        "localId": m["homeId"], "visitanteId": m["awayId"],
        "esLocal": m["isHome"], "golesLocal": m["scoreHome"], "golesVisitante": m["scoreAway"],
        "descansa": m["isBye"], "estado": m["status"],
    }


def player_events(match_id):
    d = get(f"/match/view/team/{match_id}")
    side = "home" if d["header"]["homeId"] == TEAM_ID else "away"
    mvp = d["header"].get("mvpUserId")
    rows = []
    for p in d["lineUps"][side]["players"]:
        rows.append({
            "userId": p["userId"], "jugo": p["played"], "goles": p["goals"], "asistencias": p["assists"],
            "amarillas": p["cardsYellow"], "rojas": p["cardsRed"], "golesRecibidos": p["goalsReceived"],
            "porteria": p["isKeeper"], "mvp": p["userId"] == mvp,
        })
    return rows


def matches_round(played, pending):
    return (played + pending)[0]["roundId"]


def matches_group(played, pending):
    return (played + pending)[0]["groupId"]


def main(out):
    team = get(f"/team/event/{EVENT_ID}/{TEAM_ID}")
    players = [{
        "userId": p["userId"], "dorsal": p["number"], "nombre": p["name"], "apellido": p["surname"],
        "alias": p["alias"], "posicion": p["positionName"], "portero": p["isKeeper"], "capitan": p["captain"],
        "foto": p["photoUrl"], "partidos": p["played"], "goles": p["goals"], "asistencias": p["assists"],
        "amarillas": p["cardsYellow"], "rojas": p["cardsRed"],
    } for p in team["squad"]["players"]]
    played = team["calendar"]["played"]
    pending = team["calendar"]["pending"]
    matches = [match_row(m) for m in played] + [match_row(m) for m in pending]
    stats = {str(m["matchId"]): player_events(m["matchId"]) for m in played}
    group = get(f"/event/standings/{EVENT_ID}/{matches_round(played, pending)}/{matches_group(played, pending)}")["groups"][0]
    standings = [{"id": t["id"], "nombre": t["name"], "pos": t["pos"], "pts": t["points"], "pj": t["played"], "g": t["won"], "e": t["drawn"],
                  "p": t["lost"], "gf": t["scoreFor"], "gc": t["scoreAgainst"], "racha": t["trayectory"]} for t in group["standings"]]
    logos = {}
    for t in group["standings"]:
        logos[str(t["id"])] = logo_uri(t["logoUrl"])
    logos[str(TEAM_ID)] = logo_uri(team["header"]["logoUrl"])
    fotos = {}
    for p in players:
        pub = get(f"/event-team-player/get/public/{EVENT_ID}/{TEAM_ID}/{p['userId']}")
        fotos[str(p["userId"])] = image_uri(pub.get("photoUrl"), 128)
    for p in players:
        p.pop("foto", None)
    data = {"actualizado": datetime.now(timezone.utc).isoformat(timespec="minutes"), "equipo": team["header"]["name"], "eventoId": EVENT_ID, "equipoId": TEAM_ID,
            "jugadores": players, "partidos": matches, "estadisticas": stats,
            "clasificacion": standings, "grupo": group["groupName"], "escudos": logos, "fotos": fotos}
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"{len(players)} jugadores, {len(matches)} partidos, {len(stats)} actas -> {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data.json")
