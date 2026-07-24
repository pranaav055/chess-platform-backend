from dataclasses import dataclass
from io import StringIO

import chess
import chess.pgn


class InvalidBoardStateError(ValueError):
    """Raised when persisted chess state cannot be reconstructed safely."""


class InvalidMoveFormatError(ValueError):
    """Raised when a move is not valid UCI notation."""


class IllegalMoveError(ValueError):
    """Raised when a well-formed move is not legal in the current position."""


@dataclass(frozen=True)
class AppliedMove:
    move: chess.Move
    san: str
    current_fen: str
    outcome: chess.Outcome | None


def load_board(current_fen: str) -> chess.Board:
    try:
        return chess.Board(current_fen)
    except ValueError as exc:
        raise InvalidBoardStateError("The stored board position is invalid") from exc


def parse_uci_move(move_text: str) -> chess.Move:
    try:
        return chess.Move.from_uci(move_text)
    except ValueError as exc:
        raise InvalidMoveFormatError(
            "Move must use UCI notation, for example e2e4 or e7e8q"
        ) from exc


def apply_move(board: chess.Board, move_text: str) -> AppliedMove:
    move = parse_uci_move(move_text)
    if move not in board.legal_moves:
        raise IllegalMoveError("Move is not legal in the current position")

    san = board.san(move)
    board.push(move)
    return AppliedMove(
        move=move,
        san=san,
        current_fen=board.fen(),
        outcome=board.outcome(claim_draw=True),
    )


def winner_player_id(
    outcome: chess.Outcome | None,
    white_player_id: int,
    black_player_id: int,
) -> int | None:
    if outcome is None or outcome.winner is None:
        return None
    return white_player_id if outcome.winner == chess.WHITE else black_player_id


def update_pgn(
    existing_pgn: str,
    previous_fen: str,
    move: chess.Move,
    outcome: chess.Outcome | None,
) -> str:
    if existing_pgn.strip():
        game = chess.pgn.read_game(StringIO(existing_pgn))
        if game is None:
            raise InvalidBoardStateError("The stored PGN is invalid")
    else:
        game = chess.pgn.Game()

    node = game.end()
    if node.board().fen() != previous_fen:
        raise InvalidBoardStateError(
            "The stored FEN and PGN do not describe the same game"
        )

    node.add_main_variation(move)
    game.headers["Result"] = outcome.result() if outcome else "*"
    exporter = chess.pgn.StringExporter(headers=True, variations=False, comments=False)
    return game.accept(exporter)
