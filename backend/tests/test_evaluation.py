from app.evaluation import run_benchmark


def test_reference_benchmark_is_reproducible():
    result = run_benchmark()
    assert result["total"] == 8
    assert result["accuracy"] == 1.0
