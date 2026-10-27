# Discord Application Permission Deleter

Python-Skript zum Widerrufen autorisierter Discord-Anwendungen mit definierten verbotenen OAuth2-Scopes.

Nutzt Discord API **v10** und die aktuelle Scope-Liste (inkl. Social SDK / RPC).

Automatisierung eines Nutzerkontos verstößt gegen die Discord-Nutzungsbedingungen und kann zur Kontosperre führen. Nur mit dem eigenen Konto verwenden.

## Installation

1. Python 3.11+ empfohlen (Pillow 13 braucht mindestens 3.11).

2. Abhängigkeiten:

    ```bash
    pip install -r requirements.txt
    ```

## Verwendung

1. `starten.bat` doppelklicken (schönes Konsolenfenster) oder `python main.py`

2. Token setzen (Option `1`):
    - manuell, oder
    - per QR-Code (Discord-App scannen und bestätigen)

3. Verbotene Berechtigungen setzen (Option `2`). Standard: `guilds.join`. Grün = aktuell verboten.

4. Optional Whitelist in `whitelist.txt` (`client_id # beschreibung`).

5. Start (Option `4`), Treffer prüfen, mit `y` widerrufen.

Treffer bzw. gelöschte Apps stehen danach in `result.r`.
