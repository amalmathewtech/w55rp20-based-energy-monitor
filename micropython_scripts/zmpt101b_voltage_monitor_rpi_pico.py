import machine  
import time     
import math 
   
class ZMPT101B:
    def __init__(self, pin, frequency):
        """
        Initialize the ZMPT101B sensor.

        :param pin: The ADC pin number to which the ZMPT101B is connected.
        :param frequency: The AC frequency in Hz (e.g., 50 or 60 Hz).
        """
        self.pin = machine.ADC(pin)  # Create an ADC object for reading voltage
        self.period = 1000000 // frequency  # Calculate microseconds per AC cycle
        self.sensitivity = 1.0  # Default sensitivity setting
        self.VREF = 3.3  # Reference voltage (typically 3.3V or 5V depending on the board)
        self.ADC_SCALE = 65535  # 16-bit ADC scale (0 to 65535 for read_u16)

    def set_sensitivity(self, value):
        """
        Set the sensitivity of the ZMPT101B sensor.

        :param value: Sensitivity value based on calibration.
        """
        self.sensitivity = value

    def get_zero_point(self):
        """
        Calculate the zero point (average center value of the waveform).

        :return: The average zero-point value over one AC cycle.
        """
        Vsum = 0  # Initialize the sum of voltage readings
        measurements_count = 0  # Initialize measurement count
        t_start = time.ticks_us()  # Start timing in microseconds

        # Sample values over one AC cycle
        while time.ticks_diff(time.ticks_us(), t_start) < self.period:
            Vsum += self.pin.read_u16()  # Read ADC value using read_u16()
            measurements_count += 1  # Increment the measurement count

        if measurements_count == 0:
            return 0  # Prevent division by zero in case no measurements were taken

        return Vsum // measurements_count  # Return average zero-point value

    def get_rms_voltage(self, loop_count):
        """
        Calculate RMS voltage over a set number of cycles.

        :param loop_count: The number of AC cycles to average for the RMS calculation.
        :return: The average RMS voltage over the specified cycles.
        """
        reading_voltage = 0.0  # Initialize total reading voltage

        # Loop for the specified number of cycles to get a better average RMS
        for _ in range(loop_count):
            zero_point = self.get_zero_point()  # Get the zero point for this cycle

            Vsum = 0  # Initialize the sum of squared voltages
            measurements_count = 0  # Initialize measurement count
            t_start = time.ticks_us()  # Start timing for one AC cycle

            # Collect data over one AC cycle
            while time.ticks_diff(time.ticks_us(), t_start) < self.period:
                Vnow = self.pin.read_u16() - zero_point  # Remove the zero-point offset
                Vsum += (Vnow * Vnow)  # Square the voltage for RMS calculation
                measurements_count += 1  # Increment the measurement count

            if measurements_count == 0:
                return 0.0  # Prevent division by zero in case no measurements were taken

            # Calculate RMS value
            rms = math.sqrt(Vsum / measurements_count)  # Calculate the square root of the average

            # Convert to actual voltage
            voltage = (rms / self.ADC_SCALE) * self.VREF * self.sensitivity
            reading_voltage += voltage  # Accumulate the voltage readings

        # Return the average RMS voltage over the specified cycles
        return reading_voltage / loop_count

# Example usage
adc_pin = 26  # Pin connected to the ZMPT101B (use your specific pin)
frequency = 50  # AC frequency (50 Hz for many regions, 60 Hz in others)

# Initialize the ZMPT101B sensor
zmpt = ZMPT101B(adc_pin, frequency)

# Optionally set the sensitivity (you should set this based on your calibration)
zmpt.set_sensitivity(500.00)  # Example sensitivity value, adjust based on your sensor

# Continuous RMS voltage reading loop
while True:
    rms_voltage = zmpt.get_rms_voltage(loop_count=50)  # Calculate RMS voltage over 50 cycles
    print("RMS Voltage:", rms_voltage, "V")  # Print the measured RMS voltage
    time.sleep(1)  # Delay for readability, adjust as necessary
