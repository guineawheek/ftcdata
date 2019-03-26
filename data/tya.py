from models import *
from helpers import RegionHelper, OPRHelper
from db.orm import orm
import aiohttp
import uvloop
import asyncio
import datetime
import re

__all__ = ["TheYellowAlliance"]
DEBUG = False
to_datetime = lambda s: datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S")

class TheYellowAlliance:
    REGION_MAP = {
        "canccmp": "California NorCal",
        "casdcmp": "California San Diego",
        "nylicmp": "New York Long Island",
        "nyhvcmp": "New York Hudson Valley",
        # strictly speaking excelsior didn't exist but it's a good approximation
        "nyptcmp": "New York Excelsior",
        "txphcmp": "Texas Panhandle",
        "txsecmp": "Texas Southeast",
        # and neither did alamo...lol
        "txswcmp": "Texas Alamo",
        "azcmp": "Arizona/New Mexico",
    }

    # maps tya awards values to AwardType values
    AWARDS_MAP = {
        '1': AwardType.INSPIRE,
        '2': AwardType.CONNECT,
        '3': AwardType.INNOVATE,
        '4': AwardType.DESIGN,
        '5': AwardType.THINK,
        '6': AwardType.MOTIVATE,
        '7': AwardType.PROMOTE,
        '8': AwardType.COMPASS,
        '9': AwardType.CONTROL,
        '10': AwardType.JUDGES,
    }

    @classmethod
    def event_type(cls, edata):
        if edata['event_uuid'] == 'cmp':
            return EventType.WORLD_CHAMPIONSHIP
        elif edata['type'] == "Super Regional":
            return EventType.SUPER_REGIONAL
        elif edata['type'] == "Championship":
            return EventType.REGIONAL_CMP
        elif edata['type'] == "Qualifier":
            return EventType.QUALIFIER
        else:
            raise RuntimeError(f"unknown type {edata['type']}")

    @classmethod
    async def load(cls, year):
        DATA_URL = "https://ocf.berkeley.edu/~liuderek/ftc/tya_restore.json"
        async with aiohttp.ClientSession() as session:
            async with session.get(DATA_URL) as response:
                data = await response.json()
        # first step, create all the event objects out of divisions

        # create a mapping between the tya ids and the event data
        tya_events = {d['id']: [d] for d in data[5]['data']}
        # then add in division id information to the events table
        for div in data[4]['data']:
            tya_events[div['event_id']].append(div)
        # then we'll "flatten" the events table into an Event object table
        # with different Events for different divisions.
        # The keys are the tya division ids while the values are actual Event objects.
        events, event_key_map = await cls.load_events(tya_events)
        events_obj = list(events.values())
        awards_obj = await cls.load_awards(events, event_key_map, data[3]['data'])
        matches_obj = await cls.load_matches(events, data[6]['data'])
        rankings_obj = await cls.load_rankings(events, data[9]['data'])
        event_keys = list(map(lambda x: x.key, events_obj))
        print("Inserting all objects....")
        await asyncio.gather(*[o.upsert() for o in events_obj + awards_obj + matches_obj + rankings_obj])
        print('...done')

        print("Updating rank column....")
        await asyncio.gather(*[Ranking.update_ranks(k) for k in event_keys])
        print("Calculating OPRs....")
        await asyncio.gather(*[OPRHelper.update_oprs(k) for k in event_keys])

    @classmethod
    async def load_events(cls, tya_events):
        events = {}
        event_key_map = {}
        for event in tya_events.values():
            if len(event) < 2:
                raise RuntimeError(f"event {e[0]['event_uuid']} lacks divisions!")
            edata = event[0]
            if edata['state'] == "Pennsylvania":
                # ftcpenn scrapers have better data, so we completely ignore penn
                continue
            event_type = cls.event_type(edata)
            multi_div = len(event) > 2
            basename = '1314' + edata['event_uuid']
            for i, ediv in enumerate(event[1:], 1):
                e = Event(key=f"{basename}{i % 3 if multi_div else ''}",
                          year=2013,
                          name=edata['name'] + " " + edata['type'],
                          city=edata['city'],
                          state_prov=edata['state'],
                          country=edata['country'],
                          start_date=to_datetime(edata['start_date']),
                          end_date=to_datetime(edata['end_date']),
                          event_type=event_type,
                          playoff_type=PlayoffType.STANDARD)
                if multi_div:
                    if i == 3:
                        e.division_keys = [basename + "1", basename + "2"]
                        e.playoff_type = PlayoffType.BO3_FINALS
                        event_key_map[edata['id']] = e.key
                    else:
                        e.parent_event_key = basename + "0"
                        e.name += f" {ediv['name']} Division"
                else:
                    event_key_map[edata['id']] = e.key

                supers = await RegionHelper.get_supers(e.state_prov)
                # calculate advances_to for quals
                if event_type == EventType.QUALIFIER:
                    if e.state_prov != "Nebraska":
                        e.advances_to = "1314iacmp" # all TYA qualifiers are in Iowa
                    else:
                        e.advances_to = "1314necmp"
                # calculate advances_to for championships and supers
                elif event_type == EventType.REGIONAL_CMP and supers:
                    e.advances_to = f"1314{supers[0].lower()}sr0"
                elif not e.key.startswith("1314cmp"):
                    e.advances_to = "1314cmp0"
                # calculate region of event
                if event_type not in (EventType.SUPER_REGIONAL, EventType.WORLD_CHAMPIONSHIP):
                    if e.key[4:] in cls.REGION_MAP:
                        e.region = cls.REGION_MAP[e.key[4:]]
                    else:
                        e.region = e.state_prov

                events[ediv['id']] = e
                if DEBUG:
                    print(e)
                #e.insert(upsert="NOTHING")
        return events, event_key_map
    
    @classmethod
    async def load_awards(cls, events, event_key_map, tya_awards):
        awards = []
        for award in tya_awards:
            if award['event_id'] not in event_key_map:
                continue
            award_type = cls.AWARDS_MAP[award['award_id']]
            a = Award(name=AwardType.get_names(award_type, year=2013),
                      award_type=award_type,
                      award_place=int(award['place']),
                      event_key=event_key_map[award['event_id']],
                      team_key='ftc'+award['team_id'],
                      recipient_name=None)
            if DEBUG:
                print(a)
            awards.append(a)
        return awards
    
    @classmethod
    async def load_matches(cls, events, matches):
        match_ret = []
        find_matchno = re.compile(".*-([0-9]*)")
        type_map = {
                "QUALIFICATION": "q",
                "PRACTICE": "p",
                "SEMIFINAL": "sf",
                "FINAL": "f",
        }
        for match in matches:
            if match['division_id'] not in events:
                continue
            nmo = match['name'].split('-')
            # always last number
            match_number = int(nmo[-1])
            if len(nmo) == 3:
                set_number = int(nmo[1])
            else:
                set_number = None
            m = Match(event_key=events[match['division_id']].key,
                      comp_level=type_map.get(match['type']),
                      match_number=match_number,
                      set_number=set_number)
            m.gen_keys()
            if match['video']:
                m.videos = [match['video']]
            ms_red = MatchScore(key=m.red, 
                                alliance_color="red",
                                event_key=m.event_key,
                                match_key=m.key,
                                teams=["ftc" + match[t] for t in ('team_id_r1', 'team_id_r2', 'team_id_r3') if match[t] != '0'],
                                total=int(match['total_red']),
                                penalty=int(match['total_red']) - int(match['scored_red']))
            ms_blue = MatchScore(key=m.blue, 
                                alliance_color="blue",
                                event_key=m.event_key,
                                match_key=m.key,
                                teams=["ftc" + match[t] for t in ('team_id_b1', 'team_id_b2', 'team_id_b3') if match[t] != '0'],
                                total=int(match['total_blue']),
                                penalty=int(match['total_blue']) - int(match['scored_blue']))
            if ms_red.total > ms_blue.total:
                m.winner = "red"
            elif ms_blue.total > ms_red.total:
                m.winner = "blue"
            else:
                m.winner = "tie"
            if DEBUG:
                print(m, ms_red, ms_blue)
            match_ret.extend([m, ms_red, ms_blue])
        return match_ret

    @classmethod
    async def load_rankings(cls, events, tya_rank):
        ret = []
        for rank in tya_rank:
            if rank['division_id'] not in events:
                continue
            r = Ranking(event_key=events[rank['division_id']].key,
                        team_key="ftc" + rank['team_id'],
                        qp_rp=int(rank['qp']),
                        rp_tbp=int(rank['rp']),
                        high_score=int(rank['high']),
                        wins=int(rank['qual_wins']),
                        losses=int(rank['qual_losses']),
                        ties=int(rank['qual_ties']),)
            r.played = r.wins + r.losses + r.ties
            ret.append(r)
        return ret
            
async def main():
    global DEBUG
    DEBUG = True
    print("Initializing database connection...")
    await orm.connect(host="/run/postgresql/.s.PGSQL.5432", database="ftcdata", max_size=50)
    await orm.Model.create_all_tables()
    print("Loading TYA archive...")
    await TheYellowAlliance.load(2013) 
    await orm.close()

if __name__ == "__main__":
    uvloop.install()
    asyncio.get_event_loop().run_until_complete(main())
