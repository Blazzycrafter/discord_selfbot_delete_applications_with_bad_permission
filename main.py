import asyncio
import os
import random
import sys
import time
from typing import Any, Optional

import requests
import segno

import ui
import unifyQrcode
from remote_auth import RemoteAuthClient

API_BASE = "https://discord.com/api/v10"
USER_AGENT = "DiscordAuthorizedAppsCleaner/2.0"
WHITELIST_FILE = "whitelist.txt"
RESULT_FILE = "result.r"

whitelist: list[str] = []
whitelist_desc: list[str] = []

legify_settings = {
    "enabled": True,
    "forced time": 4,
    "random time range": 3,
}

whitelist_settings = {
    "enabled": True,
    "whitelist": whitelist,
}

# Scopes that can add the user to servers / DMs without extra confirmation.
forbidden_permissions = ["guilds.join"]
Global_token: Optional[str] = None


def load_whitelist() -> None:
    whitelist.clear()
    whitelist_desc.clear()
    if not os.path.isfile(WHITELIST_FILE):
        return
    with open(WHITELIST_FILE, "r", encoding="utf-8") as f:
        for line in f.read().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "#" in line:
                client_id, desc = line.split("#", 1)
            else:
                client_id, desc = line, ""
            client_id = client_id.strip()
            desc = desc.strip() or "[NO DESC]"
            if client_id:
                whitelist.append(client_id)
                whitelist_desc.append(desc)


class Permissions:
    @staticmethod
    def list():
        # Official Discord OAuth2 scopes plus commonly seen Social SDK / RPC scopes.
        return [
            "activities.read",
            "activities.write",
            "activities.invites.write",
            "applications.builds.read",
            "applications.builds.upload",
            "applications.commands",
            "applications.commands.update",
            "applications.commands.permissions.update",
            "applications.entitlements",
            "applications.store.update",
            "bot",
            "connections",
            "dm_channels.read",
            "email",
            "gdm.join",
            "guilds",
            "guilds.join",
            "guilds.members.read",
            "identify",
            "identify.premium",
            "messages.read",
            "openid",
            "relationships.read",
            "role_connections.write",
            "rpc",
            "rpc.activities.write",
            "rpc.notifications.read",
            "rpc.screenshare.read",
            "rpc.screenshare.write",
            "rpc.video.read",
            "rpc.video.write",
            "rpc.voice.read",
            "rpc.voice.write",
            "sdk.social_layer",
            "sdk.social_layer_presence",
            "voice",
            "webhook.incoming",
        ]

    @staticmethod
    def category():
        cat = []
        for scope in Permissions.list():
            split = scope.split(".")
            if split[0] not in cat:
                cat.append(split[0])
        return cat

    @staticmethod
    def categorized_list(category):
        ls = []
        if category.lower() == "misc":
            cats = Permissions.category()
            for scope in Permissions.list():
                if scope.split(".")[0] not in cats:
                    ls.append(scope)
        else:
            for scope in Permissions.list():
                if scope.split(".")[0] == category:
                    ls.append(scope)
        return ls


def discord_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": token.strip(),
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }


def discord_request(method: str, path: str, token: str, retries: int = 3) -> requests.Response:
    url = f"{API_BASE}{path}"
    headers = discord_headers(token)
    last_error: Optional[requests.Response] = None
    for attempt in range(retries):
        r = requests.request(method, url, headers=headers, timeout=30)
        if r.status_code == 429:
            retry_after = 1.0
            try:
                retry_after = float(r.json().get("retry_after", r.headers.get("Retry-After", 1)))
            except Exception:
                retry_after = float(r.headers.get("Retry-After", 1) or 1)
            time.sleep(min(max(retry_after, 0.5), 15))
            last_error = r
            continue
        return r
    return last_error if last_error is not None else r


def mask_token(token: str) -> str:
    token = token.strip()
    if len(token) <= 8:
        return "***"
    return f"{token[:4]}...{token[-4:]}"


def app_name(entry: dict[str, Any]) -> str:
    application = entry.get("application") or {}
    return application.get("name") or application.get("id") or entry.get("id") or "unknown"


def delete_connected_apps(token, matches):
    deleted = []
    for i in matches:
        application = i.get("application") or {}
        app_id = str(application.get("id") or "")
        name = app_name(i)
        if is_whitelisted(app_id):
            ui.warn(f"Übersprungen (Whitelist): {name}")
            continue
        r = discord_request("DELETE", f"/oauth2/tokens/{i['id']}", token)
        if r.status_code in (200, 204):
            ui.ok(f"Getrennt: {name}")
            deleted.append(name)
        else:
            ui.err(f"Fehler bei {name} (HTTP {r.status_code})")
        legify()
    return deleted


