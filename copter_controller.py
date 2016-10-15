import time
from serial import Serial
from pid import PIDController

class CopterController:

    dry_run = True

    def __init__(self, dry_run=True):
        #PID tuning: Throttle needs decent integral to compensate for gravity
        #PID tuning: Aileron and throttle can use differential
        #PID tuning: Pitch and yaw should not use differential since measurements are coarse approximations
        #PID tuning: Aileron, pitch, yaw shouldn't need integral (for now we will assume proper trim)
        self.pids = {}
        self.pids['throttle'] = PIDController('throttle', p=.2, i=0.1, d=0.0,
                                              output_limits=(0.0, 1.0), input_limits=(-1.0, 1.0))
        self.pids['throttle'].display = True
        self.pids['pitch'] = PIDController('pitch', p=.1, i=0.0, d=0.0,
                                           output_limits=(-1.0, 1.0), input_limits=(-1.0, 1.0))
        self.pids['aileron'] = PIDController('aileron', p=.1, i=0.0, d=0.0,
                                             output_limits=(-1.0, 1.0), input_limits=(-1.0, 1.0))
        self.pids['yaw'] = PIDController('yaw', p=.1, i=0.0, d=0.0,
                                         output_limits=(-1.0, 1.0), input_limits=(-1.0, 1.0))
        if not self.dry_run:
            # Open up the serial port and bind the quadcopter
            self.serial = Serial('COM4', 115200, timeout=1)
            try:
                self.serial.open()
            except Exception as e:
                print e
            self.serial.close()
            self.serial.open()
            while True:
                line = self.serial.readline().rstrip()
                if len(line):
                    print line
                if line == 'initialization successful':
                    self.serial.write('000101')
                if 'Telemetry data' in line:
                    raw_input('***GUIDANCE READY***')
                    break

    def update(self, vertical_dist, side_dist, forward_dist, yaw_dist, display):

        self.pids['throttle'].compute(time.time(),
                                      setpoint=0.0,
                                      input=vertical_dist,
                                      output_display=display)
        self.pids['pitch'].compute(time.time(),
                                   setpoint=0.0,
                                   input=forward_dist,
                                   output_display=display)
        self.pids['aileron'].compute(time.time(),
                                     setpoint=0.0,
                                     input=side_dist,
                                     output_display=display)
        self.pids['yaw'].compute(time.time(),
                                 setpoint=0.0,
                                 input=yaw_dist,
                                 output_display=display)
      
        #Center values around 0x7F and bound values between 00 and FF to ensure they are valid
        aileron = max(min(int(128.0 * self.pids['aileron'].output + 0x7F), 0xFF), 0)
        pitch = max(min(int(128.0 * self.pids['pitch'].output + 0x7F), 0xFF), 0)
        throttle = max(min(int(128.0 * self.pids['throttle'].output + 0x9F), 0xFF), 0)

        print 'v{:02f},s{:02f},f{:02f},y{:02f} {:02X},{:02X},{:02X}'.format(
            vertical_dist, side_dist, forward_dist, yaw_dist,
            aileron, throttle, pitch)

        #Throttle 0102XX 00-FF
        #Aileron  0104XX 45-C3
        #Elevator 0105XX 3E-BC
        #Rudder   0103XX 34-CC

        if not self.dry_run:
            self.serial.flushInput()
            self.serial.flushOutput()
            self.serial.write('0102{:02X}'.format(throttle))
            self.serial.write('0104{:02X}'.format(aileron))
            self.serial.write('0105{:02X}'.format(pitch))

