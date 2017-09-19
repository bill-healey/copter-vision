# Author: William Healey http://billhealey.com

import random

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
        self.input = 0.0
        self.output = self.clamp(0.0)
        self.i_term = self.clamp(0.0)
        self.mode = 'auto'
        self.display = Display()

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
            'setpoint_min': self.in_min + (self.in_max - self.in_min) / 5.0,
            'setpoint_max': self.in_max - (self.in_max - self.in_min) / 5.0,
            'stability_threshold': (self.in_max - self.in_min) / 100.0,
            'stability_time_threshold': 10.0,
            'stability_timeout': 30.0,
        }

    def begin_tuning(self,
                     setpoint_min=None,
                     setpoint_max=None,
                     stability_time_threshold=None,
                     stability_timeout=None,
                     stability_threshold=None):
        self.tune['status'] = None
        print "Start tuning {}".format(self.name)
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

    def tune_randomize_setpoint(self, input_value, cur_time_secs):
        self.tune['setpoint'] = None
        while self.tune['setpoint'] is None or abs(input_value - self.tune['setpoint']) < (
                    self.tune['setpoint_max'] - self.tune['setpoint_min']) / 4.0:
            self.setpoint = self.tune['setpoint'] = random.uniform(self.tune['setpoint_min'], self.tune['setpoint_max'])
        self.tune['stable_since'] = None
        self.tune['setpoint_crossings'] = 0
        if input_value < self.tune['setpoint']:
            self.tune['initial_status'] = self.tune['status'] = 'below_setpoint'
            self.tune['overshoot_status'] = 'no_setpoint_cross_under'
        else:
            self.tune['initial_status'] = self.tune['status'] = 'above_setpoint'
            self.tune['overshoot_status'] = 'no_setpoint_cross_over'
        self.tune['tune_start_time'] = cur_time_secs
        self.tune['found_tou'] = False
        self.historic_data['mins'] = []
        self.historic_data['maxes'] = []

    def handle_tuning(self, input_value, cur_time_secs):
        if not self.tune.get('status'):
            self.tune_randomize_setpoint(input_value, cur_time_secs)
            return

        # Find Min/Max and crossings
        if input_value > self.tune['setpoint']:
            # Input above setpoint
            if self.historic_data['local_max'] is None or input_value > self.historic_data['local_max']['value']:
                self.historic_data['local_max'] = {'time': cur_time_secs, 'value': input_value}
            if self.tune['status'] == 'below_setpoint':
                self.tune['status'] = 'above_setpoint'
                self.tune['setpoint_crossings'] += 1
                if self.historic_data['local_min'] is not None:
                    if self.tune['setpoint_crossings'] > 1:
                        self.historic_data['mins'].append(self.historic_data['local_min'])
                        print 'min: {}'.format(self.historic_data.get('local_min'))
                    self.historic_data['local_min'] = None
        else:
            if self.historic_data['local_min'] is None or input_value < self.historic_data['local_min']['value']:
                self.historic_data['local_min'] = {'time': cur_time_secs, 'value': input_value}
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
                    print 'Tou: {} Ti: {} Td: {} p {} i {} d {}'.format(tou, 1.5 * tou, 1.5 * tou / 4.0, self.kp,
                                                                        self.kp / (1.5 * tou),
                                                                        self.kp * 1.5 * tou / 4.0)
                    self.tune['found_tou'] = True
                else:
                    tou = self.historic_data['mins'][0]['time'] - self.historic_data['maxes'][0]['time']
                    print 'Tou: {} Ti: {} Td: {} p {} i {} d {}'.format(tou, 1.5 * tou, 1.5 * tou / 4.0, self.kp,
                                                                        self.kp / (1.5 * tou),
                                                                        self.kp * 1.5 * tou / 4.0)
                    self.tune['found_tou'] = True
            except Exception as e:
                print e

        # Check stability zone
        if abs(input_value - self.tune['setpoint']) <= self.tune['stability_threshold']:
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
                self.tune_randomize_setpoint(input_value, cur_time_secs)
                self.kp *= 1.1
        elif cur_time_secs - self.tune['tune_start_time'] >= self.tune['stability_timeout'] \
                or self.tune['setpoint_crossings'] > 8:
            # Unstable with timeout
            if self.tune['setpoint_crossings'] < 2 or len(self.historic_data['mins']) < 2 or len(
                    self.historic_data['maxes']) < 2:
                # Not a good tune, continue
                self.kp *= 1.1
                self.tune_randomize_setpoint(input_value, cur_time_secs)
                print "Insufficient crossings, continuing tune with kp {:.06f}".format(self.kp)
            else:
                # Tune using Ziegler-Nicols for no overshoot
                avg_min_tu = sum(j['time'] - i['time'] for i, j in
                                 zip(self.historic_data['mins'][:-1], self.historic_data['mins'][1:])) / (
                                 len(self.historic_data['mins']) - 1)
                avg_max_tu = sum(j['time'] - i['time'] for i, j in
                                 zip(self.historic_data['maxes'][:-1], self.historic_data['maxes'][1:])) / (
                                 len(self.historic_data['maxes']) - 1)
                tu = (avg_min_tu + avg_max_tu) / 2.0
                ku = self.kp
                print "Tune stability timeout after {} with {} crossings Ku {} Tu {:.02f}".format(
                    cur_time_secs - self.tune['tune_start_time'],
                    self.tune['setpoint_crossings'],
                    ku,
                    tu
                )
                if self.tune['stored_params'][1] != 0.0:
                    # PID Controller
                    self.kp, self.ki, self.kd = ku * 0.33, 0.33 * 2.0 * ku / tu, 0.33 * 0.33 * tu * ku
                    self.tune['stored_params'] = None
                else:
                    # PD Controller
                    self.kp, self.ki, self.kd = ku * 0.6, 0.0, 0.6 * 0.33 * ku * tu
                    self.tune['stored_params'] = None
                self.mode = 'normal'
                print 'Tuning completed, values: kp {} ki {} kd {}'.format(self.kp, self.ki, self.kd)
        else:
            self.tune['stable_since'] = None

    def compute(self, cur_time_secs, setpoint, input_value):
        if self.mode == 'manual':
            return

        if self.last_time_secs is None:
            self.last_time_secs = cur_time_secs
            return
        time_delta_secs = (cur_time_secs - self.last_time_secs)

        # Handle tuning
        if self.mode == 'tune':
            self.handle_tuning(input_value, cur_time_secs)
            setpoint = self.setpoint

        # Compute working vars
        self.setpoint = setpoint
        error = self.setpoint - input_value
        self.i_term += self.ki * error * time_delta_secs
        self.i_term = self.clamp(self.i_term)
        time_weighted_input_delta = (input_value - self.last_input) / time_delta_secs

        if self.clear_iterm_on_change and self.kd * time_weighted_input_delta > .1:
            self.i_term = 0.0

        # Compute PID output
        if self.mode == 'relay':
            self.output = self.out_max if input_value < setpoint else self.out_min
        else:
            self.output = self.clamp(self.kp * error + self.i_term - self.kd * time_weighted_input_delta)

        self.historic_data['timeseries'].append({
            'time': cur_time_secs,
            'input': input_value,
            'setpoint': self.setpoint,
            'output': self.output,
            'p': self.ki * error,
            'i': self.i_term,
            'd': -self.kd * time_weighted_input_delta,
        })

        output_text = ('{} {} diff: {:.02f} setpoint_crossings {} p {:.06f} '
                       'pterm: {:.02f} iterm: {:.02f} dterm: {:.02f}').format(
            self.name,
            self.mode,
            abs(input_value - self.setpoint),
            self.historic_data.get('setpoint_crossings', 0),
            self.kp,
            self.ki * error,
            self.i_term,
            -self.kd * time_weighted_input_delta)

        if self.display:
            self.display.add_point(
                self.name,
                output_text,
                [input_value, setpoint],
                self.in_min,
                self.in_max
            )

        # Set history vars
        self.last_input = input_value
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

    def reinit(self, input_value=0, output=0):
        self.input = input_value
        self.output = output
        self.last_input = input_value
        self.i_term = self.clamp(self.output) if self.i_term else 0.0

    def clamp(self, n):
        return min(max(n, self.out_min), self.out_max)
