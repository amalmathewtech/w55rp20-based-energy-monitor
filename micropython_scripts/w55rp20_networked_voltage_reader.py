import machine
import time
import math
from usocket import socket
from machine import Pin, WIZNET_PIO_SPI
import urequests
import network

class ZMPT101B:
    def __init__(self, pin, frequency):
        # Initialize ADC for reading voltage and calculate the period based on frequency
        self.pin = machine.ADC(pin)  # ADC object for reading voltage
        self.period = 1000000 // frequency  # Microseconds per AC cycle (for timing)
        self.sensitivity = 1.0  # Default sensitivity for voltage readings
        self.VREF = 3.3  # Reference voltage (usually 3.3V or 5V depending on the board)
        self.ADC_SCALE = 65535  # Scale for 16-bit ADC (0 to 65535 for read_u16)

    def set_sensitivity(self, value):
        """ Set the sensitivity of the ZMPT101B sensor. """
        self.sensitivity = value

    def get_zero_point(self):
        """ Calculate the zero point (average center value of the waveform). """
        Vsum = 0
        measurements_count = 0
        t_start = time.ticks_us()  # Start the timing in microseconds

        # Sample values over one AC cycle
        while time.ticks_diff(time.ticks_us(), t_start) < self.period:
            Vsum += self.pin.read_u16()  # Read ADC value using read_u16()
            measurements_count += 1

        if measurements_count == 0:
            return 0  # Prevent division by zero if no measurements were taken

        return Vsum // measurements_count  # Return average zero-point value

    def get_rms_voltage(self, loop_count):
        """ Calculate RMS voltage over a specified number of cycles (loop_count). """
        reading_voltage = 0.0

        # Loop for the specified number of cycles to get a better average RMS
        for _ in range(loop_count):
            zero_point = self.get_zero_point()  # Get zero point for current cycle

            Vsum = 0
            measurements_count = 0
            t_start = time.ticks_us()  # Start the timing for one AC cycle

            # Collect data over one AC cycle
            while time.ticks_diff(time.ticks_us(), t_start) < self.period:
                Vnow = self.pin.read_u16() - zero_point  # Remove zero-point offset
                Vsum += (Vnow * Vnow)  # Square the voltage for RMS calculation
                measurements_count += 1

            if measurements_count == 0:
                return 0.0  # Prevent division by zero if no measurements were taken

            # Calculate RMS value
            rms = math.sqrt(Vsum / measurements_count)

            # Convert RMS value to actual voltage
            voltage = (rms / self.ADC_SCALE) * self.VREF * self.sensitivity
            reading_voltage += voltage

        # Return the average RMS voltage over the specified cycles
        return reading_voltage / loop_count

# W5x00 Ethernet initialization
def w5x00_init():
    """ Initialize the W5x00 Ethernet chip for network communication. """
    # Set up SPI for the WIZNET chip
    spi = WIZNET_PIO_SPI(baudrate=31_250_000, mosi=Pin(23), miso=Pin(22), sck=Pin(21))  # W55RP20 PIO_SPI
    nic = network.WIZNET5K(spi, Pin(20), Pin(25))  # SPI, CS, reset pin
    nic.active(True)  # Activate the network interface

    # Static IP Configuration (can be switched to DHCP if needed)
    # Adjust the IP address and default gateway as necessary for your network setup
    nic.ifconfig(('192.168.18.20', '255.255.255.0', '192.168.18.1', '8.8.8.8'))

    # Wait until the device is connected to the network
    while not nic.isconnected():
        time.sleep(1)
        print("Connecting to network...")

    print('IP address:', nic.ifconfig())  # Print assigned IP address

# HTTP POST request to send the voltage
def send_voltage_data(voltage):
    """ Send the RMS voltage data to a specified server via HTTP POST request. """
    # URL to send data - it's a demo, so security is on vacation!
    # Please don't judge my lack of safety;so let’s keep this our little secret! :)
    base_url = 'https://tinkererway.dev/php/voltage_handler.php'  
    data = {'voltage': str(voltage)}  # Construct the payload with the voltage value
    try:
        response = urequests.post(base_url, json=data)  # Send POST request
        if response.status_code == 200:
            print("Data sent successfully:", response.json())  # Print response if successful
        else:
            print("Failed to send data. Status code:", response.status_code)  # Print error status
        response.close()  # Close the response
    except Exception as e:
        print("Error during HTTP request:", e)  # Print error message if the request fails

def main():
    """ Main function to initialize components and continuously read and send voltage data. """
    # Initialize the W5x00 chip for network communication
    w5x00_init()

    # Initialize the ZMPT101B sensor on ADC pin 26 with 50 Hz AC frequency
    zmpt = ZMPT101B(pin=26, frequency=50)
    zmpt.set_sensitivity(500)  # Set sensor sensitivity based on calibration

    while True:
        # Get the RMS voltage value from the ZMPT101B sensor (e.g., averaging over 50 cycles)
        rms_voltage = zmpt.get_rms_voltage(loop_count=50)
        print("RMS Voltage:", rms_voltage, "V")  # Print the RMS voltage

        # Send the RMS voltage value over HTTP to the server
        send_voltage_data(rms_voltage)

        # Delay between readings (adjust as necessary)
        time.sleep(5)

if __name__ == "__main__":
    main()  # Run the main function when the script is executed
