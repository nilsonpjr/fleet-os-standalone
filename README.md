# FleetOS Standalone

Este projeto foi separado do repositório principal da Maré Alta para funcionar como uma solução independente de gestão de frotas.

## Estrutura do Projeto

- `frontend/`: Aplicação React/Vite (Fleet Management Dashboard).
- `backend/`: API FastAPI (Python) com módulos de Frota, Clientes e Orçamentos.
- `render.yaml`: Configuração para deployment automático no Render.com.

## Configuração Supabase

1. Crie um novo projeto no **Supabase**.
2. Vá em **Project Settings -> Database** e copie a **Connection String** (URI).
3. No painel do **Render**, configure a variável de ambiente `DATABASE_URL` com esta string.
4. O backend irá criar as tabelas automaticamente no primeiro acesso via `SQLAlchemy`.

## Desenvolvimento Local

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Deployment no Render

1. Conecte este repositório ao Render.com.
2. O Render detectará o arquivo `render.yaml` e criará os serviços de Frontend e Backend.
3. Configure as variáveis de ambiente necessárias (DATABASE_URL, SUPABASE_*, etc.) no Dashboard do Render.
