import re
import time
import requests

# Configurações de Infraestrutura Local
ARQUIVO_ORIGEM = r"C:\Staging\Prontos\legenda_en.srt"
ARQUIVO_DESTINO = r"C:\Staging\Prontos\legenda_ptbr.srt"
ENDPOINT_API = "http://localhost:11434/api/generate"  # Exemplo utilizando Ollama local (ex: llama3 ou mistral)


def chamar_api_traducao(texto_ingles):
    """
    Envia o texto para o modelo de linguagem com engenharia de prompt específica
    para localização de animes/Sci-Fi.
    """
    prompt = (
        f"Você é um tradutor especialista em localização de animes de Ficção Científica e Mecha. "
        f"Traduza a seguinte frase do Inglês para o Português do Brasil (PT-BR) de forma natural, "
        f"mantendo termos militares ou técnicos contextuais da franquia Macross. "
        f"Retorne APENAS a tradução direta, sem comentários adicionais.\n\n"
        f"Frase: '{texto_ingles}'"
    )

    payload = {
        "model": "llama3",  # Substitua pelo modelo que rodar na sua máquina
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(ENDPOINT_API, json=payload, timeout=10)
        if response.status_code == 200:
            return response.json().get("response", texto_ingles).strip().replace("'", "")
    except Exception as e:
        print(f"Erro de comunicação com a API: {e}")
    return texto_ingles


def processar_legenda():
    print("[*] Iniciando processamento do arquivo de legenda...")

    with open(ARQUIVO_ORIGEM, "r", encoding="utf-8") as f:
        linhas = f.readlines()

    linhas_traduzidas = []
    buffer_texto = []

    # Expressão regular para identificar a linha de marcação de tempo do SRT
    padrao_tempo = re.compile(r'\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}')

    for linha in lines:
        linha_limpa = linha.strip()

        # Se for número de índice ou linha de tempo, preserva intacto
        if linha_limpa.isdigit() or padrao_tempo.match(linha_limpa):
            linhas_traduzidas.append(linha)
        # Se for linha vazia, indica fim do bloco do SRT
        elif not linha_limpa:
            if buffer_texto:
                texto_completo = " ".join(buffer_texto)
                print(f"[Traduzindo] -> {texto_completo}")

                # Chamada do modelo
                texto_ptbr = chamar_api_traducao(texto_completo)
                linhas_traduzidas.append(texto_ptbr + "\n")
                buffer_texto = []
            linhas_traduzidas.append("\n")
        else:
            # Acumula as linhas de diálogo (caso o bloco tenha mais de uma linha)
            buffer_texto.append(linha_limpa)

    # Gravação do resultado no NVMe (Unidade C)
    with open(ARQUIVO_DESTINO, "w", encoding="utf-8") as f:
        f.writelines(linhas_traduzidas)

    print(f"[+] Legenda traduzida com sucesso e salva em: {ARQUIVO_DESTINO}")


if __name__ == "__main__":
    inicio = time.time()
    processar_legenda()
    print(f"[!] Tempo de execução: {time.time() - inicio:.2f} segundos.")