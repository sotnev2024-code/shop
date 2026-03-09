from __future__ import annotations

from datetime import date, timedelta
import logging
from typing import Dict, List

import httpx
from fastapi import APIRouter, HTTPException

from app.config import settings


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
    Нормализованный вид матча, где сразу есть id, дата,
    а также ссылки на логотипы лиги и команд.
    """
    fixture = f.get("fixture") or {}
    league = f.get("league") or {}
    teams = f.get("teams") or {}
    home = teams.get("home") or {}
    away = teams.get("away") or {}

    return {
        "fixture_id": fixture.get("id"),
        "timestamp": fixture.get("timestamp"),
        "date": fixture.get("date"),
        "status": (fixture.get("status") or {}).get("short"),
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


async def _fetch_popular_fixtures(days_ahead: int = 7) -> dict:
    """
    Fetch fixtures from API-Football for the period:
    today ... today + days_ahead (по дням, отдельными запросами).
    Затем фильтруем их по нужным лигам.
    """
    if not settings.api_football or not settings.url_football:
        raise HTTPException(
            status_code=500,
            detail="API-Football credentials are not configured",
        )

    base_url = f"https://{settings.url_football.strip()}"
    headers = {
        # В некоторых конфигурациях используется x-apisports-key, но
        # у тебя уже работает x-rapidapi-key — оставляем его и дублируем ключ.
        "x-rapidapi-key": settings.api_football,
        "x-rapidapi-host": settings.url_football.strip(),
        "x-apisports-key": settings.api_football,
    }

    today = date.today()
    all_fixtures: list[dict] = []

    try:
        async with httpx.AsyncClient(base_url=base_url, timeout=15.0) as client:
            for offset in range(days_ahead + 1):
                day = today + timedelta(days=offset)
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


@router.get("/football/popular-matches")
async def get_popular_matches():
    """
    Debug endpoint: возвращает матчи на неделю вперёд
    только по топ‑лигам (европейские топ‑чемпионаты и еврокубки).
    """
    return await _fetch_popular_fixtures(days_ahead=7)