def check_connected_apps(token):
    r = discord_request("GET", "/oauth2/tokens", token)
    if r.status_code == 401:
        ui.err("Token ungültig.")
        return None
    if r.status_code != 200:
        ui.err(f"Apps konnten nicht geladen werden (HTTP {r.status_code})")
        try:
            print(r.text[:500])
        except Exception:
            pass
        return None
    data = r.json()
    matches = []
    ui.info("Apps mit verbotenen Berechtigungen:")
    print()
    for i in data:
        scopes = i.get("scopes") or []
        if any(x in scopes for x in forbidden_permissions):
            ui.ok(app_name(i))
            ui.info("Scopes: " + ", ".join(scopes))
            print()
            matches.append(i)
    if len(matches) == 0:
        return None
    return matches


def write_end(results):
    with open(RESULT_FILE, "w", encoding="utf-8") as f:
        f.write(results)


def SetPermissions():
    ui.clear()
    scopes = Permissions.list()
    lines = [
        f"  {ui.C.GREEN}grün = verboten{ui.C.RESET}   {ui.C.RED}rot = erlaubt{ui.C.RESET}",
        "",
    ]
    for i, scope in enumerate(scopes, start=1):
        if scope in forbidden_permissions:
            lines.append(f"  {ui.C.GREEN}[{i:>2}]  {scope}{ui.C.RESET}")
        else:
            lines.append(f"  {ui.C.RED}[{i:>2}]  {scope}{ui.C.RESET}")
    lines.append("")
    lines.append(ui.item("0", "Zurück"))
    ui.box("Gefährliche Berechtigungen", lines, "Nummer eingeben, um umzuschalten")
    choice = ui.ask()
    if choice == "0":
        return
    try:
        index = int(choice) - 1
    except ValueError:
        ui.err("Ungültige Auswahl")
        ui.pause()
        SetPermissions()
        return
    if index < 0 or index >= len(scopes):
        ui.err("Ungültige Auswahl")
        ui.pause()
        SetPermissions()
        return
    selected = scopes[index]
    if selected in forbidden_permissions:
        forbidden_permissions.remove(selected)
    else:
        forbidden_permissions.append(selected)
    SetPermissions()


def token_qr():
    c = RemoteAuthClient()

    @c.event("on_fingerprint")
    async def on_fingerprint(data):
        ui.info("QR-Code in der Discord-App scannen")
        ui.info(data)
        print()
        img = segno.make_qr(data)
        img.save("qrcode.png")
        try:
            print(img.terminal(compact=True))
        except TypeError:
            unifyQrcode.unify("qrcode.png")
        print()

    @c.event("on_userdata")
    async def on_userdata(user):
        print()
        ui.ok("QR-Code gescannt")
        ui.info(f"ID: {user.id}")
        ui.info(f"Name: {user.getName()}")
        ui.warn("Bitte auf dem Handy bestätigen …")

    @c.event("on_token")
    async def on_token(token):
        ui.ok("Token empfangen")
        global Global_token
        Global_token = token
        await asyncio.sleep(1.2)
        ui.clear()

    @c.event("on_timeout")
    async def on_timeout(*args, **kwargs):
        ui.err("QR-Login abgelaufen.")

    @c.event("on_cancel")
    async def on_cancel(*args, **kwargs):
        ui.warn("QR-Login abgebrochen.")

    try:
        asyncio.run(c.run())
    except KeyboardInterrupt:
        ui.warn("QR-Login abgebrochen.")
    except Exception as exc:
        ui.err(f"QR-Login fehlgeschlagen: {exc}")
        ui.info("Du kannst den Token auch manuell eintragen.")
        ui.pause()


def menu():
    ui.clear()
    global Global_token
    if Global_token is None:
        token_line = f"  Token   {ui.status(False, 'nicht gesetzt')}"
    else:
        token_line = (
            f"  Token   {ui.status(True, 'gesetzt')}  "
            f"{ui.C.GRAY}({mask_token(Global_token)}){ui.C.RESET}"
        )
    ui.box(
        "Discord Apps Cleaner",
        [
            f"  {ui.C.GRAY}von Blazzycrafter{ui.C.RESET}",
            "",
            token_line,
            "",
            ui.item("1", "Token setzen", "manuell oder per QR"),
            ui.item("2", "Gefährliche Berechtigungen"),
            ui.item("3", "Einstellungen"),
            ui.item("4", "Scan starten"),
            "",
            ui.item("0", "Beenden"),
        ],
        "Zahl eingeben und Enter drücken",
    )
    choice = ui.ask()
    if choice == "1":
        ui.clear()
        ui.box(
            "Token setzen",
            [
                ui.item("1", "Manuell eintragen"),
                ui.item("2", "QR-Code scannen"),
                "",
                ui.item("0", "Zurück"),
            ],
        )
        sub = ui.ask()
        if sub == "1":
            Global_token = ui.ask("Token einfügen") or None
        elif sub == "2":
            ui.clear()
            ui.box("QR-Login", [f"  {ui.C.WHITE}Warte auf Discord …{ui.C.RESET}"])
            token_qr()
    elif choice == "2":
        SetPermissions()
    elif choice == "3":
        options()
    elif choice == "4":
        ui.clear()
        Main(token=Global_token)
        ui.pause()
    elif choice == "0":
        sys.exit(0)


