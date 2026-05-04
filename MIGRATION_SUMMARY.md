# Detalhamento da Migração: FleetOS Standalone

Este documento resume todas as alterações e refatorações realizadas para separar o FleetOS do repositório principal da Maré Alta, tornando-o um projeto independente pronto para deploy no Render e Supabase.

## 1. Estrutura do Novo Projeto
O projeto foi organizado em um diretório raiz próprio: `/Users/nilsonpereira/Downloads/fleet-os-standalone/`

- **`frontend/`**: Contém o Dashboard React/Vite.
- **`backend/`**: Contém a API FastAPI (Python).
- **`render.yaml`**: Arquivo de configuração "Blueprint" para deploy automático no Render.com.
- **`Dockerfile`s**: Configurações de containerização independentes para cada serviço.

## 2. Refatorações no Backend (Python)
- **Independência de Módulos**: O código foi extraído de `backend_v2` e movido para a pasta `backend/` raiz do novo projeto.
- **Correção de Imports**: Todos os imports internos foram refatorados de `from backend_v2.core...` para `from core...`, eliminando a dependência do caminho do projeto antigo.
- **Módulos Mantidos**: 
  - `fleet`: Core do FleetOS.
  - `partners`: Gestão de oficinas e orçamentos.
  - `inventory`: Necessário para peças nos orçamentos.
  - `finance`: Necessário para transações de OS.
  - `auth`, `clients`, `notifications`: Infraestrutura de base.
- **Configuração de Ambiente**: Ajustado o `main.py` e `database.py` para carregar o `.env` local da nova pasta.
- **Deploy**: Adicionado `gunicorn` e fixada a versão do Python para `3.11.0` para garantir compatibilidade no Render.

## 3. Refatorações no Frontend (React)
- **Base URL**: O `vite.config.ts` foi ajustado de `base: '/fleet_os/'` para `base: '/'`, permitindo que o app rode na raiz do domínio do Render.
- **API Client**: O `api/client.ts` foi configurado para apontar para o novo endpoint `/api` (em vez de `/marealta_v2`), facilitando a comunicação com o novo backend independente.
- **Build Command**: Atualizado para `npm install --include=dev && npm run build` para garantir que ferramentas como TypeScript e Vite estejam disponíveis no ambiente do Render.

## 4. Integração GitHub & Deploy
- **Repositório**: Criado o repositório público [nilsonpjr/fleet-os-standalone](https://github.com/nilsonpjr/fleet-os-standalone).
- **Versionamento**: O projeto foi inicializado com Git local, os arquivos foram commitados e enviados (push) para o GitHub.
- **Render Blueprint**: O arquivo `render.yaml` foi depurado e corrigido para criar automaticamente:
  - **Web Service (Backend)**: Python FastAPI.
  - **Static Site (Frontend)**: React SPA.

## 5. Como Abrir este Projeto no Antigravity
Para continuar trabalhando apenas neste sistema:
1. Abra uma nova conversa no Antigravity.
2. Selecione a pasta `/Users/nilsonpereira/Downloads/fleet-os-standalone/` como o seu workspace.
3. O Antigravity reconhecerá a nova estrutura simplificada e você poderá focar 100% no FleetOS.

---
*Resumo gerado em 03/05/2026 para fins de transição de projeto.*
