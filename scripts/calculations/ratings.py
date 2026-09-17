#!/usr/bin/env python3
"""Calculate NCAA Dynasty team ratings from the League Scores workbook tab.

Outputs JSON files intended for a static website to consume. The script keeps
the workbook as the source of truth and leaves presentation to the site.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np



# The 2026 national scoreboard shows five FCS buckets, not four: "FCS Northwest"
# appears alongside the other four (e.g. IMG_5334, at North Dakota State).
FCS_TEAMS = {"FCS East", "FCS Midwest", "FCS Northwest", "FCS Southeast", "FCS West"}
HEADER = [
    "Week",
    "Date",
    "Away Team",
    "Home Team",
    "Away Score",
    "Home Score",
    "Neutral Site (Y/N)",
    "Notes",
]


@dataclass(frozen=True)
class Game:
    row_number: int
    source_order: int
    week: int
    date: str
    away_team: str
    home_team: str
    away_score: float
    home_score: float
    neutral: bool
    notes: str

    @property
    def away_margin(self) -> float:
        return self.away_score - self.home_score

    @property
    def home_margin(self) -> float:
        return self.home_score - self.away_score

    @property
    def winner(self) -> str:
        return self.away_team if self.away_score > self.home_score else self.home_team

    @property
    def loser(self) -> str:
        return self.home_team if self.away_score > self.home_score else self.away_team

    @property
    def margin_abs(self) -> float:
        return abs(self.away_margin)


def team_list(games: list[Game]) -> list[str]:
    teams = {g.away_team for g in games} | {g.home_team for g in games}
    return sorted(teams)


def estimate_home_field(games: list[Game], teams: list[str]) -> dict[str, Any]:
    non_neutral = [g for g in games if not g.neutral]
    if not non_neutral:
        return {
            "estimated_home_field_advantage": None,
            "raw_average_home_margin": None,
            "method": "Team fixed-effect regression on non-neutral home margins",
            "status": "not_estimated",
            "warning": "No non-neutral games were available.",
        }

    idx = {team: i for i, team in enumerate(teams)}
    x = np.zeros((len(non_neutral), len(teams) + 1), dtype=float)
    y = np.zeros(len(non_neutral), dtype=float)

    for r, game in enumerate(non_neutral):
        x[r, 0] = 1.0
        x[r, idx[game.home_team] + 1] = 1.0
        x[r, idx[game.away_team] + 1] = -1.0
        y[r] = game.home_margin

    beta, *_ = np.linalg.lstsq(x, y, rcond=None)
    team_strengths = beta[1:]
    team_strengths -= float(np.mean(team_strengths))

    fitted = x[:, 0] * beta[0]
    for r, game in enumerate(non_neutral):
        fitted[r] += team_strengths[idx[game.home_team]]
        fitted[r] -= team_strengths[idx[game.away_team]]
    residuals = y - fitted

    return {
        "estimated_home_field_advantage": float(beta[0]),
        "raw_average_home_margin": float(np.mean(y)),
        "method": "Team fixed-effect regression on non-neutral home margins",
        "status": "estimated",
        "non_neutral_games": len(non_neutral),
        "residual_rmse": float(math.sqrt(np.mean(residuals**2))) if len(residuals) else 0.0,
    }


def calculate_records(games: list[Game], teams: list[str]) -> dict[str, dict[str, float]]:
    stats = {
        team: {"games": 0.0, "wins": 0.0, "losses": 0.0, "pf": 0.0, "pa": 0.0}
        for team in teams
    }
    for g in games:
        away = stats[g.away_team]
        home = stats[g.home_team]
        away["games"] += 1
        home["games"] += 1
        away["pf"] += g.away_score
        away["pa"] += g.home_score
        home["pf"] += g.home_score
        home["pa"] += g.away_score
        if g.away_score > g.home_score:
            away["wins"] += 1
            home["losses"] += 1
        else:
            home["wins"] += 1
            away["losses"] += 1
    return stats


def apply_fcs_summary(stats: dict[str, dict[str, float]], games: list[Game]) -> None:
    for fcs in FCS_TEAMS & set(stats):
        weekly_pf: dict[int, list[float]] = defaultdict(list)
        weekly_pa: dict[int, list[float]] = defaultdict(list)
        for g in games:
            if g.away_team == fcs:
                weekly_pf[g.week].append(g.away_score)
                weekly_pa[g.week].append(g.home_score)
            elif g.home_team == fcs:
                weekly_pf[g.week].append(g.home_score)
                weekly_pa[g.week].append(g.away_score)

        stats[fcs] = {
            "games": 12.0,
            "wins": 0.0,
            "losses": 12.0,
            "pf": sum(float(np.mean(v)) for v in weekly_pf.values()) if weekly_pf else 0.0,
            "pa": sum(float(np.mean(v)) for v in weekly_pa.values()) if weekly_pa else 0.0,
        }


def win_pct(stats: dict[str, dict[str, float]], team: str) -> float:
    if team in FCS_TEAMS:
        return 0.0
    games = stats[team]["games"]
    return stats[team]["wins"] / games if games else 0.0


def win_pct_excluding(
    games: list[Game], base_stats: dict[str, dict[str, float]], team: str, excluded_opponent: str
) -> float:
    if team in FCS_TEAMS:
        return 0.0
    wins = base_stats[team]["wins"]
    losses = base_stats[team]["losses"]
    for g in games:
        if {g.away_team, g.home_team} != {team, excluded_opponent}:
            continue
        if g.winner == team:
            wins -= 1
        else:
            losses -= 1
    total = wins + losses
    return wins / total if total else 0.0


def calculate_sos(games: list[Game], teams: list[str], stats: dict[str, dict[str, float]]) -> dict[str, float]:
    opponents: dict[str, list[str]] = {team: [] for team in teams}
    for g in games:
        opponents[g.away_team].append(g.home_team)
        opponents[g.home_team].append(g.away_team)

    owp: dict[str, float] = {}
    for team in teams:
        values = [win_pct_excluding(games, stats, opp, team) for opp in opponents[team]]
        owp[team] = float(np.mean(values)) if values else 0.0

    sos: dict[str, float] = {}
    for team in teams:
        opp_owp = [owp[opp] for opp in opponents[team]]
        oowp = float(np.mean(opp_owp)) if opp_owp else 0.0
        sos[team] = (2.0 / 3.0) * owp[team] + (1.0 / 3.0) * oowp
    return sos


def calculate_srs(
    games: list[Game], teams: list[str], home_field_points: float | None
) -> tuple[dict[str, float], int, float]:
    hfa = float(home_field_points or 0.0)
    idx = {team: i for i, team in enumerate(teams)}
    margins: dict[str, list[float]] = {team: [] for team in teams}
    opponents: dict[str, list[str]] = {team: [] for team in teams}

    for g in games:
        away_adjusted_margin = g.away_margin + (0.0 if g.neutral else hfa)
        margins[g.away_team].append(away_adjusted_margin)
        margins[g.home_team].append(-away_adjusted_margin)
        opponents[g.away_team].append(g.home_team)
        opponents[g.home_team].append(g.away_team)

    adjusted_mov = {
        team: (float(np.mean(values)) if values else 0.0) for team, values in margins.items()
    }
    if not teams:
        return {}, 0, 0.0

    rows = []
    y = []
    for team in teams:
        row = np.zeros(len(teams), dtype=float)
        row[idx[team]] = 1.0
        if opponents[team]:
            weight = 1.0 / len(opponents[team])
            for opponent in opponents[team]:
                row[idx[opponent]] -= weight
        rows.append(row)
        y.append(adjusted_mov[team])

    # Center ratings around zero to anchor disconnected or weakly connected schedules.
    rows.append(np.ones(len(teams), dtype=float))
    y.append(0.0)

    matrix = np.vstack(rows)
    target = np.array(y, dtype=float)
    solution, *_ = np.linalg.lstsq(matrix, target, rcond=None)
    solution -= float(np.mean(solution))
    residual = matrix @ solution - target
    rmse = float(math.sqrt(np.mean(residual**2))) if len(residual) else 0.0
    ratings = {team: float(solution[idx[team]]) for team in teams}
    return ratings, 1, rmse


def calculate_elo(
    games: list[Game],
    teams: list[str],
    home_field_points: float | None,
    starting_rating: float = 1500.0,
    k_factor: float = 20.0,
) -> dict[str, float]:
    ratings = {team: starting_rating for team in teams}
    hfa_elo = float(home_field_points or 0.0) * 25.0

    ordered_games = sorted(games, key=lambda g: (g.week, g.date, g.source_order))
    for g in ordered_games:
        home_for_expectation = ratings[g.home_team] + (0.0 if g.neutral else hfa_elo)
        away_for_expectation = ratings[g.away_team]
        expected_home = 1.0 / (1.0 + 10 ** ((away_for_expectation - home_for_expectation) / 400.0))
        home_result = 1.0 if g.home_score > g.away_score else 0.0
        mov_multiplier = math.log(g.margin_abs + 1.0)
        change = k_factor * mov_multiplier * (home_result - expected_home)
        ratings[g.home_team] += change
        ratings[g.away_team] -= change

    return ratings


def calculate_bradley_terry(
    games: list[Game], teams: list[str], max_iter: int = 200
) -> tuple[dict[str, float], float, int]:
    if not games:
        return {team: 1500.0 for team in teams}, 0.0, 0

    idx = {team: i for i, team in enumerate(teams)}
    x = np.zeros((len(games), len(teams) + 1), dtype=float)
    y = np.zeros(len(games), dtype=float)

    for r, g in enumerate(games):
        x[r, idx[g.home_team]] = 1.0
        x[r, idx[g.away_team]] = -1.0
        x[r, len(teams)] = 0.0 if g.neutral else 1.0
        y[r] = 1.0 if g.home_score > g.away_score else 0.0

    theta = np.zeros(len(teams) + 1, dtype=float)
    ridge = 1e-4
    completed = 0

    for iteration in range(1, max_iter + 1):
        z = x @ theta
        p = 1.0 / (1.0 + np.exp(-np.clip(z, -35.0, 35.0)))
        w = p * (1.0 - p)
        gradient = x.T @ (y - p) - ridge * theta
        hessian = -(x.T @ (x * w[:, None])) - ridge * np.eye(len(theta))

        step = np.linalg.lstsq(hessian, gradient, rcond=None)[0]
        theta -= step
        theta[: len(teams)] -= float(np.mean(theta[: len(teams)]))
        completed = iteration
        if float(np.max(np.abs(step))) < 1e-7:
            break

    ratings = {
        team: float(theta[idx[team]] * 400.0 / math.log(10.0) + 1500.0) for team in teams
    }
    return ratings, float(theta[len(teams)]), completed


def glicko_g(phi: float) -> float:
    return 1.0 / math.sqrt(1.0 + 3.0 * phi * phi / (math.pi * math.pi))


def glicko_e(mu: float, mu_j: float, phi_j: float) -> float:
    return 1.0 / (1.0 + math.exp(-glicko_g(phi_j) * (mu - mu_j)))


def update_glicko_player(
    rating: float,
    rd: float,
    sigma: float,
    matches: list[tuple[float, float, float]],
    tau: float = 0.5,
) -> tuple[float, float, float]:
    mu = (rating - 1500.0) / 173.7178
    phi = rd / 173.7178

    if not matches:
        phi_star = math.sqrt(phi * phi + sigma * sigma)
        return rating, 173.7178 * phi_star, sigma

    converted = [
        ((opp_rating - 1500.0) / 173.7178, opp_rd / 173.7178, score)
        for opp_rating, opp_rd, score in matches
    ]

    v_inv = 0.0
    delta_sum = 0.0
    for mu_j, phi_j, score in converted:
        e_val = glicko_e(mu, mu_j, phi_j)
        g_val = glicko_g(phi_j)
        v_inv += g_val * g_val * e_val * (1.0 - e_val)
        delta_sum += g_val * (score - e_val)
    v = 1.0 / v_inv
    delta = v * delta_sum

    a = math.log(sigma * sigma)
    epsilon = 1e-6

    def f(x: float) -> float:
        ex = math.exp(x)
        numerator = ex * (delta * delta - phi * phi - v - ex)
        denominator = 2.0 * (phi * phi + v + ex) ** 2
        return numerator / denominator - (x - a) / (tau * tau)

    A = a
    if delta * delta > phi * phi + v:
        B = math.log(delta * delta - phi * phi - v)
    else:
        k = 1
        while f(a - k * tau) < 0:
            k += 1
        B = a - k * tau

    f_a = f(A)
    f_b = f(B)
    while abs(B - A) > epsilon:
        C = A + (A - B) * f_a / (f_b - f_a)
        f_c = f(C)
        if f_c * f_b <= 0:
            A = B
            f_a = f_b
        else:
            f_a /= 2.0
        B = C
        f_b = f_c

    sigma_prime = math.exp(A / 2.0)
    phi_star = math.sqrt(phi * phi + sigma_prime * sigma_prime)
    phi_prime = 1.0 / math.sqrt(1.0 / (phi_star * phi_star) + 1.0 / v)
    mu_prime = mu + phi_prime * phi_prime * delta_sum

    return (
        173.7178 * mu_prime + 1500.0,
        173.7178 * phi_prime,
        sigma_prime,
    )


def calculate_glicko2(
    games: list[Game],
    teams: list[str],
    home_field_points: float | None,
    initial_rating: float = 1500.0,
    initial_rd: float = 350.0,
    initial_volatility: float = 0.06,
    tau: float = 0.5,
) -> dict[str, dict[str, float]]:
    state = {
        team: {
            "rating": initial_rating,
            "rd": initial_rd,
            "volatility": initial_volatility,
        }
        for team in teams
    }
    hfa_rating = float(home_field_points or 0.0) * 25.0

    for week in sorted({g.week for g in games}):
        week_games = [g for g in games if g.week == week]
        matches: dict[str, list[tuple[float, float, float]]] = defaultdict(list)

        for g in week_games:
            away_state = state[g.away_team]
            home_state = state[g.home_team]
            adjustment = 0.0 if g.neutral else hfa_rating
            away_score = 1.0 if g.away_score > g.home_score else 0.0
            home_score = 1.0 - away_score

            matches[g.away_team].append(
                (home_state["rating"] + adjustment, home_state["rd"], away_score)
            )
            matches[g.home_team].append(
                (away_state["rating"] - adjustment, away_state["rd"], home_score)
            )

        new_state = {}
        for team in teams:
            rating, rd, volatility = update_glicko_player(
                state[team]["rating"],
                state[team]["rd"],
                state[team]["volatility"],
                matches.get(team, []),
                tau=tau,
            )
            new_state[team] = {
                "rating": float(rating),
                "rd": float(rd),
                "volatility": float(volatility),
            }
        state = new_state

    return state


def build_rows(
    games: list[Game],
    teams: list[str],
    stats: dict[str, dict[str, float]],
    sos: dict[str, float],
    srs: dict[str, float],
    elo: dict[str, float],
    bt: dict[str, float],
    glicko: dict[str, dict[str, float]],
) -> list[dict[str, Any]]:
    rows = []
    for team in teams:
        team_stats = stats[team]
        games_count = team_stats["games"]
        rows.append(
            {
                "team": team,
                "games": int(games_count),
                "wins": int(team_stats["wins"]),
                "losses": int(team_stats["losses"]),
                "win_pct": win_pct(stats, team),
                "pf": team_stats["pf"],
                "pa": team_stats["pa"],
                "pf_per_game": team_stats["pf"] / games_count if games_count else 0.0,
                "pa_per_game": team_stats["pa"] / games_count if games_count else 0.0,
                "mov": (team_stats["pf"] - team_stats["pa"]) / games_count if games_count else 0.0,
                "sos": sos.get(team, 0.0),
                "srs": srs.get(team, 0.0),
                "elo": elo.get(team, 1500.0),
                "bradley_terry": bt.get(team, 1500.0),
                "glicko2_rating": glicko.get(team, {}).get("rating", 1500.0),
                "glicko2_rd": glicko.get(team, {}).get("rd", 350.0),
                "glicko2_volatility": glicko.get(team, {}).get("volatility", 0.06),
                "synthetic_team": "Y" if team in FCS_TEAMS else "N",
            }
        )

    return sorted(rows, key=lambda row: row["srs"], reverse=True)


