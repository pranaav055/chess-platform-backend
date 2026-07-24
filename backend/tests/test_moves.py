import chess

from app.models.game import Game
from app.services.chess_service import apply_move
from tests.conftest import (
    auth_header,
    create_game,
    login_user,
    register_user,
)


def setup_game(client):
    register_user(client, "white")
    register_user(client, "black")
    white_token = login_user(client, "white")
    black_token = login_user(client, "black")
    game = create_game(client, white_token, "black").json()
    return game, white_token, black_token


def submit_move(client, game_id, token, move):
    return client.post(
        f"/games/{game_id}/move",
        headers=auth_header(token),
        json={"move": move},
    )


def test_white_can_make_first_move_and_state_changes(client, db_session):
    game, white_token, _ = setup_game(client)

    response = submit_move(client, game["id"], white_token, "e2e4")

    assert response.status_code == 200
    body = response.json()
    assert body["san"] == "e4"
    assert body["game"]["current_fen"] != chess.STARTING_FEN
    assert "1. e4" in body["game"]["pgn"]
    stored_game = db_session.get(Game, game["id"])
    assert stored_game.current_fen == body["game"]["current_fen"]
    assert stored_game.pgn == body["game"]["pgn"]


def test_black_cannot_move_first(client):
    game, _, black_token = setup_game(client)

    response = submit_move(client, game["id"], black_token, "e7e5")

    assert response.status_code == 409
    assert response.json()["detail"] == "It is not your turn"


def test_illegal_move_is_rejected(client):
    game, white_token, _ = setup_game(client)

    response = submit_move(client, game["id"], white_token, "e2e5")

    assert response.status_code == 422
    assert response.json()["detail"] == "Move is not legal in the current position"


def test_malformed_move_is_rejected(client):
    game, white_token, _ = setup_game(client)

    response = submit_move(client, game["id"], white_token, "nope")

    assert response.status_code == 422
    assert "UCI notation" in response.json()["detail"]


def test_unrelated_user_cannot_move(client):
    game, _, _ = setup_game(client)
    register_user(client, "other")
    token = login_user(client, "other")

    response = submit_move(client, game["id"], token, "e2e4")

    assert response.status_code == 403


def test_turns_alternate(client):
    game, white_token, black_token = setup_game(client)

    white_response = submit_move(client, game["id"], white_token, "e2e4")
    black_response = submit_move(client, game["id"], black_token, "e7e5")

    assert white_response.status_code == 200
    assert black_response.status_code == 200
    assert black_response.json()["san"] == "e5"


def test_promotion_uci_notation_is_supported():
    board = chess.Board("8/4P3/8/8/8/8/8/k6K w - - 0 1")

    applied = apply_move(board, "e7e8q")

    assert applied.move.promotion == chess.QUEEN
    assert applied.san == "e8=Q"


def test_fools_mate_completes_game_and_blocks_more_moves(client):
    game, white_token, black_token = setup_game(client)
    moves = [
        (white_token, "f2f3"),
        (black_token, "e7e5"),
        (white_token, "g2g4"),
        (black_token, "d8h4"),
    ]

    response = None
    for token, move in moves:
        response = submit_move(client, game["id"], token, move)
        assert response.status_code == 200

    completed = response.json()["game"]
    assert response.json()["san"] == "Qh4#"
    assert completed["status"] == "completed"
    assert completed["winner_id"] == game["black_player_id"]
    assert completed["pgn"].rstrip().endswith("0-1")

    blocked = submit_move(client, game["id"], white_token, "e2e4")
    assert blocked.status_code == 409
    assert blocked.json()["detail"] == "This game is no longer active"
