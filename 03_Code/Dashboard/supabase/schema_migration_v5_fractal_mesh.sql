-- Fusion Hero OS — Supabase Schema v5 (Fractal Mainframe Mesh + Virtual Exit Nodes)
-- Nach schema_migration_v4_faden.sql ausführen. Idempotent.

create table if not exists public.fusion_mesh_fractal_manifests (
  tree_hash text primary key,
  device_id text not null,
  anchor_hash text not null,
  slice_count int not null default 0,
  layers jsonb not null default '{}'::jsonb,
  mesh_snapshot jsonb not null default '{}'::jsonb,
  slice_hashes jsonb not null default '[]'::jsonb,
  manifest jsonb not null default '{}'::jsonb,
  ts double precision not null default extract(epoch from now()),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.fusion_mesh_exit_state (
  device_id text primary key,
  active_profile text not null default 'direct',
  resolution jsonb not null default '{}'::jsonb,
  peers jsonb not null default '[]'::jsonb,
  ts double precision not null default extract(epoch from now()),
  updated_at timestamptz not null default now()
);

alter table public.fusion_mesh_fractal_manifests enable row level security;
alter table public.fusion_mesh_exit_state enable row level security;

create policy "fusion_mesh_fractal_manifests_anon_insert" on public.fusion_mesh_fractal_manifests
  for insert to anon with check (true);
create policy "fusion_mesh_fractal_manifests_anon_select" on public.fusion_mesh_fractal_manifests
  for select to anon using (true);
create policy "fusion_mesh_fractal_manifests_anon_update" on public.fusion_mesh_fractal_manifests
  for update to anon using (true);

create policy "fusion_mesh_exit_state_anon_insert" on public.fusion_mesh_exit_state
  for insert to anon with check (true);
create policy "fusion_mesh_exit_state_anon_select" on public.fusion_mesh_exit_state
  for select to anon using (true);
create policy "fusion_mesh_exit_state_anon_update" on public.fusion_mesh_exit_state
  for update to anon using (true);

create index if not exists fusion_mesh_fractal_ts_idx on public.fusion_mesh_fractal_manifests (ts desc);
create index if not exists fusion_mesh_fractal_device_idx on public.fusion_mesh_fractal_manifests (device_id, ts desc);