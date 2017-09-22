from rc_ppm_generator import RCPPMGenerator


class DroneRCController:
    def __init__(self):
        self.dry_run = True
        self.rc_ppm = RCPPMGenerator()

    def update_channels(self, aileron, pitch, throttle, yaw):
        self.rc_ppm.set_channel_values([aileron, pitch, throttle, yaw,
                                        0.0, 0.0, 0.0, 0.0])
