from typing import List
from enum import Enum
import secrets
from collections import defaultdict

sys_rand = secrets.SystemRandom()

"""
Game State for Hold Em' specifically.
Other variants will have their own game state.
"""


class GameState(Enum):
    GAME_NOT_STARTED = 0
    # could have Discarding here
    # [BEFORE_HAND] all playerStates are locked in here
    BEFORE_HAND = 1  # deal hole cards, make people pay big blinds, move dealer
    PREFLOP = 2
    FLOP = 3
    TURN = 4
    RIVER = 5
    SHOWDOWN = 6  # if more than 1 player left after river, show down, else end hand
    # updates stacks, hand info, action_num=0, sets playerState to IN_HAND
    #   handles disconnects/sit ins/outs etc. waits 2s
    #   if player has 0 money, force sit out
    END_HAND = 7


class PlayerState(Enum):
    NOT_SEATED = 0  # just watching

    SITTING_OUT = 1  # chose to sit out and not play hands

    NOT_IN_HAND = (
        2  # seated but waiting for next hand, similar to folded, if joins late
    )

    IN_HAND = 3  # playing current hand, haven't chose an action this street
    # previous action in street, at start of each street is set to IN_HAND
    FOLDED = 4
    CHECKED = 5
    CALLED = 6
    BET = 7  # same as raised but only if everyone before checks
    RAISED = 8
    ALL_IN = 9

    # DISCONNECTED = 10  # should check/fold if time is called


# player states who are in the current hand
ACTIVE_PLAYER_STATES = [
    PlayerState.IN_HAND,
    PlayerState.FOLDED,
    PlayerState.CHECKED,
    PlayerState.CALLED,
    PlayerState.BET,
    PlayerState.RAISED,
    PlayerState.ALL_IN,
    # PlayerState.DISCONNECTED,
]

# player states who still may need to act
NOT_ACTED_PLAYER_STATES = [
    PlayerState.IN_HAND,
    PlayerState.CHECKED,
    PlayerState.CALLED,
    PlayerState.BET,
    PlayerState.RAISED,
    # PlayerState.DISCONNECTED,
]

POT_ELIGIBLE_PLAYER_STATES = [
    PlayerState.IN_HAND,
    PlayerState.CHECKED,
    PlayerState.CALLED,
    PlayerState.BET,
    PlayerState.RAISED,
    PlayerState.ALL_IN,
]


"""
Once exhausted a new Deck must be created
"""


class Deck:
    def __init__(self):
        # self.next_deck_ind = 0
        self.cards: List[Card] = []
        for suit in range(4):
            for rank in range(13):
                self.cards.append(Card(rank, suit))
        # https://en.wikipedia.org/wiki/Fisher%E2%80%93Yates_shuffle#The_modern_algorithm
        sys_rand.shuffle(self.cards)

    def draw_card(self, face_up=False):
        if len(self.cards) == 0:
            raise ValueError("Deck is empty")
        card = self.cards.pop(0)
        # card.deck_index = self.next_deck_ind
        self.next_deck_ind += 1
        return card

    def remaining_cards(self):
        return len(self.cards)


class Card:
    def __init__(self, rank, suit, face_up=False):
        # self.deck_index = deck_index  # unique per Deck, assigned when dealt
        self.rank = rank
        self.suit = suit
        self.face_up = False  # if a player chooses to show their card


"""
Shared Data Structure
Different from PlayerState since it's only used to send to clients.
  Tells the Client what info the server is waiting on.
"""


class ClientPlayerState(Enum):
    NO_ACTION = 0  # may not need, if we just set to None
    CHOOSE_BET = 1  # also raise, check, etc.
    SELECT_CARDS = 2  # UNUSED - to be used for discarding, etc.


class ClientNextActionType(Enum):
    NO_ACTION = 0
    FOLD = 1
    CHECK = 2
    CALL = 3
    BET = 5  # same as raise
    # RAISE = 6
    # ALL_IN = 6


class ClientNextAction:
    def __init__(self, action=ClientNextActionType.NO_ACTION, bet_amount=None):
        self.action: ClientNextActionType = action
        self.bet_amount = bet_amount  # only used for ClientNextActionType.BET


