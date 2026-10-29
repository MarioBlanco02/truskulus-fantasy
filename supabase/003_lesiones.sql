-- Migración 003: lesionados. Un lesionado que no se presenta no resta puntos ni valor de mercado.
-- Pégala en SQL Editor > New query > Run (una sola vez).

create table public.injuries (
  player_id   int  not null,
  since       int  not null,                 -- primera jornada lesionado
  until       int,                           -- última jornada lesionado; null = sigue lesionado
  set_by      uuid references public.members on delete set null,
  created_at  timestamptz not null default now(),
  primary key (player_id, since)
);

alter table public.injuries enable row level security;
create policy injuries_read   on public.injuries for select to authenticated using (true);
create policy injuries_insert on public.injuries for insert to authenticated with check (set_by = auth.uid());
create policy injuries_update on public.injuries for update to authenticated using (true) with check (true);
revoke update on public.injuries from authenticated;
grant  update (until) on public.injuries to authenticated;

-- Arturo, lesionado (desde la J2). Cámbialo desde su ficha en la app si no es correcto.
insert into public.injuries (player_id, since) values (9003, 2);
