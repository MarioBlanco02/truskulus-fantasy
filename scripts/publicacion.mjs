// Genera la publicación de Instagram de la última jornada con votación cerrada:
// una imagen por carta, una con las dos juntas y el texto. Sin servidor, usa data.json; con Supabase añade eventos, votos y lesiones.
import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";

const OUT = process.env.OUT_DIR || "publicacion";
const URL_SB = (process.env.SUPABASE_URL || "").replace(/\/$/, "");
const KEY = process.env.SUPABASE_SERVICE_KEY || "";
fs.mkdirSync(OUT, { recursive: true });

async function tabla(nombre, cols) {
  if (!URL_SB || !KEY) return [];
  const r = await fetch(`${URL_SB}/rest/v1/${nombre}?select=${cols}`, { headers: { apikey: KEY, Authorization: `Bearer ${KEY}` } });
  if (!r.ok) throw new Error(`${nombre}: ${r.status}`);
  return r.json();
}

const [events, votes, injuries, jornadas] = await Promise.all([
  tabla("events", "jornada,player_id,kind,qty,by_member"),
  tabla("votes", "jornada,voter,first,second,third"),
  tabla("injuries", "player_id,since,until"),
  tabla("jornadas", "jornada,kickoff"),
]);

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 420, height: 900 } });
page.on("pageerror", (e) => console.error("error en la página:", e.message));
await page.goto("file://" + path.resolve("site-local/index.html"));
await page.waitForFunction(() => typeof compute === "function" && document.getElementById("app").innerHTML.length > 0);

const resultado = await page.evaluate(async ({ events, votes, injuries, jornadas }) => {
  CLOUD = true;                                            // activa el plazo real de la votación
  if (events.length) EVENTS = events;
  VOTES = votes;
  if (injuries.length) INJ = injuries;
  JK = {}; jornadas.forEach((j) => { JK[j.jornada] = new Date(j.kickoff).getTime(); });
  compute();
  const cerradas = PLAYED.map((m) => m.jornada).filter((j) => votesClosed(j) && bestOfRound(j).length);
  if (!cerradas.length) return null;
  const j = cerradas[cerradas.length - 1], mejores = bestOfRound(j), out = { jornada: j, edicion: editionFor(j).label, archivos: {} };
  out.texto = instaCaption(j);
  out.archivos[`instagram-J${j}-las-dos.png`] = (await instaImage(j)).url;
  for (const r of mejores) out.archivos[`instagram-${norm(r.p.n).replace(/\W+/g, "-")}-J${j}.png`] = (await cardPost(r, j)).url;
  return out;
}, { events, votes, injuries, jornadas });
await browser.close();

if (!resultado) { console.log("No hay cartas que publicar todavía."); process.exit(0); }
for (const [nombre, url] of Object.entries(resultado.archivos)) fs.writeFileSync(path.join(OUT, nombre), Buffer.from(url.split(",")[1], "base64"));
fs.writeFileSync(path.join(OUT, `texto-J${resultado.jornada}.txt`), resultado.texto);
fs.writeFileSync(path.join(OUT, "jornada.txt"), String(resultado.jornada));
fs.writeFileSync(path.join(OUT, "edicion.txt"), resultado.edicion);
console.log(`Publicación de la jornada ${resultado.jornada} (${resultado.edicion}) → ${OUT}`);
