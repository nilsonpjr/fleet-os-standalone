"""
scaffold.py — Creates schema/crud/router placeholder files for all backend_v2 modules.
Run once: python backend_v2/scaffold.py
"""
import pathlib

MODULES = {
    "boats": ("/api/boats", "Barcos"),
    "inventory": ("/api/inventory", "Estoque"),
    "orders": ("/api/orders", "Ordens de Servico"),
    "fiscal": ("/api/fiscal", "Fiscal"),
    "finance": ("/api/finance", "Financeiro"),
    "partners": ("/api/partners", "Parceiros"),
    "config": ("/api/config", "Configuracoes"),
    "mercury": ("/api/mercury", "Mercury"),
    "public": ("/api/public", "Publico"),
}

BASE = pathlib.Path(__file__).parent / "modules"

for mod, (prefix, tag) in MODULES.items():
    base = BASE / mod

    # schemas.py
    p = base / "schemas.py"
    if not p.exists():
        p.write_text(f'"""Schemas for {mod} module."""\n', encoding="utf-8")
        print(f"  schemas: {p}")

    # crud.py
    if mod not in ("mercury", "public"):
        p = base / "crud.py"
        if not p.exists():
            p.write_text(f'"""CRUD for {mod} module."""\n', encoding="utf-8")
            print(f"  crud:    {p}")

    # router.py
    p = base / "router.py"
    if not p.exists():
        original = f"backend/routers/{mod}_router.py"
        content = f'''"""
{mod.title()} module router — {prefix} endpoints.

Scaffold — implement by migrating from {original}
with imports updated to backend_v2.
"""
from fastapi import APIRouter

router = APIRouter(prefix="{prefix}", tags=["{tag}"])

# TODO: Port endpoints from {original}
'''
        p.write_text(content, encoding="utf-8")
        print(f"  router:  {p}")

    print(f"[OK] {mod}")
