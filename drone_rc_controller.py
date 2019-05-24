from rc_ppm_generator import RCPPMGenerator


class DroneRCController:
    def __init__(self):
        self.dry_run = True
        self.rc_ppm = RCPPMGenerator()

    def pause_stream(self):
        self.rc_ppm.pause_stream()

    def kill_throttle(self):
        self.rc_ppm.set_channel_values([0.0,
                                        0.0, 0.0, -1.0, 0.0,
                                        0.0, 0.0, 0.5])

    def update_channels(self, aileron, pitch, throttle, yaw):
        self.rc_ppm.set_channel_values([0.0,
                                        aileron, pitch, throttle, yaw,
                                        0.0, 0.0, 0.5])
