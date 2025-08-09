#!/usr/bin/env python3

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


ALLOWED_OUTCOMES = {
    "1B", "2B", "3B", "HR", "BB", "HBP", "SF", "SH", "K", "OUT", "ROE", "FC",
}


def default_db() -> Dict[str, Any]:
    return {"games": [], "next_id": 1}


def load_db(file_path: str) -> Dict[str, Any]:
    if not os.path.exists(file_path):
        return default_db()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Error: could not parse JSON at {file_path}", file=sys.stderr)
        sys.exit(1)


def save_db(db: Dict[str, Any], file_path: str) -> None:
    tmp_path = file_path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, file_path)


def parse_outcomes(outcomes_str: str) -> List[str]:
    if not outcomes_str:
        return []
    outcomes = []
    for token in outcomes_str.split(","):
        t = token.strip().upper()
        if not t:
            continue
        if t not in ALLOWED_OUTCOMES:
            raise ValueError(f"Unknown outcome '{t}'. Allowed: {sorted(ALLOWED_OUTCOMES)}")
        outcomes.append(t)
    return outcomes


def compute_counts(outcomes: List[str]) -> Dict[str, int]:
    counts = {
        "pa": 0,
        "ab": 0,
        "h": 0,
        "single": 0,
        "double": 0,
        "triple": 0,
        "hr": 0,
        "bb": 0,
        "hbp": 0,
        "sf": 0,
        "sh": 0,
        "k": 0,
        "roe": 0,
        "fc": 0,
        "tb": 0,
        "outs_in_play": 0,
    }

    for oc in outcomes:
        counts["pa"] += 1
        if oc in {"1B", "2B", "3B", "HR", "K", "OUT", "ROE", "FC"}:  # counts as AB
            counts["ab"] += 1
        if oc == "1B":
            counts["h"] += 1
            counts["single"] += 1
            counts["tb"] += 1
        elif oc == "2B":
            counts["h"] += 1
            counts["double"] += 1
            counts["tb"] += 2
        elif oc == "3B":
            counts["h"] += 1
            counts["triple"] += 1
            counts["tb"] += 3
        elif oc == "HR":
            counts["h"] += 1
            counts["hr"] += 1
            counts["tb"] += 4
        elif oc == "BB":
            counts["bb"] += 1
        elif oc == "HBP":
            counts["hbp"] += 1
        elif oc == "SF":
            counts["sf"] += 1
        elif oc == "SH":
            counts["sh"] += 1
        elif oc == "K":
            counts["k"] += 1
        elif oc == "OUT":
            counts["outs_in_play"] += 1
        elif oc == "ROE":
            counts["roe"] += 1
        elif oc == "FC":
            counts["fc"] += 1

    return counts


def safe_div(numer: float, denom: float) -> float:
    return (numer / denom) if denom else 0.0


def compute_rate_stats(totals: Dict[str, int]) -> Dict[str, float]:
    ab = totals.get("ab", 0)
    h = totals.get("h", 0)
    bb = totals.get("bb", 0)
    hbp = totals.get("hbp", 0)
    sf = totals.get("sf", 0)
    tb = totals.get("tb", 0)

    ba = safe_div(h, ab)
    obp = safe_div(h + bb + hbp, ab + bb + hbp + sf)
    slg = safe_div(tb, ab)
    ops = obp + slg

    return {"ba": ba, "obp": obp, "slg": slg, "ops": ops}


def fmt_rate(x: float) -> str:
    return f"{x:.3f}".lstrip("0") if x < 1 else f"{x:.3f}"


