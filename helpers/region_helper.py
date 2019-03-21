from helpers import NominatimHelper

def dist(lat1, lon1, lat2, lon2): return ((lat2-lat1)**2 + (lon2-lon2)**2) ** 0.5 
class RegionHelper:
    # these states lack a real state championship and so are redirected to others.
    COMBINED_STATES = {
            "Maine": "New Hampshire",
            "South Dakota": "North Dakota",
            "Arizona": "Arizona/New Mexico",
            "New Mexico": "Arizona/New Mexico",
            "Kansas": "Missouri",
            "District Of Columbia": "Maryland"
    }

    # these teams did not compete in FiM; instead they competed at the separate
    # Michigan High School championship. 
    # You may be gone, but you will never be forgotten.
    # o7
    MI_HS_TEAMS = [
        37,
        38,
        39,
        5256,
        4507,
        6288,
        7599,
        7952,
        9345,
        11314,
        12062,
        12086,
    ]

    NYHV_COUNTIES = [i + " County" for i in (
        "Clinton",
        "Essex",
        "Warren",
        "Washington",
        "Saratoga",
        "Fulton",
        "Montgomery",
        "Rensselaer",
        "Schenectady",
        "Albany",
        "Schoharie",
        "Delaware",
        "Greene",
        "Columbia",
        "Ulster",
        "Dutchess",
        "Sullivan",
        "Orange",
        "Putnam", 
        "Westchester",
        "Rockland"
    )]

    NYC_COUNTIES = [i + " County" for i in (
        "Bronx",
        "Kings",
        "New York",
        "Queens",
        "Richmond"
    )]

    # ntx
    TX_NTX = [i + " County" for i in (
        "Wichita", 
        "Clay", 
        "Montague", 
        "Cooke", 
        "Grayson", 
        "Fannin", 
        "Lamar", 
        "Red River", 
        "Bowie", 
        "Cass", 
        "Morris", 
        "Titus", 
        "Franklin", 
        "Hopkins", 
        "Delta", 
        "Hunt", 
        "Collin", 
        "Denton", 
        "Wise", 
        "Jack", 
        "Young", 
        "Archer", 
        "Stephens", 
        "Palo Pinto", 
        "Parker", 
        "Tarrant", 
        "Dallas", 
        "Rockwall", 
        "Kaufman", 
        "Van Zandt", 
        "Rains", 
        "Wood", 
        "Camp", 
        "Upshur", 
        "Marion", 
        "Harrison", 
        "Gregg", 
        "Smith", 
        "Rusk", 
        "Panola", 
        "Henderson", 
        "Cherokee", 
        "Anderson", 
        "Ellis", 
        "Navarro", 
        "Freestone", 
        "Limestone", 
        "Hill", 
        "Johnson", 
        "Hood", 
        "Somervell", 
        "Bosque", 
        "McLennan", 
        "Falls", 
        "Bell", 
        "Coryell", 
        "Hamilton", 
        "Erath", 
        "Eastland", 
        "Comanche", 
        "Brown", 
        "Mills", 
        "Lampasas", 
        "San Saba", 
    )]

    # Southeast
    TX_SE = [i + " County" for i in (
        "Shelby", 
        "Nacogdoches", 
        "San Augustine", 
        "Sabine", 
        "Angelina", 
        "Jasper", 
        "Newton", 
        "Tyler", 
        "Polk", 
        "Trinity", 
        "Houston", 
        "Leon", 
        "Robertson", 
        "Brazos", 
        "Burleson", 
        "Madison", 
        "Walker", 
        "San Jacinto", 
        "Grimes", 
        "Montgomery", 
        "Liberty", 
        "Hardin", 
        "Orange", 
        "Jefferson", 
        "Chambers", 
        "Harris", 
        "Waller", 
        "Washington", 
        "Fayette", 
        "Austin", 
        "Colorado", 
        "Fort Bend", 
        "Wharton", 
        "Brazoria", 
        "Galveston", 
        "Matagorda", 
        "Jackson", 
        "Victoria", 
        "Calhoun", 
    )]

    # Alamo, the hardest region xd
    TX_AL = [i + " County" for i in (
        "Crockett", 
        "Schleicher", 
        "Menard", 
        "Mason", 
        "Llano", 
        "Burnet", 
        "Williamson", 
        "Milam", 
        "Lee", 
        "Bastrop", 
        "Travis", 
        "Caldwell", 
        "Hays", 
        "Blanco", 
        "Gillespie", 
        "Kimble", 
        "Sutton", 
        "Val Verde", 
        "Edwards", 
        "Real", 
        "Bandera", 
        "Kerr", 
        "Kendall", 
        "Comal", 
        "Guadalupe", 
        "Gonzales", 
        "Lavaca", 
        "Dewitt", 
        "Karnes", 
        "Wilson", 
        "Bexar", 
        "Medina", 
        "Uvalde", 
        "Kinney", 
        "Maverick", 
        "Zavala", 
        "Frio", 
        "Atascosa", 
        "Live Oak", 
        "Bee", 
        "Goliad", 
        "Refugio", 
        "Aransas", 
        "San Patricio", 
        "McMullen", 
        "La Salle", 
        "Dimmit", 
        "Webb", 
        "Duval", 
        "Jim Wells", 
        "Nueces", 
        "Kleberg", 
        "Kenedy", 
        "Brooks", 
        "Jim Hogg", 
        "Zapata", 
        "Starr", 
        "Hidalgo", 
        "Willacy", 
        "Cameron", 
    )]

    # Original supers layouts, edge cases are handled by get_supers.
    # Don't query this directly.
    EAST_SUPERS = [
            "Maine",
            "New Hampshire",
            "Vermont",
            "Massachusetts",
            "Rhode Island",
            "Connecticut", 
            "New York",
            "Pennsylvania",
            "New Jersey",
            "Maryland",
            "District of Columbia",
            "Delaware",
            "Virginia"
    ]
    NORTH_SUPERS = [
            "West Virginia",
            "Ohio",
            "Michigan",
            "Indiana",
            "Wisconsin",
            "Illinois",
            "Minnesota",
            "Iowa",
            "Missouri",
            "North Dakota",
            "South Dakota",
            "Nebraska",
            "Kansas"
    ]
    WEST_SUPERS = [
            "Montana",
            "Wyoming",
            "Colorado",
            "New Mexico",
            "Idaho",
            "Utah",
            "Arizona",
            "Washington",
            "Oregon",
            "Nevada",
            "California",
            "Alaska"
            # Hawaii omitted because they are like international 
    ]
    SOUTH_SUPERS = [
            "North Carolina",
            "South Carolina",
            "Georgia",
            "Florida",
            "Kentucky",
            "Tennessee",
            "Alabama",
            "Missisippi",
            "Arkansas",
            "Louisiana",
            "Oklahoma",
            "Texas"
    ]


    @classmethod
    def region_abbrev(cls, region_name):
        pass 

    @classmethod
    async def get_region(cls, team):
        if team.country not in ("USA", "Canada"):
            return team.country
        
        # handle all the niches of regional bs in first lol
        # canada is pretty simple, we can usually assume that teams
        # have their own regional ig?
        if team.country == "Canada":
            return team.state_prov

        if team.state_prov in cls.COMBINED_STATES:
            return cls.COMBINED_STATES[team.state_prov]

        if team.number in cls.MI_HS_TEAMS:
            return "Michigan Highschool"
        
        # New York, Texas, and California are all subdivided into like, four regions.
        # These are a mess, so let's start with New York
        if team.state_prov == "New York":
            # let's start with an easy one:
            if team.city.startswith("New York"):
                return "New York City"

            county = await NominatimHelper.get_county(round(team.lat, 2), round(team.lon, 2))
            if county in cls.NYC_COUNTIES:
                return "New York City"
            if county in cls.NYHV_COUNTIES:
                return "New York Hudson Valley"
            elif county in ["Suffolk County", "Nassau County"]:
                return "New York Long Island"

            # If we can't figure it out, we'll just assume Excelsior.
            return "New York Excelsior"

        if team.state_prov == "California":
            # California seems to lack stricty defined borders, so we're just gonna get
            # coordinates and check their proximity to San Jose, Los Angeles, and San Diego.

            # god i hope this works alright

            # get the ez ones out of the way:
            if team.city.strip() == "San Diego":
                return "California San Diego"
            if team.city.strip() == "Los Angeles":
                return "California Los Angeles"
            
            return min([
                ("California NorCal", dist(team.lat, team.lon, 37.338, 121.886)),
                ("California Los Angeles", dist(team.lat, team.lon, 34.052, 118.244)),
                ("California San Diego", dist(team.lat, team.lon, 32.716, 117.161)),
            ], key=lambda n: n[1])[0]

        elif team.state_prov == "Texas":
            # oops texas is thicc!
            county = await NominatimHelper.get_county(round(team.lat, 2), round(team.lon, 2))
            if county in cls.TX_NTX:
                return "Texas NTX"
            elif county in cls.TX_SE:
                return "Texas Southeast"
            elif county in cls.TX_AL:
                return "Texas Alamo"
            else:
                return "Texas Panhandle"

        return team.state_prov

    @classmethod
    async def get_supers(cls, state_prov, year=None):
        # use state_prov, don't use region!!!
        spr = state_prov
        if year is None:
            year = 2018

        # supers location swaps after resq
        if year > 2015:
            if spr == "Kentucky":
                return "North"

            if spr == "West Virginia":
                return "East"
        # supers location swaps because of 2champs
        if spr in ("Missouri", "Kansas") and year > 2016:
            return "South"
        
        if spr in cls.EAST_SUPERS:
            return "East"
        
        elif spr in cls.NORTH_SUPERS:
            return "North"
        
        elif spr in cls.WEST_SUPERS:
            return "West"
        
        elif spr in cls.SOUTH_SUPERS:
            return "South"

        return None
