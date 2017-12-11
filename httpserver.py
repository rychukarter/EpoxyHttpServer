import threading
import socket
import queue
from flask import Flask, request, render_template
import time

HTTP_HOST = 'localhost'
HTTP_PORT = 8080

TCP_IP = '127.0.0.1'
TCP_PORT = 10000

LOGSTASH_IP = '192.168.1.105'
LOGSTASH_PORT = 5010
LOGSTASH_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

BUFFER_SIZE = 1024
client_list = list()

app = Flask(__name__)


@app.route('/')
def api_root():
    return render_template('index.html')


@app.route('/main.js')
def js():
    return render_template('main.js')


@app.route('/services/start-client', methods=['POST'])
def api_start_client():
    if 'clientID' in request.json:
        cli = locate_client(client_list, request.json['clientID'])
        if not cli:
            cli = TCPClient(request.json['clientID'])
            cli.start_client()
            return "Client started", 201
        else:
            return "ID already taken", 409
    else:
        return "Specify client ID", 400


@app.route('/services/stop-client', methods=['POST'])
def api_stop_client():
    if 'clientID' in request.json:
        cli = locate_client(client_list, request.json["clientID"])
        if cli:
            cli.stop_client()
            client_list.remove(cli)
            return "Client stopped", 200
        else:
            return "No such client ID", 409
    else:
        return "Specify client ID", 400


@app.route('/services/connect-client', methods=['POST'])
def api_connect_client():
    if ('clientID' and 'ip' and 'port') in request.json:
        cli = locate_client(client_list, request.json["clientID"])
        if cli:
            cli_cmd = ClientCommand(ClientCommand.ConnectClient, (request.json["ip"], int(request.json["port"])))
            ans = cli.push_command(cli_cmd)
            return ans.data, 201
        else:
            return "No such client ID", 409
    else:
        return "Specify client ID", 400


@app.route('/services/disconnect-client', methods=['POST'])
def api_disconnect_client():
    if 'clientID' in request.json:
        cli = locate_client(client_list, request.json["clientID"])
        if cli:
            cli_cmd = ClientCommand(ClientCommand.DisconnectClient)
            ans = cli.push_command(cli_cmd)
            return ans.data, 201
        else:
            return "No such client ID", 409
    else:
        return "Specify client ID", 400


@app.route('/services/start-calibration', methods=['POST'])
def api_start_calibration():
    if (
                            'clientID' and 'calibrationChannel' and 'calibrationResistance' and 'calibrationFrequency' and 'calibrationPhase') in request.json:
        cli = locate_client(client_list, request.json["clientID"])
        if cli:
            cli_cmd = ClientCommand(ClientCommand.StartCalibration, ("DEVCMD_STARTCALIBRATION_" +
                                                                     str(request.json["calibrationChannel"]) + "_" +
                                                                     str(request.json["calibrationResistance"]) + "_" +
                                                                     str(request.json["calibrationFrequency"]) + "_" +
                                                                     str(request.json["calibrationPhase"])))
            ans = cli.push_command(cli_cmd)
            return ans.data, 201
        else:
            return "No such client ID", 409
    else:
        return "Specify client ID", 400


@app.route('/services/start-measurement', methods=['POST'])
def api_start_measurement():
    if (
                            'clientID' and 'measurementFrequency' and 'timeBetween' and 'measurementNumber' and 'channelNumber') in request.json:
        cli = locate_client(client_list, request.json["clientID"])
        if cli:
            cli_cmd = ClientCommand(ClientCommand.StartMeasurement, ("DEVCMD_STARTMEASUREMENT_" +
                                                                     str(request.json["measurementFrequency"]) + "_" +
                                                                     str(request.json["timeBetween"]) + "_" +
                                                                     str(request.json["measurementNumber"]) + "_" +
                                                                     str(request.json["channelNumber"])))
            ans = cli.push_command(cli_cmd)
            return ans.data, 201
        else:
            return "No such client ID", 409
    else:
        return "Specify client ID", 400


