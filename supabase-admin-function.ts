// Deploy sebagai Edge Function bernama "admin-actions" di Supabase Dashboard:
// Edge Functions > Create a new function > beri nama "admin-actions" > tempel kode ini > Deploy
//
// Fungsi ini HANYA bisa dipanggil oleh user yang login DAN profiles.is_admin = true.
// Dipakai oleh admin.html untuk membuat, menghapus, mereset password, dan mendaftar user.

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

function json(obj: unknown, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
    const anonKey = Deno.env.get("SUPABASE_ANON_KEY")!;
    const serviceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
    const authHeader = req.headers.get("Authorization") ?? "";

    // Client atas nama pemanggil, untuk verifikasi siapa dia & apakah admin
    const callerClient = createClient(supabaseUrl, anonKey, {
      global: { headers: { Authorization: authHeader } },
    });

    const { data: { user }, error: userErr } = await callerClient.auth.getUser();
    if (userErr || !user) return json({ error: "Belum login" }, 401);

    const { data: profile, error: profileErr } = await callerClient
      .from("profiles")
      .select("is_admin")
      .eq("id", user.id)
      .single();

    if (profileErr || !profile?.is_admin) {
      return json({ error: "Bukan admin, akses ditolak" }, 403);
    }

    // Client service-role, untuk aksi admin sesungguhnya (tidak pernah dikirim ke browser)
    const admin = createClient(supabaseUrl, serviceKey);
    const body = await req.json();

    if (body.action === "list") {
      const { data: profiles, error } = await admin
        .from("profiles")
        .select("id, full_name, is_admin, created_at")
        .order("created_at", { ascending: false });
      if (error) return json({ error: error.message }, 400);

      const { data: authUsers, error: listErr } = await admin.auth.admin.listUsers({ perPage: 1000 });
      if (listErr) return json({ error: listErr.message }, 400);

      const emailById = new Map(authUsers.users.map((u) => [u.id, u.email]));
      const merged = profiles.map((p) => ({ ...p, email: emailById.get(p.id) ?? null }));
      return json({ users: merged });
    }

    if (body.action === "create") {
      const { email, password, full_name } = body;
      if (!email || !password || !full_name) {
        return json({ error: "email, password, dan full_name wajib diisi" }, 400);
      }
      if (String(password).length < 8) {
        return json({ error: "Password minimal 8 karakter" }, 400);
      }
      const { data, error } = await admin.auth.admin.createUser({
        email,
        password,
        email_confirm: true,
        user_metadata: { full_name },
      });
      if (error) return json({ error: error.message }, 400);
      return json({ ok: true, user_id: data.user?.id });
    }

    if (body.action === "reset_password") {
      const { user_id, password } = body;
      if (!user_id || !password) return json({ error: "user_id dan password wajib diisi" }, 400);
      if (String(password).length < 8) return json({ error: "Password minimal 8 karakter" }, 400);
      const { error } = await admin.auth.admin.updateUserById(user_id, { password });
      if (error) return json({ error: error.message }, 400);
      return json({ ok: true });
    }

    if (body.action === "delete") {
      const { user_id } = body;
      if (!user_id) return json({ error: "user_id wajib diisi" }, 400);
      if (user_id === user.id) return json({ error: "Tidak bisa menghapus akun sendiri" }, 400);
      const { error } = await admin.auth.admin.deleteUser(user_id);
      if (error) return json({ error: error.message }, 400);
      return json({ ok: true });
    }

    return json({ error: "Aksi tidak dikenal" }, 400);
  } catch (e) {
    return json({ error: String(e) }, 500);
  }
});
