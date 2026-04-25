"""
Module for capturing keyboard and mouse events.

This module provides classes to listen for input events (keyboard and mouse)
and react to specific key combinations. It relies on the pynput library
for system-level event capture.

Classes:
    InputListener: Abstract base class for listening to input events.
    CombinationListener: Specialized listener for detecting key combinations.
    InputHook: Main entry point capturing keyboard and mouse events.
"""

import logging
import threading
from typing import List

from pynput import keyboard, mouse
from pynput.keyboard import  KeyCode

from input.listener import InputListener, CombinationListener, combination_from_str

logger = logging.getLogger("input.hook")


class InputHook(object):
    """
    Captures keyboard and mouse events.

    :param listeners: List of registered listeners receiving events.
    :param mouse_pos: Current mouse position, updated on every move.
    :param press_start: Mouse position at the start of a key press.
    :param last_region: Last selected region.
    :param is_pressing: Whether a key is currently pressed.
    """

    listeners: List[InputListener] = []
    key_listener: keyboard.Listener = None
    mouse_listener: mouse.Listener = None

    def __init__(self):
        """
        Construct an InputHook. Initializes internal state.
        """
        self.mouse_pos = (0, 0)
        self.press_start = None
        self.last_region = None
        self.is_pressing = False
        self.listeners = []

    def run(self):
        """
        Run the keyboard and mouse event capture loop, and blocs until the end.
        """
        with keyboard.Listener(on_press=self._on_press, on_release=self._on_release, suppress=False) as key_listener, \
                mouse.Listener(on_move=self._on_move, suppress=False) as mouse_listener:
            self.mouse_listener = mouse_listener
            self.key_listener = key_listener
            mouse_listener.join()
            key_listener.join()

    def start(self) -> threading.Thread:
        """
        Start capturing events in a daemon thread.

        The thread is configured as a daemon so that it is automatically
        stopped when the main program exits.

        :return: The thread running the capture loop.
        """
        thread = threading.Thread(target=self.run)
        thread.daemon = True
        thread.start()
        return thread

    def _on_press(self, key: KeyCode):
        """
        Internal callback invoked by pynput when a key is pressed.

        Dispatches the event to all registered listeners with the current
        mouse position.

        :param key: The key pressed as reported by pynput.
        """
        for listener in self.listeners:
            listener.on_press(key, *self.mouse_pos)

    def _on_release(self, key: KeyCode):
        """
        Internal callback invoked by pynput when a key is released.

        Dispatches the event to all registered listeners with the current
        mouse position.

        :param key: The key released as reported by pynput.
        """
        for listener in self.listeners:
            listener.on_release(key, *self.mouse_pos)

    def _on_move(self, x, y):
        """
        Internal callback invoked by pynput when the mouse is moved.

        Updates the current mouse position.

        :param x: Mouse X coordinate.
        :param y: Mouse Y coordinate.
        """
        self.mouse_pos = (x, y)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app = InputHook()
    c = CombinationListener(combination_from_str("ctrl+f1"), strict=True)
    c.on_combination_typed = lambda mouse_start, mouse_end: print(mouse_start, mouse_end)
    app.listeners.append(c)
    app.run()
