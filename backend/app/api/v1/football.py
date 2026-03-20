from __future__ import annotations

from datetime import date, timedelta
import logging
from typing import Dict, List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from pydantic import BaseModel

from app.config import settings
from app.db.session import get_db, async_session
from app.db.models.user import User
from app.db.models.competition_bet import CompetitionBet
from app.db.models.competition_accrual import CompetitionAccrual
from app.api.deps import get_current_user_optional, get_current_user, get_admin_user


router = APIRouter()
logger = logging.getLogger(__name__)


# Топ‑лиги, которые нужны именно тебе: фильтруем по названию и стране
TOP_LEAGUES = [
    {"name": "Premier League", "country": "England"},
    {"name": "La Liga", "country": "Spain"},
    {"name": "Serie A", "country": "Italy"},
    {"name": "Bundesliga", "country": "Germany"},
    {"name": "Ligue 1", "country": "France"},
    {"name": "UEFA Champions League", "country": "World"},
    {"name": "UEFA Europa League", "country": "World"},
]


def _is_top_league(league: dict) -> bool:
    name = (league or {}).get("name")
    country = (league or {}).get("country")
    if not name or not country:
        return False
    for item in TOP_LEAGUES:
        if item["name"] == name and item["country"] == country:
            return True
    return False


def _simplify_fixture(f: dict) -> dict:
    """
    Нормализованный вид матча, где сразу есть id, дата, таймзон, рефери, периоды,
    а также ссылки на логотипы лиги и команд.
    """
    fixture = f.get("fixture") or {}
    league = f.get("league") or {}
    teams = f.get("teams") or {}
    home = teams.get("home") or {}
    away = teams.get("away") or {}
    status_obj = fixture.get("status") or {}

    return {
        "fixture_id": fixture.get("id"),
        "timestamp": fixture.get("timestamp"),
        "date": fixture.get("date"),
        "referee": fixture.get("referee"),
        "timezone": fixture.get("timezone"),
        "periods": fixture.get("periods"),
        "status": status_obj.get("short"),
        "status_long": status_obj.get("long"),
        "league": {
            "id": league.get("id"),
            "name": league.get("name"),
            "country": league.get("country"),
            "logo": league.get("logo"),
            "flag": league.get("flag"),
            "season": league.get("season"),
            "round": league.get("round"),
        },
        "home_team": {
            "id": home.get("id"),
            "name": home.get("name"),
            "logo": home.get("logo"),
            "winner": home.get("winner"),
        },
        "away_team": {
            "id": away.get("id"),
            "name": away.get("name"),
            "logo": away.get("logo"),
            "winner": away.get("winner"),
        },
    }


async def _fetch_popular_fixtures(
    days_ahead: int = 7,
    from_date: Optional[date] = None,
) -> dict:
    """
    Fetch fixtures from API-Football for the period:
    from_date (или сегодня) ... from_date + days_ahead.
    Затем фильтруем их по нужным лигам.
    """
    if not settings.api_football or not settings.url_football:
        raise HTTPException(
            status_code=500,
            detail="API-Football credentials are not configured",
        )

    base_url = f"https://{settings.url_football.strip()}"
    headers = {
        "x-rapidapi-key": settings.api_football,
        "x-rapidapi-host": settings.url_football.strip(),
        "x-apisports-key": settings.api_football,
    }

    start = from_date if from_date is not None else date.today()
    all_fixtures: list[dict] = []

    try:
        async with httpx.AsyncClient(base_url=base_url, timeout=15.0) as client:
            for offset in range(days_ahead + 1):
                day = start + timedelta(days=offset)
                params = {
                    "date": day.isoformat(),
                    "timezone": "Europe/Moscow",
                }
                try:
                    response = await client.get("/fixtures", headers=headers, params=params)
                except httpx.RequestError as e:
                    logger.error("API-Football request error for %s: %s", day, e)
                    continue

                if response.status_code != 200:
                    logger.error(
                        "API-Football returned error status %s for %s: %s",
                        response.status_code,
                        day,
                        response.text,
                    )
                    continue

                data = response.json()
                day_fixtures = data.get("response", []) or []
                all_fixtures.extend(day_fixtures)
    except Exception as e:
        logger.error("API-Football unexpected error: %s", e)
        raise HTTPException(status_code=502, detail="Failed to fetch fixtures from API-Football") from e

    # Фильтруем матчи по нужным лигам (название + страна)
    filtered_fixtures = [f for f in all_fixtures if _is_top_league(f.get("league") or {})]

    return {
        "total": len(all_fixtures),
        "count": len(filtered_fixtures),
        "fixtures": filtered_fixtures,
        "matches": [_simplify_fixture(f) for f in filtered_fixtures],
        "all_fixtures": all_fixtures,
    }


