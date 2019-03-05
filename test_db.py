import asyncio
import asyncpg
import datetime
import pprint
from models import Team
from db.orm import orm

async def main():
    # Establish a connection to an existing database named "test"
    # as a "postgres" user.
    #conn = await asyncpg.connect('postgresql://')
    # Execute a statement to create a new table.
    # await conn.execute('''
    #     CREATE TABLE IF NOT EXISTS users(
    #         id serial PRIMARY KEY,
    #         name text,
    #         dob date
    #     )
    # ''')

    # # Insert a record into the created table.
    # await conn.execute('''
    #     INSERT INTO users(name, dob) VALUES($1, $2)
    # ''', 'Bob', datetime.date(1984, 3, 1))

    # Select a row from the table.
    #row = await conn.fetchrow(
    #    'SELECT * FROM users WHERE name = $1', 'Bob')
    #print(row)
    #pprint.pprint(await conn.fetch("SELECT column_name from information_schema.columns WHERE table_name = 'users' AND table_schema='public'"))
    # *row* now contains
    # asyncpg.Record(id=1, name='Bob', dob=datetime.date(1984, 3, 1))
    await orm.connect(dsn="postgresql://")
    await orm.pool.execute("DROP TABLE IF EXISTS teams;")
    await orm.Model.create_all_tables()

    """
    key: varchar(20)
    year: integer
    rookie_year: integer
    name: text
    org: text
    motto: text
    home_cmp: text
    city: text
    state_prov: text
    country: text
    postalcode: text
    normalized_location: text
    website: text
    """
    t = Team(key="ftc9971",
            year=2018,
            rookie_year=2015,
            name="LANbros",
            org="EDGE Robotics Club/Family Friends",
            motto="",
            home_cmp="north",
            city="Vincentown",
            state_prov="NJ",
            country="USA",
            postalcode="meme",
            normalized_location="",
            website="http://lanbros.org")
    print(await t.insert())
    t.motto = "ez 4 9971"
    t.normalized_location = f"{t.city}, {t.state_prov}, {t.country}"
    print(await Team.select_one({"key":"ftc9971", "home_cmp":"north"}))
    print(await t.update())
    print(t)
    print(await t.delete())
    print(await Team.select())

    # Close the connection.
    await orm.close()

asyncio.get_event_loop().run_until_complete(main())
