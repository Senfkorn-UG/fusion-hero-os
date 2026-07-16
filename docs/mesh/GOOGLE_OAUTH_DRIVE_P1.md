# P1 — Google OAuth für Drive-API

**Ist:** Drive-Ordner + Documents-Mirror + MCP (create_folder/search/read).  
**Fehlt:** programmatischer Upload/List mit `~/.fusion/google-oauth/`.

## Setup (Operator)

1. Google Cloud Console → OAuth Client (Desktop)  
2. JSON speichern als:

```
%USERPROFILE%\.fusion\google-oauth\credentials.json
```

3. Optional env:

```
GOOGLE_OAUTH_CREDENTIALS=%USERPROFILE%\.fusion\google-oauth\credentials.json
```

4. Connector-Scopes (siehe `src/normal_os/connectors/google_oauth.py`):

- `drive.file` / `drive.readonly` nach Bedarf  

5. Einmal-Flow (Browser Chrome personal / 5TB-Konto):

```powershell
# wenn Connector-CLI vorhanden:
python -c "from src.normal_os.connectors.google_oauth import oauth_status; print(oauth_status())"
```

## Nach Login

- Token: `~/.fusion/google-oauth/token.json`  
- Sicherung: Snapshots programmatisch nach `Fusion_Hero_OS_Sicherung/snapshots`  

**Policy:** credentials nie committen · freemium=false  
