# Dados de exemplo

`amostra_leituras.csv` é **sintético**, criado apenas para teste estrutural e documentação. Não contém medições industriais reais.

## Colunas

- `timestamp`: data/hora no formato ISO 8601 (sem fuso informado no exemplo)
- `origem`: origem fictícia da leitura
- `estado_processo`: estado do ciclo (`RECARREGANDO`, `AQUECENDO`, `MATURANDO`, `TRANSFERINDO`)
- `ciclo`: identificador do ciclo
- `temperatura_entrada` e `temperatura_saida`: °C
- `vazao_l_min`: litros por minuto
- `valvula_entrada` e `valvula_saida`: 0/1 (0 = fechada, 1 = aberta)
- `nivel_tubulacao_percentual`: nível percentual de referência
- `tempo_maturacao_min`: duração configurada em minutos
- `delta_t`: diferença calculada entre as temperaturas (°C)

**Importante:** compare esse esquema com as colunas esperadas pelos seus `.py`. O aplicativo pode exigir mudanças antes de utilizar a amostra.
