from network import WLAN
import machine

WIFI_SSID = "ServerSnitchConnection"
WIFI_PWD = "FHJDASK78#SDd"

class ServerSnitch():

    def __init__(self):
        self.wlan = None
        self.lora = None

    def set_up_lora(self):
        return False

    def set_up_wifi(self):
        try:
            self.wlan = WLAN(mode=WLAN.STA)
            self.wlan.antenna(WLAN.EXT_ANT)
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
        
    def loop_lora():
        print("Not implemented")
    
    def loop_wifi():
        # TODO: implement socket and stablish connection to server
        return
        
    def loop(self, connection="LoRa"):
        #TODO: Make the main program here.
        if connection == "LoRa":
            loop_lora()
        else:
            loop_wifi()

    def run(self):
        if self.set_up_lora():
            #TODO: Call the starter loop
            pass
        elif self.set_up_wifi():
            print('WiFi connection succeeded!')
            self.loop(connection="WiFi")
        else:
            print("No module LoRa or WiFi could be loaded")
            pass


app = ServerSnitch()
app.run()