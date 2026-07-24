from tests.conftest import (
    auth_header,
    create_game,
    login_user,
    register_user,
)


def setup_players(client):
    register_user(client, "alice")
    register_user(client, "bob")
    return login_user(client, "alice"), login_user(client, "bob")


def test_game_can_be_created(client):
    alice_token, _ = setup_players(client)

    response = create_game(client, alice_token, "bob")

    assert response.status_code == 201
    assert response.json()["status"] == "active"
    assert response.json()["current_fen"]
    assert response.json()["pgn"] == ""


def test_user_cannot_play_against_self(client):
    register_user(client, "alice")
    token = login_user(client, "alice")

    response = create_game(client, token, "alice")

    assert response.status_code == 400


def test_nonexistent_opponent_is_rejected(client):
    register_user(client, "alice")
    token = login_user(client, "alice")

    response = create_game(client, token, "missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Opponent not found"


def test_both_players_can_retrieve_game(client):
    alice_token, bob_token = setup_players(client)
    game_id = create_game(client, alice_token, "bob").json()["id"]

    alice_response = client.get(
        f"/games/{game_id}",
        headers=auth_header(alice_token),
    )
    bob_response = client.get(
        f"/games/{game_id}",
        headers=auth_header(bob_token),
    )

    assert alice_response.status_code == 200
    assert bob_response.status_code == 200


def test_unrelated_user_cannot_retrieve_game(client):
    alice_token, _ = setup_players(client)
    register_user(client, "carol")
    carol_token = login_user(client, "carol")
    game_id = create_game(client, alice_token, "bob").json()["id"]

    response = client.get(
        f"/games/{game_id}",
        headers=auth_header(carol_token),
    )

    assert response.status_code == 403


def test_my_games_returns_game_for_both_players(client):
    alice_token, bob_token = setup_players(client)
    game_id = create_game(client, alice_token, "bob").json()["id"]

    alice_games = client.get(
        "/games/my-games",
        headers=auth_header(alice_token),
    ).json()
    bob_games = client.get(
        "/games/my-games",
        headers=auth_header(bob_token),
    ).json()

    assert [game["id"] for game in alice_games] == [game_id]
    assert [game["id"] for game in bob_games] == [game_id]


def test_my_games_is_empty_for_user_without_games(client):
    register_user(client, "carol")
    token = login_user(client, "carol")

    response = client.get("/games/my-games", headers=auth_header(token))

    assert response.status_code == 200
    assert response.json() == []
