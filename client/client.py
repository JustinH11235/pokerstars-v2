#!/usr/bin/env python3

# DONT REMOVE!! Version Identifier: |=V=| VERSION 3 |=V=|

import curses
import subprocess
import requests
import re
import math
import sys
import os
from enum import Enum

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared import (
    Suit,
    ClientPlayerAction,
    ClientNextActionType,
    ClientNextAction,
    ClientPlayerState,
    PlayerState,
)

import socketio
import npyscreen
import art


def extract_version_from_file(file_content):
    match = re.search(r"\|\=V\=\| VERSION (\d+) \|\=V\=\|", file_content)
    if match:
        return match.group(1)
    else:
        return None


def get_latest_version():
    github_client_url = f"https://raw.githubusercontent.com/JustinH11235/pokerstars-v2/main/client/client.py"
    github_shared_url = (
        f"https://raw.githubusercontent.com/JustinH11235/pokerstars-v2/main/shared.py"
    )

    # Fetch file contents from GitHub
    response = requests.get(github_client_url)
    if response.status_code == 200:
        response.encoding = "utf-8"
        github_file_content = response.text

        # Extract version number from GitHub file
        github_version = extract_version_from_file(github_file_content)

        # Extract version number from local file
        client_filepath = os.path.abspath(__file__)
        with open(client_filepath, "r", encoding="utf-8") as local_file:
            local_file_content = local_file.read()
            local_version = extract_version_from_file(local_file_content)

        # Compare version numbers
        if github_version and local_version:
            if github_version != local_version:
                # Replace local file with GitHub file contents
                with open(client_filepath, "w", encoding="utf-8") as local_file:
                    local_file.write(github_file_content)

                import shared

                shared_filepath = os.path.abspath(shared.__file__)
                shared_response = requests.get(github_shared_url)
                if shared_response.status_code == 200:
                    shared_response.encoding = "utf-8"
                    shared_file_content = shared_response.text
                    with open(shared_filepath, "w", encoding="utf-8") as shared_file:
                        shared_file.write(shared_file_content)
                    return True
    return False