def add_game(db_path: str, date: str, opponent: str, outcomes_str: str,
             runs: Optional[int], rbis: Optional[int], sb: Optional[int], cs: Optional[int], notes: Optional[str]) -> None:
    db = load_db(db_path)

    # Validate/parse date
    try:
        # allow YYYY-MM-DD only
        dt = datetime.strptime(date, "%Y-%m-%d")
        date_iso = dt.date().isoformat()
    except ValueError:
        print("Error: date must be YYYY-MM-DD", file=sys.stderr)
        sys.exit(1)

    try:
        outcomes = parse_outcomes(outcomes_str)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    game = {
        "id": db["next_id"],
        "date": date_iso,
        "opponent": opponent,
        "outcomes": outcomes,
        "r": runs if runs is not None else 0,
        "rbi": rbis if rbis is not None else 0,
        "sb": sb if sb is not None else 0,
        "cs": cs if cs is not None else 0,
        "notes": notes or "",
    }

    db["games"].append(game)
    db["next_id"] = int(db.get("next_id", 0)) + 1

    save_db(db, db_path)
    print(f"Added game #{game['id']} on {game['date']} vs {opponent} with {len(outcomes)} PA")


def remove_game(db_path: str, game_id: int) -> None:
    db = load_db(db_path)
    games = db.get("games", [])
    new_games = [g for g in games if int(g.get("id")) != game_id]
    if len(new_games) == len(games):
        print(f"No game with id {game_id} found", file=sys.stderr)
        sys.exit(1)
    db["games"] = new_games
    save_db(db, db_path)
    print(f"Removed game #{game_id}")


def list_games(db_path: str, year: Optional[int]) -> None:
    db = load_db(db_path)
    games: List[Dict[str, Any]] = db.get("games", [])
    if year is not None:
        games = [g for g in games if g.get("date", "").startswith(f"{year:04d}-")]

    if not games:
        print("No games found")
        return

    games_sorted = sorted(games, key=lambda g: g.get("date", ""))

    print("ID   Date        Opponent        PA  AB  R   H   RBI BB  K   HR  SB  CS  Line")
    print("-" * 90)
    for g in games_sorted:
        counts = compute_counts(g.get("outcomes", []))
        ab = counts["ab"]
        h = counts["h"]
        hr = counts["hr"]
        bb = counts["bb"]
        k = counts["k"]
        pa = counts["pa"]
        line = f"{ab}-{h}{' HR:' + str(hr) if hr else ''}{' BB:' + str(bb) if bb else ''}{' K:' + str(k) if k else ''}"
        print(
            f"{int(g['id']):<4} {g['date']:<10}  {g['opponent']:<14}  {pa:<2}  {ab:<2}  {int(g['r']):<2}  {h:<2}  {int(g['rbi']):<3} {bb:<2} {k:<2} {hr:<2} {int(g['sb']):<2} {int(g['cs']):<2} {line}"
        )


def aggregate_totals(games: List[Dict[str, Any]]) -> Dict[str, int]:
    totals: Dict[str, int] = {
        "pa": 0, "ab": 0, "h": 0, "single": 0, "double": 0, "triple": 0, "hr": 0,
        "bb": 0, "hbp": 0, "sf": 0, "sh": 0, "k": 0, "roe": 0, "fc": 0, "tb": 0,
        "r": 0, "rbi": 0, "sb": 0, "cs": 0,
    }
    for g in games:
        c = compute_counts(g.get("outcomes", []))
        for key in ("pa", "ab", "h", "single", "double", "triple", "hr", "bb", "hbp", "sf", "sh", "k", "roe", "fc", "tb"):
            totals[key] += c[key]
        totals["r"] += int(g.get("r", 0))
        totals["rbi"] += int(g.get("rbi", 0))
        totals["sb"] += int(g.get("sb", 0))
        totals["cs"] += int(g.get("cs", 0))
    return totals


