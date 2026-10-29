-- Fantasy Truskulus FC · esquema de Supabase
-- Pégalo entero en SQL Editor > New query > Run.
-- Antes: Authentication > Providers > Email: desactiva "Confirm email".

create table public.members (
  id          uuid primary key references auth.users on delete cascade,
  player_id   int  not null unique,                       -- userId del jugador en Liga Elite
  pos         text check (pos in ('POR','DEF','MED','DEL')),
  photo       text check (photo is null or length(photo) < 60000),
  created_at  timestamptz not null default now()
);

create table public.jornadas (
  jornada  int primary key,
  kickoff  timestamptz not null                           -- a partir de aquí ya no se puede cambiar el 7
);

create table public.lineups (
  member_id   uuid not null references public.members on delete cascade,
  jornada     int  not null references public.jornadas,
  formation   text not null check (formation in ('2-3-1','3-2-1','2-2-2','3-1-2','1-3-2')),
  slots       int[] not null check (cardinality(slots) = 7),
  captain     int,
  confirmed   boolean not null default false,
  updated_at  timestamptz not null default now(),
  primary key (member_id, jornada)
);

-- Alta automática de la ficha cuando alguien crea su acceso
create function public.handle_new_user() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  insert into public.members (id, player_id) values (new.id, (new.raw_user_meta_data->>'player_id')::int);
  return new;
end $$;
create trigger on_auth_user_created after insert on auth.users
  for each row execute function public.handle_new_user();

-- Qué fichas están ya reclamadas (la pantalla de entrada lo necesita sin sesión)
create function public.claimed_players() returns int[]
language sql security definer stable set search_path = public as
$$ select coalesce(array_agg(player_id), '{}') from public.members $$;
grant execute on function public.claimed_players() to anon, authenticated;

-- Seguridad
alter table public.members  enable row level security;
alter table public.jornadas enable row level security;
alter table public.lineups  enable row level security;

create policy members_read   on public.members  for select to authenticated using (true);
create policy members_update on public.members  for update to authenticated using (id = auth.uid()) with check (id = auth.uid());
revoke update on public.members from authenticated;
grant  update (pos, photo) on public.members to authenticated;

create policy jornadas_read on public.jornadas for select to anon, authenticated using (true);

-- Cada uno escribe su 7 solo antes del inicio; el de los demás se ve cuando empieza el partido
create policy lineups_read on public.lineups for select to authenticated using (
  member_id = auth.uid()
  or now() >= (select j.kickoff from public.jornadas j where j.jornada = lineups.jornada));
create policy lineups_insert on public.lineups for insert to authenticated with check (
  member_id = auth.uid()
  and now() < (select j.kickoff from public.jornadas j where j.jornada = lineups.jornada));
create policy lineups_update on public.lineups for update to authenticated
  using      (member_id = auth.uid() and now() < (select j.kickoff from public.jornadas j where j.jornada = lineups.jornada))
  with check (member_id = auth.uid() and now() < (select j.kickoff from public.jornadas j where j.jornada = lineups.jornada));
