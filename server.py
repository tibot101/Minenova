from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import os
import random
import re
import secrets
import sqlite3
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import jwt
import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent
VOLUME_ROOT = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH")
DEFAULT_DB_PATH = (Path(VOLUME_ROOT) / "minenova.db") if VOLUME_ROOT else (ROOT / "minenova.db")
DB_PATH = Path(os.environ.get("MINENOVA_DB", DEFAULT_DB_PATH))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
SECRET = os.environ.get("MINENOVA_SECRET", "minenova-dev-secret-change-this-before-public-deploy")
TOKEN_DAYS = 30
PBKDF2_ITERS = 240_000
LEVELS = {
    "beginner": {"w": 9, "h": 9, "m": 10},
    "intermediate": {"w": 16, "h": 16, "m": 40},
    "expert": {"w": 30, "h": 16, "m": 99},
}
USERNAME_RE = re.compile(r"^[A-Za-z0-9_-]{3,20}$")
RANKED_MODES = tuple(LEVELS)
LIVE_TTL_SECONDS = 35.0
QUEUE_TTL_SECONDS = 90.0
logger = logging.getLogger("minenova")

@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="MineNova Server", version="4.0", lifespan=lifespan)


def db() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    return con


def init_db() -> None:
    with db() as con:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                rating INTEGER NOT NULL DEFAULT 1000,
                wins INTEGER NOT NULL DEFAULT 0,
                losses INTEGER NOT NULL DEFAULT 0,
                matches INTEGER NOT NULL DEFAULT 0,
                streak INTEGER NOT NULL DEFAULT 0,
                best_streak INTEGER NOT NULL DEFAULT 0,
                progress_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                last_seen TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS match_history (
                id TEXT PRIMARY KEY,
                player1_id INTEGER NOT NULL,
                player2_id INTEGER NOT NULL,
                winner_id INTEGER,
                reason TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                duration_ms INTEGER NOT NULL,
                p1_rating_before INTEGER NOT NULL,
                p1_rating_after INTEGER NOT NULL,
                p2_rating_before INTEGER NOT NULL,
                p2_rating_after INTEGER NOT NULL,
                played_at TEXT NOT NULL,
                FOREIGN KEY(player1_id) REFERENCES users(id),
                FOREIGN KEY(player2_id) REFERENCES users(id),
                FOREIGN KEY(winner_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS mode_ratings (
                user_id INTEGER NOT NULL,
                mode TEXT NOT NULL,
                rating INTEGER NOT NULL DEFAULT 1000,
                wins INTEGER NOT NULL DEFAULT 0,
                losses INTEGER NOT NULL DEFAULT 0,
                matches INTEGER NOT NULL DEFAULT 0,
                streak INTEGER NOT NULL DEFAULT 0,
                best_streak INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(user_id, mode),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_users_rating ON users(rating DESC, wins DESC);
            CREATE INDEX IF NOT EXISTS idx_mode_ratings ON mode_ratings(mode, rating DESC, wins DESC);
            CREATE INDEX IF NOT EXISTS idx_history_p1 ON match_history(player1_id, played_at DESC);
            CREATE INDEX IF NOT EXISTS idx_history_p2 ON match_history(player2_id, played_at DESC);
            """
        )


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERS)
    return "pbkdf2_sha256$%d$%s$%s" % (
        PBKDF2_ITERS,
        base64.urlsafe_b64encode(salt).decode(),
        base64.urlsafe_b64encode(digest).decode(),
    )


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iter_s, salt_s, digest_s = stored.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        salt = base64.urlsafe_b64decode(salt_s.encode())
        expected = base64.urlsafe_b64decode(digest_s.encode())
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(iter_s))
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def create_token(user_id: int, username: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": str(user_id), "username": username, "iat": now, "exp": now + timedelta(days=TOKEN_DAYS)}
    return jwt.encode(payload, SECRET, algorithm="HS256")


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, SECRET, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired session") from exc


def get_user_by_id(user_id: int) -> sqlite3.Row | None:
    with db() as con:
        return con.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()


def tier_for(rating: int) -> str:
    if rating < 900:
        return "Bronze"
    if rating < 1050:
        return "Silver"
    if rating < 1200:
        return "Gold"
    if rating < 1400:
        return "Platinum"
    if rating < 1600:
        return "Diamond"
    return "Nova"


def get_mode_ratings(user_id: int) -> dict[str, dict[str, int | str]]:
    result: dict[str, dict[str, int | str]] = {}
    with db() as con:
        for mode in RANKED_MODES:
            con.execute("INSERT OR IGNORE INTO mode_ratings(user_id,mode) VALUES(?,?)", (user_id, mode))
        rows = con.execute("SELECT * FROM mode_ratings WHERE user_id=?", (user_id,)).fetchall()
    by_mode = {r["mode"]: r for r in rows}
    for mode in RANKED_MODES:
        r = by_mode.get(mode)
        rating = int(r["rating"]) if r else 1000
        result[mode] = {
            "rating": rating,
            "tier": tier_for(rating),
            "wins": int(r["wins"]) if r else 0,
            "losses": int(r["losses"]) if r else 0,
            "matches": int(r["matches"]) if r else 0,
            "streak": int(r["streak"]) if r else 0,
            "bestStreak": int(r["best_streak"]) if r else 0,
        }
    return result


def public_user(row: sqlite3.Row, include_progress: bool = False) -> dict[str, Any]:
    out = {
        "id": row["id"],
        "username": row["username"],
        "rating": row["rating"],
        "tier": tier_for(row["rating"]),
        "wins": row["wins"],
        "losses": row["losses"],
        "matches": row["matches"],
        "streak": row["streak"],
        "bestStreak": row["best_streak"],
    }
    if include_progress:
        try:
            out["progress"] = json.loads(row["progress_json"] or "{}")
        except Exception:
            out["progress"] = {}
        out["modeRatings"] = get_mode_ratings(int(row["id"]))
    return out


def public_user_for_mode(row: sqlite3.Row, mode: str) -> dict[str, Any]:
    out = public_user(row)
    ranked = get_mode_ratings(int(row["id"])).get(mode, {})
    out["overallRating"] = out["rating"]
    out["overallTier"] = out["tier"]
    out["rating"] = int(ranked.get("rating", 1000))
    out["tier"] = str(ranked.get("tier", tier_for(out["rating"])))
    out["modeWins"] = int(ranked.get("wins", 0))
    out["modeLosses"] = int(ranked.get("losses", 0))
    out["modeMatches"] = int(ranked.get("matches", 0))
    return out


async def auth_user(authorization: str | None = Header(default=None)) -> sqlite3.Row:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Sign in required")
    payload = decode_token(authorization.split(" ", 1)[1].strip())
    row = get_user_by_id(int(payload["sub"]))
    if not row:
        raise HTTPException(status_code=401, detail="Account not found")
    return row


class AuthPayload(BaseModel):
    username: str
    password: str


class ProgressPayload(BaseModel):
    progress: dict[str, Any]


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(ROOT / "index.html", headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/health")
async def health() -> dict[str, Any]:
    clean_stale_queues()
    return {"ok": True, "online": live_count(), "queued": sum(len(v) for v in waiting.values()), "version": app.version}


@app.post("/api/register")
async def register(body: AuthPayload) -> dict[str, Any]:
    username = body.username.strip()
    if not USERNAME_RE.fullmatch(username):
        raise HTTPException(status_code=400, detail="Username must be 3–20 characters using letters, numbers, _ or -")
    if len(body.password) < 8 or len(body.password) > 128:
        raise HTTPException(status_code=400, detail="Password must be 8–128 characters")
    now = utc_now()
    try:
        with db() as con:
            cur = con.execute(
                "INSERT INTO users(username,password_hash,created_at,last_seen) VALUES(?,?,?,?)",
                (username, hash_password(body.password), now, now),
            )
            user_id = cur.lastrowid
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="That username is already taken") from exc
    row = get_user_by_id(int(user_id))
    assert row is not None
    return {"token": create_token(row["id"], row["username"]), "user": public_user(row, True)}


@app.post("/api/login")
async def login(body: AuthPayload) -> dict[str, Any]:
    with db() as con:
        row = con.execute("SELECT * FROM users WHERE username=? COLLATE NOCASE", (body.username.strip(),)).fetchone()
        if not row or not verify_password(body.password, row["password_hash"]):
            raise HTTPException(status_code=401, detail="Incorrect username or password")
        con.execute("UPDATE users SET last_seen=? WHERE id=?", (utc_now(), row["id"]))
    return {"token": create_token(row["id"], row["username"]), "user": public_user(row, True)}


@app.get("/api/me")
async def me(user: sqlite3.Row = Depends(auth_user)) -> dict[str, Any]:
    fresh = get_user_by_id(user["id"])
    assert fresh is not None
    return {"user": public_user(fresh, True)}


@app.post("/api/progress")
async def save_progress(body: ProgressPayload, user: sqlite3.Row = Depends(auth_user)) -> dict[str, Any]:
    raw = json.dumps(body.progress, separators=(",", ":"))
    if len(raw) > 30_000:
        raise HTTPException(status_code=413, detail="Progress payload too large")
    with db() as con:
        con.execute("UPDATE users SET progress_json=?, last_seen=? WHERE id=?", (raw, utc_now(), user["id"]))
    return {"ok": True}


@app.get("/api/leaderboard")
async def leaderboard(limit: int = 50, mode: str = "overall") -> dict[str, Any]:
    limit = max(1, min(100, limit))
    mode = mode.lower().strip()
    if mode == "overall":
        with db() as con:
            rows = con.execute(
                "SELECT * FROM users ORDER BY rating DESC, wins DESC, matches ASC, id ASC LIMIT ?", (limit,)
            ).fetchall()
        return {"mode": mode, "players": [{"rank": i + 1, **public_user(row)} for i, row in enumerate(rows)]}
    if mode not in RANKED_MODES:
        raise HTTPException(status_code=400, detail="Unknown ranked mode")
    with db() as con:
        con.execute(
            "INSERT OR IGNORE INTO mode_ratings(user_id,mode) SELECT id, ? FROM users",
            (mode,),
        )
        rows = con.execute(
            """
            SELECT u.id, u.username, mr.rating, mr.wins, mr.losses, mr.matches, mr.streak, mr.best_streak
            FROM mode_ratings mr
            JOIN users u ON u.id=mr.user_id
            WHERE mr.mode=? AND mr.matches>0
            ORDER BY mr.rating DESC, mr.wins DESC, mr.matches ASC, u.id ASC
            LIMIT ?
            """,
            (mode, limit),
        ).fetchall()
    players = []
    for i, row in enumerate(rows):
        players.append({
            "rank": i + 1,
            "id": row["id"],
            "username": row["username"],
            "rating": row["rating"],
            "tier": tier_for(int(row["rating"])),
            "wins": row["wins"],
            "losses": row["losses"],
            "matches": row["matches"],
            "streak": row["streak"],
            "bestStreak": row["best_streak"],
        })
    return {"mode": mode, "players": players}


@app.get("/api/matches")
async def match_history(user: sqlite3.Row = Depends(auth_user), limit: int = 20) -> dict[str, Any]:
    limit = max(1, min(50, limit))
    uid = user["id"]
    with db() as con:
        rows = con.execute(
            """
            SELECT h.*, u1.username AS p1_name, u2.username AS p2_name
            FROM match_history h
            JOIN users u1 ON u1.id=h.player1_id
            JOIN users u2 ON u2.id=h.player2_id
            WHERE h.player1_id=? OR h.player2_id=?
            ORDER BY h.played_at DESC LIMIT ?
            """,
            (uid, uid, limit),
        ).fetchall()
    out = []
    for r in rows:
        me_p1 = r["player1_id"] == uid
        opponent = r["p2_name"] if me_p1 else r["p1_name"]
        before = r["p1_rating_before"] if me_p1 else r["p2_rating_before"]
        after = r["p1_rating_after"] if me_p1 else r["p2_rating_after"]
        result = "draw" if r["winner_id"] is None else ("win" if r["winner_id"] == uid else "loss")
        out.append({
            "id": r["id"], "opponent": opponent, "result": result, "difficulty": r["difficulty"],
            "reason": r["reason"], "durationMs": r["duration_ms"], "ratingDelta": after - before,
            "playedAt": r["played_at"],
        })
    return {"matches": out}


@app.get("/api/status")
async def status() -> dict[str, Any]:
    clean_stale_queues()
    return {
        "online": live_count(),
        "queued": sum(len(v) for v in waiting.values()),
        "activeMatches": sum(1 for m in matches.values() if not m.ended),
        "queues": {k: len(v) for k, v in waiting.items()},
        "version": app.version,
    }


def neighbor_indices(w: int, h: int, index: int) -> list[int]:
    x, y = index % w, index // w
    out: list[int] = []
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h:
                out.append(ny * w + nx)
    return out


def make_layout(conf: dict[str, int], opening: int, seed: int) -> tuple[set[int], list[int]]:
    w, h, m = conf["w"], conf["h"], conf["m"]
    safe = {opening, *neighbor_indices(w, h, opening)}
    pool = [i for i in range(w * h) if i not in safe]
    if len(pool) < m:
        safe = {opening}
        pool = [i for i in range(w * h) if i != opening]
    rng = random.Random(seed)
    rng.shuffle(pool)
    mines = set(pool[:m])
    numbers = [0] * (w * h)
    for i in range(w * h):
        if i not in mines:
            numbers[i] = sum(1 for n in neighbor_indices(w, h, i) if n in mines)
    return mines, numbers


@dataclass
class PlayerState:
    user_id: int
    revealed: set[int] = field(default_factory=set)
    flags: set[int] = field(default_factory=set)
    hits: set[int] = field(default_factory=set)
    lives: int = 2
    score: int = 0
    chords: int = 0
    finished: bool = False
    eliminated: bool = False


@dataclass
class Match:
    id: str
    players: tuple[int, int]
    difficulty: str
    conf: dict[str, int]
    seed: int
    opening: int
    mines: set[int]
    numbers: list[int]
    states: dict[int, PlayerState]
    started_at: float
    ended: bool = False
    winner_id: int | None = None
    reason: str = ""
    result_meta: dict[int, dict[str, int]] = field(default_factory=dict)
    rematch_requests: set[int] = field(default_factory=set)


sockets: dict[int, WebSocket] = {}
waiting: dict[str, list[int]] = {k: [] for k in LEVELS}
matches: dict[str, Match] = {}
active_match_by_user: dict[int, str] = {}
recent_match_by_user: dict[int, str] = {}
disconnect_tasks: dict[int, asyncio.Task] = {}
live_seen: dict[int, float] = {}
queued_at: dict[int, float] = {}
state_lock = asyncio.Lock()


def touch_live(uid: int) -> None:
    live_seen[uid] = time.monotonic()


def is_live(uid: int, ttl: float = LIVE_TTL_SECONDS) -> bool:
    if uid in sockets:
        return True
    return time.monotonic() - live_seen.get(uid, 0.0) <= ttl


def queue_for(uid: int) -> str | None:
    for difficulty, q in waiting.items():
        if uid in q:
            return difficulty
    return None


def clean_stale_queues() -> None:
    now = time.monotonic()
    for q in waiting.values():
        q[:] = [uid for uid in q if now - queued_at.get(uid, 0.0) <= QUEUE_TTL_SECONDS and is_live(uid, QUEUE_TTL_SECONDS)]


def live_count() -> int:
    now = time.monotonic()
    ids = set(sockets) | {uid for uid, seen in live_seen.items() if now - seen <= LIVE_TTL_SECONDS}
    return len(ids)


def flood(match: Match, state: PlayerState, start: int) -> list[int]:
    if start in match.mines or start in state.flags:
        return []
    q = [start]
    opened: list[int] = []
    seen: set[int] = set()
    while q:
        i = q.pop()
        if i in seen:
            continue
        seen.add(i)
        if i in state.revealed or i in state.flags or i in match.mines:
            continue
        state.revealed.add(i)
        opened.append(i)
        if match.numbers[i] == 0:
            q.extend(neighbor_indices(match.conf["w"], match.conf["h"], i))
    return opened


def mine_hit(match: Match, state: PlayerState, index: int) -> None:
    if index in state.hits:
        return
    state.hits.add(index)
    state.flags.add(index)
    state.lives -= 1
    state.score = max(0, state.score - 75)
    if state.lives <= 0:
        state.finished = True
        state.eliminated = True


def process_action(match: Match, state: PlayerState, action: str, index: int) -> None:
    total = match.conf["w"] * match.conf["h"]
    if match.ended or state.finished or not 0 <= index < total:
        return
    if action == "flag":
        if index in state.revealed:
            return
        if index in state.flags:
            state.flags.remove(index)
            state.hits.discard(index)
        elif len(state.flags) < match.conf["m"]:
            state.flags.add(index)
    elif action == "reveal":
        if index in state.revealed or index in state.flags:
            return
        if index in match.mines:
            mine_hit(match, state, index)
        else:
            opened = flood(match, state, index)
            state.score += 10 * len(opened)
    elif action == "chord":
        if index not in state.revealed or match.numbers[index] <= 0:
            return
        ns = neighbor_indices(match.conf["w"], match.conf["h"], index)
        if sum(1 for n in ns if n in state.flags) != match.numbers[index]:
            return
        hidden = [n for n in ns if n not in state.revealed and n not in state.flags]
        if not hidden:
            return
        state.chords += 1
        opened_all: set[int] = set()
        for n in hidden:
            if n in match.mines:
                mine_hit(match, state, n)
                if state.eliminated:
                    break
            else:
                opened_all.update(flood(match, state, n))
        state.score += len(opened_all) * 14 + 25
    safe_total = total - match.conf["m"]
    if len(state.revealed) >= safe_total:
        state.finished = True


def board_snapshot(match: Match, state: PlayerState) -> dict[str, Any]:
    revealed = [[i, match.numbers[i]] for i in sorted(state.revealed)]
    elapsed_ms = max(0, int((time.monotonic() - match.started_at) * 1000))
    safe_total = match.conf["w"] * match.conf["h"] - match.conf["m"]
    return {
        "revealed": revealed,
        "flags": sorted(state.flags),
        "hits": sorted(state.hits),
        "lives": state.lives,
        "score": state.score,
        "chords": state.chords,
        "safeOpened": len(state.revealed),
        "safeTotal": safe_total,
        "finished": state.finished,
        "eliminated": state.eliminated,
        "elapsedMs": elapsed_ms,
    }


def summary_snapshot(match: Match, state: PlayerState) -> dict[str, Any]:
    safe_total = match.conf["w"] * match.conf["h"] - match.conf["m"]
    return {
        "safeOpened": len(state.revealed),
        "safeTotal": safe_total,
        "lives": state.lives,
        "score": state.score,
        "chords": state.chords,
        "finished": state.finished,
        "eliminated": state.eliminated,
        "connected": state.user_id in sockets,
    }


def other_user(match: Match, uid: int) -> int:
    return match.players[1] if match.players[0] == uid else match.players[0]


async def send_json(uid: int, data: dict[str, Any]) -> None:
    ws = sockets.get(uid)
    if not ws:
        return
    try:
        await ws.send_json(data)
    except Exception:
        pass


def match_payload(match: Match, uid: int) -> dict[str, Any]:
    state = match.states[uid]
    oid = other_user(match, uid)
    opponent_row = get_user_by_id(oid)
    return {
        "id": match.id,
        "fieldCode": match.id.split("-")[0].upper(),
        "difficulty": match.difficulty,
        "conf": match.conf,
        "opening": match.opening,
        "player": 1 if match.players[0] == uid else 2,
        "opponent": public_user_for_mode(opponent_row, match.difficulty) if opponent_row else {"id": oid, "username": "Opponent", "rating": 1000, "tier": "Silver"},
        "me": board_snapshot(match, state),
        "opponentState": summary_snapshot(match, match.states[oid]),
        "ended": match.ended,
        "winnerId": match.winner_id,
        "reason": match.reason,
        "result": match.result_meta.get(uid),
    }


async def send_sync(match: Match, uid: int, event_type: str = "match_sync") -> None:
    await send_json(uid, {"type": event_type, "match": match_payload(match, uid)})


async def sync_both(match: Match) -> None:
    await asyncio.gather(*(send_sync(match, uid) for uid in match.players))


def initial_reveal(match: Match, state: PlayerState) -> None:
    opened = flood(match, state, match.opening)
    state.score += len(opened) * 10


async def create_match(uid1: int, uid2: int, difficulty: str, event_type: str = "match_found") -> Match:
    conf = dict(LEVELS[difficulty])
    opening = (conf["h"] // 2) * conf["w"] + conf["w"] // 2
    seed = secrets.randbits(63)
    mines, numbers = make_layout(conf, opening, seed)
    mid = str(uuid.uuid4())
    states = {uid1: PlayerState(uid1), uid2: PlayerState(uid2)}
    match = Match(mid, (uid1, uid2), difficulty, conf, seed, opening, mines, numbers, states, time.monotonic())
    for st in states.values():
        initial_reveal(match, st)
    matches[mid] = match
    active_match_by_user[uid1] = mid
    active_match_by_user[uid2] = mid
    recent_match_by_user.pop(uid1, None)
    recent_match_by_user.pop(uid2, None)
    await asyncio.gather(send_sync(match, uid1, event_type), send_sync(match, uid2, event_type))
    return match


def _elo_pair(r1: int, r2: int, winner_id: int | None, uid1: int, uid2: int) -> tuple[int, int, float, float]:
    e1 = 1 / (1 + 10 ** ((r2 - r1) / 400))
    e2 = 1 - e1
    if winner_id is None:
        s1 = s2 = 0.5
    else:
        s1, s2 = (1.0, 0.0) if winner_id == uid1 else (0.0, 1.0)
    k = 32
    return max(100, round(r1 + k * (s1 - e1))), max(100, round(r2 + k * (s2 - e2))), s1, s2


def update_ratings(match: Match, winner_id: int | None) -> None:
    uid1, uid2 = match.players
    mode = match.difficulty
    with db() as con:
        u1 = con.execute("SELECT * FROM users WHERE id=?", (uid1,)).fetchone()
        u2 = con.execute("SELECT * FROM users WHERE id=?", (uid2,)).fetchone()
        if not u1 or not u2:
            return

        # Overall rating remains as the all-modes career rating.
        gr1, gr2 = int(u1["rating"]), int(u2["rating"])
        gn1, gn2, s1, s2 = _elo_pair(gr1, gr2, winner_id, uid1, uid2)
        for row, uid, new_rating, score in ((u1, uid1, gn1, s1), (u2, uid2, gn2, s2)):
            wins = row["wins"] + (1 if score == 1 else 0)
            losses = row["losses"] + (1 if score == 0 else 0)
            streak = row["streak"] + 1 if score == 1 else (0 if score == 0 else row["streak"])
            best = max(row["best_streak"], streak)
            con.execute(
                "UPDATE users SET rating=?, wins=?, losses=?, matches=matches+1, streak=?, best_streak=?, last_seen=? WHERE id=?",
                (new_rating, wins, losses, streak, best, utc_now(), uid),
            )

        # Each ranked board size gets an independent ladder/rating.
        for uid in (uid1, uid2):
            con.execute("INSERT OR IGNORE INTO mode_ratings(user_id,mode) VALUES(?,?)", (uid, mode))
        m1 = con.execute("SELECT * FROM mode_ratings WHERE user_id=? AND mode=?", (uid1, mode)).fetchone()
        m2 = con.execute("SELECT * FROM mode_ratings WHERE user_id=? AND mode=?", (uid2, mode)).fetchone()
        mr1, mr2 = int(m1["rating"]), int(m2["rating"])
        mn1, mn2, _, _ = _elo_pair(mr1, mr2, winner_id, uid1, uid2)
        for row, uid, new_rating, score in ((m1, uid1, mn1, s1), (m2, uid2, mn2, s2)):
            wins = row["wins"] + (1 if score == 1 else 0)
            losses = row["losses"] + (1 if score == 0 else 0)
            streak = row["streak"] + 1 if score == 1 else (0 if score == 0 else row["streak"])
            best = max(row["best_streak"], streak)
            con.execute(
                "UPDATE mode_ratings SET rating=?, wins=?, losses=?, matches=matches+1, streak=?, best_streak=? WHERE user_id=? AND mode=?",
                (new_rating, wins, losses, streak, best, uid, mode),
            )

        duration_ms = max(0, int((time.monotonic() - match.started_at) * 1000))
        con.execute(
            """
            INSERT INTO match_history(id,player1_id,player2_id,winner_id,reason,difficulty,duration_ms,
            p1_rating_before,p1_rating_after,p2_rating_before,p2_rating_after,played_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (match.id, uid1, uid2, winner_id, match.reason, match.difficulty, duration_ms, mr1, mn1, mr2, mn2, utc_now()),
        )
    match.result_meta[uid1] = {"ratingBefore": mr1, "ratingAfter": mn1, "ratingDelta": mn1 - mr1, "overallRatingAfter": gn1}
    match.result_meta[uid2] = {"ratingBefore": mr2, "ratingAfter": mn2, "ratingDelta": mn2 - mr2, "overallRatingAfter": gn2}


async def finalize_match(match: Match, winner_id: int | None, reason: str) -> None:
    if match.ended:
        return
    match.ended = True
    match.winner_id = winner_id
    match.reason = reason
    for st in match.states.values():
        st.finished = True
    update_ratings(match, winner_id)
    for uid in match.players:
        if active_match_by_user.get(uid) == match.id:
            active_match_by_user.pop(uid, None)
        recent_match_by_user[uid] = match.id
    await asyncio.gather(*(send_sync(match, uid, "match_end") for uid in match.players))


async def maybe_finish(match: Match, actor_uid: int) -> None:
    if match.ended:
        return
    actor = match.states[actor_uid]
    other = match.states[other_user(match, actor_uid)]
    if actor.eliminated:
        await finalize_match(match, other.user_id, "opponent_eliminated")
    elif actor.finished:
        await finalize_match(match, actor_uid, "field_cleared")


async def remove_from_queues(uid: int) -> None:
    for q in waiting.values():
        while uid in q:
            q.remove(uid)
    queued_at.pop(uid, None)


async def join_queue(uid: int, difficulty: str) -> None:
    if difficulty not in LEVELS:
        difficulty = "intermediate"
    touch_live(uid)
    clean_stale_queues()
    await remove_from_queues(uid)
    recent_match_by_user.pop(uid, None)
    if uid in active_match_by_user:
        mid = active_match_by_user[uid]
        match = matches.get(mid)
        if match and not match.ended:
            await send_sync(match, uid, "match_resume")
            return
    q = waiting[difficulty]
    opponent = None
    while q:
        cand = q.pop(0)
        queued_at.pop(cand, None)
        if cand != uid and cand not in active_match_by_user and is_live(cand, QUEUE_TTL_SECONDS):
            opponent = cand
            break
    if opponent is None:
        q.append(uid)
        queued_at[uid] = time.monotonic()
        await send_json(uid, {"type": "queue_status", "waiting": True, "difficulty": difficulty, "position": len(q)})
    else:
        await send_json(uid, {"type": "queue_status", "waiting": False, "difficulty": difficulty, "position": 0})
        await send_json(opponent, {"type": "queue_status", "waiting": False, "difficulty": difficulty, "position": 0})
        await create_match(opponent, uid, difficulty)


async def disconnect_forfeit(uid: int, match_id: str) -> None:
    try:
        await asyncio.sleep(30)
        if is_live(uid, 28.0):
            return
        match = matches.get(match_id)
        if not match or match.ended or active_match_by_user.get(uid) != match_id:
            return
        winner = other_user(match, uid)
        await finalize_match(match, winner, "disconnect_forfeit")
    except asyncio.CancelledError:
        pass


async def arena_state(uid: int) -> dict[str, Any]:
    touch_live(uid)
    mid = active_match_by_user.get(uid)
    if mid:
        match = matches.get(mid)
        if match and not match.ended:
            oid = other_user(match, uid)
            # HTTP polling also counts as a live realtime connection.
            if not is_live(oid, 30.0):
                await finalize_match(match, uid, "disconnect_forfeit")
                return {"type": "match_end", "match": match_payload(match, uid), "transport": "polling"}
            return {"type": "match_sync", "match": match_payload(match, uid), "transport": "polling"}
    recent = recent_match_by_user.get(uid)
    if recent:
        match = matches.get(recent)
        if match and match.ended and uid in match.players:
            return {"type": "match_end", "match": match_payload(match, uid), "transport": "polling"}
    clean_stale_queues()
    difficulty = queue_for(uid)
    if difficulty:
        queued_at[uid] = time.monotonic()
        position = waiting[difficulty].index(uid) + 1 if uid in waiting[difficulty] else 1
        return {"type": "queue_status", "waiting": True, "difficulty": difficulty, "position": position, "transport": "polling"}
    return {"type": "idle", "transport": "polling"}


class QueuePayload(BaseModel):
    difficulty: str = "intermediate"


class ArenaActionPayload(BaseModel):
    matchId: str
    action: str
    index: int


class ArenaRematchPayload(BaseModel):
    matchId: str


@app.post("/api/arena/queue")
async def http_queue_join(body: QueuePayload, user: sqlite3.Row = Depends(auth_user)) -> dict[str, Any]:
    uid = int(user["id"])
    async with state_lock:
        await join_queue(uid, body.difficulty)
        return await arena_state(uid)


@app.post("/api/arena/queue/leave")
async def http_queue_leave(user: sqlite3.Row = Depends(auth_user)) -> dict[str, Any]:
    uid = int(user["id"])
    touch_live(uid)
    async with state_lock:
        await remove_from_queues(uid)
    return {"ok": True}


@app.get("/api/arena/poll")
async def http_arena_poll(user: sqlite3.Row = Depends(auth_user)) -> dict[str, Any]:
    uid = int(user["id"])
    async with state_lock:
        return await arena_state(uid)


@app.post("/api/arena/action")
async def http_arena_action(body: ArenaActionPayload, user: sqlite3.Row = Depends(auth_user)) -> dict[str, Any]:
    uid = int(user["id"])
    touch_live(uid)
    async with state_lock:
        match = matches.get(body.matchId)
        if not match or match.ended or uid not in match.states:
            raise HTTPException(status_code=409, detail="Ranked match is no longer active")
        if body.action not in {"reveal", "flag", "chord"}:
            raise HTTPException(status_code=400, detail="Unknown action")
        process_action(match, match.states[uid], body.action, int(body.index))
        await sync_both(match)
        await maybe_finish(match, uid)
        event = "match_end" if match.ended else "match_sync"
        return {"type": event, "match": match_payload(match, uid), "transport": "polling"}


@app.post("/api/arena/rematch")
async def http_arena_rematch(body: ArenaRematchPayload, user: sqlite3.Row = Depends(auth_user)) -> dict[str, Any]:
    uid = int(user["id"])
    touch_live(uid)
    async with state_lock:
        match = matches.get(body.matchId)
        if not match or not match.ended or uid not in match.players:
            raise HTTPException(status_code=409, detail="Rematch is not available")
        match.rematch_requests.add(uid)
        oid = other_user(match, uid)
        await send_json(oid, {"type": "rematch_status", "requestedBy": uid})
        if len(match.rematch_requests) == 2 and is_live(match.players[0], QUEUE_TTL_SECONDS) and is_live(match.players[1], QUEUE_TTL_SECONDS):
            new_match = await create_match(match.players[0], match.players[1], match.difficulty, "match_found")
            return {"type": "match_found", "match": match_payload(new_match, uid), "transport": "polling"}
        return {"type": "rematch_status", "waiting": True, "transport": "polling"}


@app.websocket("/ws/arena")
async def arena_socket(ws: WebSocket) -> None:
    token = ws.query_params.get("token", "")
    try:
        payload = decode_token(token)
        uid = int(payload["sub"])
        row = get_user_by_id(uid)
        if not row:
            await ws.close(code=4401)
            return
    except Exception:
        await ws.close(code=4401)
        return
    await ws.accept()
    touch_live(uid)
    old = sockets.get(uid)
    sockets[uid] = ws
    if old and old is not ws:
        try:
            await old.close(code=4000)
        except Exception:
            pass
    task = disconnect_tasks.pop(uid, None)
    if task:
        task.cancel()
    await send_json(uid, {"type": "hello", "user": public_user(row), "online": len(sockets)})
    mid = active_match_by_user.get(uid)
    if mid and mid in matches and not matches[mid].ended:
        match = matches[mid]
        await send_sync(match, uid, "match_resume")
        await send_json(other_user(match, uid), {"type": "opponent_connection", "connected": True, "graceSeconds": 0})
    try:
        while True:
            msg = await ws.receive_json()
            touch_live(uid)
            mtype = msg.get("type")
            async with state_lock:
                if mtype == "queue_join":
                    await join_queue(uid, str(msg.get("difficulty", "intermediate")))
                elif mtype == "queue_leave":
                    await remove_from_queues(uid)
                    await send_json(uid, {"type": "queue_status", "waiting": False})
                elif mtype == "action":
                    mid = str(msg.get("matchId", ""))
                    match = matches.get(mid)
                    if not match or match.ended or uid not in match.states:
                        continue
                    try:
                        index = int(msg.get("index"))
                    except Exception:
                        continue
                    action = str(msg.get("action", ""))
                    if action not in {"reveal", "flag", "chord"}:
                        continue
                    process_action(match, match.states[uid], action, index)
                    await sync_both(match)
                    await maybe_finish(match, uid)
                elif mtype == "emote":
                    mid = str(msg.get("matchId", ""))
                    match = matches.get(mid)
                    emote = str(msg.get("emote", ""))[:8]
                    if match and uid in match.states and emote in {"👋", "⚡", "😅", "🔥", "GG", "👏"}:
                        await send_json(other_user(match, uid), {"type": "emote", "from": uid, "emote": emote})
                elif mtype == "rematch_request":
                    mid = str(msg.get("matchId", ""))
                    match = matches.get(mid)
                    if not match or not match.ended or uid not in match.players:
                        continue
                    match.rematch_requests.add(uid)
                    oid = other_user(match, uid)
                    await send_json(oid, {"type": "rematch_status", "requestedBy": uid})
                    if len(match.rematch_requests) == 2 and all(p in sockets for p in match.players):
                        await create_match(match.players[0], match.players[1], match.difficulty, "match_found")
                elif mtype == "ping":
                    await send_json(uid, {"type": "pong", "t": msg.get("t")})
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("Arena websocket failed for user %s", uid)
    finally:
        if sockets.get(uid) is ws:
            sockets.pop(uid, None)
            mid = active_match_by_user.get(uid)
            match = matches.get(mid) if mid else None
            if match and not match.ended:
                oid = other_user(match, uid)
                await send_json(oid, {"type": "opponent_connection", "connected": False, "graceSeconds": 30})
                task = asyncio.create_task(disconnect_forfeit(uid, match.id))
                disconnect_tasks[uid] = task


if __name__ == "__main__":
    init_db()
    uvicorn.run("server:app", host=os.environ.get("HOST", "0.0.0.0"), port=int(os.environ.get("PORT", "8000")), reload=False)
