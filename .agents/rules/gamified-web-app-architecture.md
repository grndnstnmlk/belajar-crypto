# Gamified Web App Architecture & Supabase Sync Standards

When building gamified dashboards or single-file web applications:

## 1. Dual-Layer Persistence (LocalStorage + Supabase JSONB)
- **Zero-Latency Updates**: Always update state in `localStorage` immediately for instantaneous, responsive UI transitions.
- **Debounced Cloud Sync**: Pair `localStorage` writes with an automated debounced (300ms–500ms) sync to Supabase.
- **Schema Pattern**:
  ```sql
  create table if not exists public.user_gamification (
    user_id uuid primary key references auth.users(id) on delete cascade,
    rpg_state jsonb not null default '{}'::jsonb,
    quests_state jsonb not null default '{}'::jsonb,
    sim_state jsonb not null default '{}'::jsonb,
    updated_at timestamptz not null default now()
  );

  alter table public.user_gamification enable row level security;

  create policy "User kelola data gamifikasi sendiri"
    on public.user_gamification for all
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);
  ```
- **Cross-Device Continuity**: On authentication (`SIGNED_IN`), query Supabase `user_gamification` to merge cloud state with local storage before rendering UI.

## 2. Mobile-First App-Native Ergonomics
- **Fixed Bottom Navigation**: On mobile screens (`< 768px`), display a fixed bottom navigation bar (`.mobile-bottom-nav`) with icon and text labels for single-thumb switching between primary views.
- **Clearance Padding**: Ensure `<main>` has sufficient bottom padding (`padding-bottom: 84px`) to prevent navigation elements from occluding content.
- **Horizontal Swipe Strips**: For category tabs and module curricula, use `overflow-x: auto; flex-wrap: nowrap; scrollbar-width: none; -webkit-overflow-scrolling: touch;` to save vertical viewport height.
- **Touch Ergonomics**: Interactive targets must have minimum dimensions of 44px and `-webkit-tap-highlight-color: transparent`.

## 3. Zero-Dependency Audio & Canvas Simulation
- **Native Audio Synthesis**: Use the native Web Audio API (`AudioContext`, `OscillatorNode`, `GainNode`) for procedural sound effects (chimes, level-up fanfares, cash sounds, combat alerts) instead of relying on external audio files.
- **Simulation Invariants**: When building trading simulators or interactive sandboxes, provide bulk actions (such as "Close All Positions" or "Claim All Quests") and clear visual confirmation particles.
