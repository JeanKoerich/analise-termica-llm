# Arquitetura proposta

## Fluxo de referência

1. **Fonte:** leituras do sistema industrial (origem real) ou CSV sintético (demonstração).
2. **ETL:** conversão de tipos, checagem de ausências, ordenação temporal e validação de intervalos.
3. **Indicadores:** cálculos determinísticos de `delta_t`, vazão e indicadores de energia quando houver dados suficientes.
4. **Contexto do LLM:** fornecimento de métricas já calculadas, período, quantidade de registros, advertências e regras do processo.
5. **LLM:** síntese, explicação e recomendações contextualizadas; nenhuma medição deve ser inventada.
6. **Streamlit:** dados, gráficos, texto gerado e ressalvas ao usuário.

## Limites de responsabilidade

**Código determinístico:** calcula indicadores, filtra registros, detecta dados ausentes, gera tabelas.

**LLM:** descreve tendências, contextualiza informações fornecidas, comunica hipóteses e limitações. Não deve alterar valores calculados nem apresentar hipótese como diagnóstico confirmado.

## Arquivos existentes e revisão necessária

- `etl_monitoramento.py`: confirmar formatos de entrada e nomes de colunas.
- `function_monitoramento.py`: identificar origem dos indicadores.
- `exploratoria_monitoramento.py`: identificar gráficos e estatísticas gerados.
- `inteligencia_monitoramento.py`: localizar cliente/modelo, prompt e tratamento de erros.
- `streamlit_app.py`: verificar importações e comando de execução.
- `teste_openai.py`: remover credenciais embutidas; avaliar se é necessário publicar.

## Pendências antes da candidatura

- [ ] Confirmar como a aplicação consome o CSV.
- [ ] Validar que o LLM é realmente chamado e que sua resposta aparece na interface.
- [ ] Documentar o modelo e os parâmetros de uso, sem expor chaves.
- [ ] Executar pelo menos cinco cenários de avaliação.
- [ ] Registrar capturas e vídeo reais.
