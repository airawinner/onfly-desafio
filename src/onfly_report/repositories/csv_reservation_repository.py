"""Leitura da exportação de reservas em CSV."""

from __future__ import annotations

import csv
from pathlib import Path

from ..exceptions import InputFileError
from ..models import RawRow

# Colunas que precisam existir no cabeçalho. "booked_at" é exigida na validação,
# mas não é usada nos cálculos do relatório.
REQUIRED_COLUMNS = (
    "reservation_id",
    "traveler_name",
    "company_id",
    "hotel_id",
    "hotel_name",
    "city",
    "country",
    "checkin_date",
    "checkout_date",
    "rooms",
    "status",
    "currency",
    "amount",
    "payment_method",
    "booked_at",
)


class CsvReservationRepository:
    """Lê a exportação de reservas sem aplicar regra de negócio."""

    def __init__(self, path: Path) -> None:
        """Guarda o caminho do CSV; o arquivo só é aberto em read()."""
        self._path = path

    def read(self) -> list[RawRow]:
        """Lê todas as linhas e devolve RawRow com o número da linha física de cada uma."""
        try:
            with self._path.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                missing = [column for column in REQUIRED_COLUMNS if column not in (reader.fieldnames or [])]
                if missing:
                    raise InputFileError(f"colunas obrigatórias ausentes: {', '.join(missing)}")

                rows: list[RawRow] = []
                for values in reader:
                    # reader.line_num é a posição física no arquivo, usada nas mensagens de erro.
                    rows.append(RawRow(line_number=reader.line_num, values=values))
                return rows
        # Converte erros de sistema e de formato CSV em InputFileError, para a CLI tratar como erro de entrada.
        except FileNotFoundError as err:
            raise InputFileError(f"arquivo de reservas não encontrado: {self._path}") from err
        except (OSError, csv.Error) as err:
            raise InputFileError(f"falha ao ler {self._path}: {err}") from err
