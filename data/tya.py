from models import Event, EventType
from helpers import RegionHelper
from db.orm import orm
import aiohttp
import uvloop
import asyncio
import datetime

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
        events = {}
        for event in tya_events.values():
            if len(event) < 2:
                raise RuntimeError(f"event {e[0]['event_uuid']} lacks divisions!")
            edata = event[0]
            if edata['state'] == "Pennsylvania":
                # ftcpenn scrapers have better data, so we completely ignore penn
                continue
            event_type = cls.event_type(edata)
            multi_div = len(event) > 2
            basename = '2013' + edata['event_uuid']
            for i, ediv in enumerate(event[1:], 1):
                e = Event(key=f"{basename}{i % 3 if multi_div else ''}",
                          year=2013,
                          name=edata['name'] + " " + edata['type'],
                          city=edata['city'],
                          state_prov=edata['state'],
                          country=edata['country'],
                          start_date=to_datetime(edata['start_date']),
                          end_date=to_datetime(edata['end_date']),
                          event_type=event_type)
                if multi_div:
                    if i == 3:
                        e.division_keys = [basename + "1", basename + "2"]
                    else:
                        e.parent_event_key = basename + "0"
                        e.name += f" {ediv['name']} Division"
                supers = await RegionHelper.get_supers(e.state_prov)
                if event_type == EventType.QUALIFIER:
                    if e.state_prov != "Nebraska":
                        e.advances_to = "2013iacmp" # all TYA qualifiers are in Iowa
                    else:
                        e.advances_to = "2013necmp"
                elif event_type == EventType.REGIONAL_CMP and supers:
                    e.advances_to = f"2013{supers[0].lower()}sr0"
                elif not e.key.startswith("2013cmp"):
                    e.advances_to = "2013cmp0"
                if event_type not in (EventType.SUPER_REGIONAL, EventType.WORLD_CHAMPIONSHIP):
                    if e.key[4:] in cls.REGION_MAP:
                        e.region = cls.REGION_MAP[e.key[4:]]
                    else:
                        e.region = e.state_prov
                events[ediv['id']] = e
                #e.insert(upsert="NOTHING")
         


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
