"""Bundled endgame study positions.

Each entry is a common endgame start position. ``fen`` is a legal position
with White to move, so the side to convert (or defend) is White by default;
players can still choose to defend by switching sides in the Play panel.
"""

ENDGAMES = [
    {
        "id": "queen_mate",
        "fen": "4k3/8/8/8/8/8/8/3QK3 w - - 0 1",
    },
    {
        "id": "rook_mate",
        "fen": "4k3/8/8/8/8/8/8/4K1R1 w - - 0 1",
    },
    {
        "id": "two_rooks_mate",
        "fen": "4k3/8/8/8/8/8/8/R3K2R w - - 0 1",
    },
    {
        "id": "two_bishops_mate",
        "fen": "4k3/8/8/8/8/8/8/2B1KB2 w - - 0 1",
    },
    {
        "id": "pawn_promotion",
        "fen": "4k3/8/4K3/4P3/8/8/8/8 w - - 0 1",
    },
    {
        "id": "pawn_opposition",
        "fen": "8/8/8/4k3/8/8/4P3/4K3 w - - 0 1",
    },
    {
        "id": "queen_vs_rook",
        "fen": "3rk3/8/8/8/8/8/8/3QK3 w - - 0 1",
    },
    {
        "id": "queen_vs_pawn",
        "fen": "8/8/8/8/8/8/4p3/3QK1k1 w - - 0 1",
    },
]


def load_endgames():
    """Return the bundled endgames as ``{"id", "fen"}`` dicts."""
    return [dict(entry) for entry in ENDGAMES]
