-- Migración 002: eventos apuntados por el equipo y votación del MVP.
-- Pégala en SQL Editor > New query > Run (una sola vez, después de schema.sql).

create table public.events (
  jornada     int  not null references public.jornadas,
  player_id   int  not null,
  kind        text not null check (kind in ('asist','amarilla','roja')),
  qty         int  not null check (qty between 0 and 20),
  by_member   uuid not null references public.members on delete cascade,
  updated_at  timestamptz not null default now(),
  primary key (jornada, player_id, kind)
);

create table public.votes (
  jornada     int  not null references public.jornadas,
  voter       uuid not null references public.members on delete cascade,
  first       int  not null,
  second      int  not null,
  third       int  not null,
  updated_at  timestamptz not null default now(),
  primary key (jornada, voter),
  check (first <> second and first <> third and second <> third)
);

alter table public.events enable row level security;
alter table public.votes  enable row level security;

-- Eventos: todos los ven; se apuntan desde el inicio del partido hasta 7 días después,
-- y nadie puede apuntarse los suyos.
create policy events_read on public.events for select to authenticated using (true);
create policy events_insert on public.events for insert to authenticated with check (
  by_member = auth.uid()
  and player_id <> (select m.player_id from public.members m where m.id = auth.uid())
  and now() >= (select j.kickoff from public.jornadas j where j.jornada = events.jornada)
  and now() <  (select j.kickoff + interval '7 days' from public.jornadas j where j.jornada = events.jornada));
create policy events_update on public.events for update to authenticated
  using (player_id <> (select m.player_id from public.members m where m.id = auth.uid())
    and now() >= (select j.kickoff from public.jornadas j where j.jornada = events.jornada)
    and now() <  (select j.kickoff + interval '7 days' from public.jornadas j where j.jornada = events.jornada))
  with check (by_member = auth.uid()
    and player_id <> (select m.player_id from public.members m where m.id = auth.uid()));

-- Votos: secretos hasta que cierra la votación (3 días tras el inicio); no vale votarse.
create policy votes_read on public.votes for select to authenticated using (
  voter = auth.uid()
  or now() >= (select j.kickoff + interval '3 days' from public.jornadas j where j.jornada = votes.jornada));
create policy votes_insert on public.votes for insert to authenticated with check (
  voter = auth.uid()
  and now() >= (select j.kickoff from public.jornadas j where j.jornada = votes.jornada)
  and now() <  (select j.kickoff + interval '3 days' from public.jornadas j where j.jornada = votes.jornada)
  and (select m.player_id from public.members m where m.id = auth.uid()) not in (first, second, third));
create policy votes_update on public.votes for update to authenticated
  using (voter = auth.uid()
    and now() >= (select j.kickoff from public.jornadas j where j.jornada = votes.jornada)
    and now() <  (select j.kickoff + interval '3 days' from public.jornadas j where j.jornada = votes.jornada))
  with check (voter = auth.uid()
    and (select m.player_id from public.members m where m.id = auth.uid()) not in (first, second, third));
