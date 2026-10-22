import unittest

from derive_events import Box, derive_events, identify_ball


class EventAdapterTests(unittest.TestCase):
    def test_identifies_small_persistent_track_as_ball(self):
        frames = {
            frame: [
                Box(frame, 1, frame * 4, 40, 8, 8),
                Box(frame, 2, 100, 80, 30, 90),
            ]
            for frame in range(1, 21)
        }
        ball_id, report = identify_ball(frames, 20)
        self.assertEqual(ball_id, 1)
        self.assertEqual(report["status"], "candidate")

    def test_progression_keeps_frame_evidence(self):
        frames = {}
        for frame in range(1, 51):
            ball_x = 100 + frame * 8
            frames[frame] = [
                Box(frame, 1, ball_x, 200, 8, 8),
                Box(frame, 2, ball_x - 5, 170, 24, 50),
                Box(frame, 3, ball_x + 60, 170, 24, 50),
                Box(frame, 4, ball_x + 70, 170, 24, 50),
            ]
        meta = {"width": 1000, "height": 500, "fps": 25}
        events = derive_events(frames, meta, 1, {2: "team_a", 3: "team_b", 4: "team_b"})
        progression = [event for event in events if event["type"] == "RAPID_PROGRESSION_CANDIDATE"]
        self.assertTrue(progression)
        self.assertIn("start_frame", progression[0]["evidence"])
        self.assertEqual(progression[0]["status"], "candidate")


if __name__ == "__main__":
    unittest.main()
