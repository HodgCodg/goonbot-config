#!/usr/bin/env python3
"""
Odds Analyzer - Calculate EV and find value bets.
"""

import sys
import json

def implied_probability(odds):
    """Convert odds to implied probability."""
    if odds > 0:
        # American positive odds
        return 100 / (odds + 100)
    else:
        # American negative odds
        return abs(odds) / (abs(odds) + 100)

def calculate_ev(win_prob, odds):
    """Calculate expected value of a bet."""
    if odds > 0:
        # Positive odds: risk $100 to win $odds
        ev = (win_prob * odds) - ((1 - win_prob) * 100)
    else:
        # Negative odds: risk $|odds| to win $100
        ev = (win_prob * 100) - ((1 - win_prob) * abs(odds))
    
    # Normalize to percentage of amount wagered
    if odds > 0:
        return ev / 100  # Per $100 risked
    else:
        return ev / abs(odds)  # Per $|odds| risked

def find_value_bet(win_probability, odds):
    """Determine if bet has positive EV."""
    implied_prob = implied_probability(odds)
    edge = win_probability - implied_prob
    ev = calculate_ev(win_probability, odds)
    
    return {
        "is_value": ev > 0,
        "edge_percentage": edge * 100,
        "ev_percentage": ev,
        "implied_probability": implied_prob * 100,
        "your_probability": win_probability * 100
    }

def compare_odds(lines):
    """Compare odds across multiple books."""
    best_line = None
    best_ev = float('-inf')
    
    for book, data in lines.items():
        ev = calculate_ev(data['win_prob'], data['odds'])
        if ev > best_ev:
            best_ev = ev
            best_line = {'book': book, **data}
    
    return best_line

def bankroll_calculation(stake_pct=0.02, edge=0.05):
    """Kelly criterion approximation for bet sizing."""
    # Fractional Kelly (conservative)
    kelly_fraction = min(edge / max(1.0, 1 - edge), stake_pct)
    return kelly_fraction * 100  # Return as percentage

def analyze_spread_bet(home_team_prob, spread_odds):
    """Analyze point spread bet."""
    result = find_value_bet(home_team_prob, spread_odds)
    result['bet_type'] = 'spread'
    return result

def analyze_total_bet(over_prob, total_odds):
    """Analyze over/under bet."""
    result = find_value_bet(over_prob, total_odds)
    result['bet_type'] = 'total'
    return result

class OddsAnalyzer:
    def __init__(self):
        self.analysis_history = []
        
    def analyze_spread(self, team_name, win_probability, odds):
        """Analyze spread bet."""
        analysis = {
            "team": team_name,
            "bet_type": "spread",
            "your_win_prob": win_probability * 100,
            "odds": odds,
            **find_value_bet(win_probability, odds)
        }
        self.analysis_history.append(analysis)
        return analysis
    
    def analyze_total(self, bet_side, win_probability, odds):
        """Analyze total bet."""
        analysis = {
            "side": bet_side,
            "bet_type": "total",
            "your_win_prob": win_probability * 100,
            "odds": odds,
            **find_value_bet(win_probability, odds)
        }
        self.analysis_history.append(analysis)
        return analysis
    
    def recommend_stake(self, edge_pct):
        """Recommend bet size based on edge."""
        if edge_pct <= 0:
            return {"recommendation": "No bet", "stake_pct": 0}
        elif edge_pct < 2:
            return {"recommendation": "Small bet", "stake_pct": 1}
        elif edge_pct < 5:
            return {"recommendation": "Standard bet", "stake_pct": 2}
        else:
            return {"recommendation": "Strong value", "stake_pct": min(4, edge_pct / 2)}

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: odds_analyzer.py WIN_PROB ODDS")
        print("Example: odds_analyzer.py 0.58 -110")
        sys.exit(1)
    
    win_prob = float(sys.argv[1])
    odds = int(sys.argv[2])
    
    analyzer = OddsAnalyzer()
    result = find_value_bet(win_prob, odds)
    stake_rec = analyzer.recommend_stake(result['edge_percentage'])
    
    output = {
        **result,
        "stake_recommendation": stake_rec
    }
    
    print(json.dumps(output, indent=2))
