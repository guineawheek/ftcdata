import dataclasses

def _park_score(s):
    if s in (1, 3):
        return 5
    if s in (2, 4):
        return 10
    return 0

__all__ = ["ResQMatchDetails", "VelocityVortexMatchDetails", "RelicRecoveryMatchDetails", "RoverRuckusMatchDetails"]

@dataclasses.dataclass
class BaseMatchDetails:
    minor_penalties: int
    major_penalties: int

    @property
    def penalty(self):
        return self.minor_penalties * 10 + self.major_penalties * 40

    def to_dict(self):
        return dataclasses.asdict(self)

@dataclasses.dataclass
class ResQMatchDetails(BaseMatchDetails):
    auto_beacons: int
    auto_robot1_park: int # 1, 2, 3 is 5, 10, 20, 40 is mountain
    auto_robot2_park: int
    auto_climbers: int
    teleop_climbers: int
    teleop_floor: int
    teleop_low: int
    teleop_mid: int
    teleop_high: int
    teleop_zipline: int
    teleop_robot1_park: int #5 for tile floor, 10, 20, 40 for mountain
    teleop_robot2_park: int
    endgame_hang: int
    endgame_all_clear: int

    # TODO: finish

@dataclasses.dataclass
class VelocityVortexMatchDetails(BaseMatchDetails):
    auto_beacons: int
    auto_cap_ball: bool
    auto_center_balls: int
    auto_corner_balls: int
    auto_robot1_park: int
    auto_robot2_park: int
    teleop_center_balls: int
    teleop_corner_balls: int
    teleop_beacons: int
    endgame_cap_level: int

    @property
    def auto(self):
        return self.auto_beacons * 30 + int(self.auto_cap_ball) * 5 + self.auto_center_balls * 15 + \
               self.auto_corner_balls * 5 + _park_score(self.auto_robot1_park) + _park_score(self.auto_robot2_park)

    @property
    def teleop(self):
        return self.teleop_center_balls * 5 + self.teleop_corner_balls + self.teleop_beacons * 10

    @property
    def endgame(self):
        return int(2 ** (self.endgame_cap_level - 1))

    @property
    def total(self):
        return self.auto + self.teleop + self.endgame + self.penalty


@dataclasses.dataclass
class RelicRecoveryMatchDetails(BaseMatchDetails):
    auto_jewels: int
    auto_glyphs: int
    auto_keys: int
    auto_parks: int
    teleop_glyphs: int
    teleop_rows: int
    teleop_cols: int
    teleop_ciphers: int
    endgame_relic_1: int
    endgame_relic_2: int
    endgame_relic_3: int
    endgame_relic_standing: int
    endgame_balance: int

    @property
    def auto(self):
        return self.auto_jewels * 30 + self.auto_glyphs * 15 + self.auto_keys * 30 + self.auto_parks * 10

    @property
    def teleop(self):
        return self.teleop_glyphs * 2 + self.teleop_rows * 10 + self.teleop_cols * 20 + self.teleop_ciphers * 30

    @property
    def endgame(self):
        return self.endgame_relic_1 * 10 + self.endgame_relic_2 * 20 + self.endgame_relic_3 * 40 + \
               self.endgame_relic_standing * 15 + self.endgame_balance * 20

@dataclasses.dataclass
class RoverRuckusMatchDetails(BaseMatchDetails):
    auto_lands: int
    auto_claims: int
    auto_parks: int
    auto_samples: int
    teleop_depot: int
    teleop_gold: int
    teleop_silver: int
    endgame_latch: int
    endgame_crater: int
    endgame_crater_full: int

    @property
    def auto(self):
        return self.auto_lands * 30 + self.auto_claims * 15 + self.auto_parks * 10 + self.auto_samples * 25

    @property
    def teleop(self):
        return self.teleop_depot * 2 + (self.teleop_gold + self.teleop_silver) * 5

    @property
    def endgame(self):
        return self.endgame_latch * 50 + self.endgame_crater * 15 + self.endgame_crater_full * 25
"""
#### Autonomous
**[29] [43] Number of Beacons Pressed**: 0, 1, or 2  
**[30] [44] Moved Cap Ball**: TRUE or FALSE  
**[31] [45] Balls Scored into CenterVortex**  
**[32] [46] Balls Scored into CornerVortex**  
**[33] [47] Robot1 Parked**: 1 (on Center), 2 (Completely on Center), 3 (on Corner Vortex), 4 (Completely on Corner Vortex)  
**[34] [48] Robot2 Parked**: 1 (on Center), 2 (Completely on Center), 3 (on Corner Vortex), 4 (Completely on Corner Vortex)  
#### TeleOp  
**[35] [49] Beacons scored at end of Teleop**: 0 - 4  
**[36] [50] Balls Scored into CenterVortex**  
**[37] [51] Balls Scored into CornerVortex**  
#### Endgame
**[38] [52] Cap Ball Level**: 0 (none), 1 (above ground), 2 (high) , 3 (in Center Vortex)  
#### Penalty
**[39] [53] Minor Penalty incurred**: 0, 1, 2...  
**[40] [54] Major Penalty incurred**: 0, 1, 2...  
**[41] [55] Minor Penalty received from the opposing alliance**: 0, 1, 2...  
**[42] [56] Major Penalty received from the opposing alliance**: 0, 1, 2...  

"""
