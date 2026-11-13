# ♡ Entrega — Consolidador de reservas de hotel (Onfly)

**RELATÓRIO TÉCNICO · CORREÇÃO · VALIDAÇÃO**

*Uma análise dos defeitos, das correções implementadas e dos resultados obtidos.*

---

## 01. Apresentação

O projeto consiste na correção de um CLI responsável por consolidar reservas de hotel e gerar um relatório no formato JSON.

O código inicial apresentava inconsistências nos resultados, embora os arquivos CSV fornecidos estivessem consistentes. O trabalho foi direcionado à investigação da lógica de leitura, conversão de valores, aplicação das regras de negócio e agregação dos dados.

O objetivo foi corrigir os problemas sem alterar o contrato de execução do CLI, o formato do relatório ou os arquivos de dados originais.

## 02. Defeitos corrigidos

Foram encontrados **5 defeitos**, todos no CLI. Os dados e os testes fornecidos não foram alterados.

| # | Arquivo | Defeito | Causa raiz (uma frase) |
|:-:|---------|---------|------------------------|
| 1 | `repositories/csv_reservation_repository.py` | O relatório ignorava reservas a partir da 201ª (o CSV tem 300). | O leitor tinha um `break` ao atingir 200 linhas, truncando o arquivo em silêncio. |
| 2 | `services/currency_converter.py` | Valores em USD/EUR vinham muito menores que o real. | A conversão dividia pela taxa em vez de multiplicar, e ainda passava por `float`, perdendo a exatidão do `Decimal`. |
| 3 | `services/status_policy.py` | `NO_SHOW` entrava em noites, valores, `by_month` e `top_hotels`. | `is_billable` era `status != "CANCELLED"`, quando só `CONFIRMED` é faturável. |
| 4 | `services/stay_calculator.py` | Estadias na virada de mês davam noites erradas (ou negativas). | O cálculo usava `checkout.day - checkin.day` em vez da diferença real de datas. |
| 5 | `services/report_builder.py` | `top_hotels` listava os hotéis de menor valor primeiro. | A ordenação usava `amount` crescente, em vez de `total_brl` decrescente com desempate por `hotel_id` crescente. |

### Correções aplicadas

1. Removido o limite de 200 linhas do leitor.
2. `return amount * rate` — somente `Decimal`, sem `float`.
3. `return status == "CONFIRMED"`.
4. `return (checkout - checkin).days * rooms`.
5. `key=lambda item: (-item[1]["amount"], item[0])`.

**O que já estava correto e foi mantido:** arredondamento half-up somente na serialização (`format_money`), média `"0.00"` sem noites, `by_month` pelo mês do check-in e ordenado, contagem de status antes do filtro, offset `-03:00` e códigos de saída.

## 03. Como investiguei

1. Li o README do projeto, incluindo as regras de negócio e o contrato do CLI, além dos testes fornecidos para identificar o comportamento esperado.
2. Analisei o código seguindo o fluxo descrito no enunciado: `ler → converter tipos → contar status → filtrar CONFIRMED → agregar`. Cada etapa foi comparada com sua regra correspondente, permitindo identificar os desvios.
3. Analisei o arquivo `reservas_hoteis.csv` (300 linhas), verificando status, moedas, quantidade de quartos, campos em branco e datas de check-in e check-out. Os dados estavam consistentes, confirmando que os problemas estavam na implementação. O limite de 200 linhas ficou evidente ao comparar a quantidade de registros do arquivo com a leitura realizada pelo programa.
4. Apliquei as correções e validei os resultados em diferentes etapas:
   - Os testes fornecidos.
   - A amostra `data/exemplo-validacao.csv`, comparando os resultados com os valores esperados no README original.
   - Uma conferência independente do dataset completo, utilizando um script separado do pacote, para comparar os resultados com os produzidos pelo CLI.
5. Adicionei `tests/test_extra_regressions.py` com 11 testes para cenários adicionais não cobertos pelos testes fornecidos:
   - Arquivo com mais de 200 linhas.
   - Virada de ano com vários quartos.
   - Desempate do ranking de hotéis.
   - Argumento `--top` maior que a quantidade de hotéis.
   - Soma exata com arredondamento half-up somente no final.
   - Ausência de conversões monetárias por `float`.
   - Média zero sem reservas confirmadas.
   - Exclusão de `NO_SHOW` de `by_month` e `top_hotels`.
   - Códigos de saída 2.
   - Validação do schema do JSON.

