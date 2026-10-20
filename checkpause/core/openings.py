import os

import chess
import chess.pgn

from checkpause.resources import resource_path

OPENINGS_FILE_PARTS = ("assets", "openings.pgn")

OPENING_CATEGORY_ORDER = ("open", "semi_open", "closed", "flank", "other")

OPENING_FAMILY_CATEGORY = {
    "Italian Game": "open",
    "Ruy Lopez": "open",
    "Scotch Game": "open",
    "Petrov Defense": "open",
    "Philidor Defense": "open",
    "Four Knights Game": "open",
    "Bishop's Opening": "open",
    "Vienna Game": "open",
    "King's Gambit Accepted": "open",
    "Sicilian Defense": "semi_open",
    "French Defense": "semi_open",
    "Caro-Kann Defense": "semi_open",
    "Scandinavian Defense": "semi_open",
    "Alekhine Defense": "semi_open",
    "Pirc Defense": "semi_open",
    "Modern Defense": "semi_open",
    "Queen's Gambit Declined": "closed",
    "Slav Defense": "closed",
    "Semi-Slav Defense": "closed",
    "Queen's Gambit Accepted": "closed",
    "Catalan Opening": "closed",
    "Nimzo-Indian Defense": "closed",
    "Queen's Indian Defense": "closed",
    "Bogo-Indian Defense": "closed",
    "King's Indian Defense": "closed",
    "Grunfeld Defense": "closed",
    "Modern Benoni": "closed",
    "Benko Gambit": "closed",
    "Dutch Defense": "closed",
    "London System": "closed",
    "Trompowsky Attack": "closed",
    "English Opening": "flank",
    "Reti Opening": "flank",
    "King's Indian Attack": "flank",
    "Bird Opening": "flank",
}

OPENING_FAMILY_NAMES_ZH = {
    "Italian Game": "意大利开局",
    "Ruy Lopez": "西班牙开局",
    "Scotch Game": "苏格兰开局",
    "Petrov Defense": "彼得罗夫防御",
    "Philidor Defense": "菲利多尔防御",
    "Four Knights Game": "四马开局",
    "Bishop's Opening": "飞象开局",
    "Vienna Game": "维也纳开局",
    "King's Gambit Accepted": "王翼弃兵接受",
    "Sicilian Defense": "西西里防御",
    "French Defense": "法兰西防御",
    "Caro-Kann Defense": "卡罗-卡恩防御",
    "Scandinavian Defense": "斯堪的纳维亚防御",
    "Alekhine Defense": "阿廖欣防御",
    "Pirc Defense": "皮尔茨防御",
    "Modern Defense": "现代防御",
    "Queen's Gambit Declined": "后翼弃兵拒绝",
    "Slav Defense": "斯拉夫防御",
    "Semi-Slav Defense": "半斯拉夫防御",
    "Queen's Gambit Accepted": "后翼弃兵接受",
    "Catalan Opening": "加泰罗尼亚开局",
    "Nimzo-Indian Defense": "尼姆佐-印度防御",
    "Queen's Indian Defense": "后翼印度防御",
    "Bogo-Indian Defense": "博戈-印度防御",
    "King's Indian Defense": "王翼印度防御",
    "Grunfeld Defense": "格林菲尔德防御",
    "Modern Benoni": "现代别诺尼",
    "Benko Gambit": "本柯弃兵",
    "Dutch Defense": "荷兰防御",
    "London System": "伦敦体系",
    "Trompowsky Attack": "特龙波夫斯基攻击",
    "English Opening": "英国式开局",
    "Reti Opening": "列蒂开局",
    "King's Indian Attack": "王翼印度攻击",
    "Bird Opening": "伯德开局",
}

