import random
import string
from typing import List, Tuple, Optional, Set


class EncryptionGrid:
    def __init__(self, num_columns: int, num_rows: int):
        self._grid: List[List[str]] = self._fillGridRandomly(num_columns, num_rows)
        self._locked_fields:  Set[Tuple[int, int]]= set()  # Stores locked positions as (row, column)

    def getRawGrid(self) -> List[List[str]]:
        return self._grid

    def getLockedFields(self) -> Set[Tuple[int, int]]:
        return self._locked_fields

    def canEncodeRowMethod(self, message: str, key: List[int]) -> bool:
        """
        Checks if the given message can be encoded into the grid using the Row Method with the provided key.
        Supports looping keys.
        """
        if not key:
            return False  # An empty key cannot encode anything

        for row_idx, char in enumerate(message):
            col_idx = key[row_idx % len(key)]  # Loop over the key
            if col_idx == 0:
                continue  # Skip this row as per the key
            col_idx -= 1  # Convert 1-based index to 0-based

            if (row_idx % len(self._grid), col_idx) in self._locked_fields:
                # Field is locked: Check if it already contains the required character
                if self._grid[row_idx % len(self._grid)][col_idx] != char:
                    return False  # Conflict with locked field

        return True  # All characters can be encoded

    def canEncodeSkipMethod(self, message: str, key: List[int]) -> bool:
        """
        Checks if the given message can be encoded into the grid using the Skip Method with the provided key.
        Supports looping keys.
        """
        if not key:
            return False  # An empty key cannot encode anything

        # Flatten the grid into a single list of characters
        flat_list = [
            (row_idx, col_idx, self._grid[row_idx][col_idx])
            for row_idx in range(len(self._grid))
            for col_idx in range(len(self._grid[row_idx]))
        ]

        position = -1
        for char_idx, char in enumerate(message):
            skip = key[char_idx % len(key)]  # Loop over the key
            position += skip + 1
            if position >= len(flat_list):
                return False  # Out of bounds

            row_idx, col_idx, cell = flat_list[position]
            if (row_idx, col_idx) in self._locked_fields:
                # Field is locked: Check if it already contains the required character
                if cell != char:
                    return False  # Conflict with locked field

        return True  # All characters can be encoded

    def addMessageRowMethod(self, message: str, preset_key: Optional[List[int]] = None) -> List[int]:
        if preset_key is not None:
            if not self.canEncodeRowMethod(message, preset_key):
                raise Exception("Could not encode message with the given key and row method")

            # Message can be encoded with the given key
            key_length = len(preset_key)
            for msg_idx, char in enumerate(message):
                row_idx = msg_idx % len(self._grid)
                col_idx = (preset_key[msg_idx % key_length] - 1)  # Convert 1-based to 0-based

                if col_idx == -1:
                    continue  # Skip this row as per the key
                if (row_idx, col_idx) in self._locked_fields:
                    continue  # Field is already locked, no modification needed
                else:
                    # Field is unlocked, update the grid and lock the field
                    self._grid[row_idx][col_idx] = char
                    self._locked_fields.add((row_idx, col_idx))

            return preset_key

        # Generate a looping key dynamically
        key: List[int] = []
        key_length = len(self._grid)

        for msg_idx, char in enumerate(message):
            row_idx = msg_idx % key_length
            available_columns = [
                col_idx
                for col_idx in range(len(self._grid[row_idx]))
                if (row_idx, col_idx) not in self._locked_fields
            ]

            if not available_columns:
                raise ValueError("Could not fit message due to insufficient unlocked fields.")

            chosen_col_idx = random.choice(available_columns)
            self._grid[row_idx][chosen_col_idx] = char
            self._locked_fields.add((row_idx, chosen_col_idx))
            key.append(chosen_col_idx + 1)

        return key

    def addMessageSkipMethod(self, message: str, max_skip: int = 6, preset_key: Optional[List[int]] = None) -> List[
        int]:
        if preset_key is not None:
            if not self.canEncodeSkipMethod(message, preset_key):
                raise Exception("Could not encode message with the given key")

            flat_list = [
                (row_idx, col_idx)
                for row_idx in range(len(self._grid))
                for col_idx in range(len(self._grid[row_idx]))
            ]

            position = -1
            key_length = len(preset_key)
            for char_idx, char in enumerate(message):
                skip = preset_key[char_idx % key_length]
                position += skip + 1
                row_idx, col_idx = flat_list[position]

                if (row_idx, col_idx) in self._locked_fields:
                    if self._grid[row_idx][col_idx] != char:
                        raise Exception(f"Locked field at ({row_idx}, {col_idx}) contains a different character.")
                else:
                    self._grid[row_idx][col_idx] = char
                    self._locked_fields.add((row_idx, col_idx))

            return preset_key

        # Generate a looping key dynamically
        flat_list = [
            (row_idx, col_idx)
            for row_idx, row in enumerate(self._grid)
            for col_idx in range(len(row))
        ]

        key: List[int] = []
        position = -1

        for char in message:
            for i in range(max_skip):
                if position + i + 1 >= len(flat_list):
                    raise ValueError("Could not fit message due to insufficient unlocked fields.")
                row_idx, col_idx = flat_list[position + i + 1]
                if self._grid[row_idx][col_idx] == char:
                    key.append(i)
                    position += i + 1
                    break
            else:
                possible_fields = [
                    (i, row_idx, col_idx)
                    for i in range(max_skip)
                    if position + i + 1 < len(flat_list)
                       and (row_idx := flat_list[position + i + 1][0],
                            col_idx := flat_list[position + i + 1][1]) not in self._locked_fields
                ]
                if not possible_fields:
                    raise ValueError("Could not fit message due to insufficient unlocked fields.")

                picked_skip, picked_row_idx, picked_col_idx = random.choice(possible_fields)
                self._grid[picked_row_idx][picked_col_idx] = char
                self._locked_fields.add((picked_row_idx, picked_col_idx))
                key.append(picked_skip)
                position += picked_skip + 1

        return key

    @staticmethod
    def _fillGridRandomly(num_columns: int, num_rows: int) -> List[List[str]]:
        """Generates a random grid of letters."""
        return [
            [random.choice(string.ascii_uppercase) for _ in range(num_columns)]
            for _ in range(num_rows)
        ]

    def decodeRowMethod(self, key: List[int]) -> str:
        """
        Decodes a message encoded using the Row Method.
        The key indicates which column (1-based) to pick from each row.
        Supports looping keys.
        """
        if not key:
            raise ValueError("Key cannot be empty for decoding.")

        message = []
        for row_idx in range(len(self._grid)):
            col_idx = key[row_idx % len(key)]  # Loop over the key
            if col_idx > 0:  # 0 means no letter was selected from this row
                message.append(self._grid[row_idx][col_idx - 1])  # Convert to 0-based index
        return ''.join(message)

    def decodeSkipMethod(self, key: List[int]) -> str:
        """
        Decodes a message encoded using the Skip Method.
        Supports looping keys.
        """
        if not key:
            raise ValueError("Key cannot be empty for decoding.")

        # Flatten the grid
        flat_list = [self._grid[row_idx][col_idx] for row_idx in range(len(self._grid)) for col_idx in
                     range(len(self._grid[row_idx]))]

        position = -1
        message = []
        for char_idx in range(len(flat_list)):  # Decode as long as the flattened grid allows
            skip = key[char_idx % len(key)]  # Loop over the key
            position += skip + 1
            if position >= len(flat_list):
                break  # Stop decoding if we exceed the grid
            message.append(flat_list[position])

        return ''.join(message)





