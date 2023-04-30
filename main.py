from network import WLAN, LoRa
import machine
import time
import binascii

WIFI_SSID = "ServerSnitchConnection"
WIFI_PWD = "FHJDASK78#SDd"


class Option:
    SEND_TO_DEVICE = 1
    SEND_TO_API = 2
    CHECK_INTERNET_CONNECTION = 3

class ServerSnitch():

    def __init__(self):
        self.wlan = WLAN(mode=WLAN.STA)
        self.wlan.antenna(WLAN.EXT_ANT)
        self.lora = LoRa()
        self.uart = None
        self.__init_uart__()
        self.eui = binascii.hexlify(LoRa().mac()).decode('ascii')

    def __init_uart__(self):
        self.uart = machine.UART(0, baudrate=115200)

    def try_lora(self):
        return False

    def try_wifi(self):
        try:
            
            nets = self.wlan.scan()
            for net in nets:
                if net.ssid == WIFI_SSID:
                    self.wlan.connect(net.ssid, auth=(net.sec, WIFI_PWD), timeout=10000)
                    while not self.wlan.isconnected():
                        machine.idle() # save power while waiting
                    return True
        except Exception as e:
            print("Error while connecting to the wifi network {}".format(e))
            return False
        
    def loop_lora(self):
        print("Not implemented")
    
    def loop_wifi(self):
        # TODO: implement socket and stablish connection to server
        return
        
    def loop(self, connection="LoRa"):
        #TODO: Make the main program here.
        if connection == "LoRa":
            loop_lora()
        else:
            loop_wifi()

    def check_server_internet(self):
        message = self.send_command(Option.CHECK_INTERNET_CONNECTION)
        loop = True
        wan = lan = False
        while loop:
            if self.uart.any():
                message = self.uart.readline()
                if "serverconnection" in message:
                    message = message.decode("ascii")
                    wan = message.split("!")[1]
                    lan = message.split("!")[2]
                    loop = False

        return bool(wan), bool(lan)

    def send_command(self, command):
        message = "configsnitch!{}!{}".format(command, self.eui)
        self.uart.write(message.encode())

    def get_data(self):
        pass

    def run(self):
        while True:
            try:
                wan, lan = self.check_server_internet()

                if wan == True:
                    self.send_command(Option.SEND_TO_API)
                else:
                    self.send_command(Option.SEND_TO_DEVICE)
                    data = self.get_data()
                    success = self.try_wifi(data)
                    if not success:
                        self.try_lora(data)

                time.sleep(10)
            except Exception as e:
                print(e)


def main(argv=None):
    app = ServerSnitch()
    app.run()


if __name__ == "__main__":
    main()