def show_totals(db_path: str, year: Optional[int]) -> None:
    db = load_db(db_path)
    games: List[Dict[str, Any]] = db.get("games", [])
    if year is not None:
        games = [g for g in games if g.get("date", "").startswith(f"{year:04d}-")]

    if not games:
        print("No games found")
        return

    totals = aggregate_totals(games)
    rates = compute_rate_stats(totals)

    print("Totals")
    print("-" * 32)
    print(f"G: {len(games)}  PA: {totals['pa']}  AB: {totals['ab']}  R: {totals['r']}  H: {totals['h']}  RBI: {totals['rbi']}")
    print(f"1B: {totals['single']}  2B: {totals['double']}  3B: {totals['triple']}  HR: {totals['hr']}")
    print(f"BB: {totals['bb']}  HBP: {totals['hbp']}  SF: {totals['sf']}  SH: {totals['sh']}")
    print(f"K: {totals['k']}  ROE: {totals['roe']}  FC: {totals['fc']}  TB: {totals['tb']}  SB: {totals['sb']}  CS: {totals['cs']}")

    print("")
    print("Slash Line")
    print("-" * 32)
    print(f"BA: {fmt_rate(rates['ba'])}  OBP: {fmt_rate(rates['obp'])}  SLG: {fmt_rate(rates['slg'])}  OPS: {fmt_rate(rates['ops'])}")


def reset_db(db_path: str, yes: bool) -> None:
    if not yes:
        print("Refusing to reset without --yes")
        sys.exit(1)
    save_db(default_db(), db_path)
    print(f"Reset database at {db_path}")


def get_default_db_path() -> str:
    # Default to stats.json in current working directory
    return os.path.join(os.getcwd(), "stats.json")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Personal baseball stats tracker (JSON-based)")
    parser.add_argument("--file", dest="file", default=get_default_db_path(), help="Path to stats JSON file (default: ./stats.json)")

    sub = parser.add_subparsers(dest="cmd", required=True)

    add_p = sub.add_parser("add", help="Add a game from plate appearance outcomes")
    add_p.add_argument("--date", required=True, help="Date YYYY-MM-DD")
    add_p.add_argument("--opponent", required=True, help="Opponent/team name")
    add_p.add_argument("--pa", required=True, help="Comma-separated outcomes, e.g. '1B,OUT,BB,HR,K'")
    add_p.add_argument("--r", type=int, default=0, help="Runs scored in the game")
    add_p.add_argument("--rbi", type=int, default=0, help="RBIs in the game")
    add_p.add_argument("--sb", type=int, default=0, help="Stolen bases in the game")
    add_p.add_argument("--cs", type=int, default=0, help="Caught stealing in the game")
    add_p.add_argument("--notes", default="", help="Freeform notes")

    list_p = sub.add_parser("games", help="List games (optionally filter by --year)")
    list_p.add_argument("--year", type=int, help="Year filter, e.g. 2025")

    tot_p = sub.add_parser("totals", help="Show aggregated totals and slash line")
    tot_p.add_argument("--year", type=int, help="Year filter, e.g. 2025")

    rm_p = sub.add_parser("remove", help="Remove a game by ID")
    rm_p.add_argument("id", type=int, help="Game ID to remove")

    reset_p = sub.add_parser("reset", help="Erase all data and reinitialize the database")
    reset_p.add_argument("--yes", action="store_true", help="Confirm reset")

    args = parser.parse_args(argv)

    db_path = os.path.abspath(args.file)
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

    if args.cmd == "add":
        add_game(
            db_path=db_path,
            date=args.date,
            opponent=args.opponent,
            outcomes_str=args.pa,
            runs=args.r,
            rbis=args.rbi,
            sb=args.sb,
            cs=args.cs,
            notes=args.notes,
        )
        return 0
    elif args.cmd == "games":
        list_games(db_path=db_path, year=args.year)
        return 0
    elif args.cmd == "totals":
        show_totals(db_path=db_path, year=args.year)
        return 0
    elif args.cmd == "remove":
        remove_game(db_path=db_path, game_id=args.id)
        return 0
    elif args.cmd == "reset":
        reset_db(db_path=db_path, yes=args.yes)
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())