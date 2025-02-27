import random
import string
from typing import List, Tuple, Optional, Set
import re

class EncryptionGrid:
    def __init__(self, num_columns: int, num_rows: int):
        self._grid: List[List[str]] = self._fillGridRandomly(num_columns, num_rows)
        self._locked_fields:  Set[Tuple[int, int]]= set()  # Stores locked positions as (row, column)

    def getRawGrid(self) -> List[List[str]]:
        return self._grid

    def getLockedFields(self) -> Set[Tuple[int, int]]:
        return self._locked_fields

    @staticmethod
    def _formatMessage(message: str) -> str:
        formated_message = message.upper()

        # Strip out anything that isn't a space or uppercase
        formated_message = re.sub(r"[^A-Z ]", "", formated_message)
        if " " in message:
            formated_message = formated_message + "."
        formated_message = formated_message.replace(" ", ".")
        return formated_message

    def decodeMethod(self, method: str, key: List[int]) -> str:
        if method == "row":
            return self.decodeRowMethod(key)
        elif method == "row-plow":
            return self.decodeRowPlowMethod(key)
        elif method == "skip":
            return self.decodeSkipMethod(key)
        elif method == "skip-plow":
            return self.decodeSkipPlowMethod(key)
        else:
            return ""

    def canEncodeMethod(self, method: str, message: str, key: List[int]) -> bool:
        if method == "row":
            return self.canEncodeRowMethod(message, key)
        elif method == "row-plow":
            return self.canEncodeRowPlowMethod(message, key)
        elif method == "skip":
            return self.canEncodeSkipMethod(message, key)
        elif method == "skip-plow":
            return self.canEncodeSkipPlowMethod(message, key)
        else:
            print("Should not happen!", method)
            return False

    def addMessage(self, method, message_to_encode: str, preset_key: Optional[List[int]] = None) -> List[int]:
        if method == "row":
            return self.addMessageRowMethod(message_to_encode, preset_key)
        elif method == "row-plow":
            return self.addMessageRowPlowMethod(message_to_encode, preset_key)
        elif method == "skip":
            return self.addMessageSkipMethod(message_to_encode, preset_key = preset_key)
        elif method == "skip-plow":
            return self.addMessageSkipPlowMethod(message_to_encode, preset_key = preset_key)
        else:
            print("Should not happen!")
            return []

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

    def canEncodeRowPlowMethod(self, message: str, key: List[int]) -> bool:
        """
        Checks if the given message can be encoded into the grid using the Row-Plow Method
        with the provided key. Alternates row traversal direction (left-to-right for even rows,
        right-to-left for odd rows). Supports looping keys.
        """
        if not key:
            return False  # An empty key cannot encode anything

        for row_idx, char in enumerate(message):
            col_idx = key[row_idx % len(key)]  # Loop over the key
            if col_idx == 0:
                continue  # Skip this row as per the key

            # Adjust the column index based on the zig-zag pattern
            if row_idx % len(self._grid) % 2 == 1:  # Odd row, reverse direction
                col_idx = len(self._grid[row_idx % len(self._grid)]) - col_idx + 1
            col_idx -= 1  # Convert 1-based index to 0-based

            target_row = row_idx % len(self._grid)
            if (target_row, col_idx) in self._locked_fields:
                # Field is locked: Check if it already contains the required character
                if self._grid[target_row][col_idx] != char:
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

    def canEncodeSkipPlowMethod(self, message: str, key: List[int],) -> bool:
        """
        Checks if the given message can be encoded into the grid using the Row-Plow Skip Method
        with the provided key. Alternates row traversal direction (left-to-right for even rows,
        right-to-left for odd rows). Ensures skips do not exceed the max_skip range.

        :param message: The message to encode.
        :param key: The key representing skips for encoding the message.
        :return: True if the message can be encoded; False otherwise.
        """

        # Flatten the grid with zig-zag traversal
        flat_list = [
            (row_idx, col_idx, self._grid[row_idx][col_idx])
            for row_idx in range(len(self._grid))
            for col_idx in (
                range(len(self._grid[row_idx])) if row_idx % 2 == 0 else reversed(range(len(self._grid[row_idx])))
            )
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

    def addMessageRowMethod(self, message_to_encode: str, preset_key: Optional[List[int]] = None) -> List[int]:
        """
        Add a message to the grid using the "Row" method. The row method implies that the key indicates what position
        of the row is to be used. A 0 indicates that the row is to be ignored. The keys "loop", so if you have 8 rows
        and a key of 4 the first and 5th row are referenced by the first number of the key (second and 6th for the
        second, etc..)
        :param message_to_encode: The message to be added
        :param preset_key: If left to None, a key will be generated. Otherwise, the provided key will be used.
        :return: The key (if it was provided, it's the same key, otherwise it returns whatever was generated)
        """
        message = self._formatMessage(message_to_encode)
        if preset_key is not None:
            if not self.canEncodeRowMethod(message, preset_key):
                raise Exception(f"Could not encode message with the given key '{preset_key}' and row method")

            # Message can be encoded with the given key
            key_length = len(preset_key)
            message_idx = 0  # Keep track of the current character in the message

            for row_idx in range(len(self._grid)):
                if message_idx >= len(message):
                    break  # All characters in the message have been encoded

                col_idx = preset_key[row_idx % key_length] - 1  # Convert 1-based to 0-based

                if col_idx == -1:
                    continue  # Skip this row as per the key

                char = message[message_idx]

                if (row_idx, col_idx) in self._locked_fields:
                    # Field is locked; ensure it already contains the correct character
                    if self._grid[row_idx][col_idx] != char:
                        raise Exception(f"Locked field at ({row_idx}, {col_idx}) contains a different character.")
                else:
                    # Field is unlocked; update the grid and lock the field
                    self._grid[row_idx][col_idx] = char
                    self._locked_fields.add((row_idx, col_idx))

                message_idx += 1  # Move to the next character in the message

            return preset_key

        # Generate a looping key dynamically
        key: List[int] = []
        key_length = len(self._grid)
        if key_length < len(message):
            raise Exception("Could not fit message due to insufficient rows")
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

    def addMessageRowPlowMethod(self, message_to_encode: str, preset_key: Optional[List[int]] = None) -> List[int]:
        """
        Add a message to the grid using the "Row-Plow" method. The Row-Plow method alternates the direction of traversal
        for each row (left-to-right on even rows, right-to-left on odd rows). Keys "loop," meaning the first key value
        is reused for rows beyond the key length.

        :param message_to_encode: The message to be added.
        :param preset_key: If left to None, a key will be generated. Otherwise, the provided key will be used.
        :return: The key (if it was provided, it's the same key; otherwise, it returns the dynamically generated key).
        """
        message = self._formatMessage(message_to_encode)
        if preset_key is not None:
            # If a preset key is provided, verify if the message can be encoded
            if not self.canEncodeRowPlowMethod(message, preset_key):
                raise Exception("Could not encode message with the given key and Row-Plow method")

            # Encode the message using the preset key
            key_length = len(preset_key)
            message_idx = 0

            for row_idx in range(len(self._grid)):
                if message_idx >= len(message):
                    break  # All characters in the message have been encoded

                # Adjust the column index based on the zig-zag pattern
                col_idx = preset_key[row_idx % key_length]
                if col_idx == 0:
                    continue  # Skip this row as per the key

                if row_idx % 2 == 1:  # Odd row, reverse direction
                    col_idx = len(self._grid[row_idx]) - col_idx + 1

                col_idx -= 1  # Convert 1-based index to 0-based
                char = message[message_idx]

                if (row_idx, col_idx) in self._locked_fields:
                    if self._grid[row_idx][col_idx] != char:
                        raise Exception(f"Locked field at ({row_idx}, {col_idx}) contains a different character.")
                else:
                    self._grid[row_idx][col_idx] = char
                    self._locked_fields.add((row_idx, col_idx))

                message_idx += 1


            return preset_key

        # Dynamically generate the key
        key: List[int] = []
        key_length = len(self._grid)

        for msg_idx, char in enumerate(message):
            row_idx = msg_idx % key_length

            # Determine the available columns based on the direction of the row
            if row_idx % 2 == 0:  # Even row (left-to-right)
                available_columns = [
                    col_idx
                    for col_idx in range(len(self._grid[row_idx]))
                    if (row_idx, col_idx) not in self._locked_fields
                ]
            else:  # Odd row (right-to-left)
                available_columns = [
                    col_idx
                    for col_idx in range(len(self._grid[row_idx]) - 1, -1, -1)
                    if (row_idx, col_idx) not in self._locked_fields
                ]

            if not available_columns:
                raise ValueError("Could not fit message due to insufficient unlocked fields.")

            # Choose a column dynamically
            chosen_col_idx = random.choice(available_columns)
            self._grid[row_idx][chosen_col_idx] = char
            self._locked_fields.add((row_idx, chosen_col_idx))
            # Convert the 0-based column index to a 1-based index, adjusting for row direction
            if row_idx % 2 == 1:  # Odd row, reverse direction
                chosen_col_idx = len(self._grid[row_idx]) - chosen_col_idx
            else:
                chosen_col_idx += 1

            key.append(chosen_col_idx)

        return key

    def _encodeMessageSkipWithFlatList(self, flat_list, preset_key, message):
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

    def addMessageSkipPlowMethod(self, message_to_encode: str, max_skip: int = 5, preset_key: Optional[List[int]] = None) -> List[
        int]:
        """
        Adds a message to the grid using the Row-Plow Skip Method.
        Alternates row traversal direction (left-to-right for even rows, right-to-left for odd rows).
        Returns the key used for encoding the message.
        """
        message = self._formatMessage(message_to_encode)
        if preset_key is not None:
            # If a preset key is provided, verify if the message can be encoded
            if not self.canEncodeSkipPlowMethod(message, preset_key):
                raise Exception(f"Could not encode message with the given key '{preset_key}'and Row-Plow Skip method")

            # Encode the message using the preset key
            flat_list = [
                (row_idx, col_idx)
                for row_idx in range(len(self._grid))
                for col_idx in (
                    range(len(self._grid[row_idx])) if row_idx % 2 == 0 else reversed(range(len(self._grid[row_idx])))
                )
            ]
            return self._encodeMessageSkipWithFlatList(flat_list, preset_key, message)


        # Generate a dynamic key
        key: List[int] = []
        flat_list = [
            (row_idx, col_idx)
            for row_idx in range(len(self._grid))
            for col_idx in (
                range(len(self._grid[row_idx])) if row_idx % 2 == 0 else reversed(range(len(self._grid[row_idx])))
            )
        ]

        position = 0
        for char in message:
            # Check if the character can be placed naturally within the max skip range
            for i in range(max_skip + 1):
                if position + i >= len(flat_list):
                    raise ValueError("Could not fit message due to insufficient space in the grid.")

                row_idx, col_idx = flat_list[position + i]
                if self._grid[row_idx][col_idx] == char and (row_idx, col_idx) not in self._locked_fields:
                    key.append(i)
                    position += i + 1
                    self._locked_fields.add((row_idx, col_idx))
                    break
            else:
                # If no natural position is found, find an available unlocked position within the skip range
                possible_positions = []
                for i in range(max_skip + 1):
                    if position + i >= len(flat_list):
                        break
                    row_idx, col_idx = flat_list[position + i]
                    if (row_idx, col_idx) not in self._locked_fields:
                        possible_positions.append((i, row_idx, col_idx))

                if not possible_positions:
                    raise ValueError("Could not fit message due to insufficient unlocked fields.")

                # Choose a position randomly
                chosen_skip, chosen_row_idx, chosen_col_idx = random.choice(possible_positions)
                self._grid[chosen_row_idx][chosen_col_idx] = char
                self._locked_fields.add((chosen_row_idx, chosen_col_idx))
                key.append(chosen_skip)
                position += chosen_skip + 1

        return key

    def addMessageSkipMethod(self, message_to_encode: str, max_skip: int = 5, preset_key: Optional[List[int]] = None) -> List[
        int]:
        """
        Add a message to the grid using the "Skip" method. With the skip method you start at the first character of the
        grid and you check the first key. This indicates how many characters you must skip. So if it is 0, the first
        character of the grid is read. If the second number is also 0, you skip 0 characters (and thus, read the second
        one as well). If the third number is 1, you skip the third character and read the fourth one. If you read the end
        of your key, you start at the beginning again.
        :param message_to_encode: The message to be added
        :param max_skip: How high can any number of the key become max. This only has an effect if the preset_key is
        None
        :param preset_key: If left to None, a key will be generated. Otherwise, the provided key will be used.
        :return: The key (if it was provided, it's the same key, otherwise it returns whatever was generated)
        """
        message = self._formatMessage(message_to_encode)
        if preset_key is not None:
            if not self.canEncodeSkipMethod(message, preset_key):
                raise Exception(f"Could not encode message with key {preset_key} using skip method")

            flat_list = [
                (row_idx, col_idx)
                for row_idx in range(len(self._grid))
                for col_idx in range(len(self._grid[row_idx]))
            ]

            return self._encodeMessageSkipWithFlatList(flat_list, preset_key, message)

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
        """
        Generates a random grid of letters, including spaces represented by '.'.
        Spaces appear with a "natural" frequency.
        """
        # Define the characters and their relative frequencies
        characters = string.ascii_uppercase + "."  # Include the space character
        weights = [1] * 26 + [5]  # Weight of 5 for spaces, 1 for each letter

        return  [random.choices(characters, weights=weights, k=num_columns) for _ in range(num_rows)]


    def decodeRowPlowMethod(self, key: List[int]) -> str:
        """
        Decodes a message encoded using the Row-Plow Method.
        The key indicates which column (1-based) to pick from each row, alternating
        direction (left-to-right for even rows, right-to-left for odd rows).
        Supports looping keys.
        """
        if not key:
            raise ValueError("Key cannot be empty for decoding.")

        message = []
        for row_idx in range(len(self._grid)):
            col_idx = key[row_idx % len(key)]  # Loop over the key
            if col_idx > 0:  # 0 means no letter was selected from this row
                if row_idx % 2 == 1:  # Odd row, reverse direction
                    col_idx = len(self._grid[row_idx]) - col_idx + 1
                col_idx -= 1  # Convert to 0-based index
                message.append(self._grid[row_idx][col_idx])

        return ''.join(message)

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


    def _decodeSkipOnFlatList(self, flat_list: List[str], key: List[int]) -> str:
        position = -1
        message = []
        for char_idx in range(len(flat_list)):  # Decode as long as the flattened grid allows
            skip = key[char_idx % len(key)]  # Loop over the key
            position += skip + 1
            if position >= len(flat_list):
                break  # Stop decoding if we exceed the grid
            message.append(flat_list[position])

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
        return self._decodeSkipOnFlatList(flat_list, key)


    def decodeSkipPlowMethod(self, key: List[int]) -> str:
        """
        Decodes a message encoded using the Row-Plow Skip Method.
        Alternates row traversal direction (left-to-right for even rows, right-to-left for odd rows).
        """
        flat_list = [
            self._grid[row_idx][col_idx]
            for row_idx in range(len(self._grid))
            for col_idx in (
                range(len(self._grid[row_idx])) if row_idx % 2 == 0 else reversed(range(len(self._grid[row_idx])))
            )
        ]
        return self._decodeSkipOnFlatList(flat_list, key)


if __name__ == "__main__":
    grid = EncryptionGrid(10, 9)
    grid._grid = [
            list("HAMVUDQMVW"),
            list("EXOAVCP.KE"),
            list("BSHZHFJV.F"),
            list("IAXMSXGYWX"),
            list("VGKGAKDAOE"),
            list("GGZIE.RZM."),
            list("...KHDHE.."),
            list("STP.HN.FE."),
            list("C..F..SSME"),
        ]

    print(grid.decodeSkipPlowMethod([0,1,2]))
    print(grid.decodeSkipMethod([0, 1, 2]))

