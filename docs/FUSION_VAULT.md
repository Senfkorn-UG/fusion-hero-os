# Fusion Vault — zentraler Secrets-Broker

**Projekt:** `fusion-hero-secrets-vault` (Supabase, org `95guknow's Org`, ref `uszptbmbcwiaesootfwv`, Region eu-central-1)
**Stand:** 2026-07-12

## Prinzip

Kein Agent bekommt je ein rohes, dauerhaftes API-Secret in eine Konfigdatei
oder Umgebungsvariable geschrieben. Stattdessen:

1. Jeder Node (`claude-agent`, `grok-agent`, `kepler-agent`, `gemini-agent`,
   `mainframe-host`, `mobile-node`) hat eine **eigene Identität**
   mit einem individuellen Token, hinterlegt in `~/.fusion_agent_credentials`
   (`chmod 600`, nur auf dem jeweiligen Node).
2. Ein Connector fordert bei Bedarf über `vault_client.py` eine **kurzlebige
   Lease** (Standard 15 Min.) für einen bestimmten Service an.
3. Der Broker (`request_credential()`-Funktion in Postgres) prüft: Token
   korrekt? Existiert ein nicht widerrufener, nicht abgelaufener **Grant**
   für genau diesen Agenten + Service? Nur dann wird das Secret entschlüsselt
   und zurückgegeben — jeder Versuch wird in `credential_audit_log` protokolliert.
4. Ohne gültige Lease bleibt jeder Connector automatisch im **DRY-RUN**
   (`would_execute: false`) — es gibt keinen Fallback auf rohe env-Keys.

Deny-by-default: ein neuer Agent oder Service hat *keinen* Zugriff, bis
explizit ein Grant angelegt wird.

## Ein echtes Secret eintragen

**Nie in den Chat/an ein LLM einfügen.** Selbst im Supabase Studio SQL
Editor ausführen (Projekt `fusion-hero-secrets-vault`):

```sql
select vault.create_secret('DEIN-ECHTER-API-KEY', 'anthropic_key', 'Anthropic API Key');

insert into public.secret_refs (service_key, vault_secret_id)
  select 'anthropic', id from vault.secrets where name = 'anthropic_key'
  on conflict (service_key) do update set vault_secret_id = excluded.vault_secret_id;
```

Verfügbare `service_key`-Werte (Katalog, siehe `select * from public.services;`):
`anthropic`, `openai`, `google_gemini`, `xai_grok`, `openrouter`, `groq`,
`cerebras`, `mistral`, `huggingface`, `github`, `replicate`. Neue Zeile in
`services` einfügen, um einen weiteren Dienst hinzuzufügen.

## Einem Agenten Zugriff geben (Grant)

```sql
insert into public.grants (agent_id, service_key, expires_at)
values ('claude-agent', 'github', null);  -- null = unbefristet, bis widerrufen
```

Befristet (z.B. 24h Testzugriff):

```sql
insert into public.grants (agent_id, service_key, expires_at)
values ('grok-agent', 'openrouter', now() + interval '24 hours');
```

## Zugriff entziehen

```sql
update public.grants set revoked = true
where agent_id = 'grok-agent' and service_key = 'openrouter';
```

Wirkt sofort — der Agent bekommt bei der nächsten Anfrage (spätestens nach
Ablauf der aktuell gecachten Lease, max. 15 Min.) keine neue Lease mehr.

## Audit-Log einsehen

```sql
select * from public.credential_audit_log order by requested_at desc limit 50;
```

## Neuen Agent-Node hinzufügen

```sql
insert into public.agents (agent_id, display_name, tailscale_ip, token_hash)
values ('neuer-node', 'Beschreibung', '100.x.x.x', crypt('LANGES-ZUFALLS-TOKEN', gen_salt('bf')));
```

Das Zufalls-Token danach in `~/.fusion_agent_credentials` auf dem neuen Node
hinterlegen (analog zu den bestehenden sechs) und aus der SQL-Historie
löschen.

## Was NICHT im Vault liegt

- `03_Code/Dashboard`s eigene Supabase-Anbindung (`SUPABASE_PROJECT_REF=swmmoxhdzarmoupyssqe`)
  ist ein separates Projekt (App-Backend, keine Secrets-Verwaltung) — Status
  bei Konsolidierung 2026-07-12 nicht verifizierbar, da `list_projects` für
  die verbundene Org keine Projekte zeigte. Vor Nutzung prüfen.
- `NORMALOS_BRIDGE_TOKEN` (lokaler PC-Bridge-Dienst) bleibt bewusst außerhalb
  des Vaults — rein lokaler Loopback-Dienst, kein externer Provider.
