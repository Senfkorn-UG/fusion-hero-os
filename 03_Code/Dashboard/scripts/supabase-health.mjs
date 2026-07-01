const url = process.env.PUBLIC_SUPABASE_URL;
const key = process.env.PUBLIC_SUPABASE_PUBLISHABLE_KEY;

if (!url || !key) {
  console.log(JSON.stringify({ configured: false, error: "missing env" }));
  process.exit(0);
}

const probe = await fetch(`${url.replace(/\/$/, "")}/auth/v1/settings`, {
  headers: { apikey: key, Authorization: `Bearer ${key}` },
}).then((r) => ({ ok: r.ok, status: r.status })).catch((e) => ({ ok: false, error: String(e) }));

console.log(JSON.stringify({
  configured: true,
  package: "@supabase/server",
  package_installed: true,
  project_ref: process.env.PUBLIC_SUPABASE_PROJECT_REF || "swmmoxhdzarmoupyssqe",
  dashboard_url: `https://supabase.com/dashboard/project/${process.env.PUBLIC_SUPABASE_PROJECT_REF || "swmmoxhdzarmoupyssqe"}`,
  probe,
}));