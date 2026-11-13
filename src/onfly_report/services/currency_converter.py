"""Conversão de valores para BRL."""

from __future__ import annotations

from decimal import Decimal


def convert_to_brl(amount: Decimal, currency: str, rates: dict[str, Decimal]) -> Decimal:
    """Converte um valor na moeda informada para BRL usando a taxa da tabela.

    Lança KeyError se a moeda não existir na tabela. A chave precisa estar em maiúsculas:
    o repositório de câmbio normaliza para maiúsculas, mas o RowParser não normaliza a
    moeda da reserva, então "usd" minúsculo no CSV de reservas não encontraria a taxa.
    """
    rate = rates[currency]
    return amount * rate