## 04. Como validar

Os comandos abaixo foram utilizados no Git Bash, a partir da pasta raiz do projeto.

### Preparação do ambiente

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

### Executar os testes

```bash
python -m pytest -q
```

### Executar a amostra de validação

```bash
PYTHONPATH=src python -m onfly_report \
  --input data/exemplo-validacao.csv \
  --rates data/taxas_cambio.csv \
  --output output/exemplo.json
```

### Executar o dataset completo

```bash
PYTHONPATH=src python -m onfly_report \
  --input data/reservas_hoteis.csv \
  --rates data/taxas_cambio.csv \
  --output output/report.json
```

### Visualizar os arquivos gerados

```bash
cat output/exemplo.json
cat output/report.json
```

## 05. Resultados

### 5.1. Amostra de validação

A execução com `data/exemplo-validacao.csv` produziu os seguintes resultados.

**Saída bruta (`cat output/exemplo.json`):**

```json
{
  "report_version": "1.0",
  "generated_at": "2026-11-13T18:15:48-03:00",
  "summary": {
    "total_reservations": 12,
    "confirmed_reservations": 9,
    "cancelled_reservations": 2,
    "no_show_reservations": 1,
    "total_room_nights": 28,
    "total_amount_brl": "7566.00",
    "average_nightly_rate_brl": "270.21"
  },
  "by_month": [
    {
      "month": "2025-01",
      "reservations": 8,
      "room_nights": 25,
      "total_brl": "6684.00"
    },
    {
      "month": "2025-02",
      "reservations": 1,
      "room_nights": 3,
      "total_brl": "882.00"
    }
  ],
  "top_hotels": [
    {
      "hotel_id": "H01",
      "hotel_name": "Hotel Aurora Paulista",
      "room_nights": 3,
      "total_brl": "1200.00"
    },
    {
      "hotel_id": "H02",
      "hotel_name": "Hotel Mirante",
      "room_nights": 2,
      "total_brl": "1084.00"
    },
    {
      "hotel_id": "H12",
      "hotel_name": "Hotel Miami Beach",
      "room_nights": 1,
      "total_brl": "1000.00"
    },
    {
      "hotel_id": "H10",
      "hotel_name": "Hotel Madrid, Gran Vía",
      "room_nights": 4,
      "total_brl": "900.00"
    },
    {
      "hotel_id": "H09",
      "hotel_name": "Hotel Lisboa, Centro",
      "room_nights": 3,
      "total_brl": "882.00"
    }
  ]
}
```

**Resumo geral**

| Indicador | Resultado |
|-----------|----------:|
| `total_reservations` | 12 |
| `confirmed_reservations` | 9 |
| `cancelled_reservations` | 2 |
| `no_show_reservations` | 1 |
| `total_room_nights` | 28 |
| `total_amount_brl` | 7566.00 |
| `average_nightly_rate_brl` | 270.21 |

**Consolidação mensal**

| Mês | Reservas | Noites | Total (BRL) |
|-----|---------:|-------:|------------:|
| 2025-01 | 8 | 25 | 6684.00 |
| 2025-02 | 1 | 3 | 882.00 |

**Top 5 hotéis**

| Hotel ID | Nome | Noites | Total (BRL) |
|----------|------|-------:|------------:|
| H01 | Hotel Aurora Paulista | 3 | 1200.00 |
| H02 | Hotel Mirante | 2 | 1084.00 |
| H12 | Hotel Miami Beach | 1 | 1000.00 |
| H10 | Hotel Madrid, Gran Vía | 4 | 900.00 |
| H09 | Hotel Lisboa, Centro | 3 | 882.00 |

Os resultados correspondem aos valores esperados na amostra disponibilizada pelo desafio.

### 5.2. Dataset completo

A execução com `data/reservas_hoteis.csv` processou os 300 registros do arquivo.

**Saída bruta (`cat output/report.json`):**