async def _fetch_odds_for_fixtures(fixture_ids: List[int]) -> Dict[int, List[dict]]:
    """
    Получить коэффициенты для списка матчей по их fixture id.
    Возвращает словарь fixture_id -> список записей odds из API-Football.
    """
    if not fixture_ids:
        return {}
    if not settings.api_football or not settings.url_football:
        raise HTTPException(
            status_code=500,
            detail="API-Football credentials are not configured",
        )

    base_url = f"https://{settings.url_football.strip()}"
    headers = {
        "x-rapidapi-key": settings.api_football,
        "x-rapidapi-host": settings.url_football.strip(),
        "x-apisports-key": settings.api_football,
    }

    results: Dict[int, List[dict]] = {}

    try:
        async with httpx.AsyncClient(base_url=base_url, timeout=15.0) as client:
            for fixture_id in fixture_ids:
                params = {"fixture": fixture_id}
                try:
                    response = await client.get("/odds", headers=headers, params=params)
                except httpx.RequestError as e:
                    logger.error("API-Football odds request error for fixture %s: %s", fixture_id, e)
                    continue

                if response.status_code != 200:
                    logger.error(
                        "API-Football odds returned error status %s for fixture %s: %s",
                        response.status_code,
                        fixture_id,
                        response.text,
                    )
                    continue

                data = response.json()
                odds_entries = data.get("response", []) or []
                if odds_entries:
                    results[fixture_id] = odds_entries
    except Exception as e:
        logger.error("API-Football unexpected error while fetching odds: %s", e)
        raise HTTPException(status_code=502, detail="Failed to fetch odds from API-Football") from e

    return results


async def _fetch_fixtures_by_ids(fixture_ids: List[int]) -> Dict[int, dict]:
    """
    Получить детали матчей по fixture id из API-Football.
    Возвращает словарь fixture_id -> полный объект fixture.
    """
    if not fixture_ids:
        return {}
    if not settings.api_football or not settings.url_football:
        raise HTTPException(
            status_code=500,
            detail="API-Football credentials are not configured",
        )

    base_url = f"https://{settings.url_football.strip()}"
    headers = {
        "x-rapidapi-key": settings.api_football,
        "x-rapidapi-host": settings.url_football.strip(),
        "x-apisports-key": settings.api_football,
    }

    results: Dict[int, dict] = {}

    try:
        async with httpx.AsyncClient(base_url=base_url, timeout=15.0) as client:
            for fixture_id in fixture_ids:
                params = {"id": fixture_id}
                try:
                    response = await client.get("/fixtures", headers=headers, params=params)
                except httpx.RequestError as e:
                    logger.error("API-Football fixtures request error for fixture %s: %s", fixture_id, e)
                    continue

                if response.status_code != 200:
                    logger.error(
                        "API-Football fixtures returned error status %s for fixture %s: %s",
                        response.status_code,
                        fixture_id,
                        response.text,
                    )
                    continue

                data = response.json()
                items = data.get("response", []) or []
                if items:
                    # API-Football возвращает список; нас интересует первый элемент
                    results[fixture_id] = items[0]
    except Exception as e:
        logger.error("API-Football unexpected error while fetching fixtures: %s", e)
        raise HTTPException(status_code=502, detail="Failed to fetch fixtures from API-Football") from e

    return results


