import pytest

from ipc_gateway.config import Tag
from ipc_gateway.plc import decode


def test_coil():
    assert decode(Tag("r", "coil", 0), [True, False]) is True


def test_scale():
    assert decode(Tag("i", "holding", 101, scale=0.1), [124]) == pytest.approx(12.4)


def test_int16_negative():
    assert decode(Tag("t", "holding", 0, format="int16"), [0xFFFE]) == -2


def test_uint32_big_endian_words():
    assert decode(Tag("p", "holding", 104, format="uint32"), [0x0001, 0x0002]) == 65538


def test_float32():
    # 12.5 = 0x41480000
    assert decode(Tag("f", "holding", 0, format="float32"), [0x4148, 0x0000]) == pytest.approx(12.5)


def test_enum():
    t = Tag("mode", "holding", 103, enum={0: "LOCAL", 1: "REMOTE"})
    assert decode(t, [1]) == "REMOTE"
    assert decode(t, [7]) == "UNKNOWN(7)"