```json
{
  "report_version": "1.0",
  "generated_at": "2026-11-13T18:17:44-03:00",
  "summary": {
    "total_reservations": 300,
    "confirmed_reservations": 235,
    "cancelled_reservations": 31,
    "no_show_reservations": 34,
    "total_room_nights": 1347,
    "total_amount_brl": "396170.00",
    "average_nightly_rate_brl": "294.11"
  },
  "by_month": [
    {
      "month": "2024-12",
      "reservations": 35,
      "room_nights": 174,
      "total_brl": "61335.80"
    },
    {
      "month": "2025-01",
      "reservations": 37,
      "room_nights": 235,
      "total_brl": "64662.89"
    },
    {
      "month": "2025-02",
      "reservations": 26,
      "room_nights": 138,
      "total_brl": "45991.09"
    },
    {
      "month": "2025-03",
      "reservations": 39,
      "room_nights": 215,
      "total_brl": "65984.99"
    },
    {
      "month": "2025-04",
      "reservations": 21,
      "room_nights": 146,
      "total_brl": "31335.97"
    },
    {
      "month": "2025-05",
      "reservations": 39,
      "room_nights": 196,
      "total_brl": "63507.98"
    },
    {
      "month": "2025-06",
      "reservations": 38,
      "room_nights": 243,
      "total_brl": "63351.29"
    }
  ],
  "top_hotels": [
    {
      "hotel_id": "H06",
      "hotel_name": "Hotel Salvador Centro",
      "room_nights": 160,
      "total_brl": "45165.46"
    },
    {
      "hotel_id": "H10",
      "hotel_name": "Hotel Madrid, Gran Vía",
      "room_nights": 120,
      "total_brl": "45041.69"
    },
    {
      "hotel_id": "H12",
      "hotel_name": "Hotel Miami Beach",
      "room_nights": 106,
      "total_brl": "41647.69"
    },
    {
      "hotel_id": "H07",
      "hotel_name": "Hotel Brasília Tower",
      "room_nights": 148,
      "total_brl": "39920.52"
    },
    {
      "hotel_id": "H11",
      "hotel_name": "Hotel Buenos Aires",
      "room_nights": 102,
      "total_brl": "37455.69"
    }
  ]
}
```

**Resumo geral**

| Campo | Valor |
|-------|------:|
| `total_reservations` | 300 |
| `confirmed_reservations` | 235 |
| `cancelled_reservations` | 31 |
| `no_show_reservations` | 34 |
| `total_room_nights` | 1347 |
| `total_amount_brl` | 396170.00 |
| `average_nightly_rate_brl` | 294.11 |

**Consolidação mensal**

| Mês | Reservas | Noites | Total (BRL) |
|-----|---------:|-------:|------------:|
| 2024-12 | 35 | 174 | 61335.80 |
| 2025-01 | 37 | 235 | 64662.89 |
| 2025-02 | 26 | 138 | 45991.09 |
| 2025-03 | 39 | 215 | 65984.99 |
| 2025-04 | 21 | 146 | 31335.97 |
| 2025-05 | 39 | 196 | 63507.98 |
| 2025-06 | 38 | 243 | 63351.29 |

**Top 5 hotéis**

| Hotel ID | Nome | Noites | Total (BRL) |
|----------|------|-------:|------------:|
| H06 | Hotel Salvador Centro | 160 | 45165.46 |
| H10 | Hotel Madrid, Gran Vía | 120 | 45041.69 |
| H12 | Hotel Miami Beach | 106 | 41647.69 |
| H07 | Hotel Brasília Tower | 148 | 39920.52 |
| H11 | Hotel Buenos Aires | 102 | 37455.69 |

### 5.3. Resultado dos testes

Execução realizada com:

```bash
python -m pytest -q
```

**Resultado observado:**

```text
16 passed
```

Os 16 testes correspondem aos 5 testes fornecidos e aos 11 testes adicionais de regressão.

## 06. Estrutura dos arquivos de entrega

Os relatórios gerados durante a validação estão disponíveis na pasta `output/`:

```text
entrega/
├── README-ENTREGA.md
└── uso-de-ia/
    ├── sessao.md
    └── declaracao.md

output/
├── exemplo.json
└── report.json
```

## 07. Considerações finais

As cinco falhas identificadas foram corrigidas, preservando as regras de negócio e o contrato de saída do projeto.

A validação demonstrou que:

- A amostra produz os valores esperados pelo enunciado.
- O dataset completo é processado sem truncamento.
- Os cálculos de noites, faturamento e conversão monetária seguem as regras especificadas.
- A ordenação mensal e o ranking dos hotéis respeitam os critérios definidos.
- Os 16 testes automatizados foram aprovados.

O resultado é uma implementação que atende ao comportamento esperado do desafio e mantém a estrutura original de utilização do CLI.

---

*♡ Onfly · Relatório de entrega*
*Python · Consolidação de dados · Testes automatizados*