def _extract_1x2_odds(odds_entries: List[dict]) -> dict | None:
    """Из ответа API-Football odds извлечь первый букмекер и маркет Match Winner (1X2)."""
    if not odds_entries:
        return None
    for entry in odds_entries:
        bookmakers = entry.get("bookmakers") or []
        for bm in bookmakers:
            bets = bm.get("bets") or []
            for bet in bets:
                if bet.get("name") != "Match Winner":
                    continue
                values = bet.get("values") or []
                home = draw = away = None
                for v in values:
                    val = v.get("value")
                    odd = v.get("odd")
                    if val == "Home":
                        home = odd
                    elif val == "Draw":
                        draw = odd
                    elif val == "Away":
                        away = odd
                if home is not None and draw is not None and away is not None:
                    return {
                        "bookmaker_name": bm.get("name") or "",
                        "market_name": "Match Winner",
                        "odd_home": float(home) if home else None,
                        "odd_draw": float(draw) if draw else None,
                        "odd_away": float(away) if away else None,
                    }
    return None


@router.get("/football/matches/today")
async def get_matches_today(
    date_param: Optional[str] = Query(None, alias="date"),
):
    """
    Матчи топ‑лиг. Без date — сегодня + 2 дня. С date=YYYY-MM-DD — матчи на указанную дату.
    """
    if date_param:
        try:
            from datetime import datetime as dt
            parsed = dt.strptime(date_param, "%Y-%m-%d").date()
            data = await _fetch_popular_fixtures(from_date=parsed, days_ahead=0)
        except ValueError:
            data = await _fetch_popular_fixtures(days_ahead=2)
    else:
        data = await _fetch_popular_fixtures(days_ahead=2)
    matches = data.get("matches") or []
    if not matches:
        return {"matches": []}
    fixture_ids = [m["fixture_id"] for m in matches if m.get("fixture_id") is not None]
    odds_by_fixture = await _fetch_odds_for_fixtures(fixture_ids)
    out = []
    for m in matches:
        m = dict(m)
        fid = m.get("fixture_id")
        odds = None
        if fid is not None and fid in odds_by_fixture:
            odds = _extract_1x2_odds(odds_by_fixture[fid])
        m["odds"] = odds or {}
        m["kickoff_at"] = m.get("date")
        out.append(m)
    return {"matches": out}


async def _settle_pending_bets(db: AsyncSession, max_bets: int = 200) -> dict:
    """
    Рассчитать исходы pending-ставок по данным API-Football и начислить выигрыши.
    Возвращает статистику по обработанным ставкам.
    """
    # Берём pending-ставки с подгруженным пользователем
    q = (
        select(CompetitionBet)
        .options(selectinload(CompetitionBet.user))
        .where(CompetitionBet.status == "pending")
        .limit(max_bets)
    )
    result = await db.execute(q)
    bets: List[CompetitionBet] = result.scalars().all()
    if not bets:
        return {"processed": 0, "wins": 0, "losses": 0, "skipped": 0}

    fixture_ids = [b.fixture_id for b in bets if isinstance(b.fixture_id, int)]
    fixtures_by_id = await _fetch_fixtures_by_ids(fixture_ids)

    finished_status = {"FT", "AET", "PEN"}

    processed = wins = losses = skipped = 0

    for bet in bets:
        if bet.status != "pending":
            continue
        fx = fixtures_by_id.get(bet.fixture_id)
        if not fx:
            skipped += 1
            continue
        fixture = fx.get("fixture") or {}
        status_obj = fixture.get("status") or {}
        status_short = status_obj.get("short")
        if status_short not in finished_status:
            # матч ещё не закончен
            skipped += 1
            continue

        teams = fx.get("teams") or {}
        home = teams.get("home") or {}
        away = teams.get("away") or {}
        home_winner = home.get("winner")
        away_winner = away.get("winner")

        result_code: Optional[str] = None
        if home_winner is True and away_winner is False:
            result_code = "H"
        elif away_winner is True and home_winner is False:
            result_code = "A"
        else:
            # Пытаемся по голам
            goals = fixture.get("goals") or {}
            gh = goals.get("home")
            ga = goals.get("away")
            if gh is not None and ga is not None:
                if gh > ga:
                    result_code = "H"
                elif ga > gh:
                    result_code = "A"
                else:
                    result_code = "D"

        if result_code is None:
            skipped += 1
            continue

        user = bet.user
        if user is None:
            skipped += 1
            continue

        processed += 1
        if bet.outcome == result_code:
            # Выигрыш
            payout = float(bet.amount) * float(bet.odds or 0)
            payout = round(payout, 2)
            bet.status = "won"
            bet.payout = payout
            user.competition_points_balance = float(
                getattr(user, "competition_points_balance", 0)
            ) + payout
            acc = CompetitionAccrual(
                user_id=user.id,
                amount=payout,
                kind="bet_win",
                description=f"Выигрыш: {bet.match_label} ({_outcome_label(bet.outcome)})",
                bet_id=bet.id,
            )
            db.add(acc)
            wins += 1
        else:
            # Проигрыш
            bet.status = "lost"
            bet.payout = 0
            losses += 1

    await db.commit()
    return {"processed": processed, "wins": wins, "losses": losses, "skipped": skipped}


