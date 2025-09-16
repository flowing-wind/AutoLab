import logging
from datetime import datetime
from time import sleep
import pyvisa
import serial

from pymeasure.experiment import Procedure, Parameter

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

class Tmon8Procedure(Procedure):

    temperatures = Parameter('Temperature Setpoints', 
                             default='284.2345, 270.0012, 245.5314')
    address = Parameter('Address')     # ASRL5::INSTR

    DATA_COLUMNS = ['Time', 'Temperature']

    def startup(self):
        rm = pyvisa.ResourceManager()
        self.device = rm.open_resource(self.address)
        self.device.baud_rate = 115200
        self.device.read_termination = '\r\n'
        self.device.write_termination = '\r\n'
        identity = self.device.query('*IDN?').strip()
        log.info(f"Connected to {identity}")

        ser = serial.Serial("COM4", 115200)
        if ser.isOpen():
            log.info("COM4 connected.")
        else:
            log.info("Cannot connect to COM4.")

    def execute(self):
        setpoints = [float(t) for t in self.temperatures.split(',')]
        command_bytes = b'KRDG\xa3\xbf1'

        for temp in setpoints:
            log.info(f"Setting temperature to {temp} K")
            self.device.write(f'SETP 1,{temp}')
            sleep(5)
            log.info(f"Starting measurement at {temp} K")     # stable

            for i in range(65536):
                data = {
                    'Time': datetime.now(),
                    'Temperature': float(self.device.query(command_bytes))
                }
                self.emit('results', data)
                self.emit('progress', i)
                self.ser.write(f"Trim:{i}".encode('ascii'))
                Trim = self.ser.read(1024)
                log.info(f"{Trim}")
                sleep(0.1)

                if self.should_stop():
                    log.warning("Caught the stop flag in the procedure")
                    return
                
    def shutdown(self):
        log.info("Experiment finished. Turning off temperature control.")
        self.device.write('SETP 1,298')
        self.device.close()         
