import threading
import time

import pyaudio


class RCPPMGenerator:
    """Generates a PPM signal that encodes the specified RC channels"""

    class StreamWriterThread(threading.Thread):

        def __init__(self, pyaudio_instance, stream, shared_data):
            super(RCPPMGenerator.StreamWriterThread, self).__init__()
            self.stop = False
            self.pyaudio = pyaudio_instance
            self.stream = stream
            self.shared_data = shared_data

        def run(self):
            while not self.stop:
                self.write()
            self.stream.stop_stream()
            self.stream.close()
            self.pyaudio.terminate()
            print 'PyAudio terminated'

        def write(self):
            self.stream.write(self.shared_data['frame'])

    def __init__(self):
        self.SIGNAL_LOW = 0  # Byte value which represents a LOW PPM signal/voltage
        self.SIGNAL_HIGH = 255  # Byte value which represents a HIGH PPM signal/voltage
        self.CENTER_PW_MS = 1.5  # Length in milliseconds considered to be the 'center' value of the pulse width
        self.DELTA_PW_MS = .5  # Length in milliseconds between the center and the min or max of the pulse width
        self.MIN_PW_MS = .5  # Length in milliseconds of the minimum allowable channel pulse width
        self.FRAME_DURATION_MS = 22.5  # Length in milliseconds of a full frame
        self.NUM_CHANNELS = 8  # Number of RC channels to encode
        self.TARGET_AUDIO_DEVICE_NAME = 'Headphone Jack'  # Preferred output audio device (name contains this string)
        self.channel_values = [0.0] * self.NUM_CHANNELS  # Array representing the channel values to be transmitted
        self.output_device_index = 0

        self.pyaudio = pyaudio.PyAudio()
        for device_index in xrange(self.pyaudio.get_device_count()):
            if self.TARGET_AUDIO_DEVICE_NAME in self.pyaudio.get_device_info_by_index(device_index)['name']:
                self.output_device_index = device_index
        print 'Using device: {}'.format(self.pyaudio.get_device_info_by_index(self.output_device_index))
        self.bitrate = int(self.pyaudio.get_device_info_by_index(self.output_device_index)['defaultSampleRate'])

        self.stream = self.pyaudio.open(
            output_device_index=self.output_device_index,
            format=self.pyaudio.get_format_from_width(1),
            channels=1,
            rate=self.bitrate,
            output=True)

        self.shared_data = {
            'frame': []
        }
        self.encode_frame()
        self.write_thread = self.StreamWriterThread(self.pyaudio, self.stream, self.shared_data)
        self.write_thread.start()

    def set_channel_values(self, channel_float_array):
        """Sets the value of the channels based on the specified array.
           Values are floats that range from -1.0 to 1.0."""
        if len(channel_float_array) != self.NUM_CHANNELS:
            raise ValueError('Specified channel_float_array of length {} is not valid, self.NUM_CHANNELS is {}'.format(
                len(channel_float_array), self.NUM_CHANNELS))
        self.channel_values = channel_float_array
        self.encode_frame()

    def set_channel_value(self, channel_index, value):
        """Sets specified channel to the specified value in the range -1.0 to 1.0."""
        if value < -1.0 or value > 1.0:
            raise ValueError('Specified channel value of {} is not between -1.0 and 1.0'.format(value))
        if channel_index < 0 or channel_index > self.NUM_CHANNELS:
            raise ValueError('Specified channel index of {} is not valid, self.NUM_CHANNELS is {}'.format(
                channel_index, self.NUM_CHANNELS))
        self.channel_values[channel_index] = value
        self.encode_frame()

    def stop(self):
        self.write_thread.stop = True
        self.pyaudio = None

    def generate_bitstream(self, duration_ms, level):
        """Generates a bitstream consisting of the specified <level> for <duration_ms> milliseconds"""
        bitcount = int(duration_ms * self.bitrate / 1000)
        bitstream = chr(level) * bitcount
        return bitstream

    def encode_channel(self, channel_value):
        """Encodes the channel value (a float between -1.0 and 1.0) into a pulse duration.
        Each channel consists of a low signal for MIN_PW_MS followed by a high signal.
        The duration of the high signal represents the value of the channel.
        Returns a bitstream representing the specified channel value"""
        high_signal_duration = self.CENTER_PW_MS + channel_value * self.DELTA_PW_MS - self.MIN_PW_MS
        return self.generate_bitstream(self.MIN_PW_MS, self.SIGNAL_LOW) + \
               self.generate_bitstream(high_signal_duration, self.SIGNAL_HIGH)

    def encode_frame(self):
        bitstream = ''
        for channel_value in self.channel_values:
            bitstream += self.encode_channel(channel_value)
        bitstream_duration_ms = float(len(bitstream) * 1000) / self.bitrate

        # Fill remainder of frame with SIGNAL_LOW
        self.shared_data['frame'] = bitstream + self.generate_bitstream(self.FRAME_DURATION_MS - bitstream_duration_ms,
                                                                        self.SIGNAL_LOW)

        frame_duration_ms = float(len(self.shared_data['frame']) * 1000) / self.bitrate
        print 'Encoded RC PPM frame with total data length {:0.02f}ms {} bytes frame length {:0.02f}ms {} bytes'.format(
            bitstream_duration_ms, len(bitstream),
            frame_duration_ms, len(self.shared_data['frame']))


if __name__ == '__main__':
    rc_ppm = RCPPMGenerator()
    time.sleep(0.2)
    rc_ppm.set_channel_values([-1.0] * rc_ppm.NUM_CHANNELS)
    time.sleep(10)
    rc_ppm.stop()
