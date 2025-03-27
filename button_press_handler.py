"""
Privacy-Pac Button Handler
Author: ngeorge4
Last Updated: 2025-03-20 04:33:48 UTC
"""

try:
    import RPi.GPIO as GPIO
    import time
    import requests
    from requests.exceptions import RequestException
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

except ImportError as e:
    print(f"Error: Required modules not found - {e}")
    print("Run: sudo apt-get install python3-rpi.gpio")
    exit(1)

LEFT_BUTTON_PIN = 4
RIGHT_BUTTON_PIN = 5
DEBOUNCE_TIME = 0.5
RETRY_DELAY = 2
FLASK_HOST = "localhost"
FLASK_PORT = 5004
FLASK_SERVER_URL = f"http://{FLASK_HOST}:{FLASK_PORT}"
MAX_RETRIES = 3

class ButtonHandler:
    def __init__(self):
        self.last_left_press = 0
        self.last_right_press = 0
        self.server_available = False
        self.connection_attempts = 0
        
    def setup_gpio(self):
        try:
            GPIO.cleanup()
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            GPIO.setup(LEFT_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(RIGHT_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            logger.info("GPIO setup completed successfully")
            return True
        except Exception as e:
            logger.error(f"GPIO setup failed: {str(e)}")
            return False

    def check_server_availability(self):
        try:
            response = requests.get(f"{FLASK_SERVER_URL}/health", timeout=2)
            if response.status_code == 200:
                if not self.server_available:
                    logger.info("Server connection established")
                self.server_available = True
                self.connection_attempts = 0
                return True
        except requests.exceptions.RequestException as e:
            self.connection_attempts += 1
            if self.server_available:
                logger.error(f"Lost connection to server: {str(e)}")
            elif self.connection_attempts % 5 == 0:
                logger.warning(f"Still trying to connect... ({self.connection_attempts} attempts)")
            self.server_available = False
        return False

    def send_button_press(self, choice):
        if not self.server_available:
            if self.check_server_availability():
                logger.info("Server connection restored")
            else:
                logger.warning("Server unavailable - button press ignored")
                return False

        try:
            response = requests.post(
                f"{FLASK_SERVER_URL}/gpio-button-press",
                json={"choice": choice},
                headers={"Content-Type": "application/json"},
                timeout=2
            )
            response.raise_for_status()
            logger.info(f"Successfully sent button press: {choice}")
            return True
        except RequestException as e:
            logger.error(f"Failed to send button press: {str(e)}")
            self.server_available = False
            return False

    def check_button(self, pin, last_press_time, choice):
        if GPIO.input(pin) == GPIO.LOW:
            current_time = time.time()
            if (current_time - last_press_time) >= DEBOUNCE_TIME:
                logger.info(f"{choice.title()} button pressed")
                if self.send_button_press(choice):
                    return current_time
        return last_press_time

    def run(self):
        logger.info(f"Starting button handler... (Server URL: {FLASK_SERVER_URL})")
        
        if not self.setup_gpio():
            logger.error("Failed to setup GPIO. Exiting...")
            return

        logger.info("Checking server availability...")
        self.check_server_availability()

        try:
            while True:
                if not self.server_available and (time.time() % 5) < 0.1:
                    self.check_server_availability()

                self.last_left_press = self.check_button(
                    LEFT_BUTTON_PIN,
                    self.last_left_press,
                    "left"
                )
                
                self.last_right_press = self.check_button(
                    RIGHT_BUTTON_PIN,
                    self.last_right_press,
                    "right"
                )
                
                time.sleep(0.1)

        except KeyboardInterrupt:
            logger.info("\nButton handler stopped by user")
        except Exception as e:
            logger.error(f"\nError in button handler: {str(e)}")
        finally:
            GPIO.cleanup()
            logger.info("GPIO cleanup completed")

if __name__ == "__main__":
    handler = ButtonHandler()
    handler.run()