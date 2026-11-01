import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1]))

from hand_tracker.protocol import crc16_ccitt, decode_frame


def make_frame(payload: bytes) -> bytes:
    return payload + f"*{crc16_ccitt(payload):04X}\n".encode()


def test_decode_valid_frame():
    payload = b"HAND,42,1000000,1000,1100,1200,1300,1400,1,2,3,4,5,6,7,8,9"
    frame = decode_frame(make_frame(payload))
    assert frame.sequence == 42
    assert frame.flex_raw == (1000, 1100, 1200, 1300, 1400)
    assert frame.gyro_raw == (4, 5, 6)


def test_rejects_corrupt_crc():
    with pytest.raises(ValueError, match="CRC"):
        decode_frame(b"HAND,1,2,3*0000\n")


def test_rejects_out_of_range_adc():
    payload = b"HAND,42,1,4096,1,1,1,1,1,2,3,4,5,6,7,8,9"
    with pytest.raises(ValueError, match="ADC"):
        decode_frame(make_frame(payload))
