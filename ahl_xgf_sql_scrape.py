"""
Usage: python ahl_xgf_sql_scrape.py <latest game ID>

Populate the ahlxgf postgresql database with the shot data
"""

import requests
import json
import psycopg2
import sys

#build dataset with data from first game w/ shot and goal data
#Game is from Oct 6, 2017
first_game_id = 1017122

#callbacks._8 includes all the shot/goal data including x,y coordinates etc...
url = 'https://lscluster.hockeytech.com/feed/index.php?feed=statviewfeed&view=gameCenterPlayByPlay&game_id='
end ='&key=50c2cd9b5e18e390&client_code=ahl&lang=en&league_id=&callback=angular.callbacks._8'

# CONNECT TO POSTGRES DB #
try:
    connection = psycopg2.connect(user = <insert username>,
                                  password = <insert password>,
                                  host = <insert sql server addr>,
                                  port = <insert sql server port number>,
                                  database = <insert database name>)
    #Create cursor object. This will allow us to interact with the database and execute commands
    cursor = connection.cursor()

    # Print PostgreSQL version
    cursor.execute("SELECT version();")
    record = cursor.fetchone()
    print("You are connected to - ", record,"\n")

except (Exception, psycopg2.Error) as error :
    print ("Error while connecting to PostgreSQL", error)

if len(sys.argv) < 1:
    print("Error: Please supply the most recent game number")
    exit(1)
else:
    # last game comes from command line arg sys.argv[1]
    last_game = int(sys.argv[1])

#destroy previous table if it exists
try:
    cursor.execute("DROP TABLE ahlxgf;")
    connection.commit()
    print("Table ahlxgf has been dropped")
except (Exception, psycopg2.DatabaseError) as error :
    print ("Error while deleting PostgreSQL table", error)

try:
    create_table = '''CREATE TABLE ahlxgf ( 
        XLocation INT,
        YLocation INT,
        Goal BOOL )'''
    cursor.execute(create_table)
    connection.commit()
except (Exception, psycopg2.DatabaseError) as error :
    print ("Error while creating PostgreSQL table", error)

for n in range(first_game_id,last_game+1,1):
    ######### Loop through the game summaries ###########
    
    fullurl = url + str(n) + end
    
    resp = requests.get(fullurl)
        
    #format resp and resp2 to be json responses. Cut the beggining and end portions off
    resp = resp.text[:-1]
    resp = resp[21:]
    #this response is json
    try:
        resp = json.loads(resp)
        for i in resp:
            #get the event type and assume we have all metadata
            event = i.get("event")
            if event == "shot" or event == "goal":
                details = i.get("details")

                #set the X value relative to x distance from the net
                # this is because the home team's x value is (max X)/2 + true X
                # max x = 593/2
                # X value is out towards the blue line
                xLocation = details.get("xLocation")
                if xLocation > 593/2:
                    xLocation = 593 - xLocation
                else:
                    pass
                #get the Y value as a Y distance relative to the net
                #largest Y val is 300.
                #since origin is at top left we must flip all the y values
                yLocation = details.get("yLocation")
                yLocation = 300 - yLocation
                isGoal = details.get("isGoal")
                values = """ INSERT INTO ahlxgf (XLocation, YLocation, Goal) VALUES (%s,%s,%s)"""
                cursor.execute(values, (xLocation,yLocation,isGoal))
                connection.commit()
        print("Game ID: %i" % n)
    except:
        pass
"""
print("-------------print table---------------")
cursor.execute("SELECT * FROM ahlxgf;")
records = cursor.fetchall()
for record in records:
    print(record)
"""
#Clean up DB. Remove entries w/ Goal == NULL
None_str = "None"
sql_delete_query = """Delete from ahlxgf where Goal is NULL"""
cursor.execute(sql_delete_query)
connection.commit()

#closing database connection.
if(connection):
    cursor.close()
    connection.close()
    print("PostgreSQL connection is closed")