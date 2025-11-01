#!/usr/bin/env python3
import json, sys, urllib.request, urllib.error, os
from stashapi.stashapp import StashInterface
from stashapi import log

SCENE_FRAGMENT = """
id
title
stash_ids { endpoint stash_id }
"""

# ---------- HTTP helpers ----------
def http_get_json(url, api_key):
    req = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "X-Api-Key": api_key},
        method="GET",
    )
    with urllib.request.urlopen(req) as r:
        raw = r.read().decode("utf-8", "ignore")
        try:
            return r.status, json.loads(raw)
        except Exception:
            return r.status, raw

def http_post_json(url, body, api_key):
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "X-Api-Key": api_key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read().decode("utf-8", "ignore")
            try:
                return r.status, json.loads(raw)
            except Exception:
                return r.status, raw
    except urllib.error.HTTPError as e:
        raw = (e.read() or b"").decode("utf-8", "ignore")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw

# ---------- plugin config helpers ----------
def pick_plugin_config(stash_config: dict, server_conn: dict) -> dict:
    """Find this plugin's settings dict inside stash_config['plugins']."""
    plugins = (stash_config or {}).get("plugins") or {}
    if not plugins:
        log.error("No plugins section in stash configuration.")
        return {}

    candidates = []
    plugdir = (server_conn or {}).get("PluginDir") or ""
    if plugdir:
        candidates.append(os.path.basename(plugdir.rstrip("/")))

    candidates += [
        "whisparr-bridge",
        "Whisparr Bridge",
        "whisparr_bridge",
        "WhisparrBridge",
        "whisparrbridge",
    ]

    for key in candidates:
        cfg = plugins.get(key)
        if isinstance(cfg, dict) and cfg:
            log.info(f"Using plugin config key: {key}")
            return cfg

    log.info("Available plugin config keys: " + ", ".join(sorted(plugins.keys())))
    return {}

def read_setting(cfg: dict, snake_name: str, default=None):
    """Prefer UPPER_SNAKE (manifest), fallback to camelCase."""
    upper = snake_name.upper()
    parts = snake_name.split("_")
    camel = parts[0] + "".join(p.capitalize() for p in parts[1:])
    return (cfg or {}).get(upper, (cfg or {}).get(camel, default))

# ---------- main ----------
def main():
    STASH_DATA = json.loads(sys.stdin.read())
    ARGS = STASH_DATA.get("args") or {}
    hook = ARGS.get("hookContext") or {}
    scene_id = hook.get("id")
    if not scene_id:
        log.info("No scene id in hook; exit.")
        return

    # Stash API client
    stash = StashInterface(STASH_DATA["server_connection"])

    # Load plugin settings from Stash configuration
    try:
        stash_config = stash.get_configuration()
    except Exception as e:
        log.error(f"get_configuration failed: {e}")
        return

    plugin_cfg = pick_plugin_config(stash_config, STASH_DATA.get("server_connection"))

    whisparr_url = (read_setting(plugin_cfg, "whisparr_url", "") or "").rstrip("/")
    whisparr_key = read_setting(plugin_cfg, "whisparr_api_key", "") or ""
    match_substr = read_setting(plugin_cfg, "stashdb_endpoint_substr", "stashdb.org") or "stashdb.org"
    monitored = str(read_setting(plugin_cfg, "monitored", "false") or "false").lower() == "true"

    if not whisparr_url or not whisparr_key:
        log.error("Missing Whisparr settings (URL/API key).")
        return

    # Fetch scene
    try:
        scene = stash.find_scene(scene_id, fragment=SCENE_FRAGMENT)
    except Exception as e:
        log.error(f"find_scene failed: {e}")
        return

    if not scene:
        log.error(f"Scene {scene_id} not found.")
        return

    title = scene.get("title") or ""
    log.info(f"scene '{title}', id={scene_id}")

    # Extract matching StashDB id
    stashdb_id = None
    for sid in scene.get("stash_ids") or []:
        if match_substr in (sid.get("endpoint") or ""):
            stashdb_id = sid.get("stash_id")
            break

    if not stashdb_id:
        log.info("No matching StashDB id; skip.")
        return

    # Query Whisparr for defaults it requires
    s_qp, qps = http_get_json(f"{whisparr_url}/api/v3/qualityprofile", whisparr_key)
    if s_qp != 200 or not isinstance(qps, list) or not qps:
        log.error(f"Whisparr: cannot load quality profiles: {s_qp} {qps}")
        return
    quality_profile_id = int(qps[0]["id"])

    s_rf, rfs = http_get_json(f"{whisparr_url}/api/v3/rootfolder", whisparr_key)
    if s_rf != 200 or not isinstance(rfs, list) or not rfs:
        log.error(f"Whisparr: cannot load root folders: {s_rf} {rfs}")
        return
    root_folder_path = rfs[0]["path"]

    # Build add payload
    body = {
        "title": title,
        "qualityProfileId": quality_profile_id,
        "rootFolderPath": root_folder_path,
        "monitored": monitored,
        "addOptions": {
            "monitor": "movieOnly" if monitored else "none",
            "searchForMovie": False
        },
        "foreignId": stashdb_id,
        "stashId": stashdb_id
    }

    status, resp = http_post_json(f"{whisparr_url}/api/v3/movie", body, whisparr_key)
    if status in (200, 201):
        log.info(f"Whisparr add OK ({status})")
    elif status == 409:
        log.info("Whisparr: already exists (409)")
    else:
        log.error(f"Whisparr error {status}: {resp}")

if __name__ == "__main__":
    main()

