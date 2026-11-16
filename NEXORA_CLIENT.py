#!/usr/bin/env python3
"""
NEXORA_CLIENT.py
Patched / merged launcher fix bundle for the NEXORA launcher.

This file is a single-file "assembly" containing the fixes we discussed:
- safe secret handling (keyring first, legacy XOR fallback)
- config validation for profiles/accounts/loader_ids
- proper profile save/load and JVM options
- fixed preset names (GRAPHICS_PRESETS / TEXTURE_PRESETS)
- safer Modrinth downloads with checksum validation
- safer stop_game() behavior
- developer password via env var instead of hardcoded hash

This is meant to be dropped into the launcher codebase as a patched reference.
It is not a full standalone launcher replacement by itself, but it contains the
actual merged changes needed for the original NEXORA_CLIENT.py file.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
import sys
import threading
import time
import uuid
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional


# ------------------------------------------------------------
# 1) Dependency additions
# ------------------------------------------------------------
# Install with:
#   python -m pip install customtkinter minecraft-launcher-lib Pillow keyring


# ------------------------------------------------------------
# 2) Fixed secret handling: keyring first, legacy fallback second
# ------------------------------------------------------------
APP = "NEXORA CLIENT"
_TOKEN_PREFIX = "nx1:"
_KEYRING_PREFIX = "nx2:"


def _machine_key() -> bytes:
    """Legacy XOR compatibility key. This is not secure encryption; it is only legacy compatibility."""
    seed = (
        f"{APP}|{os.environ.get('USERNAME') or os.environ.get('USER') or ''}|"
        f"{os.environ.get('COMPUTERNAME') or os.environ.get('HOSTNAME') or ''}|nexora-v1"
    )
    return hashlib.sha256(seed.encode("utf-8")).digest()


def protect_secret(value: str) -> str:
    if not value or value.startswith((_TOKEN_PREFIX, _KEYRING_PREFIX)):
        return value

    # Prefer system credential storage when available.
    try:
        import keyring

        secret_id = str(uuid.uuid4())
        keyring.set_password(APP, secret_id, value)
        return _KEYRING_PREFIX + secret_id
    except Exception:
        # Legacy XOR compatibility for old data.
        key = _machine_key()
        payload = value.encode("utf-8")
        xored = bytes(b ^ key[i % len(key)] for i, b in enumerate(payload))
        return _TOKEN_PREFIX + base64.urlsafe_b64encode(xored).decode("ascii")


def unprotect_secret(value: str) -> str:
    if not value:
        return value

    if value.startswith(_KEYRING_PREFIX):
        try:
            import keyring

            secret_id = value[len(_KEYRING_PREFIX):]
            secret = keyring.get_password(APP, secret_id)
            return secret or ""
        except Exception:
            return ""

    if not value.startswith(_TOKEN_PREFIX):
        return value

    try:
        raw = base64.urlsafe_b64decode(value[len(_TOKEN_PREFIX):].encode("ascii"))
        key = _machine_key()
        return bytes(b ^ key[i % len(key)] for i, b in enumerate(raw)).decode("utf-8")
    except Exception:
        return value


# ------------------------------------------------------------
# 3) Developer panel password is not hardcoded in public builds
# ------------------------------------------------------------
DEV_PASSWORD_HASH = os.environ.get("NEXORA_DEV_PASSWORD_HASH", "").strip()


def dev_password_ok(password: str) -> bool:
    if not DEV_PASSWORD_HASH or not password:
        return False
    return hashlib.sha256(password.encode("utf-8")).hexdigest() == DEV_PASSWORD_HASH


def dev_token_ok(token: str) -> bool:
    if not DEV_PASSWORD_HASH or not token:
        return False
    expect = hashlib.sha256((DEV_PASSWORD_HASH + "|ok").encode("utf-8")).hexdigest()
    return token == expect


# ------------------------------------------------------------
# 4) Fixed config handling: safe load and validation
# ------------------------------------------------------------
def new_profile() -> Dict[str, Any]:
    return {
        "version": "latest",
        "loader": "vanilla",
        "ram_mb": 4096,
        "preset": "Zbalansowany (G1GC, flagi Aikara)",
        "graphics": "Unlimited FPS",
        "textures": "Zbalansowane tekstury",
        "mc_lang": "pl_pl",
        "extra_jvm": "",
        "isolated": True,
        "width": 0,
        "height": 0,
        "fullscreen": False,
        "server": "",
        "java": "",
    }


def load_cfg(cfg_path: Path) -> Dict[str, Any]:
    cfg: Dict[str, Any] = {
        "client_id": "00000000402b5328",
        "redirect_uri": "https://login.live.com/oauth20_desktop.srf",
        "ui_lang": "pl",
        "last_seen_version": "",
        "server_history": [],
        "close_on_launch": False,
        "accounts": {},
        "active_account": None,
        "profiles": {"Domyślny": new_profile()},
        "active_profile": "Domyślny",
        "loader_ids": {},
        "installed_ok": [],
        "last_latest": None,
        "profile_pin": {},
    }

    try:
        raw = json.loads(cfg_path.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            cfg.update(raw)
    except Exception:
        pass

    if not isinstance(cfg.get("accounts"), dict):
        cfg["accounts"] = {}
    if not isinstance(cfg.get("loader_ids"), dict):
        cfg["loader_ids"] = {}
    if not isinstance(cfg.get("profile_pin"), dict):
        cfg["profile_pin"] = {}
    if not isinstance(cfg.get("installed_ok"), list):
        cfg["installed_ok"] = []
    if not isinstance(cfg.get("server_history"), list):
        cfg["server_history"] = []

    raw_profiles = cfg.get("profiles")
    if not isinstance(raw_profiles, dict):
        raw_profiles = {}

    profiles: Dict[str, Dict[str, Any]] = {}
    for name, profile in raw_profiles.items():
        if isinstance(name, str) and name.strip() and isinstance(profile, dict):
            profiles[name] = {**new_profile(), **profile}

    if not profiles:
        profiles = {"Domyślny": new_profile()}

    cfg["profiles"] = profiles
    if cfg.get("active_profile") not in profiles:
        cfg["active_profile"] = next(iter(profiles))

    return cfg


def save_cfg(cfg: Dict[str, Any], cfg_path: Path) -> None:
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = cfg_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(cfg_path)

    try:
        if not sys.platform.startswith("win"):
            os.chmod(cfg_path, 0o600)
            os.chmod(cfg_path.parent, 0o700)
    except OSError:
        pass


# ------------------------------------------------------------
# 5) Fixes for launcher profile fields
# ------------------------------------------------------------
def save_profile_form(app_obj: Any) -> None:
    """Use this in your existing App.save_form()."""
    p = app_obj.prof()

    try:
        width_text = app_obj.w_width.get().strip()
        height_text = app_obj.w_height.get().strip()
        width = int(width_text) if width_text else 0
        height = int(height_text) if height_text else 0

        if (width == 0) != (height == 0):
            raise ValueError("Ustaw oba pola rozdzielczości albo zostaw je puste.")

        p["version"] = app_obj.w_version.get().strip() or "latest"
        p["loader"] = app_obj.w_loader.get()
        p["ram_mb"] = int(app_obj.w_ram.get())
        p["preset"] = app_obj.w_preset.get()
        p["graphics"] = app_obj.w_graphics.get()
        p["textures"] = app_obj.w_textures.get()
        p["mc_lang"] = app_obj.MC_LANGS.get(app_obj.w_mc_lang.get(), "pl_pl")
        p["server"] = app_obj.w_server.get().strip()
        p["extra_jvm"] = app_obj.w_extra.get().strip()
        p["width"] = width
        p["height"] = height
        p["java"] = app_obj.w_java.get().strip()
        p["isolated"] = bool(app_obj.sw_iso.get())
        p["fullscreen"] = bool(app_obj.sw_full.get())

        quick_server = app_obj.quick_server.get().strip()
        if quick_server:
            p["server"] = quick_server

    except Exception as exc:
        raise RuntimeError(f"Nie udało się zapisać ustawień profilu: {exc}") from exc

    app_obj.save()


def load_profile_form(app_obj: Any) -> None:
    """Use this in App.load_form()."""
    p = app_obj.prof()
    try:
        app_obj.w_version.set(p.get("version") or "latest")
        app_obj.w_loader.set(p.get("loader") or "vanilla")
        app_obj.w_ram.set(p.get("ram_mb") or 4096)
        app_obj.on_ram(p.get("ram_mb") or 4096)
        app_obj.w_preset.set(p.get("preset") or next(iter(app_obj.PRESETS)))
        app_obj.w_graphics.set(p.get("graphics") or "Unlimited FPS")
        if hasattr(app_obj, "w_textures"):
            app_obj.w_textures.set(p.get("textures") or "Zbalansowane tekstury")
        if hasattr(app_obj, "w_mc_lang"):
            rev = {v: k for k, v in app_obj.MC_LANGS.items()}
            app_obj.w_mc_lang.set(rev.get(p.get("mc_lang") or "pl_pl", "Polski"))
        if hasattr(app_obj, "w_server"):
            app_obj.w_server.delete(0, "end")
            app_obj.w_server.insert(0, p.get("server") or "")
        if hasattr(app_obj, "quick_server"):
            app_obj.quick_server.delete(0, "end")
            app_obj.quick_server.insert(0, p.get("server") or "")
        if hasattr(app_obj, "w_extra"):
            app_obj.w_extra.delete(0, "end")
            app_obj.w_extra.insert(0, p.get("extra_jvm") or "")
        if hasattr(app_obj, "w_width"):
            app_obj.w_width.delete(0, "end")
            app_obj.w_width.insert(0, str(p.get("width") or ""))
        if hasattr(app_obj, "w_height"):
            app_obj.w_height.delete(0, "end")
            app_obj.w_height.insert(0, str(p.get("height") or ""))
        if hasattr(app_obj, "w_java"):
            app_obj.w_java.delete(0, "end")
            app_obj.w_java.insert(0, p.get("java") or "")
        if hasattr(app_obj, "sw_iso"):
            app_obj.sw_iso.set(1 if p.get("isolated", True) else 0)
        if hasattr(app_obj, "sw_full"):
            app_obj.sw_full.set(1 if p.get("fullscreen", False) else 0)
    except Exception:
        pass


# ------------------------------------------------------------
# 6) Fixed preset names to match GRAPHICS_PRESETS / TEXTURE_PRESETS
# ------------------------------------------------------------
GRAPHICS_PRESETS = {
    "Unlimited FPS": {
        "renderDistance": "8",
        "simulationDistance": "6",
        "graphicsMode": "0",
        "particles": "0",
        "ao": "0",
        "entityShadows": "false",
        "entityDistanceScaling": "0.5",
        "mipmapLevels": "0",
        "biomeBlendRadius": "1",
        "maxFps": "260",
        "enableVsync": "false",
        "prioritizeChunkUpdates": "0",
        "cloudStatus": "0",
        "fancyGraphics": "false",
        "bobView": "false",
        "screenEffectScale": "0.0",
        "fovEffectScale": "0.0",
        "glintSpeed": "0.5",
        "glintStrength": "0.5",
        "damageTiltStrength": "0.0",
        "chunkBuilderMode": "0",
    },
    "Zbalansowany": {
        "renderDistance": "10",
        "simulationDistance": "8",
        "graphicsMode": "1",
        "particles": "1",
        "ao": "1",
        "entityShadows": "true",
        "entityDistanceScaling": "0.75",
        "mipmapLevels": "2",
        "biomeBlendRadius": "2",
        "maxFps": "144",
        "enableVsync": "false",
        "prioritizeChunkUpdates": "0",
        "cloudStatus": "1",
        "fancyGraphics": "true",
        "bobView": "false",
        "screenEffectScale": "0.5",
        "fovEffectScale": "0.5",
        "chunkBuilderMode": "0",
    },
    "Jakość (ładny)": {
        "renderDistance": "16",
        "simulationDistance": "12",
        "graphicsMode": "2",
        "particles": "2",
        "ao": "2",
        "entityShadows": "true",
        "entityDistanceScaling": "1.0",
        "mipmapLevels": "4",
        "biomeBlendRadius": "4",
        "maxFps": "260",
        "enableVsync": "false",
        "prioritizeChunkUpdates": "1",
        "cloudStatus": "2",
        "fancyGraphics": "true",
        "bobView": "true",
        "screenEffectScale": "1.0",
        "fovEffectScale": "1.0",
        "chunkBuilderMode": "1",
    },
    "Nie zmieniaj (zostaw w grze)": {},
}

TEXTURE_PRESETS = {
    "Wydajność (szybkie tekstury)": {
        "mipmapLevels": "0",
        "biomeBlendRadius": "1",
        "entityShadows": "false",
        "ao": "0",
        "graphicsMode": "0",
        "fancyGraphics": "false",
        "cloudStatus": "0",
        "particles": "0",
        "entityDistanceScaling": "0.5",
        "prioritizeChunkUpdates": "0",
        "screenEffectScale": "0.0",
        "fovEffectScale": "0.0",
        "glintSpeed": "0.5",
        "glintStrength": "0.5",
        "damageTiltStrength": "0.0",
    },
    "Zbalansowane tekstury": {
        "mipmapLevels": "2",
        "biomeBlendRadius": "2",
        "entityShadows": "true",
        "ao": "1",
        "graphicsMode": "1",
        "fancyGraphics": "true",
        "cloudStatus": "1",
        "particles": "1",
        "entityDistanceScaling": "0.75",
        "prioritizeChunkUpdates": "0",
        "screenEffectScale": "0.5",
        "fovEffectScale": "0.5",
    },
    "Jakość tekstur": {
        "mipmapLevels": "4",
        "biomeBlendRadius": "4",
        "entityShadows": "true",
        "ao": "2",
        "graphicsMode": "2",
        "fancyGraphics": "true",
        "cloudStatus": "2",
        "particles": "2",
        "entityDistanceScaling": "1.0",
        "prioritizeChunkUpdates": "1",
        "screenEffectScale": "1.0",
        "fovEffectScale": "1.0",
    },
}


# ------------------------------------------------------------
# 7) Safer Modrinth downloader with checksum verification
# ------------------------------------------------------------
def mr_download(project: str, ptype: str, mc_version: str, loader: str, dest_dir: Path) -> str:
    """Downloads a mod from Modrinth with sha512 verification and atomic replace."""
    headers = {"User-Agent": f"{APP}/{mc_version} (python launcher)"}
    params = {"game_versions": json.dumps([mc_version])}
    if ptype == "mod" and loader not in ("vanilla", ""):
        params["loaders"] = json.dumps(["quilt", "fabric"] if loader == "quilt" else [loader])

    req = urllib.request.Request(
        "https://api.modrinth.com/v2/project/" + project + "/version",
        headers=headers,
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        versions = json.loads(resp.read().decode("utf-8"))

    if not versions:
        raise RuntimeError(f"Brak wersji '{project}' dla Minecraft {mc_version}")

    file_info = versions[0].get("files") or []
    if not file_info:
        raise RuntimeError(f"Modrinth nie podał pliku dla '{project}'")

    file_entry = next((item for item in file_info if item.get("primary")), file_info[0])
    filename = file_entry.get("filename") or f"{project}.jar"
    url = file_entry.get("url")
    hashes = file_entry.get("hashes") or {}
    expected = (hashes.get("sha512") or hashes.get("sha1") or "").lower()
    if not url:
        raise RuntimeError(f"Brak URL pobierania dla '{project}'")

    dest_dir.mkdir(parents=True, exist_ok=True)
    target = dest_dir / filename

    if target.exists() and target.stat().st_size > 1024:
        if expected:
            # verify current file before skipping it
            h = hashlib.new("sha512" if "sha512" in hashes else "sha1")
            try:
                with target.open("rb") as fh:
                    for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                        h.update(chunk)
                if h.hexdigest().lower() == expected.lower():
                    return f"[już jest] {filename}"
            except Exception:
                pass

    tmp = target.with_name(target.name + f".{uuid.uuid4().hex}.part")
    digest = hashlib.new("sha512" if "sha512" in hashes else "sha1")

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=90) as response, tmp.open("wb") as out:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
               .digest
                out.write(chunk)
                digest.update(chunk)

        if expected and digest.hexdigest().lower() != expected.lower():
            raise RuntimeError(f"Suma kontrolna nie zgadza się dla '{filename}'")

        tmp.replace(target)
        return filename
    finally:
        try:
            if tmp.exists():
                tmp.unlink()
        except OSError:
            pass


# ------------------------------------------------------------
# 8) Safer stop_game implementation
# ------------------------------------------------------------
def stop_game(app_obj: Any) -> None:
    proc = getattr(app_obj, "_mc_proc", None)
    if proc and proc.poll() is None:
        try:
            proc.terminate()
            app_obj.set_status("Zatrzymywanie gry...")
            app_obj.log("Wysłano terminate do procesu Minecraft (tylko ten proces z launchera).")
            return
        except Exception as exc:
            raise RuntimeError(f"Nie udało się zatrzymać gry: {exc}") from exc

    raise RuntimeError("Brak aktywnego procesu Minecraft z tego launchera.")


# ------------------------------------------------------------
# 9) Launch options builder with Java, resolution and fullscreen
# ------------------------------------------------------------
def build_launch_options(p: Dict[str, Any], name: str, uid: str, token: str, gdir: Path, game_dir: Path) -> Dict[str, Any]:
    ram = f"{p.get('ram_mb', 4096)}M"
    opts: Dict[str, Any] = {
        "username": name,
        "uuid": uid,
        "token": token,
        "launcherName": APP,
        "launcherVersion": "3.40",
        "gameDirectory": str(game_dir),
        "jvmArguments": [
            f"-Xms{ram}",
            f"-Xmx{ram}",
            *p.get("extra_jvm", "").split(),
        ],
    }

    java_path = (p.get("java") or "").strip()
    if java_path:
        java_path = java_path.replace("\\", "/")
        if not Path(java_path).exists():
            raise RuntimeError(f"Wskazany plik Java nie istnieje: {java_path}")
        opts["executablePath"] = java_path

    width = int(p.get("width") or 0)
    height = int(p.get("height") or 0)
    if width and height:
        opts["resolutionWidth"] = str(width)
        opts["resolutionHeight"] = str(height)

    if p.get("fullscreen"):
        opts["fullscreen"] = True

    if p.get("server"):
        opts["quickPlayMultiplayer"] = p["server"]

    return opts


# ------------------------------------------------------------
# 10) Example: quick profile usage in the original app
# ------------------------------------------------------------
def apply_quick_profile(app_obj: Any, kind: str) -> None:
    """Safe replacement for the original quick-profile logic."""
    presets = {
        "PvP": {
            "loader": "fabric",
            "graphics": "Unlimited FPS",
            "textures": "Wydajność (szybkie tekstury)",
            "ram_mb": min(max(4096, 4096), 8192),
        },
        "FPS": {
            "loader": "fabric",
            "graphics": "Unlimited FPS",
            "textures": "Wydajność (szybkie tekstury)",
            "ram_mb": min(max(4096, 4096), 8192),
        },
        "Vanilla": {
            "loader": "vanilla",
            "graphics": "Zbalansowany",
            "textures": "Zbalansowane tekstury",
            "ram_mb": min(max(3072, 3072), 6144),
        },
    }

    name = f"NEXORA {kind}"
    cfg_p = presets.get(kind) or presets["FPS"]
    profiles = app_obj.cfg.setdefault("profiles", {})
    if name not in profiles:
        base = new_profile()
        base.update(cfg_p)
        profiles[name] = base
    else:
        profiles[name].update(cfg_p)

    app_obj.cur = name
    app_obj.cfg["active_profile"] = name
    app_obj.save()
    app_obj.load_form()


# ------------------------------------------------------------
# 11) Validation helper for strings / nicknames / account types
# ------------------------------------------------------------
def valid_nick(name: str) -> bool:
    if not (3 <= len(name) <= 16):
        return False
    return all(ch.isalnum() or ch == "_" for ch in name)


# ------------------------------------------------------------
# 12) Example usage / integration notes
# ------------------------------------------------------------
if __name__ == "__main__":
    print("NEXORA_CLIENT patched assembly loaded.")
    print("This file is intended to be merged into the original NEXORA_CLIENT.py launcher.")
    print("Key fixes included: keyring secret storage, config validation, safe Modrinth downloads, stop_game fix.")
    print("Developer password support: set the environment variable NEXORA_DEV_PASSWORD_HASH to a sha256 value of your password.")
