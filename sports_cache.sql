-- Portal del Conductor · Deportes: tabla de caché de la función «deportes».
-- Pégalo en Supabase -> SQL Editor -> Run. Se puede ejecutar más de una vez sin problema.
create table if not exists public.sports_cache (
  key        text primary key,
  payload    jsonb       not null default '{}'::jsonb,
  fetched_at timestamptz not null default now(),
  ttl_s      integer     not null default 3600
);

-- Solo la función (con su clave interna de servicio) puede leer y escribir aquí.
-- La app, que usa la clave publicable, no tiene ningún permiso sobre esta tabla.
alter table public.sports_cache enable row level security;
revoke all on public.sports_cache from anon, authenticated;
