from .models import EventType, MatchEvent


def demo_events():
    rows = [
        ("e01", 1, 64, EventType.POSSESSION_RECOVERY, "east", "p_a_reid", "A. Reid", 71, 24, "won"),
        ("e02", 2, 78, EventType.SHOT, "east", "player_7", "Player 7", 88, 46, "saved"),
        ("e03", 3, 151, EventType.POSSESSION_RECOVERY, "east", "p_m_sol", "M. Sol", 76, 71, "won"),
        ("e04", 4, 171, EventType.SHOT, "east", "player_7", "Player 7", 91, 55, "blocked"),
        ("e05", 5, 232, EventType.POSSESSION_RECOVERY, "east", "p_a_reid", "A. Reid", 73, 46, "won"),
        ("e06", 6, 244, EventType.SHOT, "east", "player_7", "Player 7", 93, 49, "goal"),
    ]
    return [
        MatchEvent(
            id=id_, sequence_number=seq, event_time_seconds=time, event_type=kind,
            team_id=team, player_id=player_id, player_name=player_name,
            location_x=x, location_y=y, outcome=outcome,
        )
        for id_, seq, time, kind, team, player_id, player_name, x, y, outcome in rows
    ]
