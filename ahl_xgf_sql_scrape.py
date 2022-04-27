"""
Usage: python ahl_xgf_sql_scrap.py <latest game ID>

Populate the ahlxgf postgresql database with the shot data
"""

from urllib import request
import requests
import json
import psycopg2
import sys
import numpy as np
from requests.sessions import Session
from concurrent.futures import ThreadPoolExecutor
from threading import local,Lock
from tqdm import tqdm

#build dataset with data from first game w/ shot and goal data
#Game is from Oct 6, 2017
first_game_id = 1017122

#callbacks._8 includes all the shot/goal data including x,y coordinates etc...
#callbacks._5 also works
url = 'https://lscluster.hockeytech.com/feed/index.php?feed=statviewfeed&view=gameCenterPlayByPlay&game_id='
end ='&key=50c2cd9b5e18e390&client_code=ahl&lang=en&league_id=&callback=angular.callbacks._8'
thread_local = local()
mutex = Lock()

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

#drop previous table if it exists
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
        Goal BOOL,
        Strength INT)'''
    cursor.execute(create_table)
    connection.commit()
except (Exception, psycopg2.DatabaseError) as error :
    print ("Error while creating PostgreSQL table", error)

def make_url_list() -> list:
    url_list = []
    for n in range(first_game_id,last_game+1,1):
        fullurl = url + str(n) + end
        url_list.append(fullurl)
    return url_list

def request_all(url_list:list) -> None:
    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(request_url,url_list)

def get_session() -> Session:
    if not hasattr(thread_local,'session'):
        thread_local.session = requests.Session()
    return thread_local.session

def request_url(url:str) -> None:
    session = get_session()
    with session.get(url) as resp:
        resp = resp.text[:-1]
        resp = resp[21:]
        json_data = json.loads(resp)
        bar.update(1)

        #Team1 is the team that the strengths will be calculated for
        #Team2 is just the inverse of Team1
        #ie, if Team1 is on the PP (strength = +1), Team2 must have the inverse strength == -1 (5v4 PK)
        team = []
        for i in json_data:
            event = i['event']
            if event == "goalie_change":
                team_id = i['details']['team_id']
                team.append(team_id) 
        Team1 = int(team[0])
        Team2 = int(team[1])
        # Create and populate array with strengths
        # 3 20 min periods plus possible 5 min OT (for regular season) = 65 min * 60 secs = 3900 secs
        # gametime == [0,1,2.......,3899]
        gametime = np.arange(0,3900)
        zero_array = np.zeros(3900)
        #combine arrays into a 2D array where a row is the time combined with the strength at that moment 
        #in time (for Team1)
        # Access as: strengths[row,col]
        strengths = np.vstack((gametime, zero_array)).T
        # First run through the events, we create and populate the strength array
        # Strengths are calculated as the advantage or disadvantage of Team 1
        # ie, +1 can indicate 5v4 OR 4v3 in favor of Team1
        for i in json_data:
            #get the event type and assume we have all metadata
            event = i['event']

            ######### calculate strengths at each moment in time ########

            #keep the time of (the last penalty + penalty length) 
            last_penalty_time = 0

            if event == "penalty":
                time_raw = i['details']['time'].split(":")
                period = i['details']['period']['id']
                period = int(period)
                #get time in seconds of the penalty
                time = ((period-1) * 20 * 60) + (int(time_raw[0]) * 60) + int(time_raw[1])
                length = i['details']['minutes'].split(".")
                length = int(length[0])
                against_team = i['details']['againstTeam']['id']
                against_team = int(against_team)
                #Team1 goes on the PP
                if against_team == Team2:
                    if length == 2:
                        last_penalty_time = time + 120
                        #set the strength 
                        for i in range(121):
                            if int(strengths[time+i,1]) < 2:
                                strengths[time+i,1] += 1
                    if length == 5:
                        last_penalty_time = time + 300
                        for i in range(301):
                            if int(strengths[time+i,1]) < 2:
                                strengths[time+i,1] += 1
                
                #Team1 goes on the PK
                elif against_team == Team1:
                    if length == 2:
                        last_penalty_time = time + 120
                        #set the strength 
                        for i in range(121):
                            if int(strengths[time+i,1]) > -2:
                                strengths[time+i,1] -= 1
                    if length == 5:
                        last_penalty_time = time + 300
                        for i in range(301):
                            if int(strengths[time+i,1]) > -2:
                                strengths[time+i,1] -= 1
            
            #we only care about PP goals becuase SH or EV goals don't change strength
            elif event == "goal":
                pp_goal = i['details']['properties']['isPowerPlay']
                pp_goal = int(pp_goal)
                team_id = i['details']['team']['id']
                team_id = int(team_id)
                if pp_goal == 1:
                    #time of goal in seconds
                    time_raw = i['details']['time'].split(":")
                    period = i['details']['period']['id']
                    period = int(period)
                    time_of_goal = ((period-1) * 20 * 60) + (int(time_raw[0]) * 60) + int(time_raw[1])

                    #time of previous penalty + length of penalty is last_penalty_time
                    #remove the additional "strengths" after a PP goal is scored
                    #ie, if Team1 goes on the PP at 10:00 and the PP goal is scored at 8:50, then remove
                    #the additional +1 strengths from 8:51 to 8:00
                    if team_id == Team1:
                        for i in range(time_of_goal+1,last_penalty_time+1):
                            if int(strengths[i,1]) > -2:
                                strengths[i,1] -= 1

                    elif team_id == Team2:
                        for i in range(time_of_goal+1,last_penalty_time+1):
                            if int(strengths[i,1]) < 2:
                                strengths[i,1] += 1
        
        # 2nd run through the events, we get the goal and combine that with strength. Add to SQL DB.
        for i in json_data:
            #get the event type and assume we have all metadata
            event = i['event']
            if event == "shot" or event == "goal":
                #set the X value relative to x distance from the net
                # this is because the home team's x value is (max X)/2 + true X
                # max x = 593/2
                # X value is out towards the blue line
                xLocation = i['details']['xLocation']
                if xLocation > 593/2:
                    xLocation = 593 - xLocation
                else:
                    pass
                #get the Y value as a Y distance relative to the net
                #largest Y val is 300.
                #since origin is at top left we must flip all the y values
                yLocation = i['details']['yLocation']
                yLocation = 300 - yLocation
                isGoal = i['details']['isGoal']

                #get the team id of the shooter
                if event == "goal":
                    team_id = i['details']['team']['id']
                    team_id = int(team_id)
                elif event == "shot":
                    team_id = i['details']['shooterTeamId']
                    team_id = int(team_id)

                #get time of goal or shot and match to strength
                time_raw = i['details']['time'].split(":")
                period = i['details']['period']['id']
                period = int(period)
                event_time = ((period-1) * 20 * 60) + (int(time_raw[0]) * 60) + int(time_raw[1])
                
                #if the team who shot on net or scored is Team1, set strength equal to the strength array 
                #if the team who shot on net or scored is Team1, set strength to the inverse of the strength array
                if team_id == Team1:
                    event_strength = strengths[event_time,1]
                    event_strength = int(event_strength)
                else:
                    event_strength = strengths[event_time,1]
                    event_strength = -int(event_strength)
                
                values = """ INSERT INTO ahlxgf (XLocation, YLocation, Goal, Strength) VALUES (%s,%s,%s,%s)"""
                mutex.acquire()
                cursor.execute(values, (xLocation,yLocation,isGoal,event_strength))
                connection.commit()
                mutex.release()
                
#setup the progress bar
global bar 
bar = tqdm(desc="Progress",total=(last_game-first_game_id))

url_list = make_url_list()
request_all(url_list)

bar.close()

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