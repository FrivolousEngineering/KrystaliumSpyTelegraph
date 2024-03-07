import serial
import logging
import threading
import time


class PeripheralSerialController:
    def __init__(self,  baud_rate = 115200):
        # Handle listening to serial.
        self._serial_send_thread = threading.Thread(target=self._handleSerial, daemon=True)

        self._serial_read_thread = threading.Thread(target=self._handleSerialRead, daemon=True)
        self._baud_rate = baud_rate
        self._serial = None

        self._recreate_serial_timer = None
        self._serial_recreate_time = 5

        self._active_led: int = -1
        self._volt_meter_active = False
        self._arm_position = "Relay"

    def start(self) -> None:
        # TODO: Should probably handle starting it multiple times?
        self._createSerial()

    def setActiveLed(self, active_led: int) -> None:
        self._active_led = active_led

    def setVoltMeterActive(self, active: bool) -> None:
        self._volt_meter_active = active

    def stop(self):
        self._serial = None
        if self._recreate_serial_timer:
            self._recreate_serial_timer.cancel()

    def getArmPosition(self) -> str:
        return self._arm_position

    def _sendCommand(self, command=""):
        # TODO: add command validity checking.
        if self._serial:
            self._serial.write(b"\n")
            command += "\n"
            self._serial.write(command.encode('utf-8'))
        else:
            logging.error("Unable to write command %s without serial connection" % command)

    def _handleSerialRead(self):
        logging.info("Starting serial read thread")
        while self._serial is not None:
            try:
                line = self._serial.readline().decode('utf-8')
                if line.startswith("Arm position: "):
                    arm_position = line.replace("Arm position: ", "")
                    self._arm_position = arm_position.strip()

                # print("READLINE SERIAL", line)
            except Exception as e:
                logging.error(f"Serial broke with exception [{e}]")
                time.sleep(0.1)  # Prevent error spam.

    def _handleSerial(self):
        logging.info("Starting serial send thread")
        while self._serial is not None:
            try:
                self._sendCommand(f"light {self._active_led}")
                if self._volt_meter_active:
                    self._sendCommand("volt 1")
                else:
                    self._sendCommand("volt 0")
                time.sleep(2)  # Throttle the sending a bit.

                pass
            except serial.SerialException as e:
                logging.warning(f"Previously working serial has stopped working, try to re-create! {e}, {type(e)}")
                self._serial = None
                # Try to re-create it after a few seconds
                self._recreate_serial_timer = threading.Timer(self._serial_recreate_time, self._createSerial)
                self._recreate_serial_timer.start()
                pass
            except Exception as e:
                logging.error(f"Serial broke with exception of type {type(e)}: {e}")
                time.sleep(0.1)  # Prevent error spam.

    def _startSerialThread(self) -> None:
        self._serial_send_thread.start()
        self._serial_read_thread.start()

    def _createSerial(self) -> None:
        logging.info("Attempting to create serial")
        try:
            self._serial_send_thread.join()  # Ensure that previous thread has closed
            self._serial_send_thread = threading.Thread(target=self._handleSerial, daemon=True)
        except RuntimeError:
            # If the thread hasn't started before it will cause a runtime. Ignore that.
            pass
        try:
            self._serial_read_thread.join()
            self._serial_read_thread = threading.Thread(target=self._handleSerialRead(), daemon=True)
        except RuntimeError:
            pass

        for i in range(0, 10):
            try:
                port = f"/dev/ttyUSB{i}"
                self._serial = serial.Serial(port, self._baud_rate, timeout=2)
                logging.info(f"Connected with serial {port}")
                break
            except Exception:
                pass
            try:
                port = f"/dev/ttyACM{i}"
                self._serial = serial.Serial(port, self._baud_rate, timeout=2)
                logging.info(f"Connected with serial {port}")
                break
            except Exception:
                pass

        if self._serial is not None:
            # Call later
            threading.Timer(2, self._startSerialThread).start()
        else:
            logging.warning("Unable to create serial. Attempting again in a few seconds.")
            # Check again after a bit of time has passed
            self._recreate_serial_timer = threading.Timer(self._serial_recreate_time, self._createSerial)
            self._recreate_serial_timer.start()