def legify_settings_menu():
    while True:
        ui.clear()
        enabled = legify_settings["enabled"]
        ui.box(
            "Wartezeiten (Legify)",
            [
                ui.item("1", "Legify", "AN" if enabled else "AUS"),
                ui.item("2", "Feste Wartezeit", f"{legify_settings['forced time']} s"),
                ui.item("3", "Zufällige Extra-Zeit", f"0–{legify_settings['random time range']} s"),
                "",
                ui.item("0", "Zurück"),
            ],
        )
        choice = ui.ask()
        if choice == "0":
            break
        elif choice == "1":
            legify_settings["enabled"] = not enabled
        elif choice == "2":
            try:
                legify_settings["forced time"] = int(ui.ask("Sekunden"))
            except ValueError:
                ui.err("Bitte eine Zahl eingeben")
                ui.pause()
        elif choice == "3":
            try:
                legify_settings["random time range"] = int(ui.ask("Maximale Extra-Sekunden"))
            except ValueError:
                ui.err("Bitte eine Zahl eingeben")
                ui.pause()


def whitelist_settings_menu():
    while True:
        ui.clear()
        enabled = whitelist_settings["enabled"]
        ui.box(
            "Whitelist",
            [
                ui.item("1", "Whitelist", "AN" if enabled else "AUS"),
                ui.item("2", "Einträge anzeigen"),
                ui.item("3", "whitelist.txt neu laden"),
                "",
                ui.item("0", "Zurück"),
            ],
        )
        choice = ui.ask()
        if choice == "0":
            break
        elif choice == "1":
            whitelist_settings["enabled"] = not enabled
        elif choice == "2":
            ui.clear()
            if not whitelist:
                lines = [f"  {ui.C.GRAY}(leer){ui.C.RESET}"]
            else:
                lines = [
                    f"  {ui.C.CYAN}{whitelist[i]}{ui.C.RESET}  {ui.C.GRAY}{whitelist_desc[i]}{ui.C.RESET}"
                    for i in range(len(whitelist))
                ]
            ui.box("Whitelist-Einträge", lines)
            ui.pause()
        elif choice == "3":
            load_whitelist()
            ui.ok(f"{len(whitelist)} Einträge geladen")
            ui.pause()


def options():
    while True:
        ui.clear()
        ui.box(
            "Einstellungen",
            [
                ui.item("1", "Wartezeiten (Legify)"),
                ui.item("2", "Whitelist"),
                "",
                ui.item("0", "Zurück"),
            ],
        )
        choice = ui.ask()
        if choice == "0":
            break
        elif choice == "1":
            legify_settings_menu()
        elif choice == "2":
            whitelist_settings_menu()


def is_whitelisted(client_id):
    return whitelist_settings["enabled"] and str(client_id) in whitelist


def legify():
    if not legify_settings["enabled"]:
        return
    delay = max(0, int(legify_settings["forced time"]))
    extra_max = max(0, int(legify_settings["random time range"]))
    extra = random.randint(0, extra_max) if extra_max else 0
    time.sleep(delay + extra)


def Main(token):
    if not token:
        ui.err("Kein Token gesetzt. Zuerst Menüpunkt 1.")
        write_end("none")
        return
    matches = check_connected_apps(token)
    if not matches:
        ui.ok("Keine Treffer. Nichts zu trennen.")
        write_end("none")
        return
    confirm = ui.ask("Diese Apps wirklich trennen? (j/n)")
    if confirm.lower() in ("y", "j", "ja"):
        deleted = delete_connected_apps(token, matches)
        write_end("\n".join(deleted) if deleted else "none")
    else:
        names = [app_name(i) for i in matches]
        write_end("\n".join(names))


def Debug():
    options()
    CID = input("Enter Client ID: ")
    print(f"is whitelisted: {is_whitelisted(CID)}")


DEBUG = False
if __name__ == "__main__":
    ui.setup_console()
    load_whitelist()
    try:
        if not DEBUG:
            while True:
                menu()
        else:
            Debug()
    except KeyboardInterrupt:
        print(f"\n  {ui.C.GRAY}Tschüss.{ui.C.RESET}")
        sys.exit(0)
