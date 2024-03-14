import sys
import os
from typing import List
import random

# import time

import asyncio
import socketio
import uvicorn

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared import (
    TableInfo,
    GameState,
    PlayerState,
    ClientPlayerState,
    ClientPlayerAction,
    PlayerInfo,
    Pot,
    Deck,
    Card,
)

sio = socketio.AsyncServer(async_mode="asgi")
app = socketio.ASGIApp(sio)

address = "0.0.0.0"
port = 8000


@sio.event
async def connect(sid, environ, auth):
    print("connect ", sid)
    # TODO2 this will happen after the game creation screen
    if table_info is not None:
        open_seats = table_info.get_open_seats()
        table_info.add_player(
            name="Player " + str(len(table_info.players)),
            seat=random.choice(open_seats),
            sio_id=sid,
        )


@sio.event
async def disconnect(sid):
    print("disconnect ", sid)
    if table_info is not None:
        p = table_info.get_player_by_sio_id(sid)
        p.is_connected = False
        # player will get set to sitting out at the end of the round (or if they take long enough to act)


@sio.on("my_event")
async def on_my_event(sid, data):
    print("got my_event " + str(data["data"]))
    # await self.emit('my_response', data)


# async def poker():
#     print("Start of main()")
#     x = 0
#     # print("In main()")
#     while True:
#         print("starting to calculate x")
#         for i in range(10**8 // 3):
#             x += 1
#             # asyncio.slee
#             # await asyncio.sleep(10)
#             pass
#         print(" x = ", x)
#         await asyncio.sleep(5)


# async def test_sending():
#     ind = 0
#     while True:
#         await sio.emit("my_response", ind)
#         print("sent my_response " + str(ind))
#         ind += 1
#         await asyncio.sleep(0.5)


# def get_sio_player_by_sio_id(sio_id):
#     for player in sio_players:
#         if player["sio_id"] == sio_id:
#             return player
#     return None


"""
We don't want to change state in the middle of a loop 
iteration. If we get an unexpected event, ignore it.
Events like ShowCard/Change Stack can work the same.
Idea: Incoming events should just set a NextPlayerAction, 
not actually change state. Then the game loop will look 
and see if there's any actions to process.
"""
# TODO2 these should be set in game creation screen
NUM_SEATS = 4
SM_BLIND = 50
BG_BLIND = 100
TABLE_NAME = "Test Table 1"
# sio_players = []