"""
Shared Data Structure - Info for Client UI to use to display options to player.
    Lets player send next_action to server also.
"""


class ClientPlayerAction:
    def __init__(
        self,
        hand_num=None,
        action_num=None,
        action=ClientPlayerState.NO_ACTION,
        message=None,
        can_check=None,
        # can_call=None,
        call_amount=None,
        can_raise=None,
        bet_instead_of_raise=None,
        min_raise=None,
        next_action=None,
    ):
        self.hand_num = hand_num
        self.action_num = action_num
        self.action: ClientPlayerState = action
        self.message = message  # show on screen
        # if players current bet == latest bet but they still need to act (first to act or BB)
        self.can_check = can_check
        # calling includes All-ins when stack <= last bet
        # raising includes All-ins when stack > last_bet
        # betting includes All-ins all the time, only other option is check
        # self.can_call = can_call  # if not, must all-in or fold (calling > stack)
        self.call_amount = call_amount  # if can_call is true
        self.can_raise = (
            can_raise  # may not if all-in doesn't reopen action or (stack < last bet)
        )
        self.bet_instead_of_raise = (
            bet_instead_of_raise  # if true, Bet, otherwise Raise
        )
        self.min_raise = min_raise  # doubles as min raise if betting not an option

        self.next_action: ClientNextAction = (
            next_action  # set when server gets action events from player
        )


class PlayerInfo:
    def __init__(self, name, seat, sio_id):
        self.sio_id = sio_id
        self.name = name  # unique among players at table
        self.buy_in_amount = 0
        self.stack = 0
        self.buy_in(10_000)
        self.seat = seat
        # could change if I make sure click sit
        self.state: PlayerState = PlayerState.NOT_IN_HAND
        self.current_bet = 0
        self.last_full_raise_responded_to = None  # determines if action is re-opened
        self.last_bet_responded_to = None
        self.is_all_in = False  # just for displaying to clients
        self.client_player_action: ClientPlayerAction = None
        self.hole_cards: List[Card] = []
        self.stats = PlayerStats()
        self.is_connected = True

    def get_json(self, viewer_id):
        # if viewer is not myself, do not show my cards,
        #  unless it's showdown and I have to
        # when translating PlayerState, show in terms of ClientPlayerState
        return {
            # TODO
        }

    def get_profit(self):
        return self.stack - self.buy_in_amount

    """
    Just handles updating stack and current_bet. None if invalid.
    """

    def bet(self, new_bet):
        if new_bet < self.current_bet:
            return None
        added_amt = new_bet - self.current_bet
        if added_amt > self.stack:
            return None
        self.stack -= added_amt
        self.current_bet += added_amt
        return self.current_bet

    # forcefully change their stack, buy in/buy out
    def buy_in(self, new_stack):
        if new_stack < 0:
            raise ValueError("Stack cannot be negative")
        self.buy_in_amount += new_stack - self.stack
        self.stack = new_stack

    def bet_is_all_in(self, new_bet):
        return new_bet - self.current_bet == self.stack


class PlayerStats:
    def __init__(self):
        # TODO track vpip, pfr, 3bet %, maybe fold to 3 bet %, etc.
        pass


class Pot:
    def __init__(self):
        self.pot_size = 0
        # everyone is eligible for a main pot, only relevant for side pots
        self.players_eligible = []

    def get_json(self):
        return {
            # TODO
        }


