'''
@File:      temp_monitoring.py
@Time:      2025-08-21
@Author:    Fuuraiko
@Desc:      read real-time temperature reading from instrument, and provide api start/stop to record 'temperature - time' to csv file.
'''

import asyncio
import csv
import datetime
import os
from typing import Optional


class TemperatureRecorder:

    def __init__(self, instrument, filename: str="temperature_log.csv"):
        self._instrument = instrument
        self._filename = filename
        self._recording_task: Optional[asyncio.Task] = None
        self._stop_event: Optional[asyncio.Event] = None

    @property
    def is_running(self) -> bool:
        # check if the task is running
        return self._recording_task is not None and not self._recording_task.done()
    
    def _get_temperature_sync(self):
        # generate simulated data
        import random
        temperature = 25 + round(random.uniform(-0.5, 0.5), 2)
        import time
        time.sleep(0.1)
        return temperature
    
    async def _recorder_loop(self):
        print(f"Start recording temperature to {self._filename}")
        with open(self._filename, "a+", newline="", encoding="utf-8") as f:     # a+  append, read and write
            writer = csv.writer(f)
            # file is empty
            if os.fstat(f.fileno()).st_size == 0:
                writer.writerow(["timestamp", "temperature"])

                while not self._stop_event.is_set():
                    loop_start_time = asyncio.get_event_loop().time()

                    # use asyncio.to_thread to wrap _get_temperature_sync()
                    try:
                        temperature = await asyncio.to_thread(self._get_temperature_sync)
                        timestamp = datetime.datetime.now().isoformat()

                        writer.writerow([timestamp, temperature])
                        f.flush()   # write immediately

                        print(f"Record: {timestamp} - {temperature}")

                    except Exception as e:
                        print(f"Errors in record loop: {e}")

                    # calculate 1s precisely
                    elapsed = asyncio.get_event_loop().time() - loop_start_time
                    sleep_for = 1.0 - elapsed
                    if sleep_for > 0:
                        await asyncio.sleep(sleep_for)

        print("Recording task completed.")

    async def start(self):
        if self.is_running:
            print("Recording task is in progress.")
            return
        
        self._stop_event = asyncio.Event()
        self._recording_task = asyncio.create_task(self._recorder_loop())
        print("Recording task is created and started.")

    async def stop(self):
        if not self.is_running:
            print("Recording task is not running.")
            return
        
        self._stop_event.set()

        await self._recording_task

        self._recording_task = None
        self._stop_event = None
        print("Task is completed.")
