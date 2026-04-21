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
import sys
import threading
from typing import Callable, List, Tuple, Union, Set

from pynput import keyboard, mouse
from pynput.keyboard import Key, KeyCode

logger = logging.getLogger("input_hook")

KEY_ALIASES = {
    "ctrl": Key.ctrl,
    "ctrl_l": Key.ctrl_l,
    "ctrl_r": Key.ctrl_r,
    "maj": Key.shift,
    "shift": Key.shift,
    "shift_l": Key.shift_l,
    "shift_r": Key.shift_r,
    "alt": Key.alt,
    "alt_l": Key.alt_l,
    "alt_r": Key.alt_r,
    "alt_gr": Key.alt_gr,
    "cmd": Key.cmd,
    "cmd_r": Key.cmd_r,
    "space": Key.space,
    "tab": Key.tab,
    "enter": Key.enter,
    "retour": Key.backspace,
    "backspace": Key.backspace,
    "suppr": Key.delete,
    "delete": Key.delete,
    "esc": Key.esc,
    "echap": Key.esc,
    "haut": Key.up,
    "up": Key.up,
    "bas": Key.down,
    "down": Key.down,
    "gauche": Key.left,
    "left": Key.left,
    "droite": Key.right,
    "right": Key.right,
    "home": Key.home,
    "fin": Key.end,
    "end": Key.end,
    "page_haut": Key.page_up,
    "page_up": Key.page_up,
    "page_bas": Key.page_down,
    "page_down": Key.page_down,
    "insert": Key.insert,
    "verr_maj": Key.caps_lock,
    "caps_lock": Key.caps_lock,
    "num_lock": Key.num_lock,
    "scroll_lock": Key.scroll_lock,
    "print_screen": Key.print_screen,
    "pause": Key.pause,
    "menu": Key.menu,
    "f1": Key.f1, "f2": Key.f2, "f3": Key.f3, "f4": Key.f4,
    "f5": Key.f5, "f6": Key.f6, "f7": Key.f7, "f8": Key.f8,
    "f9": Key.f9, "f10": Key.f10, "f11": Key.f11, "f12": Key.f12,
    "f13": Key.f13, "f14": Key.f14, "f15": Key.f15, "f16": Key.f16,
    "f17": Key.f17, "f18": Key.f18, "f19": Key.f19, "f20": Key.f20,
    "f21": Key.f21, "f22": Key.f22, "f23": Key.f23, "f24": Key.f24,
    "media_next": Key.media_next,
    "media_previous": Key.media_previous,
    "media_play_pause": Key.media_play_pause,
    "media_stop": Key.media_stop,
    "media_volume_mute": Key.media_volume_mute,
    "media_volume_down": Key.media_volume_down,
    "media_volume_up": Key.media_volume_up,
}

KEY_NORMALIZE = {
    Key.ctrl_l: Key.ctrl,
    Key.ctrl_r: Key.ctrl,
    Key.shift_l: Key.shift,
    Key.shift_r: Key.shift,
    Key.alt_l: Key.alt,
    Key.alt_r: Key.alt,
}


def key_from_str(key_str: str) -> Union[KeyCode, Key]:
    """
    Convert a textual key specification to a KeyCode or Key object.

    Accepts special key names in French or English (e.g. "ctrl", "maj", "echap",
    "haut", "f1") as well as single characters (e.g. "a", "1"). Comparison is
    case-insensitive and ignores leading/trailing whitespace.

    :param key_str: Key specification (e.g. "ctrl", "maj", "a", "f1", "up").
    :return: The corresponding Key or KeyCode object.
    :raises ValueError: If the specification does not match any known key.
    """
    key_str = key_str.strip().lower()
    if key_str in KEY_ALIASES:
        return KEY_ALIASES[key_str]
    if len(key_str) == 1:
        return KeyCode.from_char(key_str)
    raise ValueError(f"Unknown key: {key_str!r}")


def combination_from_str(combination_str: str) -> List[Union[KeyCode, Key]]:
    """
    Convert a textual key combination specification to a list of KeyCode/Key.

    The string must contain keys separated by "+" (e.g. "ctrl+f1", "maj+alt+f1",
    "ctrl+c"). Each element is converted individually via :func:`key_from_str`.

    :param combination_str: Key combination separated by "+" (e.g. "ctrl+c", "maj+alt+f1").
    :return: List of Key or KeyCode objects composing the combination.
    :raises ValueError: If any element does not match a known key.
    """
    return [key_from_str(k) for k in combination_str.split("+")]


def _normalize_key(key: Union[KeyCode, Key]) -> Union[KeyCode, Key]:
    """
    Normalize modifier variants to their generic form.

    Maps left/right variants (ctrl_l, ctrl_r, shift_l, shift_r, alt_l, alt_r)
    to their generic counterpart (ctrl, shift, alt) so that combinations
    involving a generic modifier accept either side.

    :param key: The key to normalize.
    :return: The normalized key.
    """
    return KEY_NORMALIZE.get(key, key)


def _patch_win32_key(key: KeyCode):
    """
    Patch a win32-specific bug where KeyCode characters have incorrect offsets.

    On Windows, pynput may return characters with ASCII codes below 65 that
    are shifted by 64. This method corrects such cases by adding 64 to the
    character code and converting it back to lowercase.

    :param key: The key to patch.
    :return: The patched key, or the original key if no patch is needed.
    """
    if not "win32" in key.__class__.__module__:
        return key

    if hasattr(key, "char") and key.char:
        o = ord(key.char[0])
        if o < 65:
            return KeyCode.from_char(chr(o+64).lower())

    return key


