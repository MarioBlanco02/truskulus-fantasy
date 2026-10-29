# Fantasy Truskulus FC

Fantasy interno del equipo. Los datos salen de Liga Elite Fútbol (API pública, sin credenciales) y cada compañero monta su 7 inicial.

## Cómo funciona

| Pieza | Qué hace |
|---|---|
| `scrape.py` | Descarga plantilla, calendario, clasificación, actas, escudos y fotos → `data.json`. |
| `template.html` + `build.py` | Generan la web (`site/index.html`). Con `SUPABASE_URL` y `SUPABASE_ANON_KEY` activan el modo equipo; sin ellas funciona en local. |
| `supabase/schema.sql` | Tablas y seguridad: fichas, hora de cada jornada y 7 iniciales. |
| `scripts/sync_jornadas.py` | Sube a Supabase la hora de inicio de cada jornada. |
| `.github/workflows/actualizar.yml` | **Cada martes** actualiza los datos y vuelve a publicar la web. También se lanza a mano. |

Reglas del juego: puntos desde la J4, presupuesto de 34 M€, capitán x2, valor de mercado que se mueve tras cada partido. Se cambian al principio de `template.html` (`START_JORNADA`, `BUDGET`, `POINTS`).

## Puesta en marcha (una sola vez)

1. **Supabase**: crea un proyecto en supabase.com (plan gratuito).
   - *Authentication → Providers → Email*: desactiva **Confirm email**.
   - *SQL Editor → New query*: pega `supabase/schema.sql` y pulsa **Run**.
   - *Project Settings → API*: copia la **Project URL**, la clave **anon** y la clave **service_role**.
2. **GitHub**: sube esta carpeta a un repositorio y, en *Settings → Secrets and variables → Actions*, crea:
   - `SUPABASE_URL` (Project URL)
   - `SUPABASE_ANON_KEY` (clave anon, es pública)
   - `SUPABASE_SERVICE_KEY` (clave service_role, **secreta**: solo en GitHub, nunca en el código ni en el chat)
3. *Settings → Pages → Source*: **GitHub Actions**.
4. *Actions → Actualizar y publicar → Run workflow*. Al acabar, la URL de la web aparece en el despliegue.
5. Comparte la URL por WhatsApp. Cada jugador elige su ficha y crea un PIN de 4 cifras.

## Qué ocurre cada martes

El flujo descarga las actas del domingo, recalcula puntos y valores, guarda la hora de las próximas jornadas en Supabase y publica la web. Si quieres cambiar el día, edita el `cron` del workflow.

## Límites conocidos

- El PIN protege contra despistes, no contra alguien decidido: es un juego entre amigos.
- El presupuesto y la formación se validan en la web, no en el servidor. El cierre del 7 al inicio del partido sí se valida en el servidor.
- El 7 de los demás no se ve hasta que empieza el partido.
- Las posiciones las elige cada jugador en su ficha. Hasta entonces se usan las provisionales de `DEFPOS`.
- Si la liga cambia su API, `scrape.py` puede dejar de funcionar.