def play_sound_by_name(sound_names):
    does_paplay_work = None
    try:
        subprocess.run(
            ["paplay", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        does_paplay_work = True
    except FileNotFoundError:
        does_paplay_work = False
    except subprocess.CalledProcessError:
        does_paplay_work = False
    if not does_paplay_work:
        return None
    shortest_files = {name: None for name in sound_names}
    for root, dirs, files in os.walk("/usr/share/sounds"):
        for file in files:
            for name in sound_names:
                if name in file:
                    sound_path = os.path.join(root, file)
                    if shortest_files[name] is None or len(sound_path) < len(
                        shortest_files[name]
                    ):
                        shortest_files[name] = sound_path
    for name, shortest_file in shortest_files.items():
        if shortest_file is not None:
            subprocess.run(["paplay", shortest_file])
            return True
    return None


def play_new_action_sound():
    ret = play_sound_by_name(["message", "bell", "complete"])
    if ret is None:
        # fallback for non-linux/ubuntu
        curses.beep()


def play_new_card_sound():
    # trash-empty works well for cards being placed
    ret = play_sound_by_name(["trash"])
    # if ret is None:
    #     # fallback for non-linux/ubuntu
    #     curses.beep()


class PokerTheme(npyscreen.ThemeManager):
    _colors_to_define = (
        ("BLACK_WHITE", curses.COLOR_BLACK, curses.COLOR_WHITE),
        ("BLUE_BLACK", curses.COLOR_BLUE, curses.COLOR_BLACK),
        ("CYAN_BLACK", curses.COLOR_CYAN, curses.COLOR_BLACK),
        ("GREEN_BLACK", curses.COLOR_GREEN, curses.COLOR_BLACK),
        ("MAGENTA_BLACK", curses.COLOR_MAGENTA, curses.COLOR_BLACK),
        ("RED_BLACK", curses.COLOR_RED, curses.COLOR_BLACK),
        ("YELLOW_BLACK", curses.COLOR_YELLOW, curses.COLOR_BLACK),
        ("BLACK_RED", curses.COLOR_BLACK, curses.COLOR_RED),
        ("BLACK_BLUE", curses.COLOR_BLACK, curses.COLOR_BLUE),
        ("BLACK_GREEN", curses.COLOR_BLACK, curses.COLOR_GREEN),
        ("BLACK_YELLOW", curses.COLOR_BLACK, curses.COLOR_YELLOW),
        ("BLUE_WHITE", curses.COLOR_BLUE, curses.COLOR_WHITE),
        ("CYAN_WHITE", curses.COLOR_CYAN, curses.COLOR_WHITE),
        ("GREEN_WHITE", curses.COLOR_GREEN, curses.COLOR_WHITE),
        ("MAGENTA_WHITE", curses.COLOR_MAGENTA, curses.COLOR_WHITE),
        ("RED_WHITE", curses.COLOR_RED, curses.COLOR_WHITE),
        ("YELLOW_WHITE", curses.COLOR_YELLOW, curses.COLOR_WHITE),
    )

    default_colors = {
        "DEFAULT": "WHITE_BLACK",
        "FORMDEFAULT": "WHITE_BLACK",
        "NO_EDIT": "BLUE_BLACK",
        "STANDOUT": "CYAN_BLACK",
        "CURSOR": "WHITE_BLACK",
        "CURSOR_INVERSE": "BLACK_WHITE",
        "LABEL": "GREEN_BLACK",
        "LABELBOLD": "WHITE_BLACK",
        "CONTROL": "YELLOW_BLACK",
        "WARNING": "RED_BLACK",
        "CRITICAL": "BLACK_RED",
        "GOOD": "GREEN_BLACK",
        "GOODHL": "GREEN_BLACK",
        "VERYGOOD": "BLACK_GREEN",
        "CAUTION": "YELLOW_BLACK",
        "CAUTIONHL": "BLACK_YELLOW",
        "DIAMONDS": "BLUE_BLACK",
        "HEARTS": "RED_BLACK",
        "SPADES": "WHITE_BLACK",
        "CLUBS": "GREEN_BLACK",
        "DIAMONDS_BG": "BLACK_BLUE",
        "HEARTS_BG": "BLACK_RED",
        "SPADES_BG": "BLACK_WHITE",
        "CLUBS_BG": "BLACK_GREEN",
    }


BLUE = "DIAMONDS"
GREEN = "CLUBS"
RED = "HEARTS"
BLACK = "SPADES"
RED_WITH_BACKGROUND = "HEARTS_BG"
BLACK_WITH_BACKGROUND = "SPADES_BG"
GREEN_WITH_BACKGROUND = "CLUBS_BG"
YELLOW_WITH_BACKGROUND = "CAUTIONHL"
BLUE_WITH_BACKGROUND = "DIAMONDS_BG"
ACTION_ON_COLOR = "CAUTIONHL"
# 'DEFAULT'     : 'WHITE_BLACK',
# 'FORMDEFAULT' : 'WHITE_BLACK',
# 'NO_EDIT'     : 'BLUE_BLACK',
# 'STANDOUT'    : 'CYAN_BLACK',
# 'CURSOR'      : 'WHITE_BLACK',
# 'CURSOR_INVERSE': 'BLACK_WHITE',
# 'LABEL'       : 'GREEN_BLACK',
# 'LABELBOLD'   : 'WHITE_BLACK',
# 'CONTROL'     : 'YELLOW_BLACK',
# 'IMPORTANT'   : 'GREEN_BLACK',
# 'SAFE'        : 'GREEN_BLACK',
# 'WARNING'     : 'YELLOW_BLACK',
# 'DANGER'      : 'RED_BLACK',
# 'CRITICAL'    : 'BLACK_RED',
# 'GOOD'        : 'GREEN_BLACK',
# 'GOODHL'      : 'GREEN_BLACK',
# 'VERYGOOD'    : 'BLACK_GREEN',
# 'CAUTION'     : 'YELLOW_BLACK',
# 'CAUTIONHL'   : 'BLACK_YELLOW',

HEART = "\u2665"
DIAMOND = "\u2666"
SPADE = "\u2660"
CLUB = "\u2663"


def color_of(suit: Suit):
    if suit == Suit.SPADES:
        return BLACK
    elif suit == Suit.HEARTS:
        return RED
    elif suit == Suit.DIAMONDS:
        return BLUE
    elif suit == Suit.CLUBS:
        return GREEN
    elif suit == Suit.UNKNOWN:
        return BLACK


def background_color_of(suit: Suit):
    if suit == Suit.SPADES:
        return BLACK_WITH_BACKGROUND
    elif suit == Suit.HEARTS:
        return RED_WITH_BACKGROUND
    elif suit == Suit.DIAMONDS:
        return BLUE_WITH_BACKGROUND
    elif suit == Suit.CLUBS:
        return GREEN_WITH_BACKGROUND
    elif suit == Suit.UNKNOWN:
        return "DEFAULT"


class App(npyscreen.NPSAppManaged):
    def onStart(self):
        npyscreen.setTheme(PokerTheme)
        self.addForm("MAIN", MainForm, name="PokerStars V2")


class HoleCards(npyscreen.BoxBasic):
    pass


class SeatBox(npyscreen.BoxTitle):
    _contained_widget = npyscreen.MultiLineEdit

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class NewMultiLineEdit(npyscreen.MultiLineEdit):
    def on_left(self, _):
        if self.cursor_position > 0:
            self.h_cursor_left(None)
        else:
            self.h_exit_left(None)

    def on_right(self, _):
        if self.cursor_position < len(self.value):
            self.h_cursor_right(None)
        else:
            self.h_exit_right(None)

    def set_up_handlers(self):
        super(NewMultiLineEdit, self).set_up_handlers()
        self.handlers.update(
            {
                curses.KEY_LEFT: self.on_left,
                curses.KEY_RIGHT: self.on_right,
            }
        )


class BetBox(npyscreen.BoxTitle):
    _contained_widget = NewMultiLineEdit

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.min_raise = None
        self.stack = None
        # TODO gray out if not valid raise/bet
        # self.parent.HoleCards.value = "init"
        # self.parent.HoleCards.display()

        # self._contained_widget.handlers.update(
        #     {
        #         curses.KEY_LEFT: lambda x: (),
        #         curses.KEY_RIGHT: self._contained_widget.h_cursor_right,
        #     }
        # )

    def set_up_handlers(self):
        # self.parent.HoleCards.value = "setup"
        # self.parent.HoleCards.display()
        super(BetBox, self).set_up_handlers()

        self.handlers.update(
            {
                curses.KEY_LEFT: lambda x: (),
                curses.KEY_RIGHT: self._contained_widget.h_cursor_right,
            }
        )

    def on_activate(self):
        submit = "\n" in self.parent.BetBox.value
        self.parent.BetBox.value = "".join(
            [i for i in self.parent.BetBox.value if i.isdigit() and i != "\n"]
        )
        if submit:
            the_bet = self.parent.BetBox.value
            if (
                the_bet.isdigit()
                and int(the_bet) > 0
                and (
                    self.min_raise is None
                    or int(the_bet) >= self.min_raise
                    or (self.stack is not None and int(the_bet) == self.stack)
                )
            ):
                the_bet = int(the_bet)
                sio.emit(
                    "player_bet",
                    {
                        "hand_num": client_player_action["hand_num"],
                        "action_num": client_player_action["action_num"],
                        "bet_amount": the_bet,
                    },
                )
                self.parent.BetBox.value = ""

    def whenPressed(self):
        self.on_activate()

    def handle_mouse_event(self, mouse_event):
        mouse_id, x, y, z, bstate = mouse_event
        if bstate & curses.BUTTON1_CLICKED:
            self.on_activate()

    def when_value_edited(self):
        self.parent.BoardArea.footer = "value edited"
        self.on_activate()


class BoardArea(npyscreen.BoxTitle):
    # _contained_widget = npyscreen.MultiLineEdit
    # def __init__(self, temp, **keywords):
    #     self.parent.curses_pad.addnstr(self.rely, self.relx, "hello there", self.width)
    #     pass
    pass


# class CustomFixedText(npyscreen.FixedText):
#     def display_value(self, value):
#         self.set
#         return super().display_value(value)


class CheckButton(npyscreen.ButtonPress):
    def on_activate(self):
        sio.emit(
            "player_checked",
            {
                "hand_num": client_player_action["hand_num"],
                "action_num": client_player_action["action_num"],
            },
        )

    def whenPressed(self):
        self.on_activate()

    def handle_mouse_event(self, mouse_event):
        mouse_id, x, y, z, bstate = mouse_event
        if bstate & curses.BUTTON1_CLICKED:
            self.on_activate()


class CallButton(npyscreen.ButtonPress):
    def on_activate(self):
        sio.emit(
            "player_called",
            {
                "hand_num": client_player_action["hand_num"],
                "action_num": client_player_action["action_num"],
            },
        )

    def whenPressed(self):
        self.on_activate()

    def handle_mouse_event(self, mouse_event):
        mouse_id, x, y, z, bstate = mouse_event
        if bstate & curses.BUTTON1_CLICKED:
            self.on_activate()


class FoldButton(npyscreen.ButtonPress):
    def on_activate(self):
        sio.emit(
            "player_folded",
            {
                "hand_num": client_player_action["hand_num"],
                "action_num": client_player_action["action_num"],
            },
        )

    def whenPressed(self):
        self.on_activate()

    def handle_mouse_event(self, mouse_event):
        mouse_id, x, y, z, bstate = mouse_event
        if bstate & curses.BUTTON1_CLICKED:
            self.on_activate()


class CheckButtonBox(npyscreen.BoxTitle):
    _contained_widget = CheckButton


class CallButtonBox(npyscreen.BoxTitle):
    _contained_widget = CallButton


class FoldButtonBox(npyscreen.BoxTitle):
    _contained_widget = FoldButton


def center_text(s, width, height):
    lines = s.split("\n")
    overall_first_char = float("inf")
    for l in lines:
        first_char = 0
        for ind in range(len(l)):
            if not l[ind].isspace():
                first_char = ind
                break
        overall_first_char = min(overall_first_char, first_char)
    overall_last_char = 0
    for l in lines:
        last_char = 0
        for ind in range(len(l)):
            if not l[ind].isspace():
                last_char = ind
        overall_last_char = max(overall_last_char, last_char)
    s_width = overall_last_char - overall_first_char + 1
    starting_x_goal = width // 2 - math.ceil(s_width / 2)
    x_padding = starting_x_goal - overall_first_char

    # assume first line is not blank
    last_line = 0
    for ind in range(len(lines)):
        if not lines[ind].isspace():
            last_line = ind
    starting_y_goal = height // 2 - ((last_line + 1) // 2)
    y_padding = starting_y_goal
    return ("\n" * y_padding) + "\n".join([(" " * x_padding) + l for l in lines])


class LargeCardWidget(npyscreen.BoxTitle):
    # _contained_widget = npyscreen.MultiLineEdit

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # print(
        #     f"LargeCardWidget relx {self.relx} rely {self.rely} width {self.width} height {self.height}",
        #     file=sys.stderr,
        # )
        self.text = self.parent.add(
            npyscreen.MultiLineEdit,
            value="",
            editable=False,
            width=self.width,
            height=self.height,
            relx=2,
            rely=2,
        )
        self.set_relyx = self._set_relyx

    def _set_relyx(self, rely, relx):
        super().set_relyx(rely, relx)
        self.text.set_relyx(rely + 1, relx + 1)

    def set_color(self, color):
        self.color = color
        self.text.color = color

    def set_suit(self, suit):
        self.name = suit.value
        self.footer = suit.value


class LargeCard:
    def get_card_text(self, value, card_height, card_width):
        if card_height >= 6:
            card1 = art.text2art(value)
        else:
            card1 = value
        return center_text(card1, width=card_width - 2, height=card_height - 2)

    def __init__(
        self,
        card_width,
        card_height,
        form_ref,
        selectable=False,
        suit=Suit.SPADES,
        value="",
    ):
        self.suit = suit
        self.value = value
        self.selectable = selectable
        self.form_ref = form_ref
        self.card_width = card_width
        self.card_height = card_height

        color = color_of(self.suit)
        # print(f"color {color}", file=sys.stderr)
        self.card_widget = form_ref.add(
            LargeCardWidget,
            name=self.suit.value,
            footer=self.suit.value,
            height=self.card_height,
            width=self.card_width,
            editable=self.selectable,
            rely=2,
            relx=2,
            color=color,
            widgets_inherit_color=True,
            # contained_widget_arguments={
            #     "value": card_text,  # \U0001F0CB
            #     "color": color,
            #     "widgets_inherit_color": True,
            # },
        )
        self.card_widget.hidden = True
        self.card_widget.text.hidden = True
        card_text = self.get_card_text(value, card_height, card_width)
        self.card_widget.text.value = card_text

    def set_suit(self, suit):
        self.suit = suit
        color = color_of(self.suit)
        self.card_widget.set_suit(suit)
        self.card_widget.set_color(color)

    def set_value(self, value):
        self.value = value
        card_text = self.get_card_text(value, self.card_height, self.card_width)
        self.card_widget.text.value = card_text

    def set_selectable(self, selectable):
        self.selectable = selectable
        self.card_widget.editable = selectable

    def set_card(self, suit=None, value=None, selectable=None):
        if suit is not None:
            self.set_suit(suit)
        if value is not None:
            self.set_value(value)
        if selectable is not None:
            self.set_selectable(selectable)

    def move_card_rel(self, relx, rely):
        self.card_widget.set_relyx(
            self.card_widget.rely + rely, self.card_widget.relx + relx
        )

    def move_card_abs(self, relx, rely):
        self.card_widget.set_relyx(rely, relx)

    def hide(self):
        # self.card_widget.width = 1
        # self.card_widget.height = 1
        self.card_widget.hidden = True
        self.card_widget.text.hidden = True
        pass

    def show(self):
        # self.card_widget.width = self.card_width
        # self.card_widget.height = self.card_height
        self.card_widget.hidden = False
        self.card_widget.text.hidden = False
        pass


"""
[LargeCardPool] Allows you to generate new LargeCard's and "remove" them without leaking memory.
"""


class LargeCardPool:
    def __init__(self, form_ref, num_initial_cards, card_width, card_height):
        self.cards = []
        self.form_ref = form_ref
        self.card_width = card_width
        self.card_height = card_height
        for _ in range(num_initial_cards):
            c = LargeCard(
                card_width=card_width, card_height=card_height, form_ref=form_ref
            )
            self.cards.append(c)

    def return_card(self, card):
        card.hide()
        card.move_card_abs(1, 1)
        self.cards.append(card)
        # self.form_ref.display()

    def return_cards(self, cards):
        for card in cards:
            self.return_card(card)

    def get_card(self, suit, value, selectable=False):
        if len(self.cards) == 0:
            # make new card
            c = LargeCard(
                suit=suit,
                value=value,
                card_width=self.card_width,
                card_height=self.card_height,
                form_ref=self.form_ref,
                selectable=selectable,
            )
            return c
        else:
            c = self.cards.pop(0)
            c.set_card(suit, value)
            return c


"""
[CardsContainer] Handles display of cards using a resuable pool of [LargeCardWidget]'s.
    Allows you to pass in new card info and it will rerender the cards.
    TODO allow for all cards to be selectable, add method to get selected cards
        (for when server asks user to select cards, e.g. discard or swap)
"""


class CardsContainer(npyscreen.widget.Widget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.hidden = True

        # print(kwargs, file=sys.stderr)
        # TODO pass this in from game creation screen or None if server doesn't know
        self.MAX_CARDS = kwargs["max_cards"]  # 5
        self.LARGE_CARD_WIDTH = kwargs["large_card_width"]
        self.LARGE_CARD_HEIGHT = kwargs["large_card_height"]
        self.large_card_pool = LargeCardPool(
            self.parent,
            num_initial_cards=self.MAX_CARDS if self.MAX_CARDS is not None else 8,
            card_width=self.LARGE_CARD_WIDTH,
            card_height=self.LARGE_CARD_HEIGHT,
        )
        self.cards_info = []
        self.large_cards = []
        # make separate FixedText's for different colors
        self.plaintext_cards = []
        for i in range(self.width):
            self.plaintext_cards.append(
                self.parent.add(
                    npyscreen.FixedText,
                    value="",
                    editable=False,
                    relx=self.relx + i,
                    rely=self.rely + ((self.height - 1) // 2),
                    width=2,
                    height=1,
                    hidden=True,
                )
            )
        # self.plaintext_cards = self.parent.add(
        #     npyscreen.FixedText,
        #     value="TESTING",
        #     # color="LABEL",
        #     editable=False,
        #     relx=self.relx,
        #     rely=self.rely + ((self.height - 1) // 2),
        #     width=self.width,
        #     height=self.height,
        #     hidden=True,
        # )

    def clear_current_displayed_cards(self):
        self.large_card_pool.return_cards(self.large_cards)
        self.large_cards = []
        for i in range(len(self.plaintext_cards)):
            self.plaintext_cards[i].hidden = True

    def draw_large_cards(self):
        self.clear_current_displayed_cards()
        max_cards = (
            self.MAX_CARDS if self.MAX_CARDS is not None else len(self.cards_info)
        )
        middle = self.width // 2
        total_cards_width = max_cards * (self.LARGE_CARD_WIDTH + 1) - 1
        starting_x = self.relx + max(0, (middle - math.ceil(total_cards_width / 2)))
        for i in range(len(self.cards_info)):
            # print(f"card {self.cards_info}", file=sys.stderr)
            rank = self.cards_info[i]["rank"]
            suit = Suit.decode(self.cards_info[i]["suit"])
            # ignore face_up for now until we allow users to show cards
            c = self.large_card_pool.get_card(suit, rank)
            card_x = starting_x + i * (self.LARGE_CARD_WIDTH + 1)
            card_y = self.rely + (self.height - self.LARGE_CARD_HEIGHT) // 2
            c.move_card_abs(card_x, card_y)
            c.show()
            self.large_cards.append(c)

    def draw_plaintext_cards(self):
        self.clear_current_displayed_cards()
        max_cards = (
            self.MAX_CARDS if self.MAX_CARDS is not None else len(self.cards_info)
        )
        text_with_color = []
        # text = ""
        for i in range(len(self.cards_info)):
            rank = self.cards_info[i]["rank"]
            suit = Suit.decode(self.cards_info[i]["suit"])
            # text += f"{rank}{suit.value}"
            text_with_color.append(
                {"text": f"{rank}{suit.value}", "color": background_color_of(suit)}
            )
        for _ in range(max_cards - len(self.cards_info)):
            # placeholder
            # text += "  "
            text_with_color.append({"text": "  ", "color": "DEFAULT"})
        # self.plaintext_cards.value = center_text(text, self.width, self.height)
        # self.plaintext_cards.hidden = False
        centered_text = center_text(
            "".join([i["text"] for i in text_with_color]), self.width, 1
        )
        # print(f'centered_text "{centered_text}"', file=sys.stderr)
        # get whitespace padding manually
        left_padding = len(centered_text) - len(centered_text.lstrip())
        if centered_text.lstrip() != "":
            ind = 0
            while ind < left_padding:
                self.plaintext_cards[ind].hidden = True
                ind += 1
            for card in text_with_color:
                # print(
                #     f"ind {ind} plaintextlen {len(self.plaintext_cards)}",
                #     file=sys.stderr,
                # )
                # print([str(ord(i)) for i in card["text"]], file=sys.stderr)
                for char in card["text"]:
                    self.plaintext_cards[ind].value = char
                    self.plaintext_cards[ind].color = card["color"]
                    self.plaintext_cards[ind].hidden = False
                    ind += 1
            while ind < len(self.plaintext_cards):
                self.plaintext_cards[ind].hidden = True
                ind += 1

    def set_cards(self, cards_info):
        self.cards_info = cards_info

        max_cards = (
            self.MAX_CARDS if self.MAX_CARDS is not None else len(self.cards_info)
        )
        use_large_cards = (
            max_cards * (self.LARGE_CARD_WIDTH + 1) - 1 <= self.width
            and self.LARGE_CARD_HEIGHT <= self.height
        )
        if use_large_cards:
            # use MAX_CARDS to determine if we have space for LargeCards
            # center based on MAX_CARDS
            self.draw_large_cards()
        else:
            # if we CURRENTLY have enough space for LargeCards, that's enough.
            # center the current cards
            self.draw_plaintext_cards()


class MainForm(npyscreen.FormWithMenus):
    OK_BUTTON_TEXT = "2024\xA9"

    def create(self):
        self.ind = 0
        self.keypress_timeout = 1
        # self.num_seats = 4  # TODO2 maybe have this "hardcoded" game creation screen
        self.max_community_cards = 5  # have this hardcoded also from server
        self.max_hole_cards = 2  # have this hardcoded also from server

        new_handlers = {
            # Set ctrl+Q to exit
            "^Q": self.exit_func,
            # Set alt+enter to clear boxes
            # curses.ascii.alt(curses.ascii.NL): self.inputbox_clear,
        }
        self.add_handlers(new_handlers)

        y, x = self.useable_space()
        # print(f"x {x} y {y}", file=sys.stderr)
        board_height = y * 5 // 8  # just make it minus the buttons and player info
        self.BoardArea = self.add(
            BoardArea, name="Board", editable=False, max_height=board_height
        )

        BUTTON_HEIGHT = 3
        self.CheckButton = self.add(
            CheckButtonBox,
            height=BUTTON_HEIGHT,
            rely=self.BoardArea.rely + self.BoardArea.height,
            width=13,
            contained_widget_arguments={
                "name": "Check",
            },
        )
        self.CallButton = self.add(
            CallButtonBox,
            height=BUTTON_HEIGHT,
            width=16,
            relx=self.CheckButton.relx + self.CheckButton.width + 1,
            rely=self.CheckButton.rely,
            contained_widget_arguments={
                "name": "Call",
            },
        )
        self.FoldButton = self.add(
            FoldButtonBox,
            height=BUTTON_HEIGHT,
            width=13,
            relx=self.CallButton.relx + self.CallButton.width + 1,
            rely=self.CheckButton.rely,
            contained_widget_arguments={
                "name": "Fold",
            },
        )
        self.BetBox = self.add(
            BetBox,
            name="Bet/Raise",
            height=BUTTON_HEIGHT,
            width=20,
            relx=self.FoldButton.relx + self.FoldButton.width + 1,
            rely=self.CheckButton.rely,
        )

        self.HoleCards = self.add(
            HoleCards,
            name="Hole Cards",
            editable=False,
            # max_height=player_info_height,
        )
        LARGE_CARD_WIDTH = 11
        LARGE_CARD_HEIGHT = 8
        # print(
        #     f" hole cards container relx {self.HoleCards.relx+1} rely {self.HoleCards.rely+1} width {self.HoleCards.width -2} height {self.HoleCards.height -2 }",
        #     file=sys.stderr,
        # )
        self.hole_cards_container = self.add(
            CardsContainer,
            large_card_width=LARGE_CARD_WIDTH,
            large_card_height=LARGE_CARD_HEIGHT,
            # name="Hole Cards",
            editable=False,
            # max_height=player_info_height,
            relx=self.HoleCards.relx + 1,
            rely=self.HoleCards.rely + 1,
            width=self.HoleCards.width - 2,
            height=self.HoleCards.height - 2,
            max_cards=self.max_hole_cards,
        )
        self.hole_cards_container.set_cards([])

        player_width = 20
        player_height = 5
        self.SeatBoxes = []
        centerx = self.BoardArea.relx + (self.BoardArea.width / 2) - (player_width / 2)
        centery = (
            self.BoardArea.rely + (self.BoardArea.height / 2) - (player_height / 2)
        )
        seat_circle_radius_x = (
            self.BoardArea.width - 2 - (2 * math.ceil(player_width / 2))
        ) // 2
        seat_circle_radius_y = (
            self.BoardArea.height * 2 - 4 - math.ceil(player_height / 2 * 2 * 2)
        ) // 2
        e = Ellipse(seat_circle_radius_x, seat_circle_radius_y)
        seat_positions = e.get_n_arc_length_equidistant_pts(num_seats)
        seat = 1
        for delta_x, delta_y in seat_positions:
            player_x = math.ceil(centerx + (delta_x))
            player_y = int(centery + (-delta_y / 2))
            self.SeatBoxes.append(
                self.add(
                    SeatBox,
                    editable=False,
                    name=f"",
                    height=player_height,
                    width=player_width,
                    relx=player_x,
                    rely=player_y,
                )
            )
            # add villain hole card displays
            villain_hole_card_offset = 2
            self.SeatBoxes[-1].hole_cards = self.add(
                CardsContainer,
                large_card_width=LARGE_CARD_WIDTH,
                large_card_height=LARGE_CARD_HEIGHT,
                editable=False,
                relx=self.SeatBoxes[-1].relx + 1,
                rely=self.SeatBoxes[-1].rely + 1 + villain_hole_card_offset,
                width=self.SeatBoxes[-1].width - 2,
                height=1,
                max_cards=self.max_hole_cards,
            )
            seat += 1

        # find the farthest our community cards can reach without hitting a seat
        middle_y = self.BoardArea.rely + (self.BoardArea.height // 2)
        top_large = middle_y - (LARGE_CARD_HEIGHT // 2)
        bottom_large = middle_y + (LARGE_CARD_HEIGHT - LARGE_CARD_HEIGHT // 2) - 1
        left_large = (
            self.BoardArea.relx
            + (self.BoardArea.width // 2)
            - (3 * LARGE_CARD_WIDTH // 2)
        )  # 3 is arbitrary to speed it up
        right_large = (
            self.BoardArea.relx
            + (self.BoardArea.width // 2)
            + (3 * LARGE_CARD_WIDTH // 2)
        )
        while left_large >= 1 and right_large < x - 1:
            test_left = left_large - 1
            test_right = right_large + 1
            would_hit_seat = False
            for seat in self.SeatBoxes:
                if (
                    test_left <= seat.relx + seat.width - 1
                    and test_right >= seat.relx
                    and top_large <= seat.rely + seat.height - 1
                    and bottom_large >= seat.rely
                ):
                    would_hit_seat = True
                    break
            if would_hit_seat:
                break
            left_large = test_left
            right_large = test_right
        possible_large_card_width = right_large - left_large + 1
        if possible_large_card_width >= self.max_community_cards * LARGE_CARD_WIDTH:
            # print("large enough", file=sys.stderr)
            community_card_width = possible_large_card_width
            community_card_height = LARGE_CARD_HEIGHT
            community_card_relx = left_large
            community_card_rely = top_large
        else:
            # print("not large enough", file=sys.stderr)
            middle_y = self.BoardArea.rely + (self.BoardArea.height // 2)
            top_large = middle_y
            bottom_large = middle_y
            left_large = self.BoardArea.relx + (self.BoardArea.width // 2)
            right_large = self.BoardArea.relx + (self.BoardArea.width // 2)
            while left_large >= 0 and right_large < x:
                test_left = left_large - 1
                test_right = right_large + 1
                would_hit_seat = False
                for seat in self.SeatBoxes:
                    if (
                        test_left <= seat.relx + seat.width - 1
                        and test_right >= seat.relx
                        and top_large <= seat.rely + seat.height - 1
                        and bottom_large >= seat.rely
                    ):
                        would_hit_seat = True
                        break
                if would_hit_seat:
                    break
                left_large = test_left
                right_large = test_right
            possible_large_card_width = right_large - left_large + 1
            community_card_width = possible_large_card_width
            community_card_height = 1
            community_card_relx = left_large
            community_card_rely = top_large
        # print(
        #     f"relx {community_card_relx} rely {community_card_rely} width {community_card_width} height {community_card_height}\n\n",
        #     file=sys.stderr,
        # )
        self.community_cards_container = self.add(
            CardsContainer,
            editable=False,
            large_card_width=LARGE_CARD_WIDTH,
            large_card_height=LARGE_CARD_HEIGHT,
            max_cards=self.max_community_cards,
            relx=community_card_relx,
            rely=community_card_rely,
            width=community_card_width,
            height=community_card_height,
        )

    # async def while_waiting(self):
    #     ind = 0
    #     # send 'on_my_event' to server
    #     self.BoardArea.footer = "while waiting async"
    #     # print('while waiting async', file=sys.stderr)
    #     print('sending event ' + str(ind))
    #     await sio.emit('my_event', {'data': ind})
    #     print('sent')
    #     ind += 1
    #     await asyncio.sleep(1)

    def while_waiting(self):
        pass
        # self.BoardArea.footer = "while waiting not async " + str(self.ind)
        # self.display()
        # sio.emit('my_event', {'data': str(self.ind)})
        # self.ind += 1
        # print('while waiting not async ', file=sys.stderr)

    def exit_func(self, _input):
        exit(0)


class Ellipse:
    def __init__(self, radius_x, radius_y):
        self.radius_x = radius_x
        self.radius_y = radius_y
        self.r_of_theta = lambda theta: (
            (self.radius_x * self.radius_y)
            / (
                math.sqrt(
                    (self.radius_x * math.sin(theta)) ** 2
                    + (self.radius_y * math.cos(theta)) ** 2
                )
            )
        )

    def get_x_y(self, theta):
        return (
            (self.r_of_theta(theta) * math.cos(theta)),
            (self.r_of_theta(theta) * math.sin(theta)),
        )

    def euclidean_distance(self, x1, y1, x2, y2):
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    def get_n_arc_length_equidistant_pts(self, n):
        circumference = 0
        # integrate over theta from 0 to Pi / 2
        last_x, last_y = self.get_x_y(0)
        t = 0
        while t < math.pi / 2:
            x, y = self.get_x_y(t)
            circumference += self.euclidean_distance(last_x, last_y, x, y)
            last_x, last_y = x, y
            t += 0.01
        circumference *= 4

        # go around ellipse from 3pi/2 to 3pi/2 + 2pi and find x,y coordinates
        #  that divide arc length evenly
        start = 3 * math.pi / 2  # bottom
        points = [self.get_x_y(start)]
        nextDistance = circumference / n
        curDistance = 0
        last_x, last_y = self.get_x_y(start)
        t = start
        while len(points) < n and t < start + 2 * math.pi:
            x, y = self.get_x_y(t)
            curDistance += self.euclidean_distance(last_x, last_y, x, y)
            if curDistance >= nextDistance:
                points.append((x, y))
                nextDistance += circumference / n
            last_x, last_y = x, y
            t += 0.01
        return points


"""
Hole Cards
Your actions: Fold, Check, Call, Bet, Raise (allow user to type amount to bet) (maybe check on frontend for correctness but prob not).
Community Cards
Pot
Opponents (stack sizes, actions (amount bet)) (Icon for who action is on) (icon for dealer button (or bold/color))
TODO:
- see if you can click on boxes by adding an event handler for check/call
- Raise is when someones bet, set to min raise. If no bet set to Bet (min is BB)
- way to edit your own stack size
- server track overall profit/loss
- add raise slider
- record hand histories on server
- sound cues
- run it 2x
- button to popup a graph of everyone's profit/loss
- buttons for check/call etc. instead of boxes?
- allow showing cards with popup to confirm
- add dealer button icon (D) next to name
- If hold card (or board) area is small enough, show cards as text like A♠️2♠️
- make player names only normal chars (below certain ascii value)
- menu settings:
    - setting to just show the A2 with color instead of suit icon next to it
    - BB view
    - download P/L graph as image
- add Pot/Sidepots under the community cards
- create ThemeManager to get access to blue background and black background?
- give percent of pot odds/pot odds as setting
- track vpip, pfr, 3-bet % as optional setting
- on connect have server tell client if it's on the right version, 
    if not, client should error out
- animation on cards when they are dealt
- allow players to choose their seat
"""

sio = socketio.Client()
MyApp = App()


@sio.event
def connect():
    # print(sio.transport, sio.sid)
    # print("I'm connected!")
    pass


@sio.event
def connect_error(data):
    # do nothing, the user may reconnect, let disconnect handle it.
    pass


@sio.event
def disconnect():
    # print("I'm disconnected!")
    form = MyApp.getForm("MAIN")
    form.name = "PokerStars V2 - Disconnected..."
    form.display()
    pass


@sio.on("my_response")
def on_my_response(data):
    # print('I received a message! ' + str(data))
    MyApp.getForm("MAIN").BoardArea.footer = "I received a message! " + str(data)
    MyApp.getForm("MAIN").display()


num_seats = 4  # TODO2 maybe have this "hardcoded" game creation screen
client_player_action = None
my_seat = None


def seatbox_ind_from_seat(seat):
    if my_seat is not None:
        return ((seat - my_seat) + num_seats) % num_seats
    else:
        return seat


@sio.on("updated_table_info")
def on_updated_table_info(data):
    global client_player_action
    global my_seat
    # print(data, file=sys.stderr)
    form = MyApp.getForm("MAIN")

    for seat in range(len(form.SeatBoxes)):
        # reset seat
        form.SeatBoxes[seat].name = ""
        form.SeatBoxes[seat]._my_widgets[0].value = ""
        form.SeatBoxes[seat].color = "DEFAULT"
        form.SeatBoxes[seat].footer = ""
        form.SeatBoxes[seat].hole_cards.set_cards([])

    form.name = f'{data["name"]} ({data["sm_blind"]}/{data["bg_blind"]}) - Hand #{data["hand_num"]}'
    form.num_seats = str(data["num_seats"])

    if len(data["side_pots"]) > 0:
        form.BoardArea.footer = f'Pot: {data["main_pot_including_bets"]} ⛁; Sidepots: {"⛁, ".join(str(d["pot_size"]) for d in data["side_pots"])}'
    else:
        form.BoardArea.footer = f'Pot: {data["main_pot_including_bets"]} ⛁'  # \u26C3

    if (
        data["community_cards"] != form.community_cards_container.cards_info
        and data["community_cards"] != []
    ):
        play_new_card_sound()
    form.community_cards_container.set_cards(data["community_cards"])

    for player in data["players"]:
        p_state = PlayerState.decode(player["state"])

        seat = player["seat"]
        if player["is_player"]:
            my_seat = player["seat"]
            if (
                player["hole_cards"] != form.hole_cards_container.cards_info
                and player["hole_cards"] != []
            ):
                play_new_card_sound()
            form.hole_cards_container.set_cards(player["hole_cards"])
            if player["client_player_action"] is not None:
                if client_player_action is None:
                    # alert player new action is required
                    curses.flash()
                    play_new_action_sound()
                client_player_action = player["client_player_action"]
                if client_player_action["can_raise"]:
                    form.BetBox.hidden = False
                    form.BetBox.editable = True
                    form.BetBox.min_raise = client_player_action["min_raise"]
                    form.BetBox.stack = player["stack"] + player["current_bet"]
                    if form.BetBox.value == "":
                        form.BetBox.value = str(client_player_action["min_raise"])
                    if client_player_action["bet_instead_of_raise"]:
                        form.BetBox.name = "Bet"
                    else:
                        form.BetBox.name = "Raise"
                else:
                    form.BetBox.hidden = True
                    form.BetBox.editable = False

                form.CheckButton.hidden = not client_player_action["can_check"]
                form.CheckButton.editable = client_player_action["can_check"]
                form.CallButton.hidden = not client_player_action["can_call"]
                form.CallButton.editable = client_player_action["can_call"]
                form.FoldButton.hidden = False
                form.FoldButton.editable = True
                if form._widgets__[form.editw].hidden and hasattr(
                    form._widgets__[form.editw], "entry_widget"
                ):
                    form._widgets__[form.editw].entry_widget.h_exit_right(None)
                if client_player_action["can_call"]:
                    form.CallButton.name = f"{client_player_action['call_amount']}"
            else:
                client_player_action = None
                # don't have any action
                form.BetBox.min_raise = None
                form.BetBox.stack = None
                form.BetBox.value = ""
                form.BetBox.hidden = True
                form.BetBox.editable = False
                form.CheckButton.hidden = True
                form.CheckButton.editable = False
                form.CallButton.hidden = True
                form.CallButton.editable = False
                form.FoldButton.hidden = True
                form.FoldButton.editable = False
                if form._widgets__[form.editw].hidden:
                    form._widgets__[form.editw].entry_widget.h_exit_right(None)
        else:
            if p_state != PlayerState.NOT_SEATED:
                form.SeatBoxes[seatbox_ind_from_seat(seat)].hole_cards.set_cards(
                    player["hole_cards"]
                )
        if p_state != PlayerState.NOT_SEATED:
            seat_name = f"{player['name']}"
            if data["dealer"] == seat:
                seat_name += f" {chr(0x24B9)}"
            form.SeatBoxes[seatbox_ind_from_seat(seat)].name = seat_name
            inside_box_text = [
                f"Stack: {player['stack']} ⛁",
                # f"Bet: {player['current_bet']} ⛁",
            ]
            if player["current_bet"] > 0:
                inside_box_text.append(f"Bet: {player['current_bet']} ⛁")
            form.SeatBoxes[seatbox_ind_from_seat(seat)]._my_widgets[0].value = (
                "\n".join(inside_box_text)
            )
            last_action_text = None
            if p_state == PlayerState.FOLDED:
                last_action_text = "Folded"
            elif p_state == PlayerState.ALL_IN:
                last_action_text = "All In"
            elif p_state == PlayerState.CHECKED:
                last_action_text = "Checked"
            elif p_state == PlayerState.CALLED:
                last_action_text = "Called"
            elif p_state == PlayerState.BET:
                last_action_text = f"Bet {player['current_bet']}"
            elif p_state == PlayerState.RAISED:
                last_action_text = f"Raised to {player['current_bet']}"
            if last_action_text != None:
                form.SeatBoxes[seatbox_ind_from_seat(seat)].footer = last_action_text

    if data["action_on"] is not None:
        form.SeatBoxes[seatbox_ind_from_seat(data["action_on"])].footer = ""
        form.SeatBoxes[seatbox_ind_from_seat(data["action_on"])].color = ACTION_ON_COLOR

    form.display()


def connect_to_server():
    auto_update = "--no-auto-update" not in sys.argv
    # remove --no-auto-update from sys.argv
    if "--no-auto-update" in sys.argv:
        sys.argv.remove("--no-auto-update")
    if auto_update:
        if get_latest_version():
            print("Updated to latest version, please try again.")
            exit(0)
    if len(sys.argv) == 2:
        address = sys.argv[1]
        port = 8000
    elif len(sys.argv) == 3:
        address = sys.argv[1]
        port = int(sys.argv[2])
    else:
        address = "localhost"
        port = 8000
    sio.connect(f"http://{address}:{port}")


if __name__ == "__main__":
    connect_to_server()
    MyApp.run()
