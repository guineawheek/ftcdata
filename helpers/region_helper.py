import .NominatimHelper

class RegionHelper:
    # these states lack a real state championship and so are redirected to others.
    COMBINED_STATES = {
            "Maine": "New Hampshire",
            "South Dakota": "North Dakota",
            "Arizona": "Arizona/New Mexico",
            "New Mexico": "Arizona/New Mexico",
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

    NYHV_COUNTIES = [
            "Clinton",
            "Essex",
            "Warren",
            "Washington",
            "Saratoga",
            "Fulton",
            "Schenectady",
            "Montgomery",
    ]

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

        if team.number in MI_HS_TEAMS:
            return "Michigan Highschool"
        
        # New York, Texas, and California are all subdivided into like, four regions.
        # These are a mess, so let's start with New York
        if team.state_prov == "New York":
            # let's start with an easy one:
            if team.city.startswith("New York"):
                return "New York City"

            county = await NominatimHelper.get_county(team)
            if county in NYHV_COUNTIES:
                return "New York Hudson Valley"
            elif county in ["Suffolk", "Nassau"]:
                return "New York Long Island"

            # If we can't figure it out, we'll just assume Excelsior.
            return "New York Excelsior"

        if team.state_prov == "California":
            # California seems to lack stricty defined borders, so we're just gonna get
            # coordinates and check their proximity to San Jose, Los Angeles, and San Diego.