class InputListener(object):
    """
    Base class for listening to keyboard and mouse input events.

    Subclasses should override :meth:`on_press` and/or :meth:`on_release`
    to react to key press and release events.
    """

    def on_press(self, key: KeyCode, mouse_x: int, mouse_y: int):
        """
        Called when a key is pressed.

        :param key: The key that was pressed.
        :param mouse_x: Mouse X coordinate at the time of the event.
        :param mouse_y: Mouse Y coordinate at the time of the event.
        """
        pass

    def on_release(self, key: KeyCode, mouse_x: int, mouse_y: int):
        """
        Called when a key is released.

        :param key: The key that was released.
        :param mouse_x: Mouse X coordinate at the time of the event.
        :param mouse_y: Mouse Y coordinate at the time of the event.
        """
        pass


class CombinationListener(InputListener):
    """
    Specialized listener detecting the simultaneous press of a key combination.

    The :attr:`on_combination_typed` callback is triggered upon release of the
    first key of the combination, only if the keys that were pressed just before
    this release exactly match the expected combination.

    The starting mouse position is recorded when the first key of the combination
    is pressed. The ending position corresponds to the moment of the triggering
    release.

    :param combination: Set of keys constituting the expected combination.
    :param pressed_keys: Set of currently pressed keys.
    :param mouse_start: Mouse position at the start of the combination.
    :param mouse_end: Mouse position when the combination is detected.
    :param strict: If True, any key outside the combination invalidates the attempt.
    :param tainted: Indicates whether a foreign key was pressed (strict mode).
    """
    normalized_pressed_keys: Set[KeyCode]
    pressed_keys: Set[KeyCode]
    combination: Set[KeyCode]
    mouse_start: Tuple[int, int]
    tainted: bool
    strict: bool

    def __init__(self, combination: List[KeyCode] | str, strict: bool = False):
        """
        Construct a CombinationListener.

        :param combination: List of keys composing the expected combination (order does not matter).
        :param strict: If True, no other key must have been pressed during the combination.
            If False, the combination is accepted even if a foreign key was pressed and
            released in the meantime.
        """
        self.combination = set(combination_from_str(combination) if isinstance(combination, str) else combination)
        self.normalized_pressed_keys = set()
        self.pressed_keys = set()
        self.mouse_start = 0, 0
        self.strict = strict
        self.tainted = False

    def on_press(self, key: KeyCode, mouse_x: int, mouse_y: int):
        """
        Handle a key press event.

        Records the mouse position if this is the first key of the combination
        being pressed. In strict mode, marks the attempt as invalid if a foreign
        key is pressed.

        :param key: The key that was pressed.
        :param mouse_x: Mouse X coordinate at the time of the event.
        :param mouse_y: Mouse Y coordinate at the time of the event.
        """
        key = _patch_win32_key(key)
        nkey = _normalize_key(key)

        if not self.pressed_keys:
            self.mouse_start = mouse_x, mouse_y

        self.pressed_keys.add(key)
        self.normalized_pressed_keys.add(nkey)

        if self.pressed_keys == self.combination or self.normalized_pressed_keys == self.combination:
            logger.debug(f"Key combination pressed : {self.pressed_keys}")
            self.on_combination_pressed(self.mouse_start, (mouse_x, mouse_y))

        if self.strict and key not in self.combination and nkey not in self.combination:
            logger.debug(f"Key combination was tainted by {key}")
            self.tainted = True

    def on_release(self, key: KeyCode, mouse_x: int, mouse_y: int):
        """
        Handle a key release event.

        If, just before the release, the set of pressed keys exactly matches the
        combination (and the attempt is not invalidated in strict mode), triggers
        the callback. Then removes the key from the pressed keys set. Resets the
        taint flag if no keys remain pressed.

        :param key: The key that was released.
        :param mouse_x: Mouse X coordinate at the time of the event.
        :param mouse_y: Mouse Y coordinate at the time of the event.
        """
        key = _patch_win32_key(key)
        nkey = _normalize_key(key)

        if ((self.pressed_keys == self.combination
                or self.normalized_pressed_keys == self.combination)
                and not self.tainted):
            logger.debug(f"Key combination released : {self.pressed_keys}")
            self.on_combination_released(self.mouse_start, (mouse_x, mouse_y))
            self.on_combination_typed(self.mouse_start, (mouse_x, mouse_y))

        self.pressed_keys.discard(key)
        self.normalized_pressed_keys.discard(nkey)

        if not self.pressed_keys:
            self.normalized_pressed_keys.clear()
            self.tainted = False

    def on_combination_pressed(self, mouse_start: Tuple[int, int], mouse_end: Tuple[int, int]):
        """
        Called when all keys of the combination are pressed simultaneously.

        :param mouse_start: Mouse position when the first key was pressed.
        :param mouse_end: Mouse position when the last key was pressed.
        """
        pass

    def on_combination_released(self, mouse_start: Tuple[int, int], mouse_end: Tuple[int, int]):
        """
        Called when all keys of the combination are released simultaneously.

        :param mouse_start: Mouse position when the first key was pressed.
        :param mouse_end: Mouse position when the last key was released.
        """
        pass

    def on_combination_typed(self, mouse_start: Tuple[int, int], mouse_end: Tuple[int, int]):
        """
        Called when the combination is fully typed (all keys pressed then released).

        :param mouse_start: Mouse position when the first key was pressed.
        :param mouse_end: Mouse position when the last key was released.
        """
        pass


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
                mouse.Listener(on_move=self._on_move) as mouse_listener:
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
    c = CombinationListener(combination_from_str("ctrl+a"), strict=True)
    c.on_combination_typed = lambda mouse_start, mouse_end: print(mouse_start, mouse_end)
    app.listeners.append(c)
    app.run()
