import sys, os, requests
PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
if PASTA_SCRIPT not in sys.path:
    sys.path.insert(0, PASTA_SCRIPT)
import batch_translator_origin_zh as translator
import re

def test_line(texto_orig):
    system_prompt = translator.SYSTEM_PROMPT.replace(
        'Traduza as linhas de legenda numeradas fornecidas do Chinês Simplificado (CHS) para o Português do Brasil (PT-BR) de forma fluida e natural.',
        'Traduza a linha de legenda fornecida do Chinês Simplificado (CHS) para o Português do Brasil (PT-BR) de forma fluida e natural.'
    )

    instrucao_user = (
        "This Chinese subtitle line failed automatic translation before and needs careful attention. "
        "Think step by step about the best Brazilian Portuguese (PT-BR) translation, considering "
        "Gundam The Origin / Universal Century context, tone, protected terms, and the glossary. "
        "The final output must NOT contain Chinese characters.\n\n"
        f"Line: {texto_orig}\n\n"
        "After your reasoning, output the final translation on its own line in this exact format "
        "(nothing else after it):\nFINAL: <your PT-BR translation>"
    )

    payload = {
        "model": "qwen2.5-7b-instruct",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": instrucao_user}
        ],
        "temperature": 0.2,
        "max_tokens": 3000
    }

    res = requests.post(translator.LM_STUDIO_URL, json=payload, timeout=120)
    raw = res.json()['choices'][0]['message']['content'].strip()

    # extrair_traducao_final
    conteudo = re.sub(r'<think(?:ing)?>.*?</think(?:ing)?>', '', raw, flags=re.DOTALL | re.IGNORECASE)
    conteudo = re.sub(r'<think(?:ing)?>.*', '', conteudo, flags=re.DOTALL | re.IGNORECASE).strip()
    m = re.search(r'FINAL\s*:\s*(.+?)(?:\n|$)', conteudo, flags=re.IGNORECASE)
    if m:
        conteudo = m.group(1).strip()
    else:
        linhas = [l.strip() for l in conteudo.split('\n') if l.strip()]
        conteudo = linhas[-1] if linhas else ''

    m = re.match(r'^\d+[\s.)\-:]+\s*(.+)', conteudo)
    if m:
        conteudo = m.group(1).strip()

    conteudo = conteudo.replace("*", "").replace("_", "").strip().strip('"').strip("'")
    conteudo_proc = translator.post_processar_traducao(conteudo)
    valid = translator.validar_traducao(texto_orig, conteudo_proc)

    with open(os.path.join(PASTA_SCRIPT, "debug_test.txt"), "a", encoding="utf-8") as f:
        f.write("====================================\n")
        f.write(f"Origem: {texto_orig}\n")
        f.write(f"Raw output: {raw}\n")
        f.write(f"Parsed output: {conteudo_proc}\n")
        f.write(f"Valid: {valid}\n")
        f.write("====================================\n")

# Limpa o arquivo de debug
if os.path.exists(os.path.join(PASTA_SCRIPT, "debug_test.txt")):
    os.remove(os.path.join(PASTA_SCRIPT, "debug_test.txt"))

test_line("这里是自行重迫击炮队...")
test_line("库姆朗还哭了出来...")
test_line("接舷码头的抵抗也基本上清除了")
