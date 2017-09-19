import subprocess
import zmq

class OrbSlam:
    def __init__(self):
        self.connection_string = 'tcp://localhost:5555'
        self.connect()

    def start_orbslam(self):
        self.proc = subprocess.Popen(['D:\\orbslam\\ORB_SLAM2\\Examples\\Live'], stdout=subprocess.PIPE)

    def read_orbslam_pose(self):
        if self.proc is None:
            return
        line = self.proc.stdout.readline()
        if line != '':
            print line.rstrip()

    def connect(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)

        print 'Attempting connection to ORBSLAM on {}'.format(self.connection_string)
        self.socket.connect(self.connection_string)
        self.socket.setsockopt_string(zmq.SUBSCRIBE, "pose".decode('ascii'))

    def process(self):
        try:
            string = self.socket.recv(flags=zmq.NOBLOCK)
            topic, messagedata = string.split('|')
            print("recv {} {}".format(topic, messagedata))
        except zmq.Again as e:
            #print "No SLAM pose received"
            pass

    def cleanup(self):
        #self.context.term()
        pass