OPENING_NAMES_ZH = {
    "Italian Game: Giuoco Piano": "意大利开局：平静变例",
    "Italian Game: Two Knights Defense": "意大利开局：双马防御",
    "Ruy Lopez: Morphy Defense": "西班牙开局：莫菲防御",
    "Ruy Lopez: Berlin Defense": "西班牙开局：柏林防御",
    "Ruy Lopez: Exchange Variation": "西班牙开局：交换变例",
    "Scotch Game: Classical": "苏格兰开局：古典变例",
    "Scotch Game: Mieses": "苏格兰开局：米泽斯变例",
    "Petrov Defense": "彼得罗夫防御",
    "Philidor Defense": "菲利多尔防御",
    "Four Knights Game": "四马开局",
    "Bishop's Opening": "飞象开局",
    "Vienna Game": "维也纳开局",
    "King's Gambit Accepted": "王翼弃兵接受",
    "Sicilian Defense: Najdorf": "西西里防御：纳伊多夫变例",
    "Sicilian Defense: Dragon": "西西里防御：龙式变例",
    "Sicilian Defense: Classical": "西西里防御：古典变例",
    "Sicilian Defense: Sveshnikov": "西西里防御：斯维什尼科夫变例",
    "Sicilian Defense: Taimanov": "西西里防御：泰曼诺夫变例",
    "Sicilian Defense: Accelerated Dragon": "西西里防御：加速龙式",
    "Sicilian Defense: Alapin": "西西里防御：阿拉平变例",
    "French Defense: Winawer": "法兰西防御：维纳维尔变例",
    "French Defense: Classical": "法兰西防御：古典变例",
    "French Defense: Tarrasch": "法兰西防御：塔拉什变例",
    "French Defense: Advance": "法兰西防御：前进变例",
    "Caro-Kann Defense: Advance": "卡罗-卡恩防御：前进变例",
    "Caro-Kann Defense: Classical": "卡罗-卡恩防御：古典变例",
    "Caro-Kann Defense: Panov Attack": "卡罗-卡恩防御：帕诺夫攻击",
    "Scandinavian Defense": "斯堪的纳维亚防御",
    "Alekhine Defense": "阿廖欣防御",
    "Pirc Defense": "皮尔茨防御",
    "Modern Defense": "现代防御",
    "Queen's Gambit Declined": "后翼弃兵拒绝",
    "Queen's Gambit Declined: Exchange": "后翼弃兵拒绝：交换变例",
    "Slav Defense": "斯拉夫防御",
    "Semi-Slav Defense: Meran": "半斯拉夫防御：梅兰变例",
    "Queen's Gambit Accepted": "后翼弃兵接受",
    "Catalan Opening": "加泰罗尼亚开局",
    "Nimzo-Indian Defense": "尼姆佐-印度防御",
    "Queen's Indian Defense": "后翼印度防御",
    "Bogo-Indian Defense": "博戈-印度防御",
    "King's Indian Defense: Classical": "王翼印度防御：古典变例",
    "King's Indian Defense: Fianchetto": "王翼印度防御：侧翼象变例",
    "Grunfeld Defense": "格林菲尔德防御",
    "Modern Benoni": "现代别诺尼",
    "Benko Gambit": "本柯弃兵",
    "Dutch Defense": "荷兰防御",
    "London System": "伦敦体系",
    "Trompowsky Attack": "特龙波夫斯基攻击",
    "English Opening": "英国式开局",
    "English Opening: Symmetrical": "英国式开局：对称变例",
    "Reti Opening": "列蒂开局",
    "King's Indian Attack": "王翼印度攻击",
    "Bird Opening": "伯德开局",
}


def _openings_path():
    path = resource_path(*OPENINGS_FILE_PARTS)
    if os.path.isfile(path):
        return path
    return None


def _opening_meta(name):
    family, _, variation = name.partition(":")
    family = family.strip()
    variation = variation.strip()
    category = OPENING_FAMILY_CATEGORY.get(family, "other")
    family_zh = OPENING_FAMILY_NAMES_ZH.get(family, family)
    name_zh = OPENING_NAMES_ZH.get(name, name)
    if "：" in name_zh:
        variation_zh = name_zh.split("：", 1)[1]
    elif name_zh != family_zh:
        variation_zh = name_zh
    else:
        variation_zh = ""
    return {
        "category": category,
        "family": family,
        "family_zh": family_zh,
        "variation": variation,
        "variation_zh": variation_zh,
        "name_zh": name_zh,
    }


def load_openings(path=None):
    """Return the bundled opening lines as ``{"name", "moves"}`` dicts.

    ``moves`` is a list of legal ``chess.Move`` objects leading from the
    starting position. Unreadable or illegal lines are skipped.
    """
    path = path or _openings_path()
    if not path or not os.path.isfile(path):
        return []

    openings = []
    with open(path, encoding="utf-8", errors="replace") as handle:
        while True:
            try:
                game = chess.pgn.read_game(handle)
            except Exception:
                break
            if game is None:
                break
            moves = _legal_moves(game.mainline_moves())
            if not moves:
                continue
            name = game.headers.get("Opening") or f"Opening {len(openings) + 1}"
            opening = {"name": name, "moves": moves}
            opening.update(_opening_meta(name))
            openings.append(opening)
    return openings


def _legal_moves(moves):
    board = chess.Board()
    legal = []
    for move in moves:
        if move not in board.legal_moves:
            return []
        board.push(move)
        legal.append(move)
    return legal


def opening_display_name(opening, language):
    """The localized opening name for menus and summaries."""
    if language == "en-US":
        return opening["name"]
    return opening.get("name_zh") or opening["name"]


def opening_san(opening):
    """The mainline in algebraic notation, e.g. ``1. e4 e5 2. Nf3``."""
    moves = opening.get("moves") or ()
    if not moves:
        return ""
    return chess.Board().variation_san(moves)
