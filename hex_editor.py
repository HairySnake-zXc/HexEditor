import os
import sys
import curses
import pyperclip
import binascii
from utils import render_string_from_bytes
from editor.hex_file import HexFile
from editor.editor import HexEditor
from commands.delete import DeleteCommand
from commands.write import WriteCommand
from commands.paste import PasteCommand

OFFSET_Y = 1
OFFSET_X = 24
HEX_CHARS = '1234567890abcdef'


def process_key(hex_editor: HexEditor, key):
    match key:
        case 'KEY_UP':
            if hex_editor.row_index == 0 and hex_editor.row_offset > 0:
                hex_editor.row_offset -= 1
            elif hex_editor.row_index > 0:
                hex_editor.row_index -= 1
        case 'KEY_DOWN':
            if hex_editor.row_index >= HexEditor.ROWS_COUNT - 1:
                hex_editor.row_offset += 1
            else:
                hex_editor.row_index += 1
        case 'KEY_LEFT':
            if hex_editor.column_index >= 0:
                if hex_editor.cell_index == 1:
                    hex_editor.cell_index = 0
                elif hex_editor.column_index > 0:
                    hex_editor.column_index -= 1
                    hex_editor.cell_index = 1
        case 'KEY_RIGHT':
            if hex_editor.column_index <= HexEditor.COLUMNS_COUNT - 1:
                if hex_editor.cell_index == 0:
                    hex_editor.cell_index = 1
                elif hex_editor.column_index < HexEditor.COLUMNS_COUNT - 1:
                    hex_editor.column_index += 1
                    hex_editor.cell_index = 0
        case 'KEY_DC':
            hex_editor.execute_command(DeleteCommand(hex_editor))
        case '':
            hex_editor.undo()
        case '':
            hex_editor.do()
        case '':
            chars = parse_input_from_clipboard()
            hex_editor.execute_command(PasteCommand(hex_editor, chars))
        case _:
            if key.lower() in HEX_CHARS:
                hex_editor.execute_command(WriteCommand(hex_editor, key.lower()))
                process_key(hex_editor, 'KEY_RIGHT')


def parse_input_from_clipboard():
    data = pyperclip.paste()
    res = []
    for ch in data:
        if ch in HEX_CHARS:
            res.append(ch)
        else:
            res.append('0')
    if len(res) % 2 != 0:
        last = res.pop()
        res.append('0')
        res.append(last)
    hexes = "".join(res).encode()
    return binascii.unhexlify(hexes)

    



def print_window(main_screen, hex_editor: HexEditor):
    position_string = hex(
        (hex_editor.row_index + hex_editor.row_offset) * 16 +
        hex_editor.column_index)[2:].rjust(10, '0')
    title = f'{position_string}\t|\t00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f'
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_WHITE)
    main_screen.addstr(0, 0, title, curses.color_pair(1))
    for index, row in enumerate(hex_editor.rows):
        main_screen.addstr(
            index + 1,
            0,
            render_string_from_bytes(
                row,
                hex_editor.row_offset + index,
                hex_editor.COLUMNS_COUNT,
            ),
        )
    main_screen.addstr(hex_editor.cursor_y + OFFSET_Y,
                       hex_editor.cursor_x + OFFSET_X,
                       '',
                       )


def main(main_screen, filename):
    mode = 'r+b' if os.path.isfile(filename) else 'w+b'
    with open(filename, mode) as file:
        hex_file = HexFile(file)
        hex_editor = HexEditor(hex_file)

        main_screen.keypad(True)
        curses.curs_set(1)
        main_screen.nodelay(0)
        while True:
            main_screen.clear()
            print_window(main_screen, hex_editor)
            key = main_screen.getkey()
            if key == ord('q'):
                break
            else:
                process_key(hex_editor, key)

            main_screen.refresh()
        curses.endwin()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide a filename.")
        sys.exit(1)
    curses.wrapper(main, sys.argv[1])
