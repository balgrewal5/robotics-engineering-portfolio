from python_temperature_monitor.temperature_logic import check_temperature


def test_hot_temperature():
    assert check_temperature(47.8, 45.0) == 'HOT'


def test_normal_temperature():
    assert check_temperature(47.8, 50.0) == 'NORMAL'
