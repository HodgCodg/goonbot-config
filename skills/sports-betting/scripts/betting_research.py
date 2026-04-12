#!/usr/bin/env python3
"""
Sports Betting Research Tool
Gathers comprehensive data for informed betting decisions.
"""

import sys
import json
from datetime import datetime, timedelta

def fetch_with_retry(url, max_attempts=2):
    """Fetch URL with retry logic."""
    try:
        result = subprocess.run(
            ['python3', '/home/botvm/.openclaw/workspace/skills/fetch/scripts/fetch.py', url],
            capture_output=True, text=True, timeout=15
        )
        return result.stdout if result.returncode == 0 else None
    except:
        return None

def search_web(query, num_results=8):
    """Search web for sports information."""
    cmd = f'python3 /home/botvm/.openclaw/workspace/skills/searxng/scripts/search.py "{query}" -n {num_results}'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
    return result.stdout

def analyze_team_form(team_name, sport="NCAAB"):
    """Analyze team's recent form and statistics."""
    queries = [
        f"{team_name} last 10 games record {sport}",
        f"{team_name} home away record {datetime.now().strftime('%Y')}",
        f"{team_name} offensive defensive rating {sport}",
    ]
    
    form_data = {
        "recent_games": [],
        "home_record": None,
        "away_record": None,
        "offensive_rating": None,
        "defensive_rating": None,
        "pace": None
    }
    
    for query in queries:
        results = search_web(query, 5)
        # Parse results for relevant data
        if "last 10" in results.lower() or "record" in results.lower():
            form_data["recent_form"] = extract_record(results)
        
    return form_data

def get_injury_report(team_name):
    """Get injury report for team."""
    query = f"{team_name} injury report {datetime.now().strftime('%Y-%m-%d')}"
    results = search_web(query, 4)
    
    injuries = []
    # Parse for player names and status
    if "out" in results.lower() or "questionable" in results.lower():
        injuries = extract_injuries(results)
    
    return {"team": team_name, "injuries": injuries}

def get_head_to_head(team1, team2):
    """Get head-to-head history between teams."""
    query = f"{team1} vs {team2} history last 5 meetings"
    results = search_web(query, 4)
    
    h2h = {
        "meetings": [],
        "team1_wins": 0,
        "team2_wins": 0
    }
    return h2h

def get_betting_trends(team_name):
    """Get betting trends for team (ATS, totals)."""
    query = f"{team_name} ATS record over under {datetime.now().strftime('%Y')}"
    results = search_web(query, 4)
    
    trends = {
        "ats_record": None,
        "over_under_record": None,
        "home_ats": None,
        "away_ats": None
    }
    return trends

def extract_record(text):
    """Extract win-loss record from text."""
    import re
    match = re.search(r'(\d+)-(\d+)', text)
    if match:
        return {"wins": int(match.group(1)), "losses": int(match.group(2))}
    return None

def extract_injuries(text):
    """Extract injury information from text."""
    injuries = []
    # Basic extraction - would need refinement
    return injuries

class BettingResearcher:
    def __init__(self, team1, team2, sport="NCAAB"):
        self.team1 = team1
        self.team2 = team2
        self.sport = sport
        
    def full_analysis(self):
        """Run complete betting analysis."""
        report = {
            "matchup": f"{self.team1} vs {self.team2}",
            "sport": self.sport,
            "timestamp": datetime.now().isoformat(),
            "team1_form": analyze_team_form(self.team1, self.sport),
            "team2_form": analyze_team_form(self.team2, self.sport),
            "team1_injuries": get_injury_report(self.team1),
            "team2_injuries": get_injury_report(self.team2),
            "head_to_head": get_head_to_head(self.team1, self.team2),
            "team1_trends": get_betting_trends(self.team1),
            "team2_trends": get_betting_trends(self.team2)
        }
        return report
    
    def quick_summary(self):
        """Quick summary for rapid decisions."""
        full = self.full_analysis()
        summary = {
            "matchup": full["matchup"],
            "team1_recent_form": full["team1_form"].get("recent_form"),
            "team2_recent_form": full["team2_form"].get("recent_form"),
            "key_injuries_team1": len(full["team1_injuries"]["injuries"]),
            "key_injuries_team2": len(full["team2_injuries"]["injuries"])
        }
        return summary

if __name__ == "__main__":
    import subprocess
    
    if len(sys.argv) < 3:
        print("Usage: betting_research.py TEAM1 TEAM2 [SPORT]")
        print("Example: betting_research.py Duke Michigan NCAAB")
        sys.exit(1)
    
    team1 = sys.argv[1]
    team2 = sys.argv[2]
    sport = sys.argv[3] if len(sys.argv) > 3 else "NCAAB"
    
    researcher = BettingResearcher(team1, team2, sport)
    report = researcher.full_analysis()
    
    print(json.dumps(report, indent=2))