@router.get("/football/points")
async def get_football_points(
    user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Игровые баллы для ставок (месячный баланс).
    Без авторизации возвращает 10_000. С X-Init-Data — баланс пользователя из БД.
    """
    from datetime import date as date_type

    today = date_type.today()
    start = today.replace(day=1)
    if today.month == 12:
        end = today.replace(day=31)
    else:
        from calendar import monthrange
        _, last = monthrange(today.year, today.month)
        end = today.replace(day=last)

    balance = 10_000
    if user is not None:
        balance = float(getattr(user, "competition_points_balance", 10_000))
    return {
        "competition_points_balance": balance,
        "current_period_start": start.isoformat(),
        "current_period_end": end.isoformat(),
    }


@router.get("/football/leaderboard")
async def get_football_leaderboard(
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
):
    """
    Топ игроков по игровым баллам (competition_points_balance).
    Возвращает список: rank, name (first_name), tag (@username), score.
    """
    q = (
        select(User)
        .order_by(User.competition_points_balance.desc())
        .limit(max(1, min(limit, 200)))
    )
    result = await db.execute(q)
    users = result.scalars().all()
    out = []
    for idx, u in enumerate(users, start=1):
        name = (u.first_name or "").strip() or "Игрок"
        tag = ("@" + u.username) if u.username else ""
        score = float(getattr(u, "competition_points_balance", 0))
        out.append({"rank": idx, "name": name, "tag": tag, "score": int(score)})
    return {"leaderboard": out}


class PlaceBetBody(BaseModel):
    fixture_id: int
    match_label: str = ""
    outcome: str  # H, D, A
    amount: float
    odds: float
    kickoff_at: Optional[str] = None  # ISO 8601, для проверки: нельзя ставить после начала матча


@router.post("/football/bets")
async def place_bet(
    body: PlaceBetBody,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Принять ставку: списать баллы, создать запись ставки и начисление."""
    from datetime import datetime, timezone

    if body.outcome not in ("H", "D", "A"):
        raise HTTPException(status_code=400, detail="outcome must be H, D or A")
    amount = float(body.amount)
    if amount <= 0:
        raise HTTPException(status_code=400, detail="amount must be positive")
    balance = float(getattr(user, "competition_points_balance", 0))
    if balance < amount:
        raise HTTPException(
            status_code=400,
            detail="Нельзя поставить больше, чем есть на балансе. Ваш баланс: {} pts".format(int(balance)),
        )
    if body.kickoff_at:
        try:
            kickoff_str = body.kickoff_at.replace("Z", "+00:00")
            kickoff = datetime.fromisoformat(kickoff_str)
            if kickoff.tzinfo is None:
                kickoff = kickoff.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) >= kickoff:
                raise HTTPException(
                    status_code=400,
                    detail="Матч уже начался. Ставки не принимаются.",
                )
        except (ValueError, TypeError):
            pass

    bet = CompetitionBet(
        user_id=user.id,
        fixture_id=body.fixture_id,
        match_label=(body.match_label or "").strip() or "Матч",
        outcome=body.outcome,
        amount=amount,
        odds=float(body.odds),
        status="pending",
    )
    db.add(bet)
    await db.flush()

    accrual = CompetitionAccrual(
        user_id=user.id,
        amount=-amount,
        kind="bet_placed",
        description=f"Ставка: {bet.match_label} ({_outcome_label(body.outcome)})",
        bet_id=bet.id,
    )
    db.add(accrual)

    user.competition_points_balance = balance - amount
    await db.commit()
    await db.refresh(user)
    await db.refresh(bet)

    return {
        "success": True,
        "competition_points_balance": float(user.competition_points_balance),
        "bet": {
            "id": bet.id,
            "fixture_id": bet.fixture_id,
            "match_label": bet.match_label,
            "outcome": bet.outcome,
            "amount": float(bet.amount),
            "odds": float(bet.odds),
            "status": bet.status,
        },
    }


