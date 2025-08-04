"""

Stonekeep Save Game Editor

This script allows the user to modify the player & parties 

Supported:
- (GOG) Stonekeep save files (*.SAV)

"""
import os
from enum import Enum, auto
from pathlib import Path

version = "1.0"
banner = f"""

 ____  _                   _                             
/ ___|| |_ ___  _ __   ___| | _____  ___ _ __            
\___ \| __/ _ \| '_ \ / _ \ |/ / _ \/ _ \ '_ \           
 ___) | || (_) | | | |  __/   <  __/  __/ |_) |          
|____/ \__\___/|_| |_|\___|_|\_\___|\___| .__/           
  ____                        _____    _|_|_             
 / ___| __ _ _ __ ___   ___  | ____|__| (_) |_ ___  _ __ 
| |  _ / _` | '_ ` _ \ / _ \ |  _| / _` | | __/ _ \| '__|
| |_| | (_| | | | | | |  __/ | |__| (_| | | || (_) | |   
 \____|\__,_|_| |_| |_|\___| |_____\__,_|_|\__\___/|_|   
Version:{version}
"""
# Enums
class character_name(Enum):
    """
    Enumeration of playable characters in the Stonekeep save file.

    Members:
        Drake: The default main character.
        Farley: A secondary or companion character.
    """
    Drake = auto()
    Farley = auto()

class attributes(Enum):
    """
    Enumeration of editable character attributes.

    These attributes map to specific offsets within the save file and determine
    what stat will be modified by the editor.

    Members:
        health: Represents the character's health stat.
        agility: Represents the character's agility stat.
    """
    health = auto()
    agility = auto()

# These are the values that will be written to the save file when a specific
# attribute is selected. All values are single-byte integers (0–255) used
# for direct binary patching.
ATTRIBUTE_VALUES = {
    attributes.health: 255,
    attributes.agility: 10
}

# Each character-attribute pair points to a known offset within the save file
# where the corresponding value can be modified. Offsets are in decimal form
# and refer to absolute byte positions in the .SAV binary structure.

# Example:
#   attributes.health for Drake is stored at offset 340 (hex 0x0154)
OFFSETS = {
    character_name.Drake: {
        attributes.health: 340, # hex 00000154
        attributes.agility: 99999
    },
    character_name.Farley: {
        attributes.health: 99999
    }
}

class game_character:
    """
    Represents a playable character and their currently selected attribute.

    This class is used to track the user's selection during the editing session,
    including which character is being edited and which attribute is targeted
    for modification in the save file.

    Attributes:
        name (character_name): The selected character (e.g., Drake, Farley).
        attributes (attributes): The selected attribute (e.g., health, agility).
    """
    def __init__(self,name:character_name=None,attributes:attributes=None):
        """
        Initializes a new game_character instance.

        Args:
            name (character_name, optional): The character to be edited.
            attributes (attributes, optional): The attribute selected for editing.
        """
        self.name = name
        self.attributes = attributes


def binary_write(value:int,max_value:int,offset:int,file_path:str):
    """
    Writes an integer value to the binary save file at a specified offset.

   This function opens the file in read+write binary mode and write the
   given 'value' at the specified byte offset.

   Args:
        value (int): The integer value to write (mustbe within 0 and max_value).
        max_value (int): The maximum allowed value for the input.
        offset (int): The byte offset in the file where the value will be written.
        file_path (str): Path to the binary file.
    
    Raises:
        ValueError: If offset is negative or value exceeds max_value.
        FileNotFoundError: If the file does not exist.
        OSError: If there is a problem accessing or writing to the file.
    """
    try:
        if offset < 0:
            raise ValueError("Offset must be non-negitive")
        if not(0 <= value <=max_value):
            raise ValueError(f"Value must no exceed max value:{max_value}")
        
        with open(file_path,"rb+") as f:
            # move to the end to get file size
            f.seek(0,2)
            file_size = f.tell()

            if offset >= file_size:
                raise ValueError(f"Offset:{offset} is beyound end of file [size]:{file_size} bytes")

            # Write value to offset
            f.seek(offset)
            f.write(bytes([value]))
            f.close()
            print(f"\nWrote value:{value} to offset:{offset}\n")

    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except ValueError as err:
        print(f"Value Error: {err}")
    except OSError as err:
        print(f"OS Error: {err}")
    
