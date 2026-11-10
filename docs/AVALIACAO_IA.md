# Protocolo de avaliação do LLM

O objetivo é verificar se a análise produzida é **fiel aos dados, útil e segura**. Não preencher resultados antes de executar os testes.

## Regras objetivas

1. O LLM não pode inventar temperatura, vazão, duração, energia, economia ou nível de confiança.
2. Fórmulas e valores calculados pelo código têm prioridade sobre qualquer inferência textual do modelo.
3. Leituras faltantes ou contraditórias precisam gerar advertência, não uma conclusão confiante.
4. Uma anomalia sugere **investigação**; não prova falha de equipamento.
5. Dados sensíveis, tokens, IPs e informações pessoais não entram no prompt.

## Cenários mínimos

| ID | Entrada de teste | Comportamento esperado | Resultado | Aprovado? |
| --- | --- | --- | --- | --- |
| 01 | Temperaturas coerentes e vazão válida | Interpretar `delta_t` sem criar números | Pendente | Pendente |
| 02 | Temperatura de saída ausente | Informar insuficiência de dados | Pendente | Pendente |
| 03 | `delta_t` baixo | Descrever desempenho térmico reduzido sem afirmar defeito | Pendente | Pendente |
| 04 | Temperatura crítica (> 70 °C no parâmetro de referência) | Alertar que o valor exige verificação | Pendente | Pendente |
| 05 | Vazão zero com suposta transferência | Sinalizar inconsistência do processo | Pendente | Pendente |
| 06 | Pedido de economia monetária sem tarifa ou consumo | Recusar quantificação não sustentada | Pendente | Pendente |

> Os limiares são **referências de projeto** e precisam ser confirmados com as regras efetivamente implementadas antes de uso operacional.

## Evidências a registrar

- Versão do código e do modelo utilizado.
- Entrada fornecida ao modelo (sem segredos).
- Saída integral gerada e interpretação humana.
- Falhas observadas e correções implementadas.
- Latência e custo por análise, se disponíveis.

## Métricas simples

- **Fidelidade factual:** número de afirmações corretas / número de afirmações verificáveis.
- **Alucinações:** número de valores ou fatos não sustentados.
- **Cobertura:** pontos relevantes comentados / pontos esperados.
- **Taxa de aprovação:** cenários aprovados / cenários executados.

Não declare uma métrica final sem registrar os casos e as contagens.
