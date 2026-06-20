# 🎵 Fase 09 — Injetor de músicas

[← Índice](README.md) · [Arquitetura](arquitetura.md) · [Guia de execução](guia-de-execucao.md)

**Pasta:** [`09_injetor_musicas/`](../09_injetor_musicas/)

---

## O que faz

`injetor_de_musicas.py` extrai as linhas de karaokê (OP/ED/Insert Songs) de uma legenda fonte (ex.: fansub) e injeta na legenda de destino (ex.: tradução oficial/Crunchyroll), preservando timing e efeitos de karaokê da fonte. **Auxiliar/opcional** — usado quando a tradução principal não tem letras de música cantáveis/sincronizadas.

---

## Script

| Script | Entrada | Saída |
|:---|:---|:---|
| `injetor_de_musicas.py` | Legenda fonte (com OP/ED) + legenda de destino (`*_PTBR.ass`) | Legenda de destino com as linhas de karaokê injetadas |

```powershell
python ".\09_injetor_musicas\injetor_de_musicas.py"
```

Sem relatório próprio em disco — saída via console (`colorama`/`tqdm`).

---

[← Fase 08](modulo-fase-08.md) · [Índice](README.md) · [Fase 10 →](modulo-fase-10.md)
