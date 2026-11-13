"""Configuração de logging do CLI (sempre em stderr)."""

from __future__ import annotations

import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    """Configura o logger raiz para stderr, mantendo o stdout para o resumo."""
    # basicConfig só tem efeito na primeira chamada; se o logger raiz já tiver handlers, não faz nada.
    logging.basicConfig(
        level=level,
        stream=sys.stderr,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
