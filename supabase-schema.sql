-- Jalankan seluruh file ini sekali di Supabase Dashboard > SQL Editor > New query > Run
-- (Kalau tabel profiles/progress sudah ada dari setup sebelumnya, bagian create table akan
-- error "already exists" — itu aman diabaikan, cukup jalankan dari bagian "alter table" ke bawah.)

-- Profil setiap user (nama, status admin, masa aktif), terhubung ke akun auth bawaan Supabase
create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  full_name text not null,
  is_admin boolean not null default false,
  created_at timestamptz not null default now()
);

alter table public.profiles enable row level security;

create policy "User bisa lihat profil sendiri"
  on public.profiles for select
  using (auth.uid() = id);

create policy "Admin bisa lihat semua profil"
  on public.profiles for select
  using (exists (
    select 1 from public.profiles p where p.id = auth.uid() and p.is_admin
  ));

-- Progress belajar per user, per resource (video/playlist/dll)
create table public.progress (
  user_id uuid not null references auth.users(id) on delete cascade,
  resource_id text not null,
  done boolean not null default true,
  updated_at timestamptz not null default now(),
  primary key (user_id, resource_id)
);

alter table public.progress enable row level security;

create policy "User kelola progress sendiri"
  on public.progress for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

-- Kolom masa aktif member. NULL = akses selamanya (dipakai untuk admin / member tanpa batas waktu).
alter table public.profiles add column if not exists expires_at timestamptz;

-- Otomatis buat baris profil setiap kali ada user baru dibuat (lewat dashboard atau admin function)
-- full_name, is_admin, expires_at diambil dari user metadata kalau ada
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.profiles (id, full_name, is_admin, expires_at)
  values (
    new.id,
    coalesce(new.raw_user_meta_data->>'full_name', new.email),
    coalesce((new.raw_user_meta_data->>'is_admin')::boolean, false),
    (new.raw_user_meta_data->>'expires_at')::timestamptz
  );
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();
