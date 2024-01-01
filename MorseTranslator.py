from typing import Dict


class MorseTranslator:
    MORSE_CODE_DICT: Dict[str, str] = {"A": ".-", "B": "-...",
                                       "C": "-.-.", "D": "-..", "E": ".",
                                       "F": "..-.", "G": "--.", "H": "....",
                                       "I": "..", "J": ".---", "K": "-.-",
                                       "L": ".-..", "M": "--", "N": "-.",
                                       "O": "---", "P": ".--.", "Q": "--.-",
                                       "R": ".-.", "S": "...", "T": "-",
                                       "U": "..-", "V": "...-", "W": ".--",
                                       "X": "-..-", "Y": "-.--", "Z": "--..",
                                       "1": ".----", "2": "..---", "3": "...--",
                                       "4": "....-", "5": ".....", "6": "-....",
                                       "7": "--...", "8": "---..", "9": "----.",
                                       "0": "-----", ",": "--..--", ".": ".-.-.-",
                                       "?": "..--..", "/": "-..-.", "-": "-....-",
                                       "(": "-.--.", ")": "-.--.-", "!": "-.-.--"}

    @staticmethod
    def textToMorse(text: str) -> str:
        result = ""

        for letter in text:
            result += MorseTranslator.MORSE_CODE_DICT.get(letter.upper(), "") + " "

        return result

    @staticmethod
    def morseToText(morse: str) -> str:
        # Extra space added at the end to access the last morse code
        morse += ' '

        text = ''
        citext = ''
        i = 0
        for letter in morse:
            if letter != ' ':
                i = 0  # counter to keep track of spaces
                citext += letter
            else:  # in case of space
                i += 1

                # if i = 2 that indicates a new word
                if i == 2:
                    # adding space to separate words
                    text += ' '
                else:
                    # accessing the keys using their values (reverse of encryption)
                    text += list(MorseTranslator.MORSE_CODE_DICT.keys())[list(MorseTranslator.MORSE_CODE_DICT
                                                                  .values()).index(citext)]
                    citext = ''

        return text

