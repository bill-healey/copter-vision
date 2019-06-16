import time
from pid import PIDController


class DronePIDs:
    def __init__(self):
        self.pids = {}

        # self.pids['aileron'] = PIDController(
        #     'aileron',  p=0.8, i=0.01, d=0.30, output_limits=(-1.0, 1.0), input_limits=(-1.0, 1.0))
        # self.pids['pitch'] = PIDController(
        #     'pitch',    p=0.6, i=0.01, d=0.40, output_limits=(-1.0, 1.0), input_limits=(-1.0, 1.0))
        # self.pids['throttle'] = PIDController(
        #     'throttle', p=1.6, i=0.30, d=0.80, output_limits=(-1.0, 1.0), input_limits=(-1.0, 1.0))
        # self.pids['yaw'] = PIDController(
        #     'yaw',      p=0.5, i=0.01, d=0.20, output_limits=(-1.0, 1.0), input_limits=(-1.0, 1.0))

        self.pids['aileron'] = PIDController(
            'aileron',  p=0.5, i=0.01, d=0.40, output_limits=(-1.0, 1.0), input_limits=(-1.0, 1.0))
        self.pids['pitch'] = PIDController(
            'pitch',    p=0.5, i=0.01, d=0.40, output_limits=(-1.0, 1.0), input_limits=(-1.0, 1.0))
        self.pids['throttle'] = PIDController(
            'throttle', p=0.8, i=0.60, d=0.8, output_limits=(-1.0, 1.0), input_limits=(-1.0, 1.0))
        self.pids['yaw'] = PIDController(
            'yaw',      p=0.25, i=0.03, d=0.08, output_limits=(-1.0, 1.0), input_limits=(-1.0, 1.0))

        self.setpoints = {
            'aileron': 0.0,
            'pitch': 0.0,
            'throttle': 0.0,
            'yaw': 0.0
        }

    def hold_current_position(self, telemetry):
        self.setpoints = {
             'aileron': telemetry['right_dist'],
             'pitch': telemetry['forward_dist'],
             'throttle': telemetry['vertical_dist'],
             'yaw': telemetry['yaw']
        }

    def update(self, telemetry):
        if telemetry is None:
            # No new data available, skip update
            return
        self.pids['aileron'].compute(time.time(),
                                     setpoint=self.setpoints['aileron'],
                                     input_value=telemetry['right_dist'])
        self.pids['pitch'].compute(time.time(),
                                   setpoint=self.setpoints['pitch'],
                                   input_value=telemetry['forward_dist'])
        self.pids['throttle'].compute(time.time(),
                                      setpoint=self.setpoints['throttle'],
                                      input_value=telemetry['vertical_dist'])
        self.pids['yaw'].compute(time.time(),
                                 setpoint=self.setpoints['yaw'],
                                 input_value=telemetry['yaw'])

        print 'v {:.02f}, s {:.02f}, f {:.02f}, y {:.02f} throttle {:.02f} pitch {:.02f} aileron {:.02f} yaw {:.02f}'.format(
            telemetry['vertical_dist'], telemetry['forward_dist'], telemetry['right_dist'], telemetry['yaw'],
            self.pids['throttle'].output, self.pids['pitch'].output, self.pids['aileron'].output,
            self.pids['yaw'].output)

        return {
            'aileron': self.pids['aileron'].output,
            'pitch': self.pids['pitch'].output,
            'throttle': self.pids['throttle'].output,
            'yaw': self.pids['yaw'].output
        }
