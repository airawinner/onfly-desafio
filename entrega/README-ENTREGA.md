# Entrega — Consolidador de reservas de hotel (Onfly)

## Defeitos corrigidos

Foram encontrados **5 defeitos**, todos no CLI (os dados e os testes não foram alterados).

| # | Arquivo | Defeito | Causa raiz (uma frase) |
|---|---------|---------|------------------------|
| 1 | `repositories/csv_reservation_repository.py` | O relatório ignorava reservas a partir da 201ª (o CSV tem 300) | O leitor tinha um `break` ao atingir 200 linhas, truncando o arquivo em silêncio. |
| 2 | `services/currency_converter.py` | Valores em USD/EUR vinham muito menores que o real | A conversão **dividia** pela taxa em vez de multiplicar, e ainda passava por `float`, perdendo a exatidão do `Decimal`. |
| 3 | `services/status_policy.py` | `NO_SHOW` entrava em noites, valores, `by_month` e `top_hotels` | `is_billable` era `status != "CANCELLED"`, quando só `CONFIRMED` é faturável. |
| 4 | `services/stay_calculator.py` | Estadias na virada de mês davam noites erradas (ou negativas) | O cálculo usava `checkout.day - checkin.day` em vez da diferença real de datas. |
| 5 | `services/report_builder.py` | `top_hotels` listava os hotéis de **menor** valor primeiro | A ordenação usava `amount` crescente, em vez de `total_brl` decrescente com desempate por `hotel_id` crescente. |

Correções aplicadas:

1. Removido o limite de 200 linhas do leitor.
2. `return amount * rate` (somente `Decimal`, sem `float`).
3. `return status == "CONFIRMED"`.
4. `return (checkout - checkin).days * rooms`.
5. `key=lambda item: (-item[1]["amount"], item[0])`.

O que **já estava correto** e foi mantido: arredondamento half-up só na serialização (`format_money`), média `0.00` sem noites, `by_month` pelo mês do check-in e ordenado, contagem de status antes do filtro, offset `-03:00`, códigos de saída.

## Como investiguei

1. Li o README (regras de negócio e contrato) e os testes fornecidos para saber o comportamento esperado.
2. Li o código seguindo o fluxo do README: `ler → converter tipos → contar status → filtrar CONFIRMED → agregar`, comparando cada etapa com a regra correspondente. Cada função tinha uma regra clara, então cada desvio apareceu como um defeito isolado.
3. Analisei o `reservas_hoteis.csv` (300 linhas; status, moedas, quartos, espaços em branco, check-out ≤ check-in) para descartar armadilhas nos dados. Estavam limpos, o que confirma que o problema era o código. O limite de 200 linhas só ficou evidente ao notar que o arquivo tem 300.
4. Apliquei as correções e validei em três camadas:
   - os 5 testes fornecidos;
   - a amostra `data/exemplo-validacao.csv`, que bate exatamente com a tabela do README (12 / 9 / 2 / 1, 28 noites, `7566.00`, `270.21`, meses e ranking);
   - uma conferência independente do dataset real, com um script separado que não usa o pacote: o resultado é idêntico ao do CLI.
5. Adicionei `tests/test_extra_regressions.py` com 11 testes para o que os fornecidos não cobrem: arquivo com mais de 200 linhas, virada de ano com vários quartos, desempate do ranking, `--top` maior que o nº de hotéis, soma exata com arredondamento half-up só no fim, ausência de erro de `float`, média zero sem confirmadas, exclusão de `NO_SHOW` de `by_month`/`top_hotels`, códigos de saída 2 e schema do JSON.

## Como validar

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q

PYTHONPATH=src python -m onfly_report \
  --input data/exemplo-validacao.csv --rates data/taxas_cambio.csv --output output/exemplo.json

PYTHONPATH=src python -m onfly_report \
  --input data/reservas_hoteis.csv --rates data/taxas_cambio.csv --output output/report.json
```

## Resultado

Dataset real (`reservas_hoteis.csv`):

| Campo | Valor |
|-------|-------|
| `total_reservations` | 300 |
| `confirmed_reservations` | 235 |
| `cancelled_reservations` | 31 |
| `no_show_reservations` | 34 |
| `total_room_nights` | 1347 |
| `total_amount_brl` | 396170.00 |
| `average_nightly_rate_brl` | 294.11 |

Top 5 hotéis: H06 (45165.46), H10 (45041.69), H12 (41647.69), H07 (39920.52), H11 (37455.69).

Resultado do `pytest -q`:

```
<COLE AQUI A SAÍDA REAL DO SEU pytest -q>
```
