from strategy import Stint, Strategy, is_valid_strategy


def test_valid_strategy_is_accepted():
    strategy = Strategy(stints=[Stint("SOFT", 15), Stint("MEDIUM", 35)])
    assert is_valid_strategy(strategy, race_length=50) is True


def test_wrong_total_laps_is_rejected():
    strategy = Strategy(stints=[Stint("SOFT", 15), Stint("MEDIUM", 30)])
    assert is_valid_strategy(strategy, race_length=50) is False


def test_single_compound_is_rejected_when_two_compounds_required():
    strategy = Strategy(stints=[Stint("SOFT", 25), Stint("SOFT", 25)])
    assert is_valid_strategy(strategy, race_length=50, require_two_compounds=True) is False


def test_single_compound_is_accepted_when_not_required():
    strategy = Strategy(stints=[Stint("SOFT", 25), Stint("SOFT", 25)])
    assert is_valid_strategy(strategy, race_length=50, require_two_compounds=False) is True


def test_non_positive_stint_length_is_rejected():
    strategy = Strategy(stints=[Stint("SOFT", 0), Stint("MEDIUM", 50)])
    assert is_valid_strategy(strategy, race_length=50) is False


def test_unknown_compound_is_rejected_when_checked():
    strategy = Strategy(stints=[Stint("SUPER-SOFT", 25), Stint("MEDIUM", 25)])
    assert is_valid_strategy(strategy, race_length=50, valid_compounds=["SOFT", "MEDIUM", "HARD"]) is False


def test_unknown_compound_is_ignored_when_not_checked():
    strategy = Strategy(stints=[Stint("SUPER-SOFT", 25), Stint("MEDIUM", 25)])
    assert is_valid_strategy(strategy, race_length=50, valid_compounds=None) is True

if __name__ == "__main__":
    test_valid_strategy_is_accepted()
    test_wrong_total_laps_is_rejected()
    test_single_compound_is_rejected_when_two_compounds_required()
    test_single_compound_is_accepted_when_not_required()
    test_non_positive_stint_length_is_rejected()
    test_unknown_compound_is_rejected_when_checked()
    test_unknown_compound_is_ignored_when_not_checked()
    print("All tests passed.")