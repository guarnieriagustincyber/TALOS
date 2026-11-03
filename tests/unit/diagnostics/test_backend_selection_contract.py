from scripts.validate_backend_selection_contract_fixtures import validate_fixtures


def test_backend_selection_adversarial_contract_fixtures():
    assert validate_fixtures() == 15
