# 🎮 Fase 03 — Otimização de vídeo (GPU)

[← Índice](README.md) · [Arquitetura](arquitetura.md) · [Guia de execução](guia-de-execucao.md)

**Pasta:** [`03_decodificador_caracteres/`](../03_decodificador_caracteres/)

---

## O que faz

`gpu_video_optimizer.py` recomprime vídeos `.mkv` para HEVC/NVENC quando o arquivo final é grande demais (ex.: fonte H.264 Hi10P ou bitrate acima de um limiar). Usa `ffprobe` para ler bitrate/codec/pixel format e `ffmpeg` com encoder `hevc_nvenc` (requer GPU NVIDIA) para recomprimir. **Auxiliar/opcional** — roda depois do remux da [Fase 12](modulo-fase-12.md), sobre o `.mkv` final já em PT-BR.

> Apesar do nome da pasta ("decodificador de caracteres"), o conteúdo atual é o otimizador de vídeo por GPU — o nome é herdado de uma reorganização anterior.

---

## Script

| Script | Entrada | Saída | Critério |
|:---|:---|:---|:---|
| `gpu_video_optimizer.py` | `mkv_final_ptbr/*_PTBR.mkv` | `otimizados/*_PTBR.mkv` | Só recomprime H.264 Hi10P ou bitrate >3 Mbps; senão pula o arquivo |

Log: `optimizer_log.txt` (raiz da pasta).

```powershell
python ".\03_decodificador_caracteres\gpu_video_optimizer.py"
```

Pré-requisito: FFmpeg com `hevc_nvenc` — verifique com `ffmpeg -encoders | Select-String nvenc`. Detalhes: [Instalação](instalacao.md#ffmpeg--ffprobe).

---

[← Fase 02](modulo-fase-02.md) · [Índice](README.md) · [Fase 04 →](modulo-fase-04.md)
