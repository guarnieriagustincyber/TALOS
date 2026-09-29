import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "generate_gate2_benchmark.py"
SPEC = importlib.util.spec_from_file_location("generate_gate2_benchmark_cli", SCRIPT)
assert SPEC and SPEC.loader
generator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(generator)


def test_cli_proposal_requires_explicit_retrieval_consent(tmp_path):
    with pytest.raises(generator.Gate2GeneratorError, match="allow-retrieval"):
        generator.main(
            [
                "--mode",
                "proposal",
                "--dataset",
                str(tmp_path / "dataset.json"),
                "--qrels",
                str(tmp_path / "qrels.json"),
                "--decisions",
                str(tmp_path / "decisions.json"),
                "--output-dir",
                str(tmp_path / "output"),
                "--version",
                "fixture",
            ]
        )
