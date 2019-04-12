from models.match_details import *
import csv

class MatchDetailsHelper:

    @classmethod
    def ftcdata_csv_helper(cls, row, offset):
        r = list(row)[offset:]
        return VelocityVortexMatchDetails(
            auto_beacons=r[0],
            auto_cap_ball=r[1] == 'TRUE',
            auto_center_balls=r[2],
            auto_corner_balls=r[3],
            auto_robot1_park=r[4],
            auto_robot2_park=r[5],
            teleop_beacons=r[6],
            teleop_center_balls=r[7],
            teleop_corner_balls=r[8],
            endgame_cap_level=r[9],
            minor_penalties=r[12],
            major_penalties=r[13]
        )
    @classmethod
    def parse_ftcdata_csv(cls, matches, data_path):
        with open(data_path) as f:
            csv_reader = csv.reader(f.read().split("\n"))
        rows = list(csv_reader)[1:]
        for match, row in zip(matches, rows):
            m, red, blue = match
            red.breakdown = cls.ftcdata_csv_helper(row, 29).to_dict()
            blue.breakdown = cls.ftcdata_csv_helper(row, 43).to_dict()

