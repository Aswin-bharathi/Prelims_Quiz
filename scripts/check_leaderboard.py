from app.services.result_service import ResultService
import json

rows = ResultService.get_leaderboard(2,50)
out = [[int(r.get('rank')) if r.get('rank') is not None else None, r.get('score'), r.get('duration'), r.get('lotname')] for r in rows]
print(json.dumps(out, indent=2))
