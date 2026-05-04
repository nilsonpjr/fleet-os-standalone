import subprocess
import json
import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from core.dependencies import require_admin
from modules.auth.models import User
from core.logger import get_logger

logger = get_logger("monitoring")
router = APIRouter(prefix="/admin/monitoring", tags=["Monitoring"])

def run_render_command(args: list):
    """Executes a Render CLI command and returns the output."""
    try:
        # Ensure render is in PATH or specify full path
        # In Docker it will be in /usr/local/bin/render
        cmd = ["render"] + args
        
        # Non-interactive mode usually needs RENDER_API_KEY env var
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=os.environ.copy(),
            timeout=30
        )
        
        if result.returncode != 0:
            logger.error(f"Render CLI error: {result.stderr}")
            return {"error": result.stderr or "Erro desconhecido no Render CLI"}
        
        return result.stdout
    except subprocess.TimeoutExpired:
        return {"error": "O comando do Render CLI expirou (timeout)."}
    except Exception as e:
        logger.exception("Erro ao executar comando Render CLI")
        return {"error": str(e)}

@router.get("/api/services")
async def get_services(current_user: User = Depends(require_admin)):
    output = run_render_command(["services", "-o", "json"])
    if isinstance(output, dict) and "error" in output:
        return JSONResponse(status_code=500, content=output)
    
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return JSONResponse(status_code=500, content={"error": "Falha ao processar resposta do Render CLI", "raw": output})

@router.get("/api/logs/{service_id}")
async def get_logs(service_id: str, current_user: User = Depends(require_admin)):
    # Get last 100 lines of logs
    output = run_render_command(["logs", service_id, "--limit", "100"])
    if isinstance(output, dict) and "error" in output:
        return JSONResponse(status_code=500, content=output)
    
    return {"logs": output}

