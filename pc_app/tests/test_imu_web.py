import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1]))

from hand_tracker.protocol import SensorFrame
from imu_web import ImuProcessor, ImuStateStore


def test_hand_view_uses_requested_right_hand_axes_and_reset():
    html = (Path(__file__).parents[1] / "imu_web.html").read_text(encoding="utf-8")

    assert "Xanh dương +X: đầu ngón → lòng bàn tay" in html
    assert "Đỏ +Y: ngón cái → ngón út" in html
    assert "Xanh lá +Z: hướng lên" in html
    assert 'id="resetOrientation"' in html
    assert "referenceQuaternion = conjugateQuaternion(sensorQuaternion)" in html
    assert "buildHandGeometry()" in html
    assert "fingerBends" in html


def test_level_imu_frame_produces_identity_quaternion():
    processor = ImuProcessor()
    frame = SensorFrame(
        sequence=7,
        timestamp_us=20_000,
        flex_raw=(0, 0, 0, 0, 0),
        accel_raw=(0, 0, -981),
        gyro_raw=(0, 0, 0),
        # +Y cảm biến được đổi thành +X của mô hình.
        mag_raw=(0, 480, 0),
    )

    state = processor.process(frame)

    assert state["connected"] is True
    assert state["sequence"] == 7
    assert state["quaternion"] == pytest.approx((1.0, 0.0, 0.0, 0.0))
    assert state["accel"] == pytest.approx((0.0, 0.0, 9.81))
    assert state["mag"] == pytest.approx((30.0, 0.0, 0.0))
    assert len(state["bends"]) == 5


def test_state_store_reports_uart_error_without_losing_last_orientation():
    stateStore = ImuStateStore()
    stateStore.update({"connected": True, "quaternion": (0.5, 0.5, 0.5, 0.5)})

    stateStore.setError("mất UART")
    snapshot = stateStore.snapshot()

    assert snapshot["connected"] is False
    assert snapshot["quaternion"] == (0.5, 0.5, 0.5, 0.5)
    assert snapshot["error"] == "mất UART"
