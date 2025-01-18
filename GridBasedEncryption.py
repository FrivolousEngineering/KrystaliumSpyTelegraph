import random
import string
from typing import List, Tuple


class EncryptionGrid:
    def __init__(self, num_columns: int, num_rows: int):
        self._grid: List[List[str]] = self._fillGridRandomly(num_columns, num_rows)
        self._locked_fields = set()  # Stores locked positions as (row, column)

    def displayLockedFields(self) -> None:
        """
        Displays the grid with `X` for locked fields and `O` for open fields.
        Only used for debugging
        """
        locked_visualization = [
            [
                'X' if (row_idx, col_idx) in self._locked_fields else 'O'
                for col_idx in range(len(row))
            ]
            for row_idx, row in enumerate(self._grid)
        ]

        print("Locked Fields Visualization:")
        for row in locked_visualization:
            print(" ".join(row))

    def visualizeRowMethodDecode(self, key: List[int]) -> None:
        """
        Visualizes which letters in the grid were used for the Row Method decode.
        Displays the grid with `-` for unused letters and the letter for used ones.
        """
        visualization = [
            [
                self._grid[row_idx][col_idx] if (col_idx + 1) == key[row_idx] else '-'
                for col_idx in range(len(row))
            ]
            for row_idx, row in enumerate(self._grid)
        ]

        print("Row Method Decode Visualization:")
        for row in visualization:
            print(" ".join(row))

    def visualizeSkipMethodDecode(self, key: List[int]) -> None:
        """
        Visualizes which letters in the grid were used for the Skip Method decode.
        Displays the grid with `-` for unused letters and the letter for used ones.
        """
        # Flatten the grid to match the decode logic
        flat_list = [
            (row_idx, col_idx)
            for row_idx, row in enumerate(self._grid)
            for col_idx in range(len(row))
        ]

        # Keep track of used positions based on skips
        used_positions = set()
        position = -1

        for skip in key:
            position += skip + 1
            used_positions.add(flat_list[position])

        # Create a visualization grid
        visualization = [
            [
                self._grid[row_idx][col_idx] if (row_idx, col_idx) in used_positions else '-'
                for col_idx in range(len(row))
            ]
            for row_idx, row in enumerate(self._grid)
        ]

        print("Skip Method Decode Visualization:")
        for row in visualization:
            print(" ".join(row))

    def addMessageRowMethod(self, message: str) -> List[int]:
        """
        Adds a message to the grid using the Row Method.
        Returns the key used for encoding the message.
        """
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
            raise ValueError("Could not fit message :(")

        # Commit the changes to the grid and locked fields
        self._grid = grid_copy
        self._locked_fields = locked_fields_copy

        return key

    def addMessageSkipMethod(self, message: str, max_skip: int = 6) -> List[int]:
        """
        Adds a message to the grid using the Skip Method.
        Returns the key used for encoding the message.
        """
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

    def displayGrid(self) -> None:
        """Displays the current state of the grid."""
        for row in self._grid:
            print(" ".join(row))

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
    num_columns = 5
    num_rows = 5
    primary_message = "HELLO"
    secondary_message = "WORLD"

    grid = EncryptionGrid(num_columns, num_rows)

    print("Initial Grid:")
    grid.displayGrid()


    print("\nAdding secondary message using Skip Method:")
    primary_key = grid.addMessageRowMethod(primary_message)
    grid.visualizeRowMethodDecode(primary_key)

    secondary_key = grid.addMessageSkipMethod(secondary_message)
    grid.visualizeSkipMethodDecode(secondary_key)

    tertiary_key = grid.addMessageSkipMethod("BEEP")
    grid.visualizeSkipMethodDecode(tertiary_key)

    grid.displayGrid()
    print("Primary Key (Row Method):", primary_key)
    print("Secondary Key (Skip Method):", secondary_key)
    print("Tertiary message (Skip Method):", tertiary_key)

    print("decoded message:", grid.decodeRowMethod(primary_key))
    print("decoded message:", grid.decodeSkipMethod(secondary_key))
    print("decoded message:", grid.decodeSkipMethod(tertiary_key))


