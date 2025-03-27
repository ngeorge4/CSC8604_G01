try:
    import nfc
    import socketio
    import logging
    import json
    import time
    from datetime import datetime

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

except ImportError as e:
    print(f"Error: Required modules not found - {e}")
    print("Run: pip install nfcpy python-socketio")
    exit(1)

# Configuration
SOCKET_URL = "http://localhost:5004"
RETRY_DELAY = 2
MAX_RETRIES = 3

class NFCHandler:
    def __init__(self):
        self.socket_connected = False
        self.connection_attempts = 0
        
        # Initialize SocketIO client
        self.sio = socketio.Client(
            logger=True,
            engineio_logger=True,
            reconnection=True,
            reconnection_attempts=0,  # Infinite reconnection attempts
            reconnection_delay=1,
            reconnection_delay_max=5
        )
        
        # Set up Socket.IO event handlers
        self.setup_socket_events()

    def setup_socket_events(self):
        """Set up Socket.IO event handlers"""
        @self.sio.event
        def connect():
            self.socket_connected = True
            self.connection_attempts = 0
            logger.info("Connected to server")

        @self.sio.event
        def connect_error(data):
            self.socket_connected = False
            self.connection_attempts += 1
            logger.error(f"Connection failed: {data}")

        @self.sio.event
        def disconnect():
            self.socket_connected = False
            logger.warning("Disconnected from server")

    def connect_socket(self):
        """Connect to Socket.IO server"""
        if not self.socket_connected:
            try:
                self.sio.connect(SOCKET_URL)
                logger.info("Socket.IO connection established")
                return True
            except Exception as e:
                logger.error(f"Socket.IO connection failed: {str(e)}")
                return False
        return True

    def on_connect(self, tag):
        """Handle NFC tag connection"""
        try:
            if not tag.ndef:
                logger.warning("No NDEF records found")
                return True

            for record in tag.ndef.records:
                try:
                    # Parse card data
                    data = json.loads(record.text)
                    
                    # Validate card data
                    if 'set_id' not in data:
                        logger.error("Invalid card data: missing set_id")
                        continue

                    # Send card detection event
                    if self.socket_connected:
                        self.sio.emit('card_detected', data)
                        logger.info(f"Card data sent: {data}")
                    else:
                        logger.warning("Socket not connected - card data not sent")

                except json.JSONDecodeError:
                    logger.error("Invalid JSON data on card")
                except Exception as e:
                    logger.error(f"Error processing card data: {str(e)}")

            return True

        except Exception as e:
            logger.error(f"Error reading card: {str(e)}")
            return False

    def run(self):
        """Main loop"""
        logger.info(f"Starting NFC handler... (Server URL: {SOCKET_URL})")
        
        # Connect to Socket.IO server
        self.connect_socket()

        try:
            # Initialize NFC reader
            with nfc.ContactlessReader('usb') as clf:
                logger.info("NFC reader initialized")
                
                while True:
                    # Poll for NFC tags
                    clf.connect(rdwr={'on-connect': self.on_connect})
                    time.sleep(0.1)

        except KeyboardInterrupt:
            logger.info("\nNFC handler stopped by user")
        except Exception as e:
            logger.error(f"\nError in NFC handler: {str(e)}")
        finally:
            if self.socket_connected:
                self.sio.disconnect()
            logger.info("Cleanup completed")

if __name__ == "__main__":
    logger.info(f"Starting Privacy-Pac NFC Handler (UTC: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')})")
    logger.info(f"Current user: recker1103")
    
    handler = NFCHandler()
    handler.run()
