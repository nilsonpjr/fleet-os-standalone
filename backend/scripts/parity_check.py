"""
Fase 2 — Script de Paridade de Endpoints
Compara os endpoints do backend/ original com backend_v2/ e reporta:
- ✅ Rotas presentes nos dois
- ⚠️  Rotas do backend/ que não existem no backend_v2/ (faltando)
- ℹ️  Rotas novas no backend_v2/ (LGPD, melhorias)

Usage: python backend_v2/scripts/parity_check.py
"""
import sys
sys.path.insert(0, ".")

import os
# Load .env
from dotenv import load_dotenv
load_dotenv(os.path.join("backend", ".env"), override=True)

# Silence startup logs
os.environ.setdefault("LOG_LEVEL", "ERROR")


def get_routes(app) -> set[str]:
    """Returns a set of 'METHOD /path' strings for all routes."""
    routes = set()
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            for method in route.methods:
                routes.add(f"{method} {route.path}")
    return routes


def normalize_path(path: str) -> str:
    """Normalizes path params: {id} → {param} for comparison."""
    import re
    return re.sub(r"\{[^}]+\}", "{param}", path)


def main():
    print("Loading backend/ (original)...")
    try:
        from backend.main import app as orig_app
        orig_routes = get_routes(orig_app)
        print(f"  ✓ {len(orig_routes)} routes loaded from backend/")
    except Exception as e:
        print(f"  ✗ Failed to load backend/: {e}")
        orig_routes = set()

    print("\nLoading backend_v2/ (modular)...")
    try:
        from main import app as v2_app
        v2_routes = get_routes(v2_app)
        print(f"  ✓ {len(v2_routes)} routes loaded from backend_v2/")
    except Exception as e:
        print(f"  ✗ Failed to load backend_v2/: {e}")
        v2_routes = set()

    # Normalize for comparison
    orig_norm = {normalize_path(r) for r in orig_routes}
    v2_norm = {normalize_path(r) for r in v2_routes}

    # Filter to only API routes
    orig_api = {r for r in orig_norm if "/api/" in r or r.endswith("/api")}
    v2_api = {r for r in v2_norm if "/api/" in r or r.endswith("/api")}

    missing_in_v2 = orig_api - v2_api
    new_in_v2 = v2_api - orig_api
    common = orig_api & v2_api

    print("\n" + "="*60)
    print(f"PARIDADE: {len(common)} rotas em comum")
    print(f"FALTANDO no v2: {len(missing_in_v2)}")
    print(f"NOVAS no v2: {len(new_in_v2)}")
    print("="*60)

    if missing_in_v2:
        print("\n⚠️  ROTAS DO BACKEND/ QUE NÃO ESTÃO NO BACKEND_V2/:")
        for r in sorted(missing_in_v2):
            print(f"  - {r}")

    if new_in_v2:
        print("\nℹ️  ROTAS NOVAS NO BACKEND_V2/ (melhorias/LGPD):")
        for r in sorted(new_in_v2):
            print(f"  + {r}")

    print("\n✅ ROTAS EM COMUM:")
    for r in sorted(common)[:20]:
        print(f"  = {r}")
    if len(common) > 20:
        print(f"  ... e mais {len(common) - 20} rotas")

    # Exit with error if critical routes missing
    critical_patterns = ["/auth", "/clients", "/boats", "/inventory", "/orders", "/transactions"]
    critical_missing = [r for r in missing_in_v2 if any(p in r for p in critical_patterns)]
    if critical_missing:
        print(f"\n🚨 {len(critical_missing)} ROTAS CRÍTICAS FALTANDO! Verifique antes de trocar para v2.")
        sys.exit(1)
    else:
        print("\n✅ Todas as rotas críticas estão presentes no backend_v2/")


if __name__ == "__main__":
    main()
