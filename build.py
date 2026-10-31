#!/usr/bin/env python3
"""Genera index.html insertando data.json y, si existen SUPABASE_URL y SUPABASE_ANON_KEY, la conexión a Supabase."""
import json
import os

tpl = open("template.html", encoding="utf-8").read()
data = json.dumps(json.load(open("data.json", encoding="utf-8")), ensure_ascii=False, separators=(",", ":"))
url, key = os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_ANON_KEY")
cfg = json.dumps({"url": url, "key": key}) if url and key else "null"
lib = ('<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/supabase.min.js"></script>'
       if cfg != "null" else "")
html = tpl.replace("/*DATA*/", data).replace("/*CONFIG*/", cfg).replace("<!--SUPABASE_SCRIPT-->", lib)
open("index.html", "w", encoding="utf-8").write(html)   # versión para el Artifact (sin envoltorio)

# Versión autónoma para publicar en una web (GitHub Pages)
os.makedirs("site", exist_ok=True)
page = ('<!doctype html><html lang="es"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<meta name="theme-color" content="#07120d">' + html + "</html>")
open("site/index.html", "w", encoding="utf-8").write(page)
# Versión sin servidor (solo para generar la publicación semanal desde la automatización; no se publica)
os.makedirs("site-local", exist_ok=True)
local = tpl.replace("/*DATA*/", data).replace("/*CONFIG*/", "null").replace("<!--SUPABASE_SCRIPT-->", "")
open("site-local/index.html", "w", encoding="utf-8").write('<!doctype html><html lang="es"><head><meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">' + local + "</html>")
print("index.html y site/index.html generados", "con Supabase" if lib else "en modo local")
