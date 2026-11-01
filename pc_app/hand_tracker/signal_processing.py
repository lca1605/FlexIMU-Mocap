import math


Quaternion = tuple[float, float, float, float]
Vector3 = tuple[float, float, float]


def sensorToBodyVector(vector: Vector3) -> Vector3:
    """Hoán đổi X/Y cảm biến và đảo Z trước khi xử lý orientation."""
    x, y, z = vector
    return (y, x, -z)


class GyroBiasEstimator:
    """Học offset gyro khi IMU đứng yên rồi trả tốc độ góc đã khử bias."""

    def __init__(self, minimumStationaryS: float = 0.5,
                 timeConstantS: float = 3.0,
                 maxGyroRadS: float = math.radians(3.0),
                 gravityTolerance: float = 1.2):
        if minimumStationaryS < 0.0 or timeConstantS <= 0.0:
            raise ValueError("Thời gian ước lượng bias gyro không hợp lệ")
        self._minimumStationaryS = minimumStationaryS
        self._timeConstantS = timeConstantS
        self._maxGyroRadS = maxGyroRadS
        self._gravityTolerance = gravityTolerance
        self._stationaryTimeS = 0.0
        self._bias: Vector3 = (0.0, 0.0, 0.0)
        self._hasBias = False

    @property
    def biasRadS(self) -> Vector3:
        return self._bias

    def update(self, accel: Vector3, gyroRadS: Vector3, dtS: float) -> Vector3:
        dtS = min(max(dtS, 0.0), 0.2)
        accelNorm = math.sqrt(sum(value * value for value in accel))
        gyroNorm = math.sqrt(sum(value * value for value in gyroRadS))
        stationary = (
            abs(accelNorm - 9.80665) <= self._gravityTolerance
            and gyroNorm <= self._maxGyroRadS
        )
        if not stationary:
            self._stationaryTimeS = 0.0
        else:
            self._stationaryTimeS += dtS
            if self._stationaryTimeS >= self._minimumStationaryS:
                # Lần khóa đầu lấy trực tiếp offset; các lần sau cập nhật chậm để
                # bám thay đổi nhiệt độ mà không đưa nhiễu tức thời vào quaternion.
                alpha = 1.0 if not self._hasBias else 1.0 - math.exp(
                    -dtS / self._timeConstantS)
                self._bias = tuple(
                    self._bias[index] + alpha * (gyroRadS[index] - self._bias[index])
                    for index in range(3))
                self._hasBias = True
        return tuple(gyroRadS[index] - self._bias[index] for index in range(3))


def _normalizeVector(vector: Vector3) -> Vector3 | None:
    """Chuẩn hóa vector; trả None khi cảm biến không cung cấp hướng hợp lệ."""
    norm = math.sqrt(sum(component * component for component in vector))
    if norm < 1e-9:
        return None
    return tuple(component / norm for component in vector)


def _normalizeQuaternion(quaternion: Quaternion) -> Quaternion:
    """Giữ quaternion đơn vị để ma trận quay không làm co giãn mô hình."""
    norm = math.sqrt(sum(component * component for component in quaternion))
    if norm < 1e-12:
        return (1.0, 0.0, 0.0, 0.0)
    return tuple(component / norm for component in quaternion)


def _multiply(left: Quaternion, right: Quaternion) -> Quaternion:
    """Nhân Hamilton hai quaternion theo thứ tự left rồi right."""
    lw, lx, ly, lz = left
    rw, rx, ry, rz = right
    return (
        lw * rw - lx * rx - ly * ry - lz * rz,
        lw * rx + lx * rw + ly * rz - lz * ry,
        lw * ry - lx * rz + ly * rw + lz * rx,
        lw * rz + lx * ry - ly * rx + lz * rw,
    )


def quaternionToRotationMatrix(quaternion: Quaternion) -> tuple[Vector3, Vector3, Vector3]:
    """Đổi quaternion (w, x, y, z) thành ma trận quay body sang world."""
    w, x, y, z = _normalizeQuaternion(quaternion)
    return (
        (1.0 - 2.0 * (y * y + z * z), 2.0 * (x * y - z * w),
         2.0 * (x * z + y * w)),
        (2.0 * (x * y + z * w), 1.0 - 2.0 * (x * x + z * z),
         2.0 * (y * z - x * w)),
        (2.0 * (x * z - y * w), 2.0 * (y * z + x * w),
         1.0 - 2.0 * (x * x + y * y)),
    )


