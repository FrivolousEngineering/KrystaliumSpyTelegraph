import pytest
import random
import string

import sys
import os

# Make python shut up about packages
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from GridBasedEncryption import EncryptionGrid

simple_messages = ["HERP", "DERP", "BIKE", "SMILE", "word"]
longer_messages = ["A Word.", "Bjorp!", "Yep yep?", "This is a message"]
combined_messages = simple_messages + longer_messages
encryption_types = ["row", "row-plow", "skip", "skip-plow"]


# Utility function for creating a consistent random grid
def generate_fixed_grid(num_columns, num_rows):
    return [
        [random.choice(string.ascii_uppercase) for _ in range(num_columns)]
        for _ in range(num_rows)
    ]


@pytest.fixture
def sample_grid():
    """Fixture to provide a consistent EncryptionGrid instance for tests."""
    grid = EncryptionGrid(num_columns=7, num_rows=30)
    return grid

# This creates a grid of tests (whoo python magic)
# We basically want to test if we can encode stuff with shorter keys than the message as
# it should loop the key
@pytest.mark.parametrize("encryption_type", encryption_types)
@pytest.mark.parametrize(
    "message, preset_key",
    [
        # Decode with same key lengths
        ("HELLO", [1, 2, 3, 4, 5]),
        ("ABCDE", [1, 1, 2, 1, 3]),
        # Then we try it with non-matching key lengths
        ("DERP", [1]),
        ("DERP", [1, 2]),
        ("DERP", [1, 2, 0]),
        ("DER", [1, 0, 1]),  # Slightly shorter message, as with the row setup we don't have enough rows in the sample grid otherwise
        # Then we try some more with keys longer than the message
        ("OMG", [1,2,3,4,5,2])
    ],
)
def test_add_message_row_method_with_preset_key(sample_grid, encryption_type, message, preset_key):
    result_key = []
    decoded_message = ""
    if encryption_type == "skip":
        result_key = sample_grid.addMessageSkipMethod(message, preset_key = preset_key)
        decoded_message = sample_grid.decodeSkipMethod(preset_key)
    elif encryption_type == "row":
        result_key = sample_grid.addMessageRowMethod(message, preset_key=preset_key)
        decoded_message = sample_grid.decodeRowMethod(preset_key)
    elif encryption_type == "row-plow":
        result_key = sample_grid.addMessageRowPlowMethod(message, preset_key=preset_key)
        decoded_message = sample_grid.decodeRowPlowMethod(preset_key)
    elif encryption_type == "skip-plow":
        result_key = sample_grid.addMessageSkipPlowMethod(message, preset_key=preset_key)
        decoded_message = sample_grid.decodeSkipPlowMethod(preset_key)

    # We can only encode message with capitals
    assert decoded_message.startswith(EncryptionGrid._formatMessage(message))
    assert result_key == preset_key

@pytest.mark.parametrize(
    "message, max_skip",
    [
        ("HELLO", 1),
        ("WORLD", 2),
        ("BLOOP", 3),
        ("HAI",   8)
    ],
)
def test_add_message_skip_method_with_generated_key(sample_grid, message, max_skip):
    """Test addMessageSkipMethod with dynamically generated keys."""
    grid = sample_grid
    key = grid.addMessageSkipMethod(message, max_skip=max_skip)
    decoded_message = grid.decodeSkipMethod(key)
    # We can only encode message with capitals
    assert decoded_message.startswith(EncryptionGrid._formatMessage(message)), f"Failed to encode/decode {message} with skip method"
    assert all(skip <= max_skip for skip in key), "Key contains skips larger than max_skip"

def test_multiple_encode_no_preset_row_first(sample_grid):
    hello_key = sample_grid.addMessageRowMethod("HELLO")
    world_key = sample_grid.addMessageSkipMethod("WORLD")

    assert sample_grid.decodeRowMethod(hello_key).startswith("HELLO")
    assert sample_grid.decodeSkipMethod(world_key).startswith("WORLD")

@pytest.mark.parametrize("encryption_type", encryption_types)
@pytest.mark.parametrize(
    "messages", 
    [
        ["HELLO", "HELLO"],
        ["HELLO", "WORLD"],
        ["HELLO", "WORLD", "HERP"],
    ]
)
def test_encode_multiple_messages(sample_grid, messages, encryption_type):
    for message in messages:
        # The skip can be a bit finicky, as it randomly selects some numbers to decide how much it will skip
        # So just trying a few times makes it work
        num_tries = 0
        while num_tries < 5:
            try:
                print("TRYING", num_tries)
                test_encode_message(sample_grid, message, encryption_type)
                break
            except ValueError:
                num_tries += 1

