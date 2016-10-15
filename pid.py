import random
import time
from display import Display

class PIDController:
    last_time_secs = None
    last_input = 0
    setpoint = 0
    i_term = 0.0

    def __init__(self, name, p, i, d, input_limits, output_limits, direction='direct'):
        self.name = name
        self.clear_iterm_on_change = False
        self.in_min, self.in_max = input_limits
        self.out_min, self.out_max = output_limits
        self.controller_direction = direction
        self.output = self.clamp(0.0)
        self.i_term = self.clamp(0.0)
        self.mode = 'auto'
        self.display = False

        if p < 0 or i < 0 or d < 0:
            raise ValueError('Invalid PIDs, use direction=\'reverse\'')
        if direction not in ('direct', 'reverse'):
            raise ValueError('Invalid direction')
        if self.in_min > self.in_max:
            raise ValueError('Invalid input_limits')
        if self.out_min > self.out_max:
            raise ValueError('Invalid output_limits')

        if self.controller_direction == 'reverse':
            self.kp = 0 - p
            self.ki = 0 - i
            self.kd = 0 - d
        else:
            self.kp = p
            self.ki = i
            self.kd = d

        self.reinit()

        self.historic_data = {
            'timeseries': [],
            'local_min': None,
            'local_max': None,
            'mins': [],
            'maxes': [],
            'tune_start_time': None,
            'setpoint_crossings': 0,
            'stable_since': None,
        }
        self.tune = {
            'stored_params': None,
            'status': None,
            'setpoint': None,
            'setpoint_min': 0.0,
            'setpoint_max': 1.0,
            'stability_time_threshold': 1.0,
            'stability_timeout': 20.0,
            'stability_threshold': 0.1
        }

    def begin_tuning(self,
                     setpoint_min=None,
                     setpoint_max=None,
                     stability_time_threshold=None,
                     stability_timeout=None,
                     stability_threshold=None):
        self.tune['status'] = None
        print "Start tuning {}".format(self.name)
        self.tune['setpoint_min'] = self.in_min + (self.in_max - self.in_min) / 3.0
        self.tune['setpoint_max'] = self.in_max - (self.in_max - self.in_min) / 3.0
        self.tune['stability_threshold'] = (self.in_max - self.in_min) / 100.0
        self.tune['stability_time_threshold'] = 10.0
        self.tune['stability_timeout'] = 30.0
        if setpoint_min is not None:
            self.tune['setpoint_min'] = setpoint_min
        if setpoint_max is not None:
            self.tune['setpoint_max'] = setpoint_max
        if stability_time_threshold is not None:
            self.tune['stability_time_threshold'] = stability_time_threshold
        if stability_timeout is not None:
            self.tune['stability_timeout'] = stability_timeout
        if stability_threshold is not None:
            self.tune['stability_threshold'] = stability_threshold
        if self.tune['stored_params'] is None:
            self.tune['stored_params'] = self.kp, self.ki, self.kd
        self.ki = self.kd = self.i_term = 0.0
        self.mode = 'tune'

    def tune_randomize_setpoint(self, input, cur_time_secs):
        self.tune['setpoint'] = None
        while self.tune['setpoint'] is None or abs(input - self.tune['setpoint']) < (self.tune['setpoint_max'] - self.tune['setpoint_min']) / 4.0:
            self.setpoint = self.tune['setpoint'] = random.uniform(self.tune['setpoint_min'], self.tune['setpoint_max'])
        self.tune['stable_since'] = None
        self.tune['setpoint_crossings'] = 0
        if input < self.tune['setpoint']:
            self.tune['initial_status'] = self.tune['status'] = 'below_setpoint'
            self.tune['overshoot_status'] = 'no_setpoint_cross_under'
        else:
            self.tune['initial_status'] = self.tune['status'] = 'above_setpoint'
            self.tune['overshoot_status'] = 'no_setpoint_cross_over'
        self.tune['tune_start_time'] = cur_time_secs
        self.tune['found_tou'] = False
        self.historic_data['mins'] = []
        self.historic_data['maxes'] = []

    def handle_tuning(self, input, cur_time_secs):
        if not self.tune.get('status'):
            self.tune_randomize_setpoint(input, cur_time_secs)
            return

        # Find Min/Max and crossings
        if input > self.tune['setpoint']:
            # Input above setpoint
            if self.historic_data['local_max'] is None or input > self.historic_data['local_max']['value']:
                self.historic_data['local_max'] = {'time': cur_time_secs, 'value': input}
            if self.tune['status'] == 'below_setpoint':
                self.tune['status'] = 'above_setpoint'
                self.tune['setpoint_crossings'] += 1
                if self.historic_data['local_min'] is not None:
                    if self.tune['setpoint_crossings'] > 1:
                        self.historic_data['mins'].append(self.historic_data['local_min'])
                        print 'min: {}'.format(self.historic_data.get('local_min'))
                    self.historic_data['local_min'] = None
        else:
            if self.historic_data['local_min'] is None or input < self.historic_data['local_min']['value']:
                self.historic_data['local_min'] = {'time': cur_time_secs, 'value': input}
            if self.tune['status'] == 'above_setpoint':
                self.tune['status'] = 'below_setpoint'
                self.tune['setpoint_crossings'] += 1
                if self.historic_data['local_max'] is not None:
                    if self.tune['setpoint_crossings'] > 1:
                        self.historic_data['maxes'].append(self.historic_data['local_max'])
                        print 'max: {}'.format(self.historic_data.get('local_max'))
                    self.historic_data['local_max'] = None

        # Calculate Overshoots (Tou method)
        if self.tune['setpoint_crossings'] == 3 and not self.tune.get('found_tou'):
            try:
                if self.tune['initial_status'] == 'above_setpoint':
                    tou = self.historic_data['maxes'][0]['time'] - self.historic_data['mins'][0]['time']
                    print 'Tou: {} Ti: {} Td: {} p {} i {} d {}'.format(tou, 1.5*tou, 1.5*tou / 4.0, self.kp, self.kp / (1.5*tou), self.kp * 1.5 * tou / 4.0)
                    self.tune['found_tou'] = True
                else:
                    tou = self.historic_data['mins'][0]['time'] - self.historic_data['maxes'][0]['time']
                    print 'Tou: {} Ti: {} Td: {} p {} i {} d {}'.format(tou, 1.5*tou, 1.5*tou / 4.0, self.kp, self.kp / (1.5*tou), self.kp * 1.5 * tou / 4.0)
                    self.tune['found_tou'] = True
            except Exception as e:
                print e

        # Check stability zone
        if abs(input - self.tune['setpoint']) <= self.tune['stability_threshold']:
            if self.tune['stable_since'] is None:
                self.tune['stable_since'] = cur_time_secs
            elif cur_time_secs - self.tune['stable_since'] >= self.tune['stability_time_threshold']:
                # Stable
                self.tune['status'] = None
                print "Stable after {} with {} crossings kp {:.06f}, increasing kp to {:.06f}".format(
                    cur_time_secs - self.tune['tune_start_time'],
                    self.tune['setpoint_crossings'],
                    self.kp,
                    self.kp * 1.1)
                self.tune_randomize_setpoint(input, cur_time_secs)
                self.kp *= 1.1
        elif cur_time_secs - self.tune['tune_start_time'] >= self.tune['stability_timeout'] or abs((input - self.last_input) / (cur_time_secs - self.last_time_secs)) < 0.01 or self.tune['setpoint_crossings'] > 10:
            # Unstable with timeout
            if self.tune['setpoint_crossings'] < 2 or len(self.historic_data['mins']) < 2 or len(self.historic_data['maxes']) < 2:
                # Not a good tune, continue
                self.kp *= 1.1
                self.tune_randomize_setpoint(input, cur_time_secs)
                print "Insufficient crossings, continuing tune with kp {:.06f}".format(self.kp)
            else:
                # Tune using Ziegler-Nicols for no overshoot
                avg_min_tu = sum(j['time'] - i['time'] for i, j in zip(self.historic_data['mins'][:-1], self.historic_data['mins'][1:])) / (len(self.historic_data['mins']) - 1)
                avg_max_tu = sum(j['time'] - i['time'] for i, j in zip(self.historic_data['maxes'][:-1], self.historic_data['maxes'][1:])) / (len(self.historic_data['maxes']) - 1)
                Tu = (avg_min_tu + avg_max_tu) / 2.0
                Ku = self.kp
                print "Tune stability timeout after {} with {} crossings Ku {} Tu {:.02f}".format(
                    cur_time_secs - self.tune['tune_start_time'],
                    self.tune['setpoint_crossings'],
                    Ku,
                    Tu
                )
                if self.tune['stored_params'][1] != 0.0:
                    #PID Controller
                    self.kp, self.ki, self.kd = Ku * 0.33, 0.33 * 2.0 * Ku / Tu, 0.33 * 0.33 * Tu * Ku
                    self.tune['stored_params'] = None
                else:
                    # PD Controller
                    self.kp, self.ki, self.kd = Ku * 0.6, 0.0, 0.6 * 0.33 * Ku * Tu
                    self.tune['stored_params'] = None
                self.mode = 'normal'
                print 'Tuning completed, values: kp {} ki {} kd {}'.format(self.kp, self.ki, self.kd)
        else:
            self.tune['stable_since'] = None

    def compute(self, cur_time_secs, setpoint, input, output_display=None):
        if self.mode == 'manual':
            return

        if self.last_time_secs is None:
            self.last_time_secs = cur_time_secs
            return
        time_delta_secs = (cur_time_secs - self.last_time_secs)

        # Handle tuning
        if self.mode == 'tune':
            self.handle_tuning(input, cur_time_secs)
            setpoint = self.setpoint

        # Compute working vars
        self.setpoint = setpoint
        error = self.setpoint - input
        self.i_term += self.ki * error * time_delta_secs
        self.i_term = self.clamp(self.i_term)
        time_weighted_input_delta = (input - self.last_input) / time_delta_secs

        if self.clear_iterm_on_change and self.kd * time_weighted_input_delta > .1:
            self.i_term = 0.0

        # Compute PID output
        if self.mode == 'relay':
            self.output = self.out_max if input < setpoint else self.out_min
        else:
            self.output = self.clamp(self.kp * error + self.i_term - self.kd * time_weighted_input_delta)

        self.historic_data['timeseries'].append({
            'time': cur_time_secs,
            'input': input,
            'setpoint': self.setpoint,
            'output': self.output,
            'p': self.ki * error,
            'i': self.i_term,
            'd': -self.kd * time_weighted_input_delta,
        })

        data = [(d['time']-self.historic_data['timeseries'][0]['time'], d['input'], d['setpoint']) for d in self.historic_data['timeseries']]

        output_text = '{} {} diff: {:.02f} setpoint_crossings {} p {:.06f} pterm: {:.02f} iterm: {:.02f} dterm: {:.02f}'.format(
            self.name,
            self.mode,
            abs(input - self.setpoint),
            self.historic_data.get('setpoint_crossings', 0),
            self.kp,
            self.ki * error,
            self.i_term,
            -self.kd * time_weighted_input_delta)

        if output_display and (self.mode == 'tune' or self.display):
            output_display.graph_data(data,
                                        self.in_min,
                                        self.in_max,
                                        output_text)

        #print '{} time {} p {:.02f} i {:.02f} d {:.02f}'.format(
        #    self.name,
        #    time_delta_secs,
        #    self.kp * error,
        #    self.i_term,
        #    - self.kd * time_weighted_input_delta)

        # Set history vars
        self.last_input = input
        self.last_time_secs = cur_time_secs

    def render_pid_term(self, value, width):
        normalized_value = (value - self.out_min) * 2.0 * width / self.out_max - width
        out = ''
        for slot in range(0, width):
            if abs(normalized_value) > slot:
                out += '*'
            else:
                out += ' '
        if normalized_value < 0:
            return out[::-1] + '|' + ' ' * width
        else:
            return ' ' * width + '|' + out[::-1]

    def set_mode(self, mode):
        if mode != 'manual' and self.mode == 'manual':
            self.reinit()
        self.mode = mode

    def reinit(self, input=0, output=0):
        self.input = input
        self.output = output
        self.last_input = input
        self.i_term = self.clamp(self.output) if self.i_term else 0.0

    def clamp(self, n):
        return min(max(n, self.out_min), self.out_max)
