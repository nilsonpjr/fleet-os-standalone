"""
Thread-local / ContextVar storage for current tenant_id.
Used by the RLS middleware in core/database.py.
"""
from __future__ import annotations
from contextvars import ContextVar

_tenant_id_var: ContextVar[int | None] = ContextVar("tenant_id", default=None)


def set_tenant_id(tenant_id: int | None) -> None:
    _tenant_id_var.set(tenant_id)


def get_tenant_id() -> int | None:
    return _tenant_id_var.get()
