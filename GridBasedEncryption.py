import random
import string
from typing import List, Tuple, Optional


class EncryptionGrid:
    def __init__(self, num_columns: int, num_rows: int):
        self._grid: List[List[str]] = self._fillGridRandomly(num_columns, num_rows)
        self._locked_fields = set()  # Stores locked positions as (row, column)

    def getRawGrid(self):
        return self._grid

    def getLockedFields(self):
        return self._locked_fields

    def canEncodeRowMethod(self, message: str, key: List[int]) -> bool:
        """
        Checks if the given message can be encoded into the grid using the Row Method with the provided key.
        """
        if sum(1 for num in key if num != 0) != len(message):
            return False

        for row_idx, col_idx in enumerate(key):
            if col_idx == 0:
                continue  # Skip this row as per the key
            col_idx -= 1  # Convert 1-based index to 0-based

            if (row_idx, col_idx) in self._locked_fields:
                # Field is locked: Check if it already contains the required character
                if self._grid[row_idx][col_idx] != message[row_idx]:
                    return False  # Conflict with locked field
            else:
                # Field is unlocked: It can be modified to encode the character
                pass

        return True  # All characters can be encoded

    def canEncodeSkipMethod(self, message: str, key: List[int]) -> bool:
        """
        Checks if the given message can be encoded into the grid using the Skip Method with the provided key.
        """
        if len(message) != len(key):
            return False  # Message and key lengths must match

        # Flatten the grid into a single list of characters
        flat_list = [
            (row_idx, col_idx, self._grid[row_idx][col_idx])
            for row_idx in range(len(self._grid))
            for col_idx in range(len(self._grid[row_idx]))
        ]

        position = -1
        for char, skip in zip(message, key):
            position += skip + 1
            if position >= len(flat_list):
                return False  # Out of bounds

            row_idx, col_idx, cell = flat_list[position]
            if (row_idx, col_idx) in self._locked_fields:
                # Field is locked: Check if it already contains the required character
                if cell != char:
                    return False  # Conflict with locked field
            else:
                # Field is unlocked: It can be modified to encode the character
                pass

        return True  # All characters can be encoded

    def addMessageRowMethod(self, message: str, preset_key: Optional[List[int]] = None) -> List[int]:
        """
        Adds a message to the grid using the Row Method.
        Returns the key used for encoding the message.
        """

        if preset_key is not None:
            if not self.canEncodeRowMethod(message, preset_key):
                raise Exception("Could not encode message with the given key and row method")

            # Message can be encoded with the given key
            for row_idx, col_idx in enumerate(preset_key):
                if col_idx == 0:
                    continue  # Skip this row as per the key
                col_idx -= 1  # Convert 1-based index to 0-based

                if (row_idx, col_idx) in self._locked_fields:
                    # Field is already locked, no modification needed
                    continue
                else:
                    # Field is unlocked, update the grid and lock the field
                    self._grid[row_idx][col_idx] = message[row_idx]
                    self._locked_fields.add((row_idx, col_idx))


            # The return is simple, as we used a key provided instead of creating our own
            return preset_key

        key: List[int] = []

        # Copy the grid and locked fields to test changes before committing
        grid_copy = [row.copy() for row in self._grid]
        locked_fields_copy = self._locked_fields.copy()

        msg_index = 0

        try:
            for row_idx, row in enumerate(self._grid):
                if msg_index >= len(message):
                    key.append(0)  # No character added for this row
                    continue

                char = message[msg_index]

                # Check if the character naturally exists in this row
                for col_idx, cell in enumerate(row):
                    if cell == char:
                        # Allow use if the field is either unlocked or naturally fits and locked
                        if (row_idx, col_idx) in locked_fields_copy:
                            # It's locked but naturally occurring; we can reuse it
                            key.append(col_idx + 1)  # Use the natural position (1-based index)
                            break
                        else:
                            # It's unlocked; we can lock and use it
                            locked_fields_copy.add((row_idx, col_idx))
                            key.append(col_idx + 1)
                            break
                else:
                    # No natural occurrence found, look for an available (unlocked) field
                    possible_fields = [
                        col_idx
                        for col_idx in range(len(row))
                        if (row_idx, col_idx) not in locked_fields_copy
                    ]

                    if not possible_fields:
                        # No available fields in this row, skip it
                        key.append(0)
                        continue

                    # Randomly pick one of the available fields
                    picked_col_idx = random.choice(possible_fields)

                    # Update the copied grid
                    grid_copy[row_idx][picked_col_idx] = char
                    locked_fields_copy.add((row_idx, picked_col_idx))

                    key.append(picked_col_idx + 1)  # Store 1-based index

                # Move to the next character in the message
                msg_index += 1

        except IndexError:
            raise ValueError("Could not fit message")

        # Commit the changes to the grid and locked fields
        self._grid = grid_copy
        self._locked_fields = locked_fields_copy

        return key

    def addMessageSkipMethod(self, message: str, max_skip: int = 6, preset_key: Optional[List[int]] = None) -> List[int]:
        """
        Adds a message to the grid using the Skip Method.
        Returns the key used for encoding the message.
        """

        if preset_key is not None:
            if not self.canEncodeSkipMethod(message, preset_key):
                raise Exception("Could not encode message with the given key")

            # Message can be encoded with the given key
            flat_list = [
                (row_idx, col_idx)
                for row_idx in range(len(self._grid))
                for col_idx in range(len(self._grid[row_idx]))
            ]

            position = -1
            for char, skip in zip(message, preset_key):
                position += skip + 1
                row_idx, col_idx = flat_list[position]

                if (row_idx, col_idx) in self._locked_fields:
                    # Field is locked; ensure it contains the correct character
                    if self._grid[row_idx][col_idx] != char:
                        raise Exception(f"Locked field at ({row_idx}, {col_idx}) contains a different character.")
                else:
                    # Field is unlocked; update the grid and lock the field
                    self._grid[row_idx][col_idx] = char
                    self._locked_fields.add((row_idx, col_idx))

            # The return is simple, as we used a key provided instead of creating our own
            return preset_key

        key: List[int] = []

        flat_list = [
            (row_idx, col_idx)
            for row_idx, row in enumerate(self._grid)
            for col_idx in range(len(row))
        ]

        # Copy the grid. We are making changes to the copied grid. If we find out the message fits, then we actually
        # replace the original grid with the old one
        grid_copy = self._grid.copy()
        locked_fields_copy = self._locked_fields.copy()

        position = 0

        try:
            for char in message:
                # Check if we already have what we want naturally occurring in the next few characters!
                for i in range(max_skip):
                    row_idx, col_idx = flat_list[position + i]
                    if self._grid[row_idx][col_idx] == char:
                        locked_fields_copy.add((row_idx, col_idx)) # We found a natural hit. Lock and use it!
                        key.append(i)
                        position += i +1
                        break
                else:
                    # We didn't find a hit "naturally", so we will have to see if we have any unlocked fields
                    possible_fields = []
                    for i in range(max_skip):
                        row_idx, col_idx = flat_list[position + i]
                        if (row_idx, col_idx) not in locked_fields_copy:
                            possible_fields.append((i, row_idx, col_idx))
                    # Now we randomly select something from the possible results
                    picked_skip, picked_row_idx, picked_col_idx = random.choice(possible_fields)

                    # We need to change the field to what we want it to be!
                    grid_copy[picked_row_idx][picked_col_idx] = char
                    # We need to lock the field
                    locked_fields_copy.add((picked_row_idx, picked_col_idx))
                    # Add it to our key
                    key.append(picked_skip)

                    position += picked_skip + 1
        except IndexError:
            raise ValueError("Could not fit message :(")

        # We were successful, so now we swap the locks and the grid!

        self._grid = grid_copy
        self._locked_fields = locked_fields_copy

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
        """
        message = []
        for row_idx, col_idx in enumerate(key):
            if col_idx > 0:  # 0 means no letter was selected from this row
                message.append(self._grid[row_idx][col_idx - 1])  # Convert to 0-based index
        return ''.join(message)

    def decodeSkipMethod(self, key: List[int]) -> str:
        """
        Decodes a message encoded using the Skip Method.
        """
        # Flatten the grid
        flat_list = [self._grid[row_idx][col_idx] for row_idx in range(len(self._grid)) for col_idx in range(len(self._grid[row_idx]))]
        position = -1

        message = ""
        for skip in key:
            position += skip + 1
            message += flat_list[position]

        return message


# Example usage
if __name__ == "__main__":
    primary_message = "HELLO"
    secondary_message = "WORLD"

    import EncryptionGridVisualizer



    grid = EncryptionGrid(5, 5)

    visualizer = EncryptionGridVisualizer.EncryptionGridVisualizer(grid)

    visualizer.displayGrid()
    print('')
    secondary_key = grid.addMessageRowMethod("WORLD", preset_key = [1,1,1,1,1])
    visualizer.displayGrid()
    #tertiary_key = grid.addMessageSkipMethod("BEEP")

   # print("Primary Key (Row Method):", primary_key)
    print("Secondary Key (Skip Method):", secondary_key)
    #print("Tertiary message (Skip Method):", tertiary_key)

    #print("decoded message:", grid.decodeRowMethod(primary_key))
    print("decoded message:", grid.decodeRowMethod(secondary_key))
    #print("decoded message:", grid.decodeSkipMethod(tertiary_key))




