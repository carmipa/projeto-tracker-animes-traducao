import os
import sys
from datetime import datetime

# Ignora apenas a pasta interna de controle do Git
PASTAS_IGNORADAS = {'.git'}

def gerar_relatorio_completo():
    diretorio_atual = os.getcwd()
    nome_projeto = os.path.basename(diretorio_atual)
    data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    linhas_relatorio = []
    
    # Cabeçalho Técnico
    linhas_relatorio.append("=" * 100)
    linhas_relatorio.append(f"RELATÓRIO DE MAPEAMENTO COMPLETO DE DIRETÓRIO E TAXONOMIA DE REPOSITÓRIO")
    linhas_relatorio.append(f"Projeto: {nome_projeto}")
    linhas_relatorio.append(f"Data/Hora de Execução: {data_hora}")
    linhas_relatorio.append("=" * 100 + "\n")
    
    arquivos_mapeados = []
    
    # Varredura recursiva total
    for raiz, diretorios, arquivos in os.walk(diretorio_atual):
        # Filtra apenas a pasta .git
        diretorios[:] = [d for d in diretorios if d not in PASTAS_IGNORADAS]
        
        for arquivo in arquivos:
            caminho_absoluto = os.path.abspath(os.path.join(raiz, arquivo))
            caminho_relativo = os.path.relpath(caminho_absoluto, diretorio_atual)
            arquivos_mapeados.append((arquivo, caminho_absoluto, caminho_relativo))

    # PARTE 1: CAMINHO ABSOLUTO COMPLETO NO SISTEMA LOCAL
    linhas_relatorio.append("PARTE 1: MAPEAMENTO DE DIRETÓRIO LOCAL (CAMINHO ABSOLUTO COMPLETO)")
    linhas_relatorio.append("-" * 100)
    
    if not arquivos_mapeados:
        linhas_relatorio.append("[AVISO] Nenhum arquivo encontrado no diretório atual.")
    else:
        for arquivo, cam_abs, _ in sorted(arquivos_mapeados, key=lambda x: x[1]):
            linhas_relatorio.append(f" Arquivo: {arquivo:<35} | Caminho: {cam_abs}")
            
    linhas_relatorio.append("\n" + "=" * 100 + "\n")
    
    # PARTE 2: QUADRO DE ALOCAÇÃO NA ESTRUTURA DO REPOSITÓRIO ONLINE
    linhas_relatorio.append("PARTE 2: ESTRUTURA DE DESTINO SUGERIDA PARA O REPOSITÓRIO ONLINE")
    linhas_relatorio.append("-" * 100)
    
    if arquivos_mapeados:
        # Cabeçalho do quadro simulado
        linhas_relatorio.append(f" {'NOME DO ARQUIVO':<35} | {'PASTA ALVO NO REPOSITÓRIO ONLINE':<45}")
        linhas_relatorio.append(f" {'-'*35} | {'-'*45}")
        
        for arquivo, _, cam_rel in sorted(arquivos_mapeados, key=lambda x: x[0]):
            # Lógica determinística de separação por extensão e metadados
            pasta_target = "raiz/"
            extensao = os.path.splitext(arquivo)[1].lower()
            
            if extensao == '.srt':
                pasta_target = "legendas/traduzidas/"
            elif extensao == '.md':
                pasta_target = "obsidian_vault/notas/"
            elif extensao == '.json':
                pasta_target = "config/json_data/"
            elif extensao in ['.log', '.txt']:
                pasta_target = "telemetria/logs_erro/"
            elif extensao in ['.py', '.sh']:
                if 'mistral' in cam_rel.lower():
                    pasta_target = "src/mistral_engine/"
                else:
                    pasta_target = "src/scripts_automacao/"
            else:
                # Mantém a árvore estruturada caso seja outra extensão específica
                pasta_pai = os.path.dirname(cam_rel)
                pasta_target = f"{pasta_pai}/" if pasta_pai else "raiz/"

            linhas_relatorio.append(f"  {arquivo:<34} | {pasta_target:<44}")
            
    linhas_relatorio.append("\n" + "=" * 100)
    linhas_relatorio.append("FIM DO RELATÓRIO - PRONTO PARA DOWNLOAD DA JANELA DE CONTEXTO")
    
    # Escrita final do arquivo texto em UTF-8
    nome_saida = "relatorio_diretorio_vps.txt"
    try:
        with open(nome_saida, "w", encoding="utf-8") as f:
            f.write("\n".join(linhas_relatorio))
        print(f"[SUCESSO] Relatório gerado em: {os.path.join(diretorio_atual, nome_saida)}")
    except Exception as e:
        print(f"[ERRO] Falha ao salvar arquivo: {e}", file=sys.stderr)

if __name__ == "__main__":
    gerar_relatorio_completo()