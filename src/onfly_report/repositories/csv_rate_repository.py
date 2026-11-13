"""Leitura da tabela de câmbio para BRL."""

from __future__ import annotations

import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ..exceptions import InputFileError

REQUIRED_COLUMNS = ("currency", "rate_to_brl")


class CsvRateRepository:
    """Carrega moeda -> taxa para BRL a partir de um CSV."""

    def __init__(self, path: Path) -> None:
        """Guarda o caminho do CSV; o arquivo só é aberto em read()."""
        self._path = path

    def read(self) -> dict[str, Decimal]:
        """Lê o CSV e devolve um dicionário moeda -> taxa; levanta InputFileError se houver problema."""
        rates: dict[str, Decimal] = {}
        try:
            with self._path.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                # fieldnames é None num arquivo vazio, por isso o "or []".
                missing = [column for column in REQUIRED_COLUMNS if column not in (reader.fieldnames or [])]
                if missing:
                    raise InputFileError(f"colunas obrigatórias ausentes em {self._path}: {', '.join(missing)}")

                for values in reader:
                    # A moeda é normalizada para maiúsculas, para casar com "BRL", "USD" e assim por diante.
                    currency = (values.get("currency") or "").strip().upper()
                    raw_rate = (values.get("rate_to_brl") or "").strip()
                    if not currency or not raw_rate:
                        raise InputFileError(f"linha de câmbio incompleta em {self._path}")
                    # Decimal (e não float) evita erro de arredondamento binário nos valores.
                    try:
                        rate = Decimal(raw_rate)
                    except InvalidOperation as err:
                        raise InputFileError(f"taxa inválida para {currency} em {self._path}") from err
                    if rate <= 0:
                        raise InputFileError(f"taxa não positiva para {currency} em {self._path}")
                    # Se a mesma moeda aparecer mais de uma vez, vale a última linha.
                    rates[currency] = rate
        # Converte erros de sistema e de formato CSV em InputFileError, para a CLI tratar como erro de entrada.
        except FileNotFoundError as err:
            raise InputFileError(f"tabela de câmbio não encontrada: {self._path}") from err
        except (OSError, csv.Error) as err:
            raise InputFileError(f"falha ao ler {self._path}: {err}") from err

        # Um CSV sem linhas de dados é erro: o relatório não teria como converter nenhum valor.
        if not rates:
            raise InputFileError(f"tabela de câmbio vazia: {self._path}")
        return rates
