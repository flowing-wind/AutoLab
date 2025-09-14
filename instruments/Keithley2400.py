from pymeasure.instruments.keithley import Keithley2400

class Ky2400:

    def __init__(self, name, addr, idn):
        self.name = name
        self.addr = addr
        self._instrument = None
        self.connected = False

    def connect(self):
        if not self.connected:
            self._instrument = Keithley2400(self.addr)
            self.connected = True
            print(f"{self.name} connected.")
        return self

    def disconnect(self):
        if self.connected and self._instrument:
            self._instrument.shutdown()
            self._instrument = None
            self.connected = False
            print(f"{self.name} disconnected")

    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

            
with Ky2400("Keithley2400", "GPIB::4") as sm:
    sm.source_mode = 'voltage'
    sm.voltage = 5.0
    measurement = sm.measure_voltage()
    print (f"Result: {measurement} V")

