from ml.energy_optimizer import optimize


def test_unoccupied_disables_hvac_and_lighting():
    action = optimize(occupied=False, ambient_light=20, temperature=30)
    assert action.light_level == 0
    assert action.hvac_enabled is False


def test_occupied_hot_room_enables_hvac():
    action = optimize(occupied=True, ambient_light=80, temperature=30)
    assert action.hvac_enabled is True
