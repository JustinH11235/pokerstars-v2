#!/usr/bin/env python3
import curses
import math
import sys
import os
import asyncio
from enum import Enum

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared import (
    Suit,
    ClientPlayerAction,
    ClientNextActionType,
    ClientNextAction,
    ClientPlayerState,
)

import socketio
import npyscreen
import art

BLUE = "NO_EDIT"
GREEN = "LABEL"
RED = "DANGER"
BLACK = "CURSOR"
RED_WITH_BACKGROUND = "CRITICAL"
BLACK_WITH_BACKGROUND = "CURSOR_INVERSE"
GREEN_WITH_BACKGROUND = "VERYGOOD"
YELLOW_WITH_BACKGROUND = "CAUTIONHL"
BLUE_WITH_BACKGROUND = "BLUE_WHITE"
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


class App(npyscreen.NPSAppManaged):
    def onStart(self):
        self.addForm("MAIN", MainForm, name="PokerStars V2")


class HoleCards(npyscreen.BoxTitle):
    # _contained_widget = npyscreen.MultiLineEdit

    # def handle_mouse_event(self, mouse_event):
    #     mouse_id, x, y, z, bstate = mouse_event  # see note below.
    #     if bstate == curses.BUTTON1_PRESSED:
    #         self.when_value_edited()

    # def when_value_edited(self):
    #     self.parent.parentApp.queue_event(npyscreen.Event("event_value_edited"))
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
        if self.cursor_position < len(self.value) - 1:
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
        if "\n" in self.parent.BetBox.value:
            the_bet = self.parent.BetBox.value.split("\n")[0]
            if the_bet.isdigit() and int(the_bet) > 0:
                the_bet = int(the_bet)
            # temp
            # self.parent.HoleCards.footer = "bet clicked"
            # self.parent.HoleCards.display()
            #
            # send to server after doing checks TODO
            self.parent.BetBox.value = ""
        else:
            self.parent.BetBox.value = "".join(
                [i for i in self.parent.BetBox.value if i.isdigit() or i == "\n"]
            )
        pass

    def whenPressed(self):
        self.on_activate()

    def handle_mouse_event(self, mouse_event):
        mouse_id, x, y, z, bstate = mouse_event
        if bstate & curses.BUTTON1_CLICKED:
            self.on_activate()

    def when_value_edited(self):
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
        # temp
        # self.parent.HoleCards.footer = "check clicked"
        # self.parent.HoleCards.display()
        #
        pass

    def whenPressed(self):
        self.on_activate()

    def handle_mouse_event(self, mouse_event):
        mouse_id, x, y, z, bstate = mouse_event
        if bstate & curses.BUTTON1_CLICKED:
            self.on_activate()


class CallButton(npyscreen.ButtonPress):
    def on_activate(self):
        # temp
        # self.parent.HoleCards.footer = "call clicked"
        # self.parent.HoleCards.display()
        #
        pass

    def whenPressed(self):
        self.on_activate()

    def handle_mouse_event(self, mouse_event):
        mouse_id, x, y, z, bstate = mouse_event
        if bstate & curses.BUTTON1_CLICKED:
            self.on_activate()


class FoldButton(npyscreen.ButtonPress):
    def on_activate(self):
        # temp
        # self.parent.HoleCards.footer = "fold clicked"
        # self.parent.HoleCards.display()
        #
        pass

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


class CardTest(npyscreen.BoxTitle):
    # _contained_widget = npyscreen.MultiLineEdit

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
            CardTest,
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
[CardsContainer] Handles display of cards using a resuable pool of [CardTest]'s.
    Allows you to pass in new card info and it will rerender the cards.
    TODO allow for all cards to be selectable, add method to get selected cards
        (for when server asks user to select cards, e.g. discard or swap)
