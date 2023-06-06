from network import WLAN, LoRa
import machine
import time
import binascii
import socket 
import ubinascii
import struct


WIFI_SSID = "ServerSnitchConnection"
WIFI_PWD = "FHJDASK78#SDd" # Correct
APP_EUI = ubinascii.unhexlify('0000000000000000')
APP_KEY = ubinascii.unhexlify('4FFC456E706BBE0370199A390B410C46')
DEV_ADDR = struct.unpack(">l", ubinascii.unhexlify('260B9B65'))[0]

class Option:
    SEND_TO_DEVICE = 1
    SEND_TO_API = 2
    CHECK_INTERNET_CONNECTION = 3

class Actions:
    START_SYSTEM = 1
    RESTART_SYSTEM = 2

class ServerSnitch():

    def __init__(self):
        self.wlan = WLAN(mode=WLAN.STA)
        self.wlan.antenna(WLAN.INT_ANT)
        self.lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868)
        self.uart = None
        self.__init_uart__()
        self.eui = binascii.hexlify(LoRa().mac()).decode('ascii')
        pin = machine.Pin('P11', mode=machine.Pin.OUT)
        pin.value(0)
        pin = machine.Pin('P12', mode=machine.Pin.OUT)
        pin.value(0)

        print("Trying to join lora")
        self.lora.join(activation=LoRa.ABP, auth=(DEV_ADDR, APP_KEY, APP_KEY), timeout=0)

        while not self.lora.has_joined():
            time.sleep(2.5)
            print('Not yet joined...')
        print("Joined!")



    def __init_uart__(self):
        self.uart = machine.UART(0, baudrate=115200)

    def try_lora(self, wan, lan, data):
        print("Trying lora")
        # create a LoRa socket
        s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

        # set the LoRaWAN data rate
        s.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)

        # make the socket blocking
        # (waits for the data to be sent and for the 2 receive windows to expire)
        s.setblocking(True)

        # send some data
        print("to send")
        message = bytes([wan, lan, data])
        print(message)
        s.send(message)

        # make the socket non-blocking
        # (because if there's no data received it will block forever...)
        s.setblocking(False)

        # get any data received (if any...)
        data = s.recv(64)
        print(data)
        return False

    def try_wifi(self, wan, lan, data):
        try:
            nets = self.wlan.scan()
            success = False
            if not self.wlan.isconnected():
                for net in nets:
                    print(net.ssid)
                    if net.ssid == WIFI_SSID:
                        self.wlan.connect(net.ssid, auth=(net.sec, WIFI_PWD), timeout=10000)
                        tries = 0
                        
                        while tries < 10:
                            print(tries)
                            tries = tries + 1
                            time.sleep(2)
                        
                        if self.wlan.isconnected():
                            success = True
                        break
            else:
                success = True

            print("JRAMOS success_try_wifi=", success)
            if success:
                if isinstance(data, bool):
                    if data:
                        message = "pcup!{}".format(self.eui)
                    else:
                        message = "pcdown!{}".format(self.eui)
                else:
                    message = "pcup!{}!{}!{}!{}".format(self.eui, wan, lan, data)
                
                print("Message to be sent= ", message)
                pybytes.send_signal(1, message)

            return success
        except Exception as e:
            print("Error while connecting to the wifi network {}".format(e))
            return False

    def check_server_internet(self):
        self.send_command(Option.CHECK_INTERNET_CONNECTION)
        loop = 1
        wan = lan = pc_up = False
        while loop < 10:
            print(loop)
            if self.uart.any():
                message = self.uart.readline()
                if "serverconnection" in message:
                    message = message.decode("ascii")
                    wan = message.split("!")[1]
                    lan = message.split("!")[2]
                    pc_up = True
                    loop = 10
            time.sleep(2)
            loop = loop+1

        return bool(wan), bool(lan), pc_up

    def send_command(self, command):
        message = "configsnitch!{}!{}".format(command, self.eui)
        self.uart.write(message.encode())

    def get_critical_config(self):
        self.send_command(Option.SEND_TO_DEVICE)
        message = ""
        loop = 1
        data = ""
        while loop < 10:
            if self.uart.any():
                message = self.uart.readline()
                if "criticalconfig" in message:
                    message = message.decode("ascii")
                    if message != "criticalconfig!none":
                        data = message
                    loop = 10
            time.sleep(2)
            loop = loop+1

        return data

    def ask_for_action(self):
        # TODO: get pybytes to check if an action is requested via IoT
        return Actions.START_SYSTEM
    
    def perform_action(self, action):
        if action is not None:
            if action == Actions.RESTART_SYSTEM:
                pin = machine.Pin('P11', mode=machine.Pin.OUT)
            elif action == Actions.START_SYSTEM:
                pin = machine.Pin('P8', mode=machine.Pin.OUT)

            pin.value(1)
            time.sleep(1)
            pin.value(0)

    def try_send(self, wan, lan, data):
        success = self.try_wifi(wan, lan, data)
        if not success:
            self.try_lora(wan, lan, data)

    def run(self):
        while True:
            try:
                wan, lan, pc_up = self.check_server_internet()
                print("JRAMOS pc_up=", pc_up)
                if pc_up:
                    if wan:
                        self.send_command(Option.SEND_TO_API)
                    else:
                        data = self.get_critical_config()
                        if data != "":
                            self.try_send(wan, lan, data)
                        else:
                            # PC UP but no critical data
                            self.try_send(wan, lan, True)
                else:
                    #PC DOWN
                    self.try_send(wan, lan, False)

            except Exception as e:
                print(e)
            
            action = self.ask_for_action()
            self.perform_action(action)

            time.sleep(10)


def main(argv=None):
    app = ServerSnitch()
    app.run()


if __name__ == "__main__":
    main()