def _outcome_label(outcome: str) -> str:
    if outcome == "H":
        return "П1"
    if outcome == "D":
        return "Х"
    if outcome == "A":
        return "П2"
    return outcome


@router.post("/football/settle-pending-bets")
async def settle_pending_bets_admin(
    max_bets: int = 200,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """
    Админ-эндпоинт: разово рассчитать pending-ставки и начислить выигрыши.
    Вызывается по кнопке в админке.
    """
    stats = await _settle_pending_bets(db, max_bets=max_bets)
    return stats


async def run_settle_pending_bets_job(max_bets: int = 500) -> None:
    """
    Фоновая задача для планировщика (каждые N минут).
    Сейчас НЕ подключена к scheduler, можно будет добавить позже.
    """
    async with async_session() as db:
        try:
            await _settle_pending_bets(db, max_bets=max_bets)
        except Exception as e:
            logger.error("Error in settle pending bets job: %s", e, exc_info=True)


@router.get("/football/bets/history")
async def get_bets_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
):
    """История ставок текущего пользователя."""
    q = (
        select(CompetitionBet)
        .where(CompetitionBet.user_id == user.id)
        .order_by(CompetitionBet.created_at.desc())
        .limit(max(1, min(limit, 100)))
    )
    result = await db.execute(q)
    bets = result.scalars().all()
    out = []
    for b in bets:
        out.append({
            "id": b.id,
            "match": b.match_label,
            "outcome": "Home" if b.outcome == "H" else ("Draw" if b.outcome == "D" else "Away"),
            "amount": int(b.amount),
            "odds": float(b.odds) if b.odds is not None else None,
            "result": b.status,
            "payout": int(b.payout) if b.payout is not None else None,
            "created_at": b.created_at.isoformat() if b.created_at else None,
        })
    return {"bets": out}


@router.get("/football/accruals")
async def get_accruals(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
):
    """Начисления/списания баллов текущего пользователя."""
    q = (
        select(CompetitionAccrual)
        .where(CompetitionAccrual.user_id == user.id)
        .order_by(CompetitionAccrual.created_at.desc())
        .limit(max(1, min(limit, 100)))
    )
    result = await db.execute(q)
    accruals = result.scalars().all()
    out = []
    for a in accruals:
        out.append({
            "id": a.id,
            "date": a.created_at.date().isoformat() if a.created_at else "",
            "type": a.description or a.kind,
            "points": int(a.amount),
            "created_at": a.created_at.isoformat() if a.created_at else None,
        })
    return {"accruals": out}


@router.get("/football/popular-matches")
async def get_popular_matches():
    """
    Debug endpoint: возвращает матчи на неделю вперёд
    только по топ‑лигам (европейские топ‑чемпионаты и еврокубки).
    """
    return await _fetch_popular_fixtures(days_ahead=7)

