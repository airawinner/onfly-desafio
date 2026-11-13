"""Testes adicionais: cobrem defeitos que os testes fornecidos não exercitam."""

import json
import subprocess
import sys

from helpers import BASE, COLUMNS, PROJECT_ROOT, SRC_DIR, run_cli


def test_reads_all_rows_beyond_200(tmp_path):
    """O leitor não pode truncar o arquivo (havia um limite silencioso de 200 linhas)."""
    rows = [{"reservation_id": f"R-{i}"} for i in range(250)]
    report = run_cli(tmp_path, rows)
    assert report["summary"]["total_reservations"] == 250
    assert report["summary"]["confirmed_reservations"] == 250
    assert report["summary"]["total_amount_brl"] == "25000.00"


def test_nights_across_year_boundary_and_rooms(tmp_path):
    """Virada de ano com 2 quartos: 3 noites x 2 quartos = 6 noites-quarto; o mês é o do check-in."""
    report = run_cli(
        tmp_path,
        [{"checkin_date": "2024-12-30", "checkout_date": "2025-01-02", "rooms": "2"}],
    )
    assert report["summary"]["total_room_nights"] == 6
    assert report["by_month"][0]["month"] == "2024-12"


def test_top_hotels_tie_breaks_by_hotel_id_ascending(tmp_path):
    """Hotéis com o mesmo valor são ordenados pelo hotel_id, em ordem crescente."""
    report = run_cli(
        tmp_path,
        [
            {"reservation_id": "R-1", "hotel_id": "H09", "hotel_name": "I", "amount": "500.00"},
            {"reservation_id": "R-2", "hotel_id": "H02", "hotel_name": "B", "amount": "500.00"},
            {"reservation_id": "R-3", "hotel_id": "H05", "hotel_name": "E", "amount": "500.00"},
        ],
    )
    assert [h["hotel_id"] for h in report["top_hotels"]] == ["H02", "H05", "H09"]


def test_top_returns_fewer_items_when_fewer_hotels(tmp_path):
    """Se há menos hotéis do que --top, o ranking traz só os que existem."""
    report = run_cli(tmp_path, [{"hotel_id": "H01"}], top=10)
    assert len(report["top_hotels"]) == 1


def test_money_is_summed_exactly_and_rounded_half_up_only_at_serialization(tmp_path):
    """0.005 + 0.005 = 0.01 exato; arredondar cada parcela daria 0.02 (ou 0.00)."""
    report = run_cli(
        tmp_path,
        [
            {"reservation_id": "R-1", "amount": "0.005"},
            {"reservation_id": "R-2", "amount": "0.005"},
        ],
    )
    assert report["summary"]["total_amount_brl"] == "0.01"
    report = run_cli(tmp_path, [{"amount": "0.125"}])
    assert report["summary"]["total_amount_brl"] == "0.13"


def test_conversion_has_no_float_error(tmp_path):
    """Conversão exata com Decimal: 33,33 x 5,42 arredonda para 180,65."""
    # 33.33 * 5.42 = 180.6486 -> 180.65
    report = run_cli(tmp_path, [{"currency": "USD", "amount": "33.33"}])
    assert report["summary"]["total_amount_brl"] == "180.65"


def test_average_is_zero_without_confirmed(tmp_path):
    """Sem reservas confirmadas, totais e médias ficam zerados, sem divisão por zero."""
    report = run_cli(tmp_path, [{"status": "CANCELLED"}, {"reservation_id": "R-2", "status": "NO_SHOW"}])
    summary = report["summary"]
    assert summary["total_room_nights"] == 0
    assert summary["total_amount_brl"] == "0.00"
    assert summary["average_nightly_rate_brl"] == "0.00"
    assert report["by_month"] == []
    assert report["top_hotels"] == []


def test_non_confirmed_do_not_enter_by_month_nor_top_hotels(tmp_path):
    """Reservas NO_SHOW não entram na série mensal nem no ranking."""
    report = run_cli(
        tmp_path,
        [
            {"reservation_id": "R-1", "status": "NO_SHOW", "hotel_id": "H09", "amount": "999.00"},
            {"reservation_id": "R-2", "status": "CONFIRMED", "hotel_id": "H01", "amount": "10.00"},
        ],
    )
    assert report["by_month"] == [{"month": "2025-01", "reservations": 1, "room_nights": 1, "total_brl": "10.00"}]
    assert [h["hotel_id"] for h in report["top_hotels"]] == ["H01"]


def _run(args, cwd=PROJECT_ROOT):
    """Executa a CLI com ambiente mínimo (sem PATH) e devolve o resultado sem checar o código de saída."""
    return subprocess.run(
        [sys.executable, "-m", "onfly_report", *args],
        cwd=str(cwd),
        env={"PYTHONPATH": str(SRC_DIR), "PATH": ""},
        capture_output=True,
        text=True,
    )


def test_exit_code_2_on_missing_input(tmp_path):
    """Arquivo de entrada inexistente deve encerrar com código 2."""
    result = _run(["--input", str(tmp_path / "nao_existe.csv"), "--rates", str(tmp_path / "r.csv")])
    assert result.returncode == 2


def test_exit_code_2_on_invalid_top(tmp_path):
    """--top 0 é rejeitado com código 2."""
    csv_path = tmp_path / "in.csv"
    csv_path.write_text(",".join(COLUMNS) + "\n" + ",".join(BASE[c] for c in COLUMNS) + "\n", encoding="utf-8")
    rates = tmp_path / "r.csv"
    rates.write_text("currency,rate_to_brl\nBRL,1\n", encoding="utf-8")
    result = _run(["--input", str(csv_path), "--rates", str(rates), "--top", "0"])
    assert result.returncode == 2


def test_report_schema_keys(tmp_path):
    """Confere as chaves e a ordem do JSON, a versão e o fuso -03:00 de generated_at."""
    report = run_cli(tmp_path, [{}])
    assert list(report) == ["report_version", "generated_at", "summary", "by_month", "top_hotels"]
    assert report["report_version"] == "1.0"
    assert report["generated_at"].endswith("-03:00")
    json.dumps(report)
