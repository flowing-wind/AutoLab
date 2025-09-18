import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

import sys
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
import numpy as np
import threading

class OverallProcedure(Procedure):

    # 全局计时器，由所有实例共享
    _overall_start_time = None

    Temperature = FloatParameter('Temperature', units='K', default=298)
    HoldTime = FloatParameter('HoldTime', units='s', default=60)

    inst_select = ListParameter('TemperatureController', choices=['TC290', 'Tmon8'], default='TC290')
    addr_tempContr = Parameter('TmpContr_addr', default="ASRL3::INSTR")
    addr_2182 = Parameter('Inst_addr', default="GPIB::22")
    addr_port = Parameter('Port', default="COM7")
    trim = Parameter('Trim', default="0, 20, 1")

    DATA_COLUMNS = ['Time (s)', 'Temperature (K)', 'Trim', 'Voltage (V)']

    def startup(self):
        log.info("Connecting to instruments...")
        self.instrument_lock = threading.Lock()
        rm = pyvisa.ResourceManager()
        
        self.tempContr = rm.open_resource(self.addr_tempContr)
        self.tempContr.baud_rate = 115200
        self.tempContr.flush(pyvisa.constants.VI_READ_BUF_DISCARD | pyvisa.constants.VI_WRITE_BUF_DISCARD)
        identity = self.tempContr.query('*IDN?').strip()
        log.info(f"Connected to {identity}")
        
        self.nanovoltmeter = Keithley2182(self.addr_2182)
        self.nanovoltmeter.adapter.connection.timeout = 10000
        self.nanovoltmeter.reset()
        self.nanovoltmeter.thermocouple = 'S'
        self.nanovoltmeter.ch_1.setup_voltage()
        log.info(f"Connected to Keithley 2182 at {self.addr_2182}")
        
        self.ser = serial.Serial(port=self.addr_port, baudrate=115200, timeout=0.2)
        log.info(f"Opened COM port at {self.addr_port}")

        self.monitoring_running = True
        self.monitoring_thread = threading.Thread(target=self._monitor_instruments)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        log.info("Started background instrument monitoring.")

    def _monitor_instruments(self):
        while self.monitoring_running:
            try:
                # 确保全局计时器已启动，否则等待
                if OverallProcedure._overall_start_time is None:
                    sleep(0.1)
                    continue

                with self.instrument_lock:
                    current_temp = self._temp_get_unlocked()
                    voltage = self.nanovoltmeter.voltage
                
                elapsed_time = time() - OverallProcedure._overall_start_time
                
                if voltage >= 9.9e37:
                    voltage = np.nan

                data = {
                    'Time (s)': elapsed_time,
                    'Temperature (K)': current_temp,
                    'Trim': np.nan,
                    'Voltage (V)': voltage,
                }
                self.emit('results', data)
            except Exception as e:
                log.error(f"Error in monitoring thread: {e}")
            
            sleep(0.5)

    def temp_set(self, tempSet):
        with self.instrument_lock:
            if self.inst_select == 'TC290':
                self.tempContr.write(f'SETP 1,{tempSet}')
            elif self.inst_select == 'Tmon8':
                self.tempContr.write(f'SETP 1,{tempSet}\r\n')

    def _temp_get_unlocked(self):
        if self.inst_select == 'TC290':
            temp = self.tempContr.query('KRDG? A')
        elif self.inst_select == 'Tmon8':
            command = b'KRDG\xa3\xbf1'
            self.tempContr.write_raw(command)
            response = self.tempContr.read_raw()
            temp = response.decode('ascii', errors='ignore').strip()
        return float(temp)

    def temp_get(self):
        with self.instrument_lock:
            return self._temp_get_unlocked()

    def temp_stable(self, setTemp, HoldTime):
        lower_bound = setTemp - 0.5
        upper_bound = setTemp + 0.5
        stable_start_time = None
        log.info(f"Waiting for temperature to stabilize between {lower_bound:.2f} K and {upper_bound:.2f} K.")
        while True:
            if self.should_stop():
                log.warning("Stop signal received while waiting for temperature stabilization.")
                return False
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
            sleep(1)

    def port_sendCommand(self, num):
        with self.instrument_lock:
            command = f"Trim:{num}\r\n"
            self.ser.write(command.encode('ascii'))      
            
    def port_receive(self):
        with self.instrument_lock:
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
        log.info(f"Starting measurement for Temperature: {self.Temperature} K, HoldTime: {self.HoldTime} s")
        self.temp_set(self.Temperature)
        sleep(0.5)
        
        if not self.temp_stable(self.Temperature, self.HoldTime):
            log.warning("Aborting measurement sequence due to interruption during stabilization.")
            return
        
        trims = [int(p.strip()) for p in self.trim.split(',')]
        if len(trims) == 1:
            start, stop, step = 0, trims[0], 1
        elif len(trims) == 2:
            start, stop, step = trims[0], trims[1], 1
        elif len(trims) == 3:
            start, stop, step = trims[0], trims[1], trims[2]
        else:
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

            with self.instrument_lock:
                voltage = self.nanovoltmeter.voltage
                current_temp = self._temp_get_unlocked()

            if voltage >= 9.9e37:
                log.warning(f"Keithley 2182 is in an overload state at Trim={Trim}. Recording NaN.")
                voltage = np.nan
            
            elapsed_time = time() - OverallProcedure._overall_start_time
            
            data = {
                'Time (s)': elapsed_time,
                'Temperature (K)': current_temp,
                'Trim': Trim,
                'Voltage (V)': voltage,
            }
            self.emit('results', data)
            self.emit('progress', 100 * (i + 1) / total_steps)
            sleep(0.1)

    def shutdown(self):
        log.info("Shutting down all instruments.")
        self.monitoring_running = False
        if hasattr(self, 'monitoring_thread'):
            self.monitoring_thread.join()
        log.info("Stopped background monitoring.")
        if hasattr(self, 'tempContr'):
            self.tempContr.close()
        if hasattr(self, 'nanovoltmeter'):
            self.nanovoltmeter.shutdown()
        if hasattr(self, 'ser') and self.ser.is_open:
            self.ser.close()
        log.info("Shutdown complete.")


class MainWindow(ManagedDockWindow):
    def __init__(self):
        super().__init__(
            procedure_class=OverallProcedure,
            inputs=['inst_select', 'addr_tempContr', 'addr_2182', 'addr_port', 'trim', 'Temperature', 'HoldTime'],
            displays=['Temperature', 'trim', 'HoldTime'],
            x_axis='Time (s)',
            y_axis=['Temperature (K)', 'Voltage (V)'],
            sequencer=True,
            sequencer_inputs=['Temperature', 'HoldTime'],
            sequence_file='sequence.txt'
        )
        self.setWindowTitle('AutoLab')
        self.filename = f'{current_time}.csv'
        self.directory = r'./measurements/'
        self.store_measurement = False
        self.file_input.extensions = ["csv", "txt"]

    def queue(self, procedure=None):
        # 检查Manager是否正在运行。如果不在运行，说明这是一个新的序列的开始。
        if not self.manager.is_running():
            # 在将第一个任务添加到队列之前，设置全局起始时间。
            OverallProcedure._overall_start_time = time()
            log.info(f"A new sequence is starting. Global timer initiated.")
        
        # 调用父类的原始queue方法，以确保实验能被正常添加到队列中。
        super().queue(procedure=procedure)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.resize(1200, 800)
    window.show()
    sys.exit(app.exec())
