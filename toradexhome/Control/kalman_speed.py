import time


class SpeedKalman:
    def __init__(self):
        # Estimated velocity (m/s)
        self.v = 0.0

        # Estimation covariance
        self.P = 1.0

        # Process noise (IMU uncertainty)
        self.Q = 0.05

        # Measurement noise (GPS uncertainty)
        self.R = 0.8

        self.last_time = None

    # ==========================================
    # Prediction step (call at 200 Hz with IMU)
    # ==========================================
    def predict(self, acceleration):
        now = time.time()

        if self.last_time is None:
            self.last_time = now
            return self.v

        dt = now - self.last_time
        self.last_time = now

        # Integrate acceleration → velocity
        self.v += acceleration * dt

        # Update covariance
        self.P += self.Q

        return self.v

    # ==========================================
    # Update step (call at 10 Hz with GPS)
    # ==========================================
    def update(self, gps_speed):
        # Kalman gain
        K = self.P / (self.P + self.R)

        # Correct velocity
        self.v += K * (gps_speed - self.v)

        # Update covariance
        self.P *= (1 - K)

        return self.v
