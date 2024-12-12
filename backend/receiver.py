# backend/receiver.py

import threading
import logging
from typing import Any, Dict
import queue  # Import the queue module

from core.udp_listener import udp_listener  # Assuming this is defined in core
from core import reset_hackrf, start_receiver

logger = logging.getLogger(__name__)

class Receiver:
    def __init__(self, stop_event: threading.Event, message_queue: queue.Queue, device_index: int, frequency: float):
        self.stop_event = stop_event
        self.message_queue = message_queue
        self.device_index = device_index
        self.frequency = frequency
        self.is_receiving = False  # Add a state variable to track if receiving is active
        self.thread = threading.Thread(
            target=self.receiver_thread,
            args=(self.stop_event, self.message_queue, self.device_index, self.frequency),
            daemon=True
        )

    def receiver_thread(self, stop_event, message_queue, device_index, frequency):
        """
        The thread function that handles receiving data. This simulates receiving.
        """
        start_receiver(stop_event, message_queue, device_index, frequency)
        self.is_receiving = True  # Update to active receiving state once receiving starts
        try:
            while not stop_event.is_set():
                if not message_queue.empty():
                    message = message_queue.get_nowait()  # Simulate processing received messages
                    # Process the message here (e.g., log or handle the received data)
                else:
                    # If there's no message, we continue the loop (still receiving, waiting for messages)
                    pass
        except Exception as e:
            logger.error("Error during receiving: %s", e)
        finally:
            self.is_receiving = False  # Mark receiving as stopped once the loop ends

    def start(self):
        self.thread.start()
        logger.info("Receiver thread started on device %d at %.2f Hz.", self.device_index, self.frequency)

    def stop(self):
        logger.info("Stopping receiver thread...")
        self.stop_event.set()
        reset_hackrf()  # Ensure HackRF is reset before joining the thread
        if self.thread.is_alive():
            self.thread.join()  # Wait up to 5 seconds for the thread to finish
            if self.thread.is_alive():
                logger.warning("Receiver thread did not terminate within timeout.")
            else:
                logger.info("Receiver thread stopped successfully.")
        else:
            logger.info("Receiver thread was not running.")
