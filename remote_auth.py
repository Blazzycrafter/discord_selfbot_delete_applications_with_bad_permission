import asyncio
import json
from base64 import b64decode, urlsafe_b64encode
from hashlib import sha256
from typing import Any, Callable, Optional

import requests
import websockets
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

GATEWAY_URL = "wss://remote-auth-gateway.discord.gg/?v=2"
LOGIN_URL = "https://discord.com/api/v10/users/@me/remote-auth/login"
ORIGIN = "https://discord.com"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


class User:
    def __init__(self, uid, username, discriminator, avatar):
        self.id = uid
        self.username = username
        self.discriminator = discriminator
        self.avatar = avatar

    def getName(self) -> str:
        if self.discriminator in ("0", "0000", None, ""):
            return self.username
        return f"{self.username}#{self.discriminator}"

    def getAvatarURL(self) -> str:
        return f"https://cdn.discord.com/avatars/{self.id}/{self.avatar}.png"


class RemoteAuthClient:
    def __init__(self):
        self.on_fingerprint = self._noop
        self.on_userdata = self._noop
        self.on_token = self._noop
        self.on_cancel = self._noop
        self.on_timeout = self._noop
        self.on_error = self._noop
        self._private_key = None

    def event(self, name: str):
        def register(handler: Callable):
            setattr(self, name, handler)
            return handler

        return register

    async def _noop(self, *args, **kwargs) -> None:
        return None

    def _init_crypto(self) -> str:
        self._private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_pem = self._private_key.public_key().public_bytes(
            Encoding.PEM, PublicFormat.SubjectPublicKeyInfo
        ).decode("utf8")
        return "".join(public_pem.split("\n")[1:-2])

    def _decrypt(self, payload: str) -> bytes:
        return self._private_key.decrypt(
            b64decode(payload),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )

    async def _call(self, handler, **kwargs) -> Any:
        if handler is self._noop:
            return None
        result = handler(**kwargs)
        if asyncio.iscoroutine(result):
            return await result
        return result

    def _exchange_ticket(self, ticket: str) -> Optional[str]:
        response = requests.post(
            LOGIN_URL,
            json={"ticket": ticket},
            headers={
                "User-Agent": USER_AGENT,
                "Content-Type": "application/json",
                "Origin": ORIGIN,
            },
            timeout=30,
        )
        data = response.json()
        if "encrypted_token" in data:
            return data["encrypted_token"]
        if "captcha_key" in data or "captcha_sitekey" in data:
            raise RuntimeError(
                "Discord verlangt ein Captcha für den QR-Login. Bitte Token manuell setzen."
            )
        raise RuntimeError(f"QR-Login fehlgeschlagen: {data}")

    async def run(self) -> None:
        public_key = self._init_crypto()
        heartbeat_task: Optional[asyncio.Task] = None

        async with websockets.connect(
            GATEWAY_URL,
            origin=ORIGIN,
            user_agent_header=USER_AGENT,
        ) as ws:

            async def heartbeat(interval_ms: int) -> None:
                while True:
                    await asyncio.sleep(interval_ms / 1000)
                    await ws.send(json.dumps({"op": "heartbeat"}))

            try:
                async for raw in ws:
                    packet = json.loads(raw)
                    op = packet.get("op")
                    if op == "hello":
                        await ws.send(
                            json.dumps({"op": "init", "encoded_public_key": public_key})
                        )
                        heartbeat_task = asyncio.create_task(
                            heartbeat(packet["heartbeat_interval"])
                        )
                    elif op == "nonce_proof":
                        nonce = self._decrypt(packet["encrypted_nonce"])
                        proof = (
                            urlsafe_b64encode(sha256(nonce).digest())
                            .decode("utf8")
                            .replace("=", "")
                        )
                        await ws.send(json.dumps({"op": "nonce_proof", "proof": proof}))
                    elif op == "pending_remote_init":
                        fingerprint = packet["fingerprint"]
                        await self._call(
                            self.on_fingerprint,
                            data=f"https://discord.com/ra/{fingerprint}",
                        )
                    elif op == "pending_ticket":
                        parts = self._decrypt(packet["encrypted_user_payload"]).decode("utf8").split(":")
                        user = User(parts[0], parts[3], parts[1], parts[2])
                        await self._call(self.on_userdata, user=user)
                    elif op == "pending_login":
                        encrypted = await asyncio.to_thread(self._exchange_ticket, packet["ticket"])
                        token = self._decrypt(encrypted).decode("utf8")
                        await self._call(self.on_token, token=token)
                        break
                    elif op == "cancel":
                        await self._call(self.on_cancel)
                        break
                    elif op == "timeout":
                        await self._call(self.on_timeout)
                        break
            except ConnectionClosedOK:
                pass
            except ConnectionClosedError as exc:
                if exc.code == 4003:
                    await self._call(self.on_timeout)
                else:
                    raise
            finally:
                if heartbeat_task:
                    heartbeat_task.cancel()
