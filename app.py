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
current_time = datetime.now().strftime('%Y%m%d_%H')

import pyvisa
from pymeasure.instruments.keithley import Keithley2182
import serial


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
        # connect to temperature controller
        rm = pyvisa.ResourceManager()
        self.tempContr = rm.open_resource(self.addr_tempContr)
        self.tempContr.baud_rate = 115200
        identity = self.tempContr.query('*IDN?').strip()
        log.info(f"Connected to {identity}")
        
        # connect to nanovoltmeter
        self.nanovoltmeter = Keithley2182(self.addr_2182)
        self.nanovoltmeter.reset()
        self.nanovoltmeter.thermocouple = 'S'
        self.nanovoltmeter.ch_1.setup_voltage()
        
        # connect to COM
        self.ser = serial.Serial(
            port=self.addr_port,
            baudrate=115200,
            timeout=0.2
        )

        self.start_time = time()

    # temperature controls
    def temp_set(self, temp):
        self.tempContr.write(f'SETP 1,{temp}')
    def temp_get(self):
        if self.inst_select == 'TC290':
            temp = self.tempContr.query('KRDG? A')
        elif self.inst_select == 'Tmon8':
            command = b'KRDG\xa3\xbf1'
            temp = self.tempContr.query(command)
            temp = temp.strip() 
        return float(temp)
    def temp_stable(self, setTemp, HoldTime):
        lower_bound = setTemp - 0.5
        upper_bound = setTemp + 0.5
        stable_start_time = None

        while True:
            current_temp = self.temp_get()
            if lower_bound <= current_temp <= upper_bound:
                if stable_start_time is None:
                    stable_start_time = time()

                elapsed_stable_time = time() - stable_start_time
                if elapsed_stable_time >= HoldTime:
                    return True
                else:
                    remaining_time = HoldTime - elapsed_stable_time

            else:
                if stable_start_time is not None:
                    stable_start_time = None
                else:
                    pass  
            sleep(1)

    # port controls
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
                if "================================" in decoded_line:    # end signal
                    break
            else:
                empty_read_count += 1
                if empty_read_count >= max_empty_reads:   # timeout
                    break
                else:
                    continue
        return response_lines


    def execute(self):
        self.temp_set(self.Temperature)

        sleep (self.HoldTime)   # for test
        # self.temp_stable(self.Temperature, self.HoldTime)

        trims = [int(p.strip()) for p in self.trim.split(',')]
        if len(trims) == 1:
            start, stop, step = 0, trims[0], 1
        elif len(trims) == 2:
            start, stop, step = trims[0], trims[1], 1
        elif len(trims) == 3:
            start, stop, step = trims[0], trims[1], trims[2]

        trims_list = list(range(start, stop, step))
        total_steps = len(trims_list)
        for i, Trim in enumerate(trims_list):
            if self.should_stop():
                log.warning("Stop signal received during measurement loop.")
                break
            self.port_sendCommand(Trim)
            port_response = self.port_receive()
            full_response_str = "\n".join(port_response)
            log.info(f"Received from COM port for Trim={Trim}:\n---\n{full_response_str}\n---")

            voltage = self.nanovoltmeter.voltage
            elapsed_time = time() - self.start_time
            data = {
                'Time (s)': elapsed_time,
                'Temperature (K)': self.temp_get(),
                'Trim': Trim,
                'Volt (V)': voltage,
            }
            self.emit('results', data)
            self.emit('progress', 100 * (i + 1) / total_steps)


    def shutdown(self):
        self.tempContr.close()
        self.nanovoltmeter.adapter.connection.close()
        self.ser.close()


class MainWindow(ManagedDockWindow):

    def __init__(self):
        super().__init__(
            procedure_class=OverallProcedure,
            inputs=['inst_select', 'addr_tempContr', 'addr_2182', 'addr_port', 'trim'],
            displays=[],
            x_axis=['Time (s)'],
            y_axis=['Temperature (K)','Volt (V)'],
            sequencer=True,
            sequencer_inputs=['Temperature', 'HoldTime'],
            sequence_file='sequence.txt' 
        )

        self.setWindowTitle('AutoLab')
        self.filename = f'{current_time}.csv'
        self.directory = r'./measurements/'
        self.store_measurement = False
        self.file_input.extensions = ["csv", "txt"]


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.resize(1200, 800)
    window.show()
    sys.exit(app.exec())
