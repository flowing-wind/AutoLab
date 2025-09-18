import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

import sys
import random
from time import sleep, time
from pymeasure.display.Qt import QtWidgets
from pymeasure.display.windows.managed_dock_window import ManagedDockWindow
from pymeasure.experiment import Procedure, Results
from pymeasure.experiment import IntegerParameter, FloatParameter, Parameter, ListParameter

from datetime import datetime
current_time = datetime.now().strftime('%Y%m%d_%H%M%S')

import pyvisa
from pymeasure.instruments.keithley import Keithley2182
import serial
import numpy as np # Using numpy for NaN


class OverallProcedure(Procedure):

    Temperature = FloatParameter('Temperature', units='K')
    HoldTime = FloatParameter('Hold Time', units='s')

    inst_select = ListParameter('TemperatureController', choices=['TC290', 'Tmon8'], default='TC290')
    addr_tempContr = Parameter('TmpContr_addr', default="ASRL5::INSTR")
    addr_2182 = Parameter('Inst_addr', default="GPIB::1")
    addr_port = Parameter('Port', default="COM4")
    trim = Parameter('Trim', default="0, 65536, 1")

    DATA_COLUMNS = ['Time (s)', 'Temperature (K)', 'Trim', 'Volt (V)']

    def startup(self):
        log.info("Connecting to instruments...")
        rm = pyvisa.ResourceManager()
        
        # connect to temperature controller
        self.tempContr = rm.open_resource(self.addr_tempContr)
        self.tempContr.timeout = 10000  # 10-second timeout in milliseconds
        self.tempContr.baud_rate = 115200
        identity = self.tempContr.query('*IDN?').strip()
        log.info(f"Connected to {identity}")
        
        # connect to nanovoltmeter
        self.nanovoltmeter = Keithley2182(self.addr_2182)
        self.nanovoltmeter.adapter.connection.timeout = 10000 # 10-second timeout
        self.nanovoltmeter.reset()
        self.nanovoltmeter.thermocouple = 'S'
        self.nanovoltmeter.ch_1.setup_voltage()
        log.info(f"Connected to Keithley 2182 at {self.addr_2182}")
        
        # connect to COM
        self.ser = serial.Serial(
            port=self.addr_port,
            baudrate=115200,
            timeout=0.2
        )
        log.info(f"Opened COM port at {self.addr_port}")

        self.start_time = time()

    # temperature controls
    def temp_get(self):
        if self.inst_select == 'TC290':
            temp = self.tempContr.query('KRDG? A')
        elif self.inst_select == 'Tmon8':
            command = b'KRDG\xa3\xbf1'
            temp = self.tempContr.query(command)
            temp = temp.strip() 
        return float(temp)
    
    def temp_stable(self, setTemp, HoldTime):
        """
        Waits until the temperature is stable within a defined range for a specified duration.
        Returns True when stable, continues indefinitely otherwise.
        """
        lower_bound = setTemp - 0.5
        upper_bound = setTemp + 0.5
        stable_start_time = None
        log.info(f"Waiting for temperature to stabilize between {lower_bound:.2f} K and {upper_bound:.2f} K.")

        while True:
            if self.should_stop():
                log.warning("Stop signal received while waiting for temperature stabilization.")
                return False # Indicate that stabilization was interrupted

            current_temp = self.temp_get()
            log.debug(f"Current temperature: {current_temp:.2f} K")
            
            if lower_bound <= current_temp <= upper_bound:
                if stable_start_time is None:
                    stable_start_time = time()
                    log.info(f"Temperature entered stability range. Holding for {HoldTime} s.")

                elapsed_stable_time = time() - stable_start_time
                if elapsed_stable_time >= HoldTime:
                    log.info(f"Temperature has been stable for {HoldTime} s. Proceeding.")
                    return True
            else:
                if stable_start_time is not None:
                    log.info("Temperature moved out of stability range. Resetting hold timer.")
                    stable_start_time = None
            
            sleep(1) # Wait for 1 second between checks

    # port controls (unchanged)
    def port_sendCommand(self, num):
        command = f"Trim:{num}\r\n"
        self.ser.write(command.encode('ascii'))
        
    def port_receive(self):
        response_lines = []
        empty_read_count = 0
        max_empty_reads = 3
        while True:
            line = self.ser.readline()
            if line:
                decoded_line = line.decode('ascii', errors='ignore').strip()
                response_lines.append(decoded_line)
                if "================================" in decoded_line:
                    break
            else:
                empty_read_count += 1
                if empty_read_count >= max_empty_reads:
                    break
                else:
                    continue
        return response_lines

    def execute(self):
        log.info(f"Starting measurement for Temperature: {self.Temperature} K")
        self.temp_set(self.Temperature)
         
        sleep (self.HoldTime)
        # if not self.temp_stable(self.Temperature, self.HoldTime):
        #      # If stabilization was stopped by the user, abort the rest of the procedure
        #     log.warning("Aborting measurement sequence due to interruption during stabilization.")
        #     return
        
        trims = [int(p.strip()) for p in self.trim.split(',')]
        if len(trims) == 1:
            start, stop, step = 0, trims[0], 1
        elif len(trims) == 2:
            start, stop, step = trims[0], trims[1], 1
        elif len(trims) == 3:
            start, stop, step = trims[0], trims[1], trims[2]
        else: # Add a fallback for malformed input
            log.error(f"Invalid Trim parameter format: '{self.trim}'. Aborting.")
            return

        trims_list = list(range(start, stop, step))
        total_steps = len(trims_list)
        log.info(f"Starting Trim scan from {start} to {stop-step} with step {step} ({total_steps} points).")
        
        for i, Trim in enumerate(trims_list):
            if self.should_stop():
                log.warning("Stop signal received during measurement loop.")
                break
                
            self.port_sendCommand(Trim)
            port_response = self.port_receive()
            full_response_str = "\n".join(port_response)
            log.info(f"Received from COM port for Trim={Trim}:\n---\n{full_response_str}\n---")

            voltage = self.nanovoltmeter.voltage
            # Keithley instruments often return a very large number (e.g., 9.9E37) on overload.
            if voltage >= 9.9e37:
                log.warning(f"Keithley 2182 is in an overload state at Trim={Trim}. Recording NaN.")
                voltage = np.nan # Use Not-a-Number for invalid readings
            
            elapsed_time = time() - self.start_time
            current_temp = self.temp_get()
            
            data = {
                'Time (s)': elapsed_time,
                'Temperature (K)': current_temp,
                'Trim': Trim,
                'Volt (V)': voltage,
            }
            self.emit('results', data)
            self.emit('progress', 100 * (i + 1) / total_steps)
            sleep(0.1) # Small delay to prevent overwhelming the instruments

    def shutdown(self):
        log.info("Shutting down all instruments.")
        if hasattr(self, 'tempContr'):
            self.tempContr.close()
        if hasattr(self, 'nanovoltmeter'):
            self.nanovoltmeter.shutdown() # Use pymeasure's shutdown method
        if hasattr(self, 'ser') and self.ser.is_open:
            self.ser.close()
        log.info("Shutdown complete.")


class MainWindow(ManagedDockWindow):
    def __init__(self):
        super().__init__(
            procedure_class=OverallProcedure,
            inputs=['inst_select', 'addr_tempContr', 'addr_2182', 'addr_port', 'trim'],
            displays=[],
            x_axis='Time (s)', # Corrected: displays expects single values
            y_axis=['Temperature (K)','Volt (V)'],
            sequencer=True,
            sequencer_inputs=['Temperature', 'HoldTime'],
            sequence_file='sequence.txt' 
        )

        self.setWindowTitle('AutoLab')
        # The filename is now generated with seconds, making it unique per run
        self.filename = f'{current_time}.csv'
        self.directory = r'./measurements/'
        self.store_measurement = False
        self.file_input.extensions = ["csv", "txt"]


if __name__ == "__main__":
    # Setup basic logging to console
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.resize(1200, 800)
    window.show()
    sys.exit(app.exec())

