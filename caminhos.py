"""Descobre onde o Kenshi está instalado, em vez de assumir um caminho.

Ordem de tentativas:
 1. variável de ambiente `KENSHI_DIR`
 2. arquivo `kenshi_dir.txt` ao lado dos scripts (uma linha, o caminho)
 3. registro do Windows: instalação da Steam -> `libraryfolders.vdf` -> a
    biblioteca que contém `steamapps\\common\\Kenshi`
 4. locais padrão da Steam

O diretório do Workshop é derivado do mesmo `steamapps` onde o jogo está, que é
onde a Steam guarda os mods baixados (app 233860).
"""
import os
import re

APPID = "233860"
ARQUIVO_LOCAL = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "kenshi_dir.txt")
ARQUIVOS_BASE = ("gamedata.base", "rebirth.mod", "Newwworld.mod", "Dialogue.mod")

PADROES = [
    r"C:\Program Files (x86)\Steam\steamapps\common\Kenshi",
    r"C:\Program Files\Steam\steamapps\common\Kenshi",
    r"C:\SteamLibrary\steamapps\common\Kenshi",
]


def _valido(caminho):
    """é de fato uma instalação do Kenshi?"""
    return bool(caminho) and os.path.isfile(os.path.join(caminho, "fcs.def"))


def _do_registro():
    """caminhos de biblioteca da Steam, lidos do registro + libraryfolders.vdf"""
    try:
        import winreg
    except ImportError:
        return []
    steam = None
    for raiz, chave in ((winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam"),
                        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")):
        try:
            with winreg.OpenKey(raiz, chave) as k:
                steam = winreg.QueryValueEx(k, "InstallPath" if raiz ==
                                            winreg.HKEY_CURRENT_USER
                                            else "InstallPath")[0]
                break
        except OSError:
            continue
    if not steam:
        return []
    achados = [os.path.join(steam, "steamapps", "common", "Kenshi")]
    vdf = os.path.join(steam, "steamapps", "libraryfolders.vdf")
    if os.path.isfile(vdf):
        try:
            with open(vdf, "r", encoding="utf-8", errors="replace") as f:
                texto = f.read()
            for lib in re.findall(r'"path"\s+"([^"]+)"', texto):
                lib = lib.replace("\\\\", "\\")
                achados.append(os.path.join(lib, "steamapps", "common", "Kenshi"))
        except OSError:
            pass
    return achados


def kenshi_dir():
    """diretório da instalação do Kenshi; levanta erro claro se não achar"""
    tentativas = []

    env = os.environ.get("KENSHI_DIR")
    if env:
        tentativas.append(env.strip('"'))

    if os.path.isfile(ARQUIVO_LOCAL):
        with open(ARQUIVO_LOCAL, "r", encoding="utf-8") as f:
            linha = f.readline().strip().strip('"')
        if linha:
            tentativas.append(linha)

    tentativas += _do_registro()
    tentativas += PADROES

    for c in tentativas:
        if _valido(c):
            return os.path.abspath(c)

    raise SystemExit(
        "Não encontrei a instalação do Kenshi.\n"
        "Aponte de um destes jeitos:\n"
        "  set KENSHI_DIR=D:\\caminho\\para\\Kenshi        (cmd)\n"
        "  $env:KENSHI_DIR='D:\\caminho\\para\\Kenshi'      (PowerShell)\n"
        f"  ou escreva o caminho em {ARQUIVO_LOCAL}\n"
        "Procurei em:\n" + "\n".join(f"  {c}" for c in tentativas))


def data_dir():
    return os.path.join(kenshi_dir(), "data")


def mods_dir():
    return os.path.join(kenshi_dir(), "mods")


def fcs_def():
    return os.path.join(kenshi_dir(), "fcs.def")


def mods_cfg():
    """lista de mods ativos, na ordem de load"""
    return os.path.join(data_dir(), "mods.cfg")


def arquivos_base():
    """os arquivos de dados do jogo, que formam a base da ordem de load"""
    return [os.path.join(data_dir(), n) for n in ARQUIVOS_BASE]


def workshop_dir():
    """mods do Workshop, no mesmo steamapps onde o jogo está.

    Devolve None se não existir (instalação sem Workshop, ou GOG).
    """
    steamapps = os.path.dirname(os.path.dirname(kenshi_dir()))
    caminho = os.path.join(steamapps, "workshop", "content", APPID)
    return caminho if os.path.isdir(caminho) else None


if __name__ == "__main__":
    print(f"Kenshi    : {kenshi_dir()}")
    print(f"data      : {data_dir()}")
    print(f"mods      : {mods_dir()}")
    print(f"workshop  : {workshop_dir() or '(não encontrado)'}")
    print(f"mods.cfg  : {mods_cfg()}")
