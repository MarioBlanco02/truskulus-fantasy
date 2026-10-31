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

Reglas del juego: puntos desde la J4, presupuesto = coste medio de 7 jugadores +5 % (se recalcula con el mercado), capitán x2, valor de mercado que se mueve tras cada partido. Se cambian al principio de `template.html` (`START_JORNADA`, `BUDGET`, `POINTS`).

## Eventos y votación MVP

- **Apuntar eventos** (Ranking → Jornadas): asistencias y tarjetas las apunta el equipo; los goles vienen del acta. Nadie puede apuntarse los suyos. Lo apuntado sustituye al dato de la liga.
- **Votación MVP** (Ranking → Jornadas): quien jugó vota a los 3 mejores (3, 2 y 1 puntos). El más votado suma +3, el 2.º +2 y el 3.º +1. Los votos son secretos hasta que cierra la votación, 3 días después del inicio del partido.
- Requiere ejecutar `supabase/002_eventos_y_votos.sql` una vez en el editor SQL.

## Cartas

Cada jornada, los 2 mejores (o el 1 que supere 6 puntos) reciben una carta con su foto, valoración y estadísticas. Se calculan en la propia app con las actas y los votos, así que aparecen solas tras la actualización del martes. Se ven en Inicio y en Ranking → Jornadas, y se pueden compartir como imagen.

La edición cambia sola según la fecha del partido: **IF** (dorada), **Halloween** (24 oct – 1 nov) y **Navidad** (1 dic – 6 ene). Al terminar la temporada aparece el **Equipo de la temporada**: los 7 con más puntos del fantasy, con una carta azul especial. Quien consigue carta recibe además una prima en su valor de mercado (+0,5 M€ el 1.º y +0,3 M€ el 2.º) y una etiqueta de carta especial en el Mercado hasta el siguiente partido. Todos empiezan con media 80 y ganan 1 punto de media por cada carta; la carta de esa jornada ya muestra el punto nuevo, y la ficha del jugador guarda todas sus cartas. Los diseños son propios, no usan material oficial de ningún juego. Se editan en `EDITIONS` y `cardImage()` de `template.html`.

## Posiciones y lesionados

- **Posiciones:** cada jugador tiene 1 o 2 posiciones (`POSICIONES` en `template.html`). El lateral juega de defensa o de interior por la banda, y el extremo de delantero o de interior. La posición cuenta según el hueco: gol de defensa +2 extra, de portero +4 extra, y portería a cero (2 goles o menos encajados) +3 si va de portero o defensa. Con el portero lesionado, de portero puede ir cualquier jugador de campo. Los jugadores que aún no salen en Liga Elite se añaden a mano en `EXTRAS` (`template.html`); cuando la liga los publique se usan sus datos reales.
- **Lesionados:** cualquier compañero marca a un jugador como lesionado desde su ficha. Si no se presenta, no resta puntos ni valor de mercado, y no se puede elegir. Requiere ejecutar `supabase/003_lesiones.sql` una vez.

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
