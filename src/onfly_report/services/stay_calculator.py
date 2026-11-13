"""Cálculo de noites ocupadas."""

from __future__ import annotations

from datetime import date


def calculate_room_nights(checkin: date, checkout: date, rooms: int) -> int:
    """Calcula noites de quarto: diferença de dias (não inclusiva) vezes quartos."""
    # Exemplo: entrada dia 10 e saída dia 13 são 3 noites. Não há validação:
    # saída anterior à entrada gera número negativo.
    return (checkout - checkin).days * rooms
