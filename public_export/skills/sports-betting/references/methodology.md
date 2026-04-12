# Sports Betting Methodology

## Research Framework

### 1. Team Form Analysis
- **Last 10 games record** - Current momentum indicator
- **Home/Away splits** - Venue advantage (especially important in NCAAB)
- **Offensive/Defensive ratings** - Efficiency metrics
- **Pace** - Games per possession affects totals

### 2. Injury Assessment
- Check official injury reports 24-48 hours before game
- Identify key players out/questionable
- Assess impact on team efficiency

### 3. Head-to-Head History
- Last 5 meetings between teams
- Style matchups (pace, defense type)
- Historical trends at neutral sites

### 4. Betting Trends Analysis
- ATS record (Against The Spread)
- Over/Under record
- Home/Away ATS splits
- Trends vs spread range

## Value Bet Criteria

| Edge | Recommendation |
|------|----------------|
| < 0% | No bet |
| 0-2% | Skip or tiny ticket |
| 2-5% | Standard unit (1-2%) |
| > 5% | Strong value (3-4%) |

## Bankroll Management

### Unit Sizing
- **Standard unit**: 1-2% of bankroll
- **Strong value**: 3-4% max
- Never bet more than 5% on single play

### Kelly Criterion (Fractional)
```
Kelly % = (Edge) / (Odds - Edge)
Use 1/4 or 1/2 Kelly for safety
```

## Common Mistakes to Avoid

1. **Betting your team** - Emotional bias kills profits
2. **Chasing losses** - Never increase bet size after loss
3. **Parlays** - House edge compounds exponentially
4. **Ignoring line movement** - Sharp money tells you something
5. **Overvaluing recent results** - Small sample sizes lie

## Sport-Specific Notes

### NCAAB (College Basketball)
- Home court advantage is HUGE (~3-4 points)
- Tournament games = neutral site, different dynamics
- Look for rest disadvantages (played 2 days ago)
- Style matchups matter more than records

### NFL
- Weather impacts totals significantly
- Divisional games tend to be lower scoring
- Playoff implications affect effort

## Tools Usage

```bash
# Full research report
python3 skills/sports-betting/scripts/betting_research.py TEAM1 TEAM2 SPORT

# Quick odds analysis
python3 skills/sports-betting/scripts/odds_analyzer.py WIN_PROB ODDS
```
