"""Política de status das reservas."""

from __future__ import annotations


def is_billable(status: str) -> bool:
    """Indica se a reserva entra nos totais financeiros e de noites.

    Só CONFIRMED conta; CANCELLED e NO_SHOW aparecem apenas nas contagens de status.
    """
    return status == "CONFIRMED"
