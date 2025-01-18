from typing import List

import GridBasedEncryption


class EncryptionGridVisualizer:
    def __init__(self, grid: GridBasedEncryption):
        self._grid = grid
        pass

    def displayGrid(self) -> None:
        """Displays the current state of the grid."""
        for row in self._grid.getRawGrid():
            print(" ".join(row))

    def displayLockedFields(self) -> None:
        """
        Displays the grid with `X` for locked fields and `O` for open fields.
        Only used for debugging
        """
        locked_visualization = [
            [
                'X' if (row_idx, col_idx) in self._grid.getLockedFields() else 'O'
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
                self._grid.getRawGrid()[row_idx][col_idx] if (col_idx + 1) == key[row_idx] else '-'
                for col_idx in range(len(row))
            ]
            for row_idx, row in enumerate(self._grid.getRawGrid())
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
            for row_idx, row in enumerate(self._grid.getRawGrid())
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
                self._grid.getRawGrid()[row_idx][col_idx] if (row_idx, col_idx) in used_positions else '-'
                for col_idx in range(len(row))
            ]
            for row_idx, row in enumerate(self._grid.getRawGrid())
        ]

        print("Skip Method Decode Visualization:")
        for row in visualization:
            print(" ".join(row))