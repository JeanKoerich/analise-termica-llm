# Como publicar sem expor o TCC privado

## 1. Criar uma pasta pública separada

Crie uma pasta local **nova**, por exemplo `analise-termica-llm`, e coloque nela somente os arquivos deste pacote e **cópias revisadas** dos arquivos `.py` e `requirements.txt` necessários. Não copie a pasta `.git` do projeto privado.

## 2. Revisar antes de publicar

- [ ] Confirmar que `data/leitura_monitoramento.csv` real não entrou no novo repositório.
- [ ] Confirmar que `../.venv/.env`, `.venv`, `.idea`, `__pycache__` e `.streamlit/secrets.toml` não entraram.
- [ ] Procurar por `sk-`, `api_key`, `password`, `token`, credenciais MQTT e strings de conexão em todos os `.py` e notebooks.
- [ ] Revisar dados operacionais, IPs, URLs internos e nomes de clientes.
- [ ] Conferir os termos de uso dos dados e bibliotecas.
- [ ] Validar que o exemplo sintético pode ser usado na demonstração.

## 3. Comandos (PowerShell, a partir da pasta nova)

```powershell
git init -b main
git add .
git status --short
git diff --cached --stat
git diff --cached -- .env
git commit -m "docs: publica portfolio de analise termica com LLM"
```

`git diff --cached -- .env` deve estar vazio: o arquivo `../.venv/.env` não pode ser versionado.

## 4. GitHub

Crie no GitHub um repositório **público vazio** chamado `analise-termica-llm`, sem README automático (ele já existe localmente). Após verificar o endereço exato indicado pelo GitHub, rode:

```powershell
git remote add origin https://github.com/JeanKoerich/analise-termica-llm.git
git push -u origin main
```

## 5. Candidatura

Envie como link principal o novo repositório público e, nele, inclua demonstração, arquitetura, avaliação do LLM e contextualização do TCC. O repositório do TCC pode permanecer privado.