async def update_state_from_actions(table_info: TableInfo):
    if (
        table_info.game_state == GameState.GAME_NOT_STARTED
    ):  # not used atm, but will after we add a Start Game button
        # if table_info.get_num_active_players() >= 2:
        table_info.game_state = GameState.BEFORE_HAND
        # set playerState to IN_HAND for all active players
        for player in table_info.players:
            if player.state not in [
                PlayerState.SITTING_OUT,
                PlayerState.NOT_SEATED,
            ]:
                player.state = PlayerState.IN_HAND
    elif table_info.game_state == GameState.BEFORE_HAND:
        # TODO handle sit ins here so people can join in this state until we get to 2
        # remove disconnected players for now, later we'd want to allow people to reconnect under the same name
        for player in table_info.players:
            if not player.is_connected:
                table_info.players.remove(player)
        # set people's states to IN_HAND
        if table_info.get_num_active_players() >= 2:
            # move dealer, here because we need to wait to know who's in the hand to move the dealer
            if table_info.dealer is None:
                table_info.dealer = table_info.get_first_seat_starting_at(
                    0, [PlayerState.IN_HAND]
                )
            else:
                table_info.dealer = table_info.get_next_seat(
                    table_info.dealer, [PlayerState.IN_HAND]
                )
            # force players to pay blinds, account for all-in,
            #   initializes min bet bookeeping info also.
            table_info.pay_blinds()
            # deal hole cards to all active players
            table_info.deal_hole_cards()
            # if players are not all in, go to preflop, otherwise go to showdown/end hand
            table_info.go_to_showdown_or_end_hand_else(GameState.PREFLOP)
    elif table_info.game_state == GameState.PROCESS_ACTIONS:
        # process one person's action at a time
        table_info.perform_next_player_action()
        table_info.goToNextActionOnIfDone()

        if not table_info.some_player_needs_to_act():
            table_info.update_pots()
            table_info.go_to_showdown_or_end_hand_else(
                table_info.process_actions_next_state
            )
            table_info.process_actions_next_state = None
    elif table_info.game_state == GameState.PREFLOP:
        # set action on
        table_info.action_on = table_info.get_first_to_act_preflop()
        # loop until everyone has acted
        table_info.game_state = GameState.PROCESS_ACTIONS
        table_info.process_actions_next_state = GameState.FLOP
        # process_player_actions(table_info)
        # # last thing, add bets to pot, create side pots
        # table_info.update_pots()
        # # go to showdown if everyone is all in, otherwise go to flop
        # table_info.go_to_showdown_or_end_hand_else(GameState.FLOP)
    elif table_info.game_state == GameState.FLOP:
        # deal flop cards
        table_info.add_n_cards_to_board(3)
        # set action on
        table_info.action_on = table_info.get_first_to_act_postflop()
        # loop until everyone has acted
        table_info.game_state = GameState.PROCESS_ACTIONS
        table_info.process_actions_next_state = GameState.TURN
        # process_player_actions(table_info)
        # last thing, add bets to pot, create side pots
        # table_info.update_pots()
        # go to showdown if everyone is all in, otherwise go to flop
        # table_info.go_to_showdown_or_end_hand_else(GameState.TURN)
    elif table_info.game_state == GameState.TURN:
        # deal turn card
        table_info.add_n_cards_to_board(1)
        # set action on
        table_info.action_on = table_info.get_first_to_act_postflop()
        # loop until everyone has acted
        table_info.game_state = GameState.PROCESS_ACTIONS
        table_info.process_actions_next_state = GameState.RIVER
        # process_player_actions(table_info)
        # last thing, add bets to pot, create side pots
        # table_info.update_pots()
        # go to showdown if everyone is all in, otherwise go to flop
        # table_info.go_to_showdown_or_end_hand_else(GameState.RIVER)
    elif table_info.game_state == GameState.RIVER:
        # deal river card
        table_info.add_n_cards_to_board(1)
        # set action on
        table_info.action_on = table_info.get_first_to_act_postflop()
        # loop until everyone has acted
        table_info.game_state = GameState.PROCESS_ACTIONS
        table_info.process_actions_next_state = GameState.SHOWDOWN
        # process_player_actions(table_info)
        # last thing, add bets to pot, create side pots
        # table_info.update_pots()
        # go to showdown if everyone is all in, otherwise go to flop
        # table_info.go_to_showdown_or_end_hand_else(GameState.SHOWDOWN)
    elif table_info.game_state == GameState.SHOWDOWN:
        # flip players cards
        table_info.show_eligible_players_cards()
        # TODO2 show remaining community cards one-by-one with timer between
        while len(table_info.community_cards) < 5:
            table_info.add_n_cards_to_board(1)
            # asyncio.sleep(1)
        table_info.game_state = GameState.END_HAND
    elif table_info.game_state == GameState.END_HAND:
        # distributes pots to winners
        table_info.distribute_pots_to_winners()
        # handle sit outs/sit ins/disconnects (actually just do in start hand)
        # set playerState to IN_HAND for all active players (maybe do this in before hand also)
        for player in table_info.players:
            if player.state not in [
                PlayerState.SITTING_OUT,
                PlayerState.NOT_SEATED,
            ]:
                player.state = PlayerState.IN_HAND
        table_info.hand_num += 1
        table_info.action_num = 0
        table_info.game_state = GameState.BEFORE_HAND


async def send_updated_state_to_players(table_info: TableInfo):
    for player in table_info.players:
        # get dict representing table_info (for each player's view, controls which cards they see, etc.)
        player_view = table_info.get_view(player)
        # send to each player
        print(player_view)
        await sio.emit("updated_table_info", player_view, room=player.sio_id)


# modified by incoming events
table_info: TableInfo = None


async def game_loop():
    # initialize table_info (different from reset table info)
    global table_info
    table_info = TableInfo(
        name=TABLE_NAME,
        num_seats=NUM_SEATS,
        sm_blind=SM_BLIND,
        bg_blind=BG_BLIND,
    )
    while True:
        # check for NextPlayerActions and update state
        await update_state_from_actions(table_info)
        print(table_info.game_state)
        # Send updated TableInfo to everyone
        #  contains actions for players also
        await send_updated_state_to_players(table_info)
        await asyncio.sleep(1.5)


async def main():
    # start printing app
    # asyncio.create_task(poker())
    asyncio.create_task(game_loop())
    # loop.create_task(test_sending())

    # start uvicorn server
    config = uvicorn.Config(app, host=address, port=port)
    server = uvicorn.Server(config)
    await server.serve()
    print("Server shut down somehow.")


if __name__ == "__main__":
    # uvicorn.run(app, host=address, port=port)
    # wait 5 seconds
    asyncio.run(main())
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(main(loop))
