import matplotlib.pyplot as plt

from .model import hand_lines
from .processing import HandState


class HandVisualizer:
    def __init__(self):
        # Interactive mode cập nhật liên tục mà không chặn vòng đọc UART.
        plt.ion()
        self._figure = plt.figure("ESP32 Right Hand Tracker")
        self._axis = self._figure.add_subplot(111, projection="3d")

    def update(self, state: HandState) -> None:
        # Vẽ lại sáu polyline: một lòng bàn tay và năm ngón.
        self._axis.clear()
        for index, points in enumerate(hand_lines(state)):
            self._axis.plot(points[:, 0], points[:, 1], points[:, 2],
                            linewidth=3 if index else 2, marker="o" if index else None)
        # Giữ scale cố định để chuyển động không làm camera tự co giãn mỗi frame.
        self._axis.set(xlim=(-0.16, 0.16), ylim=(-0.20, 0.12), zlim=(-0.20, 0.12),
                       xlabel="+X đầu ngón → lòng bàn tay", ylabel="+Y cái → út",
                       zlabel="+Z hướng lên")
        self._axis.set_box_aspect((1, 1, 1))
        # draw_idle gom yêu cầu vẽ, pause xử lý event của cửa sổ GUI.
        self._figure.canvas.draw_idle()
        plt.pause(0.001)
