from controller_actions import ControllerActions, pick_moved_channel, position


class Source:
    def __init__(self):
        self.channels = [0.0, 0.0, -1.0, 0.0]

    def poll(self):
        return [
            {
                "name": "Radiomaster",
                "vendorId": 0x1209,
                "productId": 0x4F54,
                "serial": "A1",
                "channels": list(self.channels),
            }
        ]


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def make(tmp_path):
    source, clock = Source(), Clock()
    actions = ControllerActions(source, tmp_path / "actions.json", clock=clock)
    swaps = []
    actions.swapRequested.connect(lambda: swaps.append(clock.now))
    return actions, source, clock, swaps


def test_position_and_moved_channel():
    assert [position(v, -1, 1) for v in (-1, -0.1, 0.1, 1)] == [0, 1, 1, 2]
    assert pick_moved_channel([0, 0, -1, 0], [0.02, 0, 1, 0.01]) == 2
    assert pick_moved_channel([0, 0], [0.002, 0.001]) is None, "noise is not a flip"
    assert pick_moved_channel([-1, -1], [1, 0.8]) is None, "a stick moved too: not clear"
    assert pick_moved_channel([0, 1000], [10, 2000]) == 1, "raw ranges work too"


def test_assign_by_flipping_the_switch(tmp_path):
    actions, source, clock, swaps = make(tmp_path)
    assert actions.swapText == "не призначено"
    actions.learnSwap()
    assert actions.learning
    for _ in range(3):
        actions.poll()
    source.channels[2] = 1.0
    for _ in range(3):
        actions.poll()
    assert not actions.learning and actions.swapText == "канал 3"
    assert actions.message == "Потоки міняє канал 3"
    again = ControllerActions(Source(), tmp_path / "actions.json")
    assert again.swapText == "канал 3", "remembered"


def test_each_flip_swaps_the_streams_in_flight_only(tmp_path):
    actions, source, clock, swaps = make(tmp_path)
    actions.learnSwap()
    for value in (-1.0, -1.0, 1.0, 1.0, 1.0, 1.0):
        source.channels[2] = value
        actions.poll()
    source.channels[2] = -1.0
    actions.poll()
    actions.poll()
    assert swaps == [], "not in flight: nothing happens"
    actions.setActive(True)
    actions.poll()
    source.channels[2] = 1.0
    actions.poll()
    assert swaps == [], "a single sample may be a glitch"
    actions.poll()
    assert len(swaps) == 1
    source.channels[2] = 0.0  # middle of a three-position switch
    actions.poll()
    actions.poll()
    assert len(swaps) == 2


def test_learning_gives_up_after_a_while(tmp_path):
    actions, source, clock, swaps = make(tmp_path)
    actions.learnSwap()
    actions.poll()
    clock.now += 11
    actions.poll()
    assert not actions.learning and actions.message.startswith("Тумблер не помічено")
    actions.clearSwap()
    assert not actions.assigned
