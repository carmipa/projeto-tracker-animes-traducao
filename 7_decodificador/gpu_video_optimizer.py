import os
import subprocess
import json
import sys
from datetime import datetime
from tqdm import tqdm
from colorama import init, Fore, Style

init(autoreset=True)

PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(PASTA_SCRIPT, "optimizer_log.txt")


def _log(mensagem, cor=Fore.WHITE):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tqdm.write(f"{cor}[{timestamp}] {mensagem}{Style.RESET_ALL}")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {mensagem}\n")


def obter_caminho(mensagem, padrao=""):
    entrada = input(
        f"{Fore.YELLOW}{mensagem} {'(ENTER = ' + padrao + '): ' if padrao else ': '}{Style.RESET_ALL}"
    ).strip()
    return entrada if entrada else padrao


def analisar_video(caminho):
    """Retorna (bitrate_mbps, codec, pix_fmt, profile) ou lança RuntimeError."""
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", "-show_format", caminho]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"ffprobe exit {res.returncode}: {res.stderr.strip()[:200]}")

    try:
        dados = json.loads(res.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"ffprobe retornou JSON invalido: {e}")

    stream_video = next(
        (s for s in dados.get("streams", []) if s.get("codec_type") == "video"),
        None
    )
    if stream_video is None:
        raise RuntimeError("Nenhuma stream de video encontrada.")

    bitrate = int(dados["format"].get("bit_rate", 0)) / 1_000_000
    codec   = stream_video.get("codec_name", "desconhecido")
    pix_fmt = stream_video.get("pix_fmt", "")
    profile = stream_video.get("profile", "")
    return bitrate, codec, pix_fmt, profile


def _precisa_comprimir(bitrate, codec, pix_fmt, profile):
    """Retorna (bool, motivo_str)."""
    if bitrate > 30:
        return True, f"bitrate alto ({bitrate:.1f} Mbps)"
    if codec == "h264" and ("10" in pix_fmt or "High 10" in profile):
        return True, f"H.264 Hi10P ({pix_fmt})"
    return False, "bitrate seguro e codec compativel"


def comprimir_video(entrada, saida):
    """Retorna True em sucesso."""
    cmd = [
        "ffmpeg", "-i", entrada,
        "-c:v", "hevc_amf", "-quality", "balanced",
        "-pix_fmt", "yuv420p", "-c:a", "copy", "-c:s", "copy",
        "-y", saida
    ]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return res.returncode == 0


def main():
    pasta_origem = obter_caminho("Pasta com os MKVs")
    if not os.path.isdir(pasta_origem):
        print(f"{Fore.RED}[ERRO] Diretorio nao existe: {pasta_origem}")
        sys.exit(1)

    pasta_saida = obter_caminho(
        "Pasta de saida",
        os.path.join(pasta_origem, "otimizados")
    )
    os.makedirs(pasta_saida, exist_ok=True)

    arquivos = sorted([f for f in os.listdir(pasta_origem) if f.lower().endswith(".mkv")])
    if not arquivos:
        print(f"{Fore.YELLOW}[AVISO] Nenhum .mkv encontrado em: {pasta_origem}")
        return

    inicio = datetime.now()
    _log("=" * 60, Fore.CYAN)
    _log("INICIO DO PROCESSAMENTO", Fore.CYAN)
    _log(f"Origem  : {pasta_origem}", Fore.CYAN)
    _log(f"Saida   : {pasta_saida}", Fore.CYAN)
    _log(f"Arquivos: {len(arquivos)}", Fore.CYAN)
    _log("=" * 60, Fore.CYAN)

    registros = []

    for arquivo in tqdm(arquivos, desc="Processando", unit="arq", colour="cyan"):
        entrada = os.path.join(pasta_origem, arquivo)
        saida   = os.path.join(pasta_saida, arquivo)

        if os.path.exists(saida):
            _log(f"[SKIP] {arquivo} — saida ja existe", Fore.YELLOW)
            registros.append((arquivo, 0.0, "-", "-", "PULADO", "JA_EXISTE"))
            continue

        try:
            bitrate, codec, pix_fmt, profile = analisar_video(entrada)
        except Exception as e:
            _log(f"[ERRO] {arquivo} — {e}", Fore.RED)
            registros.append((arquivo, 0.0, "?", "?", "ERRO", str(e)[:80]))
            continue

        _log(
            f"[ANALISE] {arquivo} | {codec} | {pix_fmt} | {bitrate:.2f} Mbps",
            Fore.CYAN
        )

        comprimir, motivo = _precisa_comprimir(bitrate, codec, pix_fmt, profile)

        if comprimir:
            _log(f"  -> Comprimindo ({motivo})...", Fore.YELLOW)
            ok = comprimir_video(entrada, saida)
            if ok:
                _log(f"  -> OK: {arquivo}", Fore.GREEN)
                registros.append((arquivo, bitrate, codec, pix_fmt, "COMPRIMIDO", "OK"))
            else:
                _log(f"  -> FALHA no ffmpeg: {arquivo}", Fore.RED)
                registros.append((arquivo, bitrate, codec, pix_fmt, "COMPRIMIDO", "FALHA"))
                if os.path.exists(saida):
                    os.remove(saida)
        else:
            _log(f"  -> Pulando ({motivo})", Fore.GREEN)
            registros.append((arquivo, bitrate, codec, pix_fmt, "PULADO", "-"))

    fim = datetime.now()
    duracao = fim - inicio
    _log("=" * 60, Fore.CYAN)
    _log(f"CONCLUIDO em {duracao}", Fore.GREEN)
    _log("=" * 60, Fore.CYAN)

    comprimidos_ok = [r for r in registros if r[4] == "COMPRIMIDO" and r[5] == "OK"]
    falhas         = [r for r in registros if r[5] == "FALHA"]
    pulados        = [r for r in registros if r[4] == "PULADO"]
    erros          = [r for r in registros if r[4] == "ERRO"]

    timestamp_rel = inicio.strftime("%Y-%m-%d_%H%M%S")
    arquivo_rel   = os.path.join(PASTA_SCRIPT, f"relatorio_{timestamp_rel}.txt")

    linhas = [
        "RELATORIO DE OTIMIZACAO GPU",
        f"Data/Hora : {inicio.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Duracao   : {duracao}",
        f"Origem    : {pasta_origem}",
        f"Saida     : {pasta_saida}",
        "=" * 60,
        (
            f"Total: {len(registros)}"
            f"  |  OK: {len(comprimidos_ok)}"
            f"  |  Pulados: {len(pulados)}"
            f"  |  Falhas: {len(falhas)}"
            f"  |  Erros: {len(erros)}"
        ),
        "=" * 60,
        "",
        "DETALHES:",
    ]
    for arq, br, cod, pfmt, acao, status in registros:
        br_str = f"{br:.2f} Mbps" if br else "-"
        linhas.append(f"  [{acao:<10}] [{status:<8}] {arq} | {cod} | {pfmt} | {br_str}")

    with open(arquivo_rel, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n")

    print(f"\n{Fore.GREEN}Relatorio salvo em : {arquivo_rel}")
    print(f"{Fore.CYAN}Log salvo em       : {LOG_FILE}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[AVISO] Interrompido pelo operador.")
        sys.exit(0)
