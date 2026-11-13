from .cli import main

# Permite executar com `python -m onfly_report`; o código de saída de main() vira o do processo.
raise SystemExit(main())
