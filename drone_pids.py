import time

from pid import PIDController
from drone_rc_controller import DroneRCController


class DronePIDs:
    def __init__(self):
        self.pids = {}
        self.serial = None
        self.drone_rc = DroneRCController()

        # PID tuning: Throttle needs decent integral to compensate for gravity
        # PID tuning: Aileron and throttle can use differential
        # PID tuning: Pitch and yaw should not use differential since measurements are coarse approximations
        # PID tuning: Aileron, pitch, yaw shouldn't need integral (for now we will assume proper trim)
        self.pids['throttle'] = PIDController('throttle', p=.1, i=.5, d=.1,
                                              output_limits=(-1.0, 1.0), input_limits=(-1.0, 1.0))
        self.pids['pitch'] = PIDController('pitch', p=.5, i=0.0, d=.1,
                                           output_limits=(-1.0, 1.0), input_limits=(-1.0, 1.0),
                                           direction='reverse')
        self.pids['aileron'] = PIDController('aileron', p=.5, i=0.0, d=.1,
                                             output_limits=(-1.0, 1.0), input_limits=(-1.0, 1.0))
        self.pids['yaw'] = PIDController('yaw', p=0.2, i=0.0, d=0.0,
                                         output_limits=(-1.0, 1.0), input_limits=(-1.0, 1.0))

    def update(self, telemetry):
        self.pids['throttle'].compute(time.time(),
                                      setpoint=0.0,
                                      input_value=telemetry['vertical_dist'])
        self.pids['pitch'].compute(time.time(),
                                   setpoint=0.0,
                                   input_value=telemetry['forward_dist'])
        self.pids['aileron'].compute(time.time(),
                                     setpoint=0.0,
                                     input_value=telemetry['right_dist'])
        self.pids['yaw'].compute(time.time(),
                                 setpoint=0.0,
                                 input_value=telemetry['yaw_dist'])

        self.drone_rc.update_channels(
            self.pids['aileron'].output,
            self.pids['elevator'].output,
            self.pids['throttle'].output,
            self.pids['rudder'].output
        )

        print 'v{:.02f},s{:.02f},f{:.02f},y{:.02f} throttle{:.02f} pitch{:.02f} aileron{:.02f} yaw{:.02f}'.format(
            telemetry['vertical_dist'], telemetry['forward_dist'], telemetry['right_dist'], telemetry['yaw_dist'],
            self.pids['throttle'].output, self.pids['pitch'].output, self.pids['aileron'].output,
            self.pids['yaw'].output)

    def failsafe(self):
        self.drone_rc.update_channels(0.0, 0.0, -1.0, 0.0)