@app.route('/services/stop-measurement', methods=['POST'])
def api_stop_measurement():
    if 'clientID' in request.json:
        cli = locate_client(client_list, request.json["clientID"])
        if cli:
            cli_cmd = ClientCommand(ClientCommand.StopMeasurement, "DEVCMD_STOPMEASUREMENT")
            ans = cli.push_command(cli_cmd)
            return ans.data, 201
        else:
            return "No such client ID", 409
    else:
        return "Specify client ID", 400


@app.route('/services/get-device-status')
def api_get_device_status():
    if 'clientID' in request.args:
        cli = locate_client(client_list, request.args["clientID"])
        if cli:
            cli_cmd = ClientCommand(ClientCommand.GetDeviceStatus, "DEVSTA")
            ans = cli.push_command(cli_cmd)
            return ans.data, 201
        else:
            return "No such client ID", 409
    else:
        return "Specify client ID", 400


@app.route('/services/get-measurement-settings')
def api_get_measurement_settings():
    if 'clientID' in request.args:
        cli = locate_client(client_list, request.args["clientID"])
        if cli:
            cli_cmd = ClientCommand(ClientCommand.GetMeasurementSettings, "DEVMEA")
            ans = cli.push_command(cli_cmd)
            return ans.data, 201
        else:
            return "No such client ID", 409
    else:
        return "Specify client ID", 400


class ClientCommand(object):
    ConnectClient, DisconnectClient, StartCalibration, StartMeasurement, StopMeasurement, GetDeviceStatus, GetMeasurementSettings = range(
        7)

    def __init__(self, cmd_type, data=None):
        self.cmd_type = cmd_type
        self.data = data


class ClientReply(object):
    Error, Success = range(2)

    def __init__(self, type, data=None):
        self.type = type
        self.data = data


class DeviceStatus:
    def __init__(self):
        self.comPortNum = 0
        self.TCPHandle = 0
        self.comPortOpenedFlag = 0
        self.measurementFlag = 0
        self.threadId = 0
        self.threadFuncID = 0
        self.threadInited = 0
        self.stopFlag = 0


class MeasurementSettings:
    def __init__(self):
        self.calibrationChannel = 0
        self.calibrationResistance = 0
        self.calibrationPhase = 0
        self.calibrationFrequency = 0
        self.channelNumber = 0
        self.frequency = 0
        self.timeBetween = 0
        self.measurementNumber = 0


class MeasurementReceiveThread(threading.Thread):
    def __init__(self, client_socket, logstash_socket, client_id, lock):
        super().__init__()
        self.client_socket = client_socket
        self.logstash_socket = logstash_socket
        self.client_id = client_id
        self.lock = lock
        self.alive = threading.Event()
        self.alive.set()

    def run(self):
        while self.alive.isSet():
            self.receive_data()

    def stop(self):
        self.alive.clear()

    def receive_data(self):

        buffer = ""
        return_string = ""
        while "End of measurment!" not in return_string:
            self.lock.acquire(True, 0.1)
            try:
                print("Measurment: LA")
                data = self.client_socket.recv(1024)
            finally:
                print("Measurment: LR")
                self.lock.release()
            if not data:
                break
            temp = data.decode("cp1252")
            buffer += temp
            while True:
                if '\n' not in buffer:
                    break
                else:
                    return_string, ignored, buffer = buffer.partition('\n')
                    return_string = str(self.client_id) + return_string + '\n'
                    self.logstash_socket.send(return_string.encode())
        self.alive.clear()


