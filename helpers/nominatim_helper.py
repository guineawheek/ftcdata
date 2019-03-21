from urllib.parse import urlencode
import re
import async_lru
import runtime
import aiohttp

"""
% curl 'http://localhost:8080/search.php?format=json&addressdetails=1&city=San+Jose&state=CA' | python -m json.tool
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100   585    0   585    0     0   3441      0 --:--:-- --:--:-- --:--:--  3441
[
    {
        "place_id": "7598915",
        "licence": "Data \u00a9 OpenStreetMap contributors, ODbL 1.0. https://osm.org/copyright",
        "osm_type": "relation",
        "osm_id": "112143",
        "boundingbox": [
            "37.124503",
            "37.4692175",
            "-122.045672",
            "-121.589153"
        ],
        "lat": "37.3361905",
        "lon": "-121.8905833",
        "display_name": "San Jos\u00e9, Santa Clara County, California, United States of America",
        "class": "place",
        "type": "city",
        "importance": 0.55,
        "icon": "/images/mapicons/poi_place_city.p.20.png",
        "address": {
            "city": "San Jos\u00e9",
            "county": "Santa Clara County",
            "state": "California",
            "country": "United States of America",
            "country_code": "us"
        }
    }
]
"""

class NominatimHelper:
    base = runtime.NOMINATIM_URL
    http = None
    wsfix = re.compile("\s+")

    @classmethod
    async def get_http(cls):
        if cls.http is None:
            cls.http = aiohttp.ClientSession(headers={"User-Agent": "ftcdata geolocation process"})

    @classmethod
    def _plusify(cls, s):
        return cls.wsfix.sub("+", s.strip())

    @classmethod
    async def get_lat_lon(cls, city, state, postalcode=None, misc=None):
        await cls.get_http()
        qs = {
            "format": "json",
            "addressdetails": 1,
            "city": cls._plusify(city),
            "state": cls._plusify(state),
        }
        if postalcode:     
            qs["postalcode"] = postalcode.strip()
        if misc:
            qs.update(misc)

        async with cls.http.get(cls.base + f"/search.php?{urlencode(qs)}") as r:
            data = await r.json()
        if not data:
            return None

        place = data[0]
        return float(place['lat']), float(place['lon'])

    @classmethod
    @async_lru.alru_cache(maxsize=1024)
    async def get_county(cls, lat, lon, misc=None):
        # curl 'http://localhost:8080/reverse.php?format=jsonv2&lat=40.679695&lon=-73.950292'
        await cls.get_http()
        qs = {
            "format": "jsonv2",
            "addressdetails": 1,
            "lat": lat,
            "lon": lon
        }
        async with cls.http.get(cls.base + f"/reverse.php?{urlencode(qs)}") as r:
            place = await r.json()

        if not place or "error" in place:
            if place['error'] != 'Unable to geocode':
                raise Exception(place['error'])
            return None

        try:
            return place["address"]["county"]
        except KeyError:
            pass
        # true desperation lies here
        try:
            for s in (c.strip() for c in place['display_name'].split(",")):
                if s.endswith("County"):
                    return s
        except Exception:
            raise
            return None