def _matrixToQuaternion(matrix: tuple[Vector3, Vector3, Vector3]) -> Quaternion:
    # Chọn nhánh có phần tử đường chéo lớn để tránh chia cho số gần 0.
    m00, m01, m02 = matrix[0]
    m10, m11, m12 = matrix[1]
    m20, m21, m22 = matrix[2]
    trace = m00 + m11 + m22
    if trace > 0.0:
        scale = math.sqrt(trace + 1.0) * 2.0
        quaternion = (0.25 * scale, (m21 - m12) / scale,
                      (m02 - m20) / scale, (m10 - m01) / scale)
    elif m00 > m11 and m00 > m22:
        scale = math.sqrt(1.0 + m00 - m11 - m22) * 2.0
        quaternion = ((m21 - m12) / scale, 0.25 * scale,
                      (m01 + m10) / scale, (m02 + m20) / scale)
    elif m11 > m22:
        scale = math.sqrt(1.0 + m11 - m00 - m22) * 2.0
        quaternion = ((m02 - m20) / scale, (m01 + m10) / scale,
                      0.25 * scale, (m12 + m21) / scale)
    else:
        scale = math.sqrt(1.0 + m22 - m00 - m11) * 2.0
        quaternion = ((m10 - m01) / scale, (m02 + m20) / scale,
                      (m12 + m21) / scale, 0.25 * scale)
    return _normalizeQuaternion(quaternion)


def _measuredQuaternion(accel: Vector3, mag: Vector3) -> Quaternion | None:
    # Gia tốc tĩnh xác định trục Lên trong hệ cảm biến.
    upBody = _normalizeVector(accel)
    if upBody is None:
        return None

    # Loại thành phần thẳng đứng của từ trường để lấy hướng Bắc nằm ngang.
    magneticAlongUp = sum(mag[index] * upBody[index] for index in range(3))
    northBody = _normalizeVector(tuple(
        mag[index] - magneticAlongUp * upBody[index] for index in range(3)))
    if northBody is None:
        return None

    # Tích có hướng Lên x Bắc tạo trục Đông và hoàn tất hệ tọa độ trực chuẩn.
    eastBody = _normalizeVector((
        upBody[1] * northBody[2] - upBody[2] * northBody[1],
        upBody[2] * northBody[0] - upBody[0] * northBody[2],
        upBody[0] * northBody[1] - upBody[1] * northBody[0],
    ))
    if eastBody is None:
        return None

    # Các hàng là trục Bắc, Đông, Lên biểu diễn trong hệ tọa độ cảm biến.
    return _matrixToQuaternion((northBody, eastBody, upBody))


