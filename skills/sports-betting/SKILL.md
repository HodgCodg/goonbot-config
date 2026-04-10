---
name: sports-betting
description: Sports betting analysis - picks, odds, value bets, matchup research, EV calculations.
---
# Sports Betting Analysis

```bash
# Matchup research
python3 skills/sports-betting/scripts/betting_research.py TEAM1 TEAM2 [SPORT]
# Value calculator (win_prob as decimal, odds as american)
python3 skills/sports-betting/scripts/odds_analyzer.py WIN_PROB ODDS
```

EV guide: <0%=no bet, 0-2%=skip, 2-5%=1-2% bankroll, >5%=3-4% bankroll. Never exceed 5% on single play.
