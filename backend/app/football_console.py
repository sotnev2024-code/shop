from __future__ import annotations

import asyncio
from datetime import datetime
from collections import Counter

from app.api.v1.football import _fetch_popular_fixtures, TOP_LEAGUES, _fetch_odds_for_fixtures


def _format_kickoff(utc_iso: str | None) -> str:
    if not utc_iso:
        return "время неизвестно"
    try:
        # API-Football возвращает ISO‑дату, например "2024-03-09T15:00:00+00:00"
        dt = datetime.fromisoformat(utc_iso.replace("Z", "+00:00"))
        # Можно подстроить под локальное время, но пока просто красиво форматируем
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return utc_iso


async def main() -> None:
    # Берём матчи на месяц вперёд (30 дней, по дням)
    data = await _fetch_popular_fixtures(days_ahead=30)
    all_fixtures = data.get("all_fixtures", []) or []
    fixtures = data.get("fixtures", []) or []

    print(f"Всего матчей на месяц вперёд (все лиги): {len(all_fixtures)}")
    print(f"Матчей в заданных топ‑лигах: {len(fixtures)}")
    print()

    # Покажем, какие вообще лиги пришли, чтобы можно было скорректировать фильтр
    leagues_counter: Counter[str] = Counter()
    for f in all_fixtures:
        league = f.get("league") or {}
        name = league.get("name") or "Unknown league"
        country = league.get("country") or ""
        key = f"{name} ({country})" if country else name
        leagues_counter[key] += 1

    if leagues_counter:
        print("Найденные лиги за месяц:")
        for name, cnt in leagues_counter.most_common():
            print(f" - {name}: {cnt} матчей")
    else:
        print("Лиги не найдены (в ответе нет матчей).")

    # Отдельно покажем количество матчей по каждой из выбранных топ‑лиг
    top_leagues_counter: Counter[str] = Counter()
    for f in fixtures:
        league = f.get("league") or {}
        name = league.get("name")
        country = league.get("country")
        if not name or not country:
            continue
        key = f"{name} ({country})"
        top_leagues_counter[key] += 1

    print("\nМатчи по выбранным топ‑лигам за месяц:")
    for item in TOP_LEAGUES:
        key = f"{item['name']} ({item['country']})"
        cnt = top_leagues_counter.get(key, 0)
        print(f" - {key}: {cnt} матчей")

    print("\n================= МАТЧИ В ТОП‑ЛИГАХ =================")
    if not fixtures:
        print("Нет матчей в указанных топ‑лигах в выбранный период.")
        return

    # Получаем коэффициенты для всех матчей в топ‑лигах
    fixture_ids: list[int] = []
    for f in fixtures:
        fx = f.get("fixture") or {}
        fid = fx.get("id")
        if isinstance(fid, int):
            fixture_ids.append(fid)
    odds_by_fixture = await _fetch_odds_for_fixtures(fixture_ids)

    def _summarize_odds(odds_entries: list[dict]) -> str | None:
        """
        Берём первого букмекера и маркет "Match Winner" (если есть),
        чтобы кратко показать коэффициенты 1X2.
        """
        if not odds_entries:
            return None
        entry = odds_entries[0]
        bookmakers = entry.get("bookmakers") or []
        if not bookmakers:
            return None
        bookmaker = bookmakers[0]
        bets = bookmaker.get("bets") or []
        if not bets:
            return None
        # Ищем маркет по названию, иначе берём первый
        bet = next(
            (b for b in bets if isinstance(b.get("name"), str) and "Match Winner" in b["name"]),
            bets[0],
        )
        values = bet.get("values") or []
        if not values:
            return None
        parts = []
        for v in values:
            label = v.get("value")
            odd = v.get("odd")
            if not label or not odd:
                continue
            parts.append(f"{label}: {odd}")
        if not parts:
            return None
        bm_name = bookmaker.get("name", "Bookmaker")
        market_name = bet.get("name", "Market")
        return f"{bm_name} — {market_name}: " + ", ".join(parts)

    print("-" * 60)
    for idx, f in enumerate(fixtures, start=1):
        fixture = f.get("fixture", {}) or {}
        league = f.get("league", {}) or {}
        teams = f.get("teams", {}) or {}

        home = (teams.get("home") or {}).get("name", "Unknown")
        away = (teams.get("away") or {}).get("name", "Unknown")
        league_name = league.get("name", "Unknown league")
        country = league.get("country", "")
        status = (fixture.get("status") or {}).get("short", "")
        kickoff = _format_kickoff(fixture.get("date"))
        fid = fixture.get("id")

        print(f"{idx}. {home} vs {away}")
        if country:
            print(f"   Лига: {league_name} ({country})")
        else:
            print(f"   Лига: {league_name}")
        print(f"   Время: {kickoff} | Статус: {status}")

        if isinstance(fid, int) and fid in odds_by_fixture:
            summary = _summarize_odds(odds_by_fixture[fid])
            if summary:
                print(f"   Коэффициенты: {summary}")
            else:
                print("   Коэффициенты: данные есть, но не удалось красиво разобрать формат.")
        else:
            print("   Коэффициенты: не найдены (по этому матчу нет odds или нет доступа).")

        print("-" * 60)


if __name__ == "__main__":
    asyncio.run(main())