class MadgwickFilter:
    """Madgwick MARG 9-DOF; gyro dùng rad/s, dt dùng giây."""

    def __init__(self, beta: float = 0.1):
        if beta < 0.0:
            raise ValueError("Hệ số beta Madgwick không được âm")
        self._beta = beta
        self._orientation: Quaternion = (1.0, 0.0, 0.0, 0.0)
        self._initialized = False

    def update(self, accel: Vector3, gyroRadS: Vector3, mag: Vector3,
               dtS: float) -> Quaternion:
        # Giới hạn dt để một khoảng mất frame không tạo bước tích phân quá lớn.
        dtS = min(max(dtS, 0.0), 0.2)
        accelUnit = _normalizeVector(accel)
        magUnit = _normalizeVector(mag)

        # Khởi tạo theo trọng lực và Bắc từ để mô hình không phải hội tụ từ góc 0.
        measured = _measuredQuaternion(accel, mag)
        if not self._initialized:
            if measured is not None:
                self._orientation = measured
                self._initialized = True
                return self._orientation

        q0, q1, q2, q3 = self._orientation
        gx, gy, gz = gyroRadS
        # Đạo hàm gyro giữ phản ứng nhanh; gradient Madgwick khử drift chậm.
        qDot = [
            0.5 * (-q1 * gx - q2 * gy - q3 * gz),
            0.5 * (q0 * gx + q2 * gz - q3 * gy),
            0.5 * (q0 * gy - q1 * gz + q3 * gx),
            0.5 * (q0 * gz + q1 * gy - q2 * gx),
        ]

        if accelUnit is not None:
            ax, ay, az = accelUnit
            if magUnit is None:
                step = self._imuGradient(q0, q1, q2, q3, ax, ay, az)
            else:
                mx, my, mz = magUnit
                step = self._margGradient(q0, q1, q2, q3, ax, ay, az, mx, my, mz)
            stepNorm = math.sqrt(sum(value * value for value in step))
            if stepNorm > 1e-12:
                for index in range(4):
                    qDot[index] -= self._beta * step[index] / stepNorm

        self._orientation = _normalizeQuaternion(tuple(
            self._orientation[index] + qDot[index] * dtS for index in range(4)))
        return self._orientation

    @staticmethod
    def _imuGradient(q0: float, q1: float, q2: float, q3: float,
                     ax: float, ay: float, az: float) -> Quaternion:
        """Gradient 6-DOF dùng khi từ kế bằng 0 hoặc chưa sẵn sàng."""
        return (
            4.0 * q0 * q1 * q1 + 4.0 * q0 * q2 * q2 + 2.0 * q2 * ax - 2.0 * q1 * ay,
            4.0 * q1 ** 3 + 4.0 * q1 * q2 * q2 - 4.0 * q1 + 2.0 * q3 * ax
            - 2.0 * q0 * ay + 4.0 * q1 * az,
            4.0 * q0 * q0 * q2 + 4.0 * q1 * q1 * q2 - 4.0 * q2
            - 2.0 * q0 * ax + 2.0 * q3 * ay + 4.0 * q2 * az,
            4.0 * q1 * q1 * q3 + 4.0 * q2 * q2 * q3 - 2.0 * q1 * ax + 2.0 * q2 * ay,
        )

    @staticmethod
    def _margGradient(q0: float, q1: float, q2: float, q3: float,
                      ax: float, ay: float, az: float,
                      mx: float, my: float, mz: float) -> Quaternion:
        """Gradient 9-DOF của Madgwick với tham chiếu từ trường tự cập nhật."""
        hx = 2.0 * mx * (0.5 - q2 * q2 - q3 * q3) + 2.0 * my * (
            q1 * q2 - q0 * q3) + 2.0 * mz * (q1 * q3 + q0 * q2)
        hy = 2.0 * mx * (q1 * q2 + q0 * q3) + 2.0 * my * (
            0.5 - q1 * q1 - q3 * q3) + 2.0 * mz * (q2 * q3 - q0 * q1)
        horizontal = math.sqrt(hx * hx + hy * hy)
        vertical = 2.0 * mx * (q1 * q3 - q0 * q2) + 2.0 * my * (
            q2 * q3 + q0 * q1) + 2.0 * mz * (0.5 - q1 * q1 - q2 * q2)

        f = (
            2.0 * (q1 * q3 - q0 * q2) - ax,
            2.0 * (q0 * q1 + q2 * q3) - ay,
            2.0 * (0.5 - q1 * q1 - q2 * q2) - az,
            2.0 * horizontal * (0.5 - q2 * q2 - q3 * q3)
            + 2.0 * vertical * (q1 * q3 - q0 * q2) - mx,
            2.0 * horizontal * (q1 * q2 - q0 * q3)
            + 2.0 * vertical * (q0 * q1 + q2 * q3) - my,
            2.0 * horizontal * (q0 * q2 + q1 * q3)
            + 2.0 * vertical * (0.5 - q1 * q1 - q2 * q2) - mz,
        )
        # J^T f được viết tường minh để không phụ thuộc thư viện ma trận ngoài.
        return (
            -2.0 * q2 * f[0] + 2.0 * q1 * f[1]
            - 2.0 * vertical * q2 * f[3]
            + (-2.0 * horizontal * q3 + 2.0 * vertical * q1) * f[4]
            + 2.0 * horizontal * q2 * f[5],
            2.0 * q3 * f[0] + 2.0 * q0 * f[1] - 4.0 * q1 * f[2]
            + 2.0 * vertical * q3 * f[3]
            + (2.0 * horizontal * q2 + 2.0 * vertical * q0) * f[4]
            + (2.0 * horizontal * q3 - 4.0 * vertical * q1) * f[5],
            -2.0 * q0 * f[0] + 2.0 * q3 * f[1] - 4.0 * q2 * f[2]
            + (-4.0 * horizontal * q2 - 2.0 * vertical * q0) * f[3]
            + (2.0 * horizontal * q1 + 2.0 * vertical * q3) * f[4]
            + (2.0 * horizontal * q0 - 4.0 * vertical * q2) * f[5],
            2.0 * q1 * f[0] + 2.0 * q2 * f[1]
            + (-4.0 * horizontal * q3 + 2.0 * vertical * q1) * f[3]
            + (-2.0 * horizontal * q0 + 2.0 * vertical * q2) * f[4]
            + 2.0 * horizontal * q1 * f[5],
        )
