import ctypes
import os
import re
import sys

WIDTH = 64
ANSI_RE = re.compile(r"\033\[[0-9;]*m")


class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"


def visible_len(text: str) -> int:
    return len(ANSI_RE.sub("", text))


def setup_console() -> None:
    if os.name == "nt":
        try:
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)
            mode = ctypes.c_uint32()
            if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                kernel32.SetConsoleMode(handle, mode.value | 0x0004)
            kernel32.SetConsoleOutputCP(65001)
            kernel32.SetConsoleTitleW("Discord Apps Cleaner")
        except Exception:
            pass
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def clear() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def _plain(text: str) -> str:
    return ANSI_RE.sub("", text)


def _pad(text: str, width: int = WIDTH) -> str:
    extra = width - visible_len(text)
    if extra < 0:
        plain = _plain(text)
        return plain[: width - 1] + "…"
    return text + (" " * extra)


def box(title: str, lines: list[str], footer: str | None = None) -> None:
    inner = WIDTH
    print(f"{C.BLUE}╔{'═' * inner}╗{C.RESET}")
    print(f"{C.BLUE}║{C.RESET}{_pad(f'{C.BOLD}{C.WHITE}  {title}{C.RESET}')}{C.BLUE}║{C.RESET}")
    print(f"{C.BLUE}╠{'═' * inner}╣{C.RESET}")
    if not lines:
        print(f"{C.BLUE}║{C.RESET}{_pad('')}{C.BLUE}║{C.RESET}")
    for line in lines:
        print(f"{C.BLUE}║{C.RESET}{_pad(line)}{C.BLUE}║{C.RESET}")
    print(f"{C.BLUE}╚{'═' * inner}╝{C.RESET}")
    if footer:
        print(f"  {C.GRAY}{footer}{C.RESET}")


def item(key: str, label: str, hint: str = "") -> str:
    left = f"  {C.CYAN}{C.BOLD}[{key}]{C.RESET}  {C.WHITE}{label}{C.RESET}"
    if hint:
        left += f"  {C.GRAY}{hint}{C.RESET}"
    return left


def status(ok: bool, text: str) -> str:
    if ok:
        return f"{C.GREEN}● {text}{C.RESET}"
    return f"{C.RED}● {text}{C.RESET}"


def ask(prompt: str = "Auswahl") -> str:
    try:
        return input(f"  {C.CYAN}› {prompt}:{C.RESET} ").strip()
    except EOFError:
        return "0"


def pause(text: str = "Enter zum Fortfahren") -> None:
    try:
        input(f"  {C.GRAY}{text} …{C.RESET} ")
    except (EOFError, KeyboardInterrupt):
        print()


def ok(text: str) -> None:
    print(f"  {C.GREEN}✓ {text}{C.RESET}")


def warn(text: str) -> None:
    print(f"  {C.YELLOW}! {text}{C.RESET}")


def err(text: str) -> None:
    print(f"  {C.RED}✗ {text}{C.RESET}")


def info(text: str) -> None:
    print(f"  {C.CYAN}• {text}{C.RESET}")