class TCPClientThread(threading.Thread):
    def __init__(self, cmd_q, reply_q, client_id):
        super().__init__()
        self.cmd_q = cmd_q or queue.Queue()
        self.reply_q = reply_q or queue.Queue()
        self.client_id = client_id
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.measurement_thread = None
        self.alive = threading.Event()
        self.alive.set()
        self.lock = threading.Lock()
        self.handlers = {
            ClientCommand.ConnectClient: self.connect_client,
            ClientCommand.DisconnectClient: self.disconnect_client,
            ClientCommand.StartCalibration: self.start_calibration,
            ClientCommand.StartMeasurement: self.start_measurement,
            ClientCommand.StopMeasurement: self.stop_measurement,
            ClientCommand.GetDeviceStatus: self.get_device_status,
            ClientCommand.GetMeasurementSettings: self.get_measurement_settings
        }

    def run(self):
        while self.alive.isSet():
            try:
                cmd = self.cmd_q.get(True, 0.05)
                self.handlers[cmd.cmd_type](cmd)
            except queue.Empty as e:
                continue

    def connect_client(self, cmd):
        try:
            self.client_socket.connect((cmd.data[0], cmd.data[1]))
            self.reply_q.put(self.success_reply("Connection Established"))
        except IOError as e:
            self.reply_q.put(self.error_reply(e))

    def disconnect_client(self, cmd):
        try:
            self.client_socket.close()
            self.reply_q.put(self.success_reply("Connection Closed"))
        except IOError as e:
            self.reply_q.put(self.error_reply(e))

    def start_calibration(self, cmd):
        self.lock.acquire()
        try:
            self.send_data(cmd.data)
            data = self.receive_data("Calibration Done!")
            self.reply_q.put(self.success_reply(data))
        except IOError as e:
            self.reply_q.put(self.error_reply(e))
        finally:
            self.lock.release()

    def start_measurement(self, cmd):
        self.lock.acquire()
        try:
            self.send_data(cmd.data)
            data = self.receive_data("Recived data!")
            self.reply_q.put(self.success_reply(data))
            self.measurement_thread = MeasurementReceiveThread(self.client_socket, LOGSTASH_SOCKET, self.client_id,
                                                               self.lock)
            self.measurement_thread.start()
        except IOError as e:
            self.reply_q.put(self.error_reply(e))
        finally:
            self.lock.release()

    def stop_measurement(self, cmd):
        self.lock.acquire()
        try:
            self.send_data(cmd.data)
            data = self.receive_data("Recived data!")
            self.reply_q.put(self.success_reply(data))
            self.measurement_thread.stop()
        except IOError as e:
            self.reply_q.put(self.error_reply(e))
        finally:
            self.lock.release()

    def get_device_status(self, cmd):
        self.lock.acquire()
        try:
            self.send_data(cmd.data)
            data = self.receive_data("stopFlag")
            self.reply_q.put(self.success_reply(data))
        except IOError as e:
            self.reply_q.put(self.error_reply(e))
        finally:
            self.lock.release()

    def get_measurement_settings(self, cmd):
        self.lock.acquire()
        try:
            self.send_data(cmd.data)
            data = self.receive_data("measurementNumber")
            self.reply_q.put(self.success_reply(data))
        except IOError as e:
            self.reply_q.put(self.error_reply(e))
        finally:
            self.lock.release()

    def send_data(self, data):
        try:
            self.client_socket.send(data.encode())
        except IOError as e:
            self.reply_q.put(self.error_reply(e))

    def receive_data(self, ending_string):
        buffer = ""
        last_string = ""
        return_string = ""
        try:
            while ending_string not in last_string:
                data = self.client_socket.recv(1024)
                if not data:
                    break
                temp = data.decode("cp1252")
                buffer += temp
                while True:
                    if '\n' not in buffer:
                        break
                    else:
                        last_string, ignored, buffer = buffer.partition('\n')
                        return_string += last_string
            return return_string
        except IOError as e:
            self.reply_q.put(self.error_reply(e))

    def error_reply(self, error_str):
        return ClientReply(ClientReply.Error, error_str)

    def success_reply(self, data=None):
        return ClientReply(ClientReply.Success, data)


class TCPClient:
    def __init__(self, client_id):
        self.client_id = client_id
        self.cmd_q = queue.Queue()
        self.replay_q = queue.Queue()
        self.thread = None

        client_list.append(self)

    def start_client(self):
        self.thread = TCPClientThread(self.cmd_q, self.replay_q, self.client_id)
        self.thread.start()

    def stop_client(self):
        self.thread.alive.clear()

    def push_command(self, cmd):

        self.cmd_q.put(cmd)
        while 1:
            try:
                replay = self.replay_q.get()
                if replay:
                    return replay
            except queue.Empty as e:
                continue


def locate_client(c_list, client_id):
    for c in c_list:
        if c.client_id == client_id:
            return c


def main():
    # LOGSTASH_SOCKET.connect((LOGSTASH_IP, LOGSTASH_PORT))
    app.run()


if __name__ == "__main__":
    main()