@router.get("/", response_class=HTMLResponse)
async def dashboard_page(current_user: User = Depends(require_admin)):
    html_content = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FleetOS | Monitoring Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #6366f1;
            --primary-hover: #4f46e5;
            --bg: #0f172a;
            --card-bg: rgba(30, 41, 59, 0.7);
            --text: #f8fafc;
            --text-dim: #94a3b8;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --border: rgba(255, 255, 255, 0.1);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Inter', sans-serif;
        }

        body {
            background-color: var(--bg);
            color: var(--text);
            min-height: 100vh;
            padding: 2rem;
            background-image: 
                radial-gradient(circle at 10% 20%, rgba(99, 102, 241, 0.1) 0%, transparent 40%),
                radial-gradient(circle at 90% 80%, rgba(16, 185, 129, 0.05) 0%, transparent 40%);
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 3rem;
        }

        h1 {
            font-size: 2rem;
            font-weight: 700;
            letter-spacing: -0.025em;
            background: linear-gradient(to right, #818cf8, #34d399);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .status-badge {
            padding: 0.5rem 1rem;
            border-radius: 9999px;
            font-size: 0.875rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            background: var(--card-bg);
            border: 1px solid var(--border);
        }

        .dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--success);
            box-shadow: 0 0 10px var(--success);
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 1.5rem;
            margin-bottom: 3rem;
        }

        .card {
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border);
            border-radius: 1rem;
            padding: 1.5rem;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .card:hover {
            transform: translateY(-4px);
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
            border-color: rgba(99, 102, 241, 0.4);
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 1rem;
        }

        .service-name {
            font-size: 1.25rem;
            font-weight: 700;
            color: #fff;
        }

        .service-type {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-dim);
            margin-top: 0.25rem;
        }

        .badge {
            padding: 0.25rem 0.75rem;
            border-radius: 0.5rem;
            font-size: 0.75rem;
            font-weight: 700;
        }

        .badge-live { background: rgba(16, 185, 129, 0.2); color: #34d399; }
        .badge-suspended { background: rgba(239, 68, 68, 0.2); color: #f87171; }
        .badge-building { background: rgba(245, 158, 11, 0.2); color: #fbbf24; }

        .service-info {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
            margin: 1.5rem 0;
            font-size: 0.875rem;
        }

        .info-label {
            color: var(--text-dim);
            margin-bottom: 0.25rem;
        }

        .info-value {
            font-weight: 600;
        }

        .btn {
            width: 100%;
            padding: 0.75rem;
            border-radius: 0.5rem;
            border: none;
            background: var(--primary);
            color: white;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        }

        .btn:hover {
            background: var(--primary-hover);
        }

        .logs-container {
            margin-top: 3rem;
            display: none;
        }

        .logs-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }

        .logs-window {
            background: #000;
            color: #10b981;
            font-family: 'Monaco', 'Consolas', monospace;
            padding: 1.5rem;
            border-radius: 0.5rem;
            height: 500px;
            overflow-y: auto;
            font-size: 0.8125rem;
            line-height: 1.5;
            border: 1px solid var(--border);
            white-space: pre-wrap;
        }

        .loader {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255,255,255,.3);
            border-radius: 50%;
            border-top-color: #fff;
            animation: spin 1s ease-in-out infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .refresh-btn {
            background: transparent;
            border: 1px solid var(--border);
            color: var(--text);
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            cursor: pointer;
        }

        .refresh-btn:hover {
            background: rgba(255,255,255,0.05);
        }

        #error-msg {
            background: rgba(239, 68, 68, 0.1);
            color: var(--danger);
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 2rem;
            display: none;
            border: 1px solid var(--danger);
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>Monitoramento de Produção</h1>
                <p style="color: var(--text-dim); margin-top: 0.5rem;">Gerenciamento de infraestrutura Render</p>
            </div>
            <div class="status-badge">
                <div class="dot"></div>
                Sistema Operacional
            </div>
        </header>

        <div id="error-msg"></div>

        <div id="services-grid" class="grid">
            <!-- Services will be loaded here -->
            <div style="grid-column: 1/-1; text-align: center; padding: 3rem;">
                <div class="loader"></div>
                <p style="margin-top: 1rem; color: var(--text-dim);">Carregando serviços...</p>
            </div>
        </div>

        <div id="logs-section" class="logs-container">
            <div class="logs-header">
                <h2 id="logs-title">Logs do Serviço</h2>
                <button class="refresh-btn" onclick="hideLogs()">Fechar Logs</button>
            </div>
            <div id="logs-window" class="logs-window">Aguardando seleção...</div>
        </div>
    </div>

    <script>
        async function fetchServices() {
            const grid = document.getElementById('services-grid');
            const errorMsg = document.getElementById('error-msg');
            errorMsg.style.display = 'none';

            try {
                const response = await fetch('/admin/monitoring/api/services');
                const data = await response.json();

                if (data.error) {
                    throw new Error(data.error);
                }

                renderServices(data);
            } catch (err) {
                errorMsg.innerText = "Erro ao carregar serviços: " + err.message;
                errorMsg.style.display = 'block';
                grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 3rem; color: var(--danger);">Falha na conexão com o CLI. Verifique se a RENDER_API_KEY está configurada.</div>';
            }
        }

        function renderServices(services) {
            const grid = document.getElementById('services-grid');
            grid.innerHTML = '';

            services.forEach(svc => {
                const statusClass = svc.status === 'live' ? 'badge-live' : (svc.status === 'suspended' ? 'badge-suspended' : 'badge-building');
                const card = document.createElement('div');
                card.className = 'card';
                card.innerHTML = `
                    <div class="card-header">
                        <div>
                            <div class="service-name">${svc.name}</div>
                            <div class="service-type">${svc.type}</div>
                        </div>
                        <span class="badge ${statusClass}">${svc.status.toUpperCase()}</span>
                    </div>
                    <div class="service-info">
                        <div>
                            <div class="info-label">Região</div>
                            <div class="info-value">${svc.region || 'N/A'}</div>
                        </div>
                        <div>
                            <div class="info-label">Ambiente</div>
                            <div class="info-value">${svc.env || 'Docker'}</div>
                        </div>
                    </div>
                    <button class="btn" onclick="viewLogs('${svc.id}', '${svc.name}')">
                        Ver Logs
                    </button>
                `;
                grid.appendChild(card);
            });
        }

        async function viewLogs(id, name) {
            const section = document.getElementById('logs-section');
            const window = document.getElementById('logs-window');
            const title = document.getElementById('logs-title');

            section.style.display = 'block';
            window.innerText = 'Carregando logs de ' + name + '...';
            title.innerText = 'Logs: ' + name;
            
            section.scrollIntoView({ behavior: 'smooth' });

            try {
                const response = await fetch(\`/admin/monitoring/api/logs/\${id}\`);
                const data = await response.json();

                if (data.error) {
                    window.innerText = "Erro: " + data.error;
                } else {
                    window.innerText = data.logs;
                    window.scrollTop = window.scrollHeight;
                }
            } catch (err) {
                window.innerText = "Erro ao carregar logs: " + err.message;
            }
        }

        function hideLogs() {
            document.getElementById('logs-section').style.display = 'none';
        }

        // Initial load
        fetchServices();
        // Refresh every 60s
        setInterval(fetchServices, 60000);
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)