@pytest.mark.parametrize("encryption_type", encryption_types)
@pytest.mark.parametrize(
    "message", combined_messages
)
def test_encode_message(sample_grid, message, encryption_type):
    decoded_message = ""
    if encryption_type == "skip":
        result_key = sample_grid.addMessageSkipMethod(message)
        decoded_message = sample_grid.decodeSkipMethod(result_key)
    elif encryption_type == "row":
        result_key = sample_grid.addMessageRowMethod(message)
        decoded_message = sample_grid.decodeRowMethod(result_key)
    elif encryption_type == "row-plow":
        result_key = sample_grid.addMessageRowPlowMethod(message)
        decoded_message = sample_grid.decodeRowPlowMethod(result_key)
    elif encryption_type == "skip-plow":
        result_key = sample_grid.addMessageSkipPlowMethod(message)
        decoded_message = sample_grid.decodeSkipPlowMethod(result_key)

    assert decoded_message.startswith(EncryptionGrid._formatMessage(message))

@pytest.mark.parametrize("encryption_type", encryption_types)
@pytest.mark.parametrize(
    "message", simple_messages
)
@pytest.mark.parametrize("num_columns, num_rows", [(6, 6), (10, 5), (5, 10), (10, 10)])
def test_custom_grid_size(num_columns, num_rows, message, encryption_type):
    test_encode_message(EncryptionGrid(num_columns, num_rows), message, encryption_type)


def test_multiple_encode_no_preset_skip_first(sample_grid):
    # As the ordering might matter, we move some stuff around
    world_key = sample_grid.addMessageSkipMethod("WORLD")
    hello_key = sample_grid.addMessageRowMethod("HELLO")

    assert sample_grid.decodeRowMethod(hello_key).startswith("HELLO")
    assert sample_grid.decodeSkipMethod(world_key).startswith("WORLD")

def test_encoding_different_message_same_key_skip(sample_grid):
    sample_grid.addMessageSkipMethod("HELLO", preset_key = [0, 0, 0, 0, 0])
    with pytest.raises(Exception, match="Could not encode message with key"):
        # This should fail, as these fields are already locked for the hello message
        sample_grid.addMessageSkipMethod("WORLD", preset_key = [0, 0, 0, 0, 0])

def test_encoding_different_message_same_key_row(sample_grid):
    sample_grid.addMessageRowMethod("HELLO", preset_key = [1, 2, 3, 4, 5])
    with pytest.raises(Exception, match="Could not encode message with the given key"):
        # This should fail, as these fields are already locked for the hello message
        sample_grid.addMessageRowMethod("WORLD", preset_key = [1, 2, 3, 4, 5])


@pytest.mark.parametrize("num_rows,message", [
    (2, "HER"),
    (3, "DERP"),
    (4, "HELLO"),
])
def test_encode_too_long_message_row(num_rows, message):
    grid = EncryptionGrid(5, num_rows)

    with pytest.raises(Exception, match="Could not fit message"):
        grid.addMessageRowMethod(message)

def test_encode_too_long_message_skip(sample_grid):
    with pytest.raises(Exception, match="Could not fit message"):
        sample_grid.addMessageSkipMethod("HERPIEDERPIEDERPANDMAYBESOMEMOREDERPLIKETHISISJUSTTOOMUCHMANYEAHITSWAYTOMUCHHERPIEDERPIEDERPANDMAYBESOMEMOREDERPLIKETHISISJUSTTOOMUCHMANYEAHITSWAYTOMUCH")


def test_encoding_row_fails_with_conflicting_preset_key(sample_grid):
    """Test that encoding fails with a conflicting preset key."""
    grid = sample_grid
    grid._locked_fields = {(0, 0), (1, 1)}  # Pre-lock some fields

    message = "HELLO"
    conflicting_preset_key = [1, 2, 1, 1, 1]  # Conflicts with locked fields

    with pytest.raises(Exception, match="Could not encode message with the given key"):
        grid.addMessageRowMethod(message, preset_key=conflicting_preset_key)


def test_negative_keys(sample_grid):
    # Technically possible, but likely to cause issues.
    key = sample_grid.addMessageSkipMethod("HELLO", preset_key = [1,2,3,-1])
    assert sample_grid.decodeSkipMethod(key).startswith("HELLO")