def clean_file_path(raw_path:str) -> Path:
    """
    Cleans a raw file path string for safe use with a Path object.

    This function removes leading and trailing whitespace, any PowerShell-style
    prefix '& ', and surrounding single or double qoutes.

    Args:
        raw_path (str): The raw file path string
    
    Returns:
        Path: A sanitized and normalized Path object.
    """
    cleaned = raw_path.strip()
    if cleaned.startswith("& "):
        cleaned = cleaned[2:] # remove & [space]; As seen in vs code
    cleaned = cleaned.strip('"').strip("'")
    return Path(cleaned)

def clear_screen():
    """
    Clears the terminal screen based on the operating system

    Uses the 'cls' command on Windows and 'clear' on posix systems
    """
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

def edit_menu(character:game_character,file_path):
    """
    Displays the attribute editing menu for a selected game character.

    Prompts the user to choose which attribute to modify (e.g., Health).
    Based on the selection, it looks up the corresponding offset and value,
    and writes the value directly into the provided save file.

    If the user selects "Back", control returns to the main menu.
    Invalid inputs re-display the menu.

    This function loops recursively to allow continuous editing.

    Args:
        character (game_character): The character whose attributes will be modified.
        file_path (Path or str): The path to the Stonekeep save file to be edited.
    """
    # Availible editing options
    options = {        
        "1": "Health",
        "0": "Back"
    }
    # Display options to the user
    print(f"What would you like to modify?")
    for key, value in options.items():
        print(f"[{key}] {value}")
    
    # Get and sanitize user input
    choice = input("> ").strip().lower()

    # Handle user input
    match choice:
        case "0":
            # Choice was to go back
            clear_screen()
            main_menu(file_path)
        case "1":
            # User selected Health to modify
            character.attributes = attributes.health
        case _:
            # Invalid input, redisplay options
            edit_menu(character,file_path)
    
    # Look up the offset and value related to the character
    offset = OFFSETS[character.name][character.attributes]
    value = ATTRIBUTE_VALUES[character.attributes]
    
    # Write values to .SAV file
    binary_write(value, 255, offset, str(file_path))

    # Return to edit menu 
    edit_menu(character,file_path)


def main_menu(file_path:Path):
    """
    Displays the main menu for character selection and proceeds to attribute editing.

    This function prompts the user to choose a character from a predefined list.
    Based on the selection, a `game_character` instance is populated with the corresponding
    character enum value. The function then calls `edit_menu()` to allow editing attributes
    for the selected character.

    If the user selects an invalid option, the menu is re-displayed.
    Selecting "Exit" cleanly terminates the program.

    Args:
        file_path (Path): The path to the Stonekeep save game file to be modified.
    """
    # Create a new game_character
    character = game_character()
    
    # Availible characters to display at main_menu
    options = {
        "1": "Drake",
        "2": "Farely",
        "0": "Exit"
    }
    
    # Display characters menu
    print("Select your Character:")
    for key, value in options.items():
        print(f"[{key}] {value}")
    
    # Normalizing user input
    choice = input("> ").strip().lower()

    # Handling menu selection
    match choice:
        case "0":
            print("\nBYE!!\n")
            quit(0)
        case "1":
            # User selected Drake
            character.name = character_name.Drake
        case "2":
            # User selected Farley
            character.name = character_name.Farley            
        case _:
            # Invalid input, redisplay the input
            print("\nSelection not found\n")
            main_menu(file_path)

    # Edit attribute for selected user    
    edit_menu(character,file_path)

def main():
    """
    Entry point for the Stonekeep Save Game Editor.

    Clears the terminal screen, displays the banner, and prompts the user
    to drag and drop a Stonekeep save file. The raw file path is sanitized
    and passed to `main_menu()` for character selection and attribute editing.
    
    """
    clear_screen()
    print(banner)
    raw_path = input("Drag and drop a save file here, then press Enter:\n")
    # sanitize the file_path
    file_path = clean_file_path(raw_path)
    clear_screen()
    main_menu(file_path)



if __name__ == "__main__":
    main()