class TableInfo:
    def __init__(self, name, num_seats, sm_blind, bg_blind):
        self.name = name  # unique among tables
        self.num_seats = num_seats
        self.sm_blind = sm_blind  # amt
        self.bg_blind = bg_blind  # amt
        self.game_state = GameState.GAME_NOT_STARTED
        self.hand_num = 1
        self.players: List[PlayerInfo] = []
        # self.players: List[PlayerInfo] = [
        #     PlayerInfo(player["name"], player["seat"], player["sio_id"])
        #     for player in players
        # ]
        self.main_pot: Pot = Pot()
        self.side_pots: List[Pot] = []
        self.deck: Deck = Deck()
        self.community_cards: List[Card] = []
        self.dealer = None  # seat index
        self.action_num = 0  # identifies which action a player is responding to
        self.action_on = None  # None if waiting for everyone?
        self.latest_bet = (
            None  # used to calculate how much a call is, the max bet so far.
        )
        self.latest_full_raise = None  # used to calculate min raises
        self.min_raise = None
        self.end_hand_time_start = None  # time.time() when hand ended
        # TODO2: keep table history/log of actions

    def add_player(self, name, seat, sio_id):
        if seat not in self.get_open_seats():
            return False
        self.players.append(PlayerInfo(name, seat, sio_id))
        return True

    def get_player_by_sio_id(self, sio_id):
        for player in self.players:
            if player.sio_id == sio_id:
                return player
        return None

    def get_player_at_seat(self, seat: int) -> PlayerInfo:
        for player in self.players:
            if player.seat == seat:
                return player
        return None

    def get_open_seats(self):
        return [i for i in range(self.num_seats) if self.get_player_at_seat(i) is None]

    def get_num_players(self, filter):
        return len([p for p in self.players if p.state in filter])

    def get_num_players_not(self, filter):
        return len([p for p in self.players if p.state not in filter])

    def get_num_active_players(self):
        return self.get_num_players_not(
            [PlayerState.NOT_SEATED, PlayerState.SITTING_OUT]
        )

    def get_first_seat_starting_at(
        self, start_seat: int, filter: List[PlayerState]
    ) -> int:
        for i in range(self.num_seats):
            seat = (start_seat + i) % self.num_seats
            if (
                self.get_player_at_seat(seat) is not None
                and self.get_player_at_seat(seat).state not in filter
            ):
                return seat
        return None

    def get_next_seat(self, start_seat: int, filter: List[PlayerState]) -> int:
        return self.get_first_seat_starting_at(
            (start_seat + 1) % self.num_seats, filter
        )

    def is_heads_up(self) -> bool:
        return self.get_num_active_players() == 2

    def get_small_blind_seat(self) -> int:
        if self.is_heads_up():
            return self.dealer
        else:
            return self.get_next_seat(self.dealer, ACTIVE_PLAYER_STATES)

    def get_big_blind_seat(self) -> int:
        if self.is_heads_up():
            return self.get_next_seat(self.get_small_blind_seat(), ACTIVE_PLAYER_STATES)
        else:
            return self.get_next_seat(self.get_small_blind_seat(), ACTIVE_PLAYER_STATES)

    def get_first_to_act_preflop(self) -> int:
        if self.is_heads_up():
            return self.get_small_blind_seat()
        else:
            return self.get_next_seat(self.get_big_blind_seat(), ACTIVE_PLAYER_STATES)

    def get_first_to_act_postflop(self) -> int:
        if self.is_heads_up():
            return self.get_big_blind_seat()
        else:
            return self.get_next_seat(self.dealer, ACTIVE_PLAYER_STATES)

    def pay_blinds(self):
        small_blind_seat = self.get_small_blind_seat()
        print(f"small_blind_seat: {small_blind_seat}")
        big_blind_seat = self.get_big_blind_seat()
        print(f"big_blind_seat: {big_blind_seat}")
        print(f"player seats: {[p.seat for p in self.players]}")
        small_blind_player = self.get_player_at_seat(small_blind_seat)
        big_blind_player = self.get_player_at_seat(big_blind_seat)
        sm_blind_charged = min(self.sm_blind, small_blind_player.stack)
        bg_blind_charged = min(self.bg_blind, big_blind_player.stack)
        self.get_player_at_seat(small_blind_seat).bet(sm_blind_charged)
        self.get_player_at_seat(big_blind_seat).bet(bg_blind_charged)
        if small_blind_player.stack == 0:
            small_blind_player.is_all_in = True
            small_blind_player.state = PlayerState.ALL_IN
        if big_blind_player.stack == 0:
            big_blind_player.is_all_in = True
            big_blind_player.state = PlayerState.ALL_IN
        self.latest_bet = max(bg_blind_charged, sm_blind_charged)
        self.min_raise = 2 * self.bg_blind
        self.latest_full_raise = self.bg_blind
        small_blind_player.last_full_raise_responded_to = 0
        big_blind_player.last_full_raise_responded_to = 0
        small_blind_player.last_bet_responded_to = sm_blind_charged
        big_blind_player.last_bet_responded_to = bg_blind_charged

    def deal_card_to_player(self, player: PlayerInfo):
        card = self.deck.draw_card()
        player.hole_cards.append(card)

    def deal_hole_cards(self):
        seat = self.get_next_seat(self.dealer, ACTIVE_PLAYER_STATES)
        while any(
            len(player.hole_cards) < 2
            for player in self.players
            if player.state == PlayerState.IN_HAND
        ):
            player = self.get_player_at_seat(seat)
            if player.state == PlayerState.IN_HAND:
                self.deal_card_to_player(player)
            seat = self.get_next_seat(seat, ACTIVE_PLAYER_STATES)

    # raise rules, PREFLOP min raise is 2x BB, after that min raise is previous raise
    # if someone raises with less than a min-raise, options are fold/call for people who
    #  have responded to the last full raise, but people who haven't responded can raise
    #  and the min-raise is as-if the < full raiser hadn't even acted.

    """ Performs action for player at seat self.actionOn.
     Does nothing if player doesnt have an action queued. """

    def perform_next_player_action(self):
        p: PlayerInfo = self.get_player_at_seat(self.action_on)
        if p.client_player_action is None:
            return

        if p.client_player_action.next_action.action == ClientNextActionType.FOLD:
            p.state = PlayerState.FOLDED
            p.client_player_action = None
        elif p.client_player_action.next_action.action == ClientNextActionType.CHECK:
            if p.client_player_action.can_check:
                p.state = PlayerState.CHECKED
                p.last_bet_responded_to = self.latest_bet
                p.client_player_action = None
        elif p.client_player_action.next_action.action == ClientNextActionType.CALL:
            # call is the min(last bet, stack)
            call_amt = min(self.latest_bet, p.stack)
            if call_amt == p.stack:
                if p.bet(call_amt) is not None:
                    # bet should always work
                    p.last_full_raise_responded_to = self.latest_full_raise
                    p.last_bet_responded_to = self.latest_bet
                    p.is_all_in = True
                    p.state = PlayerState.ALL_IN
                    p.client_player_action = None
            else:
                if p.bet(call_amt) is not None:
                    # bet worked
                    p.last_full_raise_responded_to = self.latest_full_raise
                    p.last_bet_responded_to = self.latest_bet
                    p.state = PlayerState.CALLED
                    p.client_player_action = None
        elif p.client_player_action.next_action.action == ClientNextActionType.BET:
            bet_amt = p.client_player_action.next_action.bet_amount

            if p.client_player_action.action == ClientPlayerState.CHOOSE_BET:
                if p.client_player_action.can_raise:
                    # if all-in, rules are different
                    if p.bet_is_all_in(bet_amt):
                        # bet should always work now, may not be full-raise
                        if p.bet(bet_amt) is not None:
                            # bet worked
                            if bet_amt >= p.client_player_action.min_raise:
                                # all-in is full-raise
                                self.latest_bet = bet_amt
                                self.min_raise = bet_amt + (
                                    bet_amt - self.latest_full_raise
                                )
                                self.latest_full_raise = bet_amt
                                p.last_full_raise_responded_to = bet_amt
                                p.last_bet_responded_to = self.latest_bet
                                p.is_all_in = True
                                p.state = PlayerState.ALL_IN
                                p.client_player_action = None
                            else:
                                # all-in is not full-raise
                                self.latest_bet = bet_amt
                                p.last_full_raise_responded_to = self.latest_full_raise
                                p.last_bet_responded_to = self.latest_bet
                                p.is_all_in = True
                                p.state = PlayerState.ALL_IN
                                p.client_player_action = None
                    else:
                        if bet_amt >= p.client_player_action.min_raise:
                            # bet is legal and is full-raise other than player's stack
                            if p.bet(bet_amt) is not None:
                                # bet worked
                                self.latest_bet = bet_amt
                                self.min_raise = bet_amt + (
                                    bet_amt - self.latest_full_raise
                                )
                                self.latest_full_raise = bet_amt
                                p.last_bet_responded_to = self.latest_bet
                                p.last_full_raise_responded_to = bet_amt
                                if p.client_player_action.bet_instead_of_raise:
                                    p.state = PlayerState.BET
                                else:
                                    p.state = PlayerState.RAISED
                                p.client_player_action = None
        # elif p.client_player_action.next_action.action == ClientNextActionType.ALL_IN:
        #     pass
        elif (
            p.client_player_action.next_action.action == ClientNextActionType.NO_ACTION
        ):
            pass
        else:
            raise ValueError("Invalid action")

    """
    Stays at current player if they're not done, otherwise goes to next player who needs to act
    """

    def goToNextActionOnIfDone(self):
        if self.player_needs_to_act(self.get_player_at_seat(self.action_on)):
            return self.action_on

        self.get_player_at_seat(self.action_on).client_player_action = None
        self.action_num += 1
        self.action_on = self.get_next_seat(self.action_on, NOT_ACTED_PLAYER_STATES)
        # if not self.player_needs_to_act(self.get_player_at_seat(self.action_on)):
        #     return None
        # set their client_player_action (allows incoming next actions to come in)
        p = self.get_player_at_seat(self.action_on)
        # assert p.client_player_action is None
        if p.client_player_action is None:
            can_check = p.current_bet == self.latest_bet
            call_amount = min(self.latest_bet, p.stack)
            can_raise = (
                p.stack > self.latest_bet
                and p.last_full_raise_responded_to != self.latest_full_raise
            )
            bet_instead_of_raise = self.latest_bet == 0
            min_raise = self.min_raise
            p.client_player_action = ClientPlayerAction(
                hand_num=self.hand_num,
                action_num=self.action_num,
                action=ClientPlayerState.CHOOSE_BET,
                can_check=can_check,
                call_amount=call_amount,
                can_raise=can_raise,
                bet_instead_of_raise=bet_instead_of_raise,
                min_raise=min_raise,
                next_action=ClientNextAction(),
            )

    def update_pots(self):
        # split pot into side pots for all-ins
        players_who_bet_money = []
        for player in self.players:
            if player.current_bet > 0:
                players_who_bet_money.append(player)
        players_who_bet_money.sort(key=lambda x: x.current_bet)
        while len(players_who_bet_money) > 0:
            lowest_committed_bet = players_who_bet_money[0].current_bet
            # if this player isn't eligible, just add to main pot
            if players_who_bet_money[0].state not in POT_ELIGIBLE_PLAYER_STATES:
                self.main_pot.pot_size += lowest_committed_bet
                players_who_bet_money[0].current_bet = 0
                players_who_bet_money.pop(0)
            else:
                # if everyone bet this amount, we add the rest to the main pot
                if all(
                    player.current_bet == lowest_committed_bet
                    for player in players_who_bet_money
                ):
                    for player in players_who_bet_money:
                        self.main_pot.pot_size += player.current_bet
                        player.current_bet = 0
                    players_who_bet_money = []
                else:
                    # otherwise, we add the amount from every player to the main pot, then make it a side pot
                    for player in players_who_bet_money:
                        self.main_pot.pot_size += lowest_committed_bet
                        player.current_bet -= lowest_committed_bet
                    self.main_pot.players_eligible = [
                        player
                        for player in players_who_bet_money
                        if player.state in POT_ELIGIBLE_PLAYER_STATES
                    ]
                    self.side_pots.append(self.main_pot)
                    self.main_pot = Pot()
                    players_who_bet_money = [
                        player
                        for player in players_who_bet_money
                        if player.current_bet > 0
                    ]

    def max_card_rank(self, cards: List[Card]) -> Card:
        return max(cards, key=lambda x: x.rank).rank

    def is_straight(self, cards: List[Card]) -> bool:
        # 12 is Ace
        new_cards = sorted(
            [card for card in cards if card.rank != 12], key=lambda x: x.rank
        )
        if len(new_cards) == 5:
            for i in range(1, 5):
                if new_cards[i].rank != new_cards[i - 1].rank + 1:
                    return (False,)
            return (True, self.max_card_rank(new_cards))
        elif len(new_cards) == 4:
            new_cards2 = new_cards + [12]
            found_straight = True
            for i in range(1, 5):
                if new_cards2[i].rank != new_cards2[i - 1].rank + 1:
                    found_straight = False
            if found_straight:
                return (True, self.max_card_rank(new_cards2))
            found_straight = True
            new_cards2 = [-1] + new_cards
            for i in range(1, 5):
                if new_cards2[i].rank != new_cards2[i - 1].rank + 1:
                    found_straight = False
            if found_straight:
                return (True, self.max_card_rank(new_cards2))
            else:
                return (False,)
        return (False,)

    def is_flush(self, cards: List[Card]) -> bool:
        return (
            all(card.suit == cards[0].suit for card in cards),
            sorted([card.rank for card in cards], reverse=True),
        )

    def is_4_of_a_kind(self, cards: List[Card]) -> tuple[bool, int]:
        card_counts = defaultdict(int)
        for card in cards:
            card_counts[card.rank] += 1
        four_of_a_kind = None
        kicker = None
        for rank, count in card_counts.items():
            if count == 4:
                four_of_a_kind = rank
            else:
                kicker = rank
        if four_of_a_kind is not None:
            return (True, four_of_a_kind, kicker)
        return (False,)

    def is_3_of_a_kind(self, cards: List[Card]) -> tuple[bool, int]:
        card_counts = defaultdict(int)
        for card in cards:
            card_counts[card.rank] += 1
        three_of_a_kind = None
        kickers = []
        for rank, count in card_counts.items():
            if count == 3:
                three_of_a_kind = rank
            else:
                kickers.append(rank)
        if three_of_a_kind is not None:
            kickers.sort(reverse=True)
            return (True, three_of_a_kind, kickers[0], kickers[1])
        return (False,)

    def is_2_pair(self, cards: List[Card]) -> tuple[bool, int, int]:
        card_counts = defaultdict(int)
        for card in cards:
            card_counts[card.rank] += 1
        pairs = []
        kicker = None
        for rank, count in card_counts.items():
            if count == 2:
                pairs.append(rank)
            if count == 1:
                kicker = rank
        if len(pairs) == 2:
            if pairs[1] > pairs[0]:
                return (True, pairs[1], pairs[0], kicker)
            else:
                return (True, pairs[0], pairs[1], kicker)
        return (False,)

    def is_pair(self, cards: List[Card]) -> tuple[bool, int, int, int, int]:
        card_counts = defaultdict(int)
        for card in cards:
            card_counts[card.rank] += 1
        pair = None
        kickers = []
        for rank, count in card_counts.items():
            if count == 2:
                pair = rank
            else:
                kickers.append(rank)
        if pair is not None:
            kickers.sort(reverse=True)
            return (True, pair, kickers[0], kickers[1], kickers[2])
        return (False,)

    def hand_strength(self, player: PlayerInfo) -> int:
        # get all combinations of 5 cards from community_cards + player.hole_cards
        all_cards = self.community_cards + player.hole_cards
        combinations = []
        for i in range(len(all_cards)):
            for j in range(i + 1, len(all_cards)):
                for k in range(j + 1, len(all_cards)):
                    for l in range(k + 1, len(all_cards)):
                        for m in range(l + 1, len(all_cards)):
                            combinations.append(
                                [
                                    all_cards[i],
                                    all_cards[j],
                                    all_cards[k],
                                    all_cards[l],
                                    all_cards[m],
                                ]
                            )
        best_hand_strength = None
        for cards in combinations:
            is_straight = self.is_straight(cards)
            is_flush = self.is_flush(cards)
            is_4_of_a_kind = self.is_4_of_a_kind(cards)
            is_3_of_a_kind = self.is_3_of_a_kind(cards)
            is_2_pair = self.is_2_pair(cards)
            is_pair = self.is_pair(cards)
            hand_strength = None
            if is_straight[0] and is_flush[0] and self.max_card_rank(cards) == 12:
                # Royal Flush
                hand_strength = (10,)
            elif is_straight[0] and is_flush[0]:
                # straight flush
                hand_strength = (9, self.max_card_rank(cards))
            elif is_4_of_a_kind[0]:
                # 4 of a kind
                hand_strength = (8, is_4_of_a_kind[1:])
            elif is_3_of_a_kind[0] and is_pair[0]:
                # full house
                hand_strength = (7, is_3_of_a_kind[1], is_pair[1])
            elif is_flush[0]:
                # flush
                hand_strength = (6, is_flush[1])
            elif is_straight[0]:
                # straight
                hand_strength = (5, is_straight[1])
            elif is_3_of_a_kind[0]:
                # 3 of a kind
                hand_strength = (4, is_3_of_a_kind[1:])
            elif is_2_pair[0]:
                # 2 pair
                hand_strength = (3, is_2_pair[1:])
            elif is_pair[0]:
                # pair
                hand_strength = (2, is_pair[1:])
            else:
                # high card
                hand_strength = (1, sorted([card.rank for card in cards], reverse=True))
            if best_hand_strength is None or hand_strength > best_hand_strength:
                best_hand_strength = hand_strength
        return best_hand_strength

    def calculate_winning_players(self, players_eligible) -> List[PlayerInfo]:
        hand_strengths = [(self.hand_strength(p), p) for p in players_eligible]
        best_hand_strength = max(hand_strengths, key=lambda x: x[0])[0]
        return [p for (hs, p) in hand_strengths if hs == best_hand_strength]

    def distribute_pot_to_winners(self, pot):
        winning_players = self.calculate_winning_players(
            [p for p in pot.players_eligible if p.state in POT_ELIGIBLE_PLAYER_STATES]
        )
        for player in winning_players:
            player.stack += pot.pot_size // len(winning_players)
        rem = pot.pot_size % len(winning_players)
        for player in winning_players:
            if rem > 0:
                player.stack += 1
                rem -= 1

    # if there's a split pot, odd chips go to earliest position
    # order of resolution: best hand first, so go from most eligible players to least,
    #   that way the player with the best hand gets paid first
    def distribute_pots_to_winners(self):
        while len(self.side_pots) > 0:
            pot = self.side_pots.pop(0)
            self.distribute_pot_to_winners(pot)
        self.distribute_pot_to_winners(self.main_pot)
        self.main_pot = Pot()

    def show_eligible_players_cards(self):
        for player in self.players:
            if player.state in POT_ELIGIBLE_PLAYER_STATES:
                for card in player.hole_cards:
                    card.face_up = True

    def add_n_cards_to_board(self, n):
        for _ in range(n):
            self.community_cards.append(self.deck.draw_card(face_up=True))

    """ Goes to Showdown if >= 2 players in hand and everyone except for one is all-in or more.
     Goes to End Hand if there's only 1 person left. Otherwise goes to next_state."""

    def go_to_showdown_or_end_hand_else(self, next_state):
        if self.get_num_players(POT_ELIGIBLE_PLAYER_STATES) == 1:
            self.game_state = GameState.END_HAND
        elif (
            self.get_num_players(POT_ELIGIBLE_PLAYER_STATES) > 1
            and self.get_num_players([PlayerState.ALL_IN])
            >= self.get_num_players(POT_ELIGIBLE_PLAYER_STATES) - 1
        ):
            self.game_state = GameState.SHOWDOWN
        else:
            self.game_state = next_state

    def some_player_needs_to_act(self):
        return any(self.player_needs_to_act(player) for player in self.players)

    def player_needs_to_act(self, player: PlayerInfo):
        if player.state == PlayerState.ALL_IN or player.state == PlayerState.FOLDED:
            return False
        # edge case of BB preflop
        if player.last_bet_responded_to == self.latest_bet:
            return False
        return True

    def get_json(self, viewer_id):
        return {
            # TODO
            "players": [player.get_json(viewer_id) for player in self.players],
        }
