import logging
from typing import List, Tuple, Union, Set
from pynput.keyboard import Key, KeyCode

from input.key import combination_from_str, normalize_key, patch_win32_key

logger = logging.getLogger("input.listener")

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
        key = patch_win32_key(key)
        nkey = normalize_key(key)

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
        key = patch_win32_key(key)
        nkey = normalize_key(key)

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