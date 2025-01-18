import pytest
import random
import string

import sys
import os

# Make python shut up about packages
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from GridBasedEncryption import EncryptionGrid

# Utility function for creating a consistent random grid
def generate_fixed_grid(num_columns, num_rows):
    return [
        [random.choice(string.ascii_uppercase) for _ in range(num_columns)]
        for _ in range(num_rows)
    ]

@pytest.fixture
def sample_grid():
    """Fixture to provide a consistent EncryptionGrid instance for tests."""
    grid = EncryptionGrid(num_columns=5, num_rows=5)
    grid._grid = [
        list("ABCDE"),
        list("FGHIJ"),
        list("KLMNO"),
        list("PQRST"),
        list("UVWXY"),
    ]
    return grid

@pytest.mark.parametrize(
    "message, expected_key",
    [
        ("HELLO", [1, 2, 3, 4, 5]),
        ("ABCDE", [1, 1, 1, 1, 1]),
        ("WORLD", [0, 2, 3, 0, 4]),
    ],
)
def test_add_message_row_method_with_generated_key(sample_grid, message, expected_key):
    """Test addMessageRowMethod with dynamically generated keys."""
    grid = sample_grid
    key = grid.addMessageRowMethod(message)
    decoded_message = grid.decodeRowMethod(key)
    assert decoded_message == message, f"Failed to encode/decode {message}"
    assert len(key) == len(grid._grid), "Key length does not match grid rows"

@pytest.mark.parametrize(
    "message, preset_key",
    [
        ("HELLO", [1, 2, 3, 4, 5]),
        ("ABCDE", [1, 1, 2, 1, 3]),
    ],
)
def test_add_message_row_method_with_preset_key(sample_grid, message, preset_key):
    """Test addMessageRowMethod with a preset key."""
    grid = sample_grid
    result_key = grid.addMessageRowMethod(message, preset_key)
    assert result_key == preset_key, "Returned key does not match the preset key"
    decoded_message = grid.decodeRowMethod(result_key)
    assert decoded_message == message, f"Failed to encode/decode {message} with preset key"

@pytest.mark.parametrize(
    "message, max_skip",
    [
        ("HELLO", 6),
        ("WORLD", 5)
    ],
)
def test_add_message_skip_method_with_generated_key(sample_grid, message, max_skip):
    """Test addMessageSkipMethod with dynamically generated keys."""
    grid = sample_grid
    key = grid.addMessageSkipMethod(message, max_skip=max_skip)
    decoded_message = grid.decodeSkipMethod(key)
    assert decoded_message == message, f"Failed to encode/decode {message} with skip method"
    assert all(skip <= max_skip for skip in key), "Key contains skips larger than max_skip"

@pytest.mark.parametrize(
    "message, preset_key",
    [
        ("HELLO", [0, 1, 2, 3, 4]),
        ("ABCDE", [1, 0, 2, 0, 3]),
    ],
)
def test_add_message_skip_method_with_preset_key(sample_grid, message, preset_key):
    """Test addMessageSkipMethod with a preset key."""
    result_key = sample_grid.addMessageSkipMethod(message, preset_key=preset_key)
    assert result_key == preset_key, "Returned key does not match the preset key"
    decoded_message = sample_grid.decodeSkipMethod(result_key)
    assert decoded_message == message, f"Failed to encode/decode {message} with preset key"


def test_encoding_row_fails_with_conflicting_preset_key(sample_grid):
    """Test that encoding fails with a conflicting preset key."""
    grid = sample_grid
    grid._locked_fields = {(0, 0), (1, 1)}  # Pre-lock some fields

    message = "HELLO"
    conflicting_preset_key = [1, 2, 1, 1, 1]  # Conflicts with locked fields

    with pytest.raises(Exception, match="Could not encode message with the given key"):
        grid.addMessageRowMethod(message, preset_key=conflicting_preset_key)