"""


class CardsContainer(npyscreen.BoxTitle):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hidden = True

        # print(kwargs, file=sys.stderr)
        # TODO pass this in from server or None if server doesn't know
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
        self.plaintext_cards = self.parent.add(
            npyscreen.FixedText,
            value="TESTING",
            relx=self.relx,
            rely=self.rely + (self.height // 2),
            width=self.width,
            height=self.height,
            hidden=True,
        )

    def clear_current_displayed_cards(self):
        self.large_card_pool.return_cards(self.large_cards)
        self.large_cards = []
        self.plaintext_cards.hidden = True

    def draw_large_cards(self):
        self.clear_current_displayed_cards()
        max_cards = (
            self.MAX_CARDS if self.MAX_CARDS is not None else len(self.cards_info)
        )
        middle = self.width // 2
        total_cards_width = max_cards * (self.LARGE_CARD_WIDTH + 1) - 1
        starting_x = self.relx + max(
            0, (middle - math.ceil(total_cards_width / 2))
        )  # TODO CENTER
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
        text = ""
        for i in range(len(self.cards_info)):
            rank = self.cards_info[i]["rank"]
            suit = Suit.decode(self.cards_info[i]["suit"])
            text += f"{rank}{suit.value}"
        for _ in range(max_cards - len(self.cards_info)):
            # placeholder
            # TODO make each card its own FixedText to have different colors
            text += "  "
        self.plaintext_cards.value = center_text(text, self.width, self.height)

        self.plaintext_cards.hidden = False

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
        #     f" hole cards container relx {self.HoleCards.relx} rely {self.HoleCards.rely} width {self.HoleCards.width -2} height {self.HoleCards.height -2 }",
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
        self.hole_cards_container.set_cards([])  # TODO pass in card data

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
            seat += 1

        # find the farthest our community cards can reach without hitting a seat
        middle_y = self.BoardArea.rely + (self.BoardArea.height // 2)
        top_large = middle_y - (LARGE_CARD_HEIGHT // 2)
        bottom_large = middle_y + (LARGE_CARD_HEIGHT - LARGE_CARD_HEIGHT // 2) - 1
        left_large = (
            self.BoardArea.relx
            + (self.BoardArea.width // 2)
            - (3 * LARGE_CARD_WIDTH // 2)
        )
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
            community_card_rely = right_large
        # print(
        #     f"relx {community_card_relx} rely {community_card_rely} width {community_card_width} height {community_card_height}",
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
        # self.community_cards_container.set_cards(
        #     [0, 0, 0, 0, 0]
        # )  # TODO pass in card data
        # TODO pot and sidepots (if not enough room,
        #  put cards in middle and sidepot on footer)

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

# create data structure storing TableInfo and PlayerInfo & CardInfo,
#  pass these structures around, setup client as sio async client


@sio.event
def connect():
    print(sio.transport, sio.sid)
    print("I'm connected!")


@sio.event
def connect_error(data):
    print("The connection failed! " + str(data))


@sio.event
def disconnect():
    print("I'm disconnected!")


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

    form.name = f'{data["name"]} ({data["sm_blind"]}/{data["bg_blind"]})'
    form.num_seats = str(data["num_seats"])
    # ignore hand_num

    if len(data["side_pots"]) > 0:
        form.BoardArea.footer = f'Pot: {data["main_pot_including_bets"]} ⛁; Sidepots: {"⛁, ".join(d["pot_size"] for d in data["side_pots"])}'
    else:
        form.BoardArea.footer = f'Pot: {data["main_pot_including_bets"]} ⛁'  # \u26C3

    form.community_cards_container.set_cards(data["community_cards"])

    for player in data["players"]:
        if player["is_player"]:
            my_seat = player["seat"]
            form.hole_cards_container.set_cards(player["hole_cards"])
            if player["client_player_action"] is not None:
                form.BetBox.hidden = False
                client_player_action = player["client_player_action"]
                form.BetBox.min_raise = client_player_action["min_raise"]
                if form.BetBox.value == "":
                    form.BetBox.value = str(client_player_action["min_raise"])
                if client_player_action["bet_instead_of_raise"]:
                    form.BetBox.name = "Bet"
                else:
                    form.BetBox.name = "Raise"

                form.CheckButton.hidden = not client_player_action["can_check"]
                form.CallButton.hidden = not client_player_action["can_call"]
                form.FoldButton.hidden = False
                if form._widgets__[form.editw].hidden:
                    form._widgets__[form.editw].entry_widget.h_exit_right(None)
                # TODO call amount
                if client_player_action["can_call"]:
                    form.CallButton.name = f"{client_player_action['call_amount']}"
            else:
                # don't have any action
                form.BetBox.hidden = True
                form.CheckButton.hidden = True
                form.CallButton.hidden = True
                form.FoldButton.hidden = True
                if form._widgets__[form.editw].hidden:
                    form._widgets__[form.editw].entry_widget.h_exit_right(None)
        seat = player["seat"]
        seat_name = f"{player['name']}"
        if data["dealer"] == seat:
            seat_name += f" {chr(0x24B9)}"
        form.SeatBoxes[seatbox_ind_from_seat(seat)].name = seat_name
        inside_box_text = [
            f"Stack: {player['stack']} ⛁",
            f"Bet: {player['current_bet']} ⛁",
        ]
        form.SeatBoxes[seatbox_ind_from_seat(seat)]._my_widgets[0].value = "\n\n".join(
            inside_box_text
        )

    if data["action_on"] is not None:
        form.SeatBoxes[seatbox_ind_from_seat(data["action_on"])].color = ACTION_ON_COLOR

    form.display()


def connect_to_server():
    port = 8000
    # address = "146.235.214.149"  # TODO take in address/port on cmdline
    address = "localhost"
    sio.connect(f"http://{address}:{port}")
    # await sio.wait()
    # ind = 0
    # while True:
    #     # send 'on_my_event' to server
    #     print('sending event ' + str(ind))
    #     await sio.emit('my_event', {'data': ind})
    #     print('sent')
    #     ind += 1
    #     await asyncio.sleep(1)


if __name__ == "__main__":
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(connect_to_server())
    connect_to_server()
    print("connected.")
    MyApp.run()


# MyApp = App()
# MyApp.run()
