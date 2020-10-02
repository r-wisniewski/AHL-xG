"""
Usage: python ahl_xgf_sql_smoothing.py 
Take the ahlxgf database & table. Find the shots that are in the vicinity of 
the datapoint. Use a smoothing swath/square to smooth the results.
"""

from datascience import Table
import psycopg2

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
    print("You are connected to the database ahlxgf")

except (Exception, psycopg2.Error) as error :
    print ("Error while connecting to PostgreSQL", error)

#destroy previous table if it exists
try:
    cursor.execute("DROP TABLE ahlxgCalc;")
    connection.commit()
    print("Table ahlxgfCalc has been dropped")
except (Exception, psycopg2.DatabaseError) as error :
    print ("Error while deleting PostgreSQL table", error)

#Create the table in ahlxgf that contains the calculated xG for each datapoint
try:
    create_table = '''CREATE TABLE ahlxgCalc ( 
        XLocation INT,
        YLocation INT,
        xG FLOAT )'''
    cursor.execute(create_table)
    connection.commit()
except (Exception, psycopg2.DatabaseError) as error :
    print ("Error while creating PostgreSQL table", error)

# events is a csv file containing "X Location" and "Y Location"
# based on the database it will calculate an xG value
events = Table.read_table("input_simple.csv")

#populate the ahlxgCalc table w/ datapoints from CSV
for event_row in events.rows:
    values = """INSERT INTO ahlxgCalc (XLocation, YLocation) VALUES (%s,%s)"""
    cursor.execute(values, (int(event_row[0]),int(event_row[1])))

#Grab every datapoint from the database
cursor.execute("SELECT * FROM ahlxgCalc;")
records = cursor.fetchall()

# Grab each datapoint and grab the N nearest neighbors from the database
# From the N nearest neighbors, calculate
# record[1] == y value. From 0 (left) to 300 (right). Left and right of the goalie
# record[0] == x value. Out from the net. 0 to max
for record in records:
    #xG's calculated using only data at that particular point
    query = '''SELECT * FROM ahlxgf WHERE XLocation = %s INTERSECT SELECT * FROM ahlxgf WHERE YLocation = %s;'''
    cursor.execute(query, (record[0],record[1]))
    matching_records = cursor.fetchall()
    goal = 0
    num_rows = len(matching_records) 
    for row in matching_records:
        if row[2] == 1:
            goal += 1
    if num_rows == 0:
        xG = 0
    else:
        xG = goal/num_rows
    print("Expected goals for (%i , %i) is %6.5f" % (record[0],record[1],xG))
    #insert the calculated xG into the table for this record
    insert_query = '''UPDATE ahlxgCalc SET xG = %s WHERE (XLocation) = (%s) AND (YLocation) = (%s);'''
    cursor.execute(insert_query, (xG,record[0],record[1]))
    connection.commit()

#Smooth out each calculated data point with a averaging function that takes values around the point.
#The swatch is var*2 wide and high
for unsmoothed_record in records:
    var = 100
    query = '''SELECT * FROM ahlxgCalc WHERE XLocation BETWEEN %s AND %s INTERSECT SELECT * FROM ahlxgCalc WHERE YLocation BETWEEN %s AND %s;'''
    cursor.execute(query, (unsmoothed_record[0]-var,unsmoothed_record[0]+var,unsmoothed_record[1]-var,unsmoothed_record[1]+var))
    unsmoothed_match = cursor.fetchall()
    num_matches = len(unsmoothed_match)
    for val in unsmoothed_match:
        xG += val[2]
    xG = xG/num_matches
    inserting = '''UPDATE ahlxgCalc SET xG = %s WHERE (XLocation) = (%s) AND (YLocation) = (%s);'''
    cursor.execute(insert_query, (xG,unsmoothed_record[0],unsmoothed_record[1]))
    connection.commit()
    print("Smoothed Expected goals for (%i , %i) is %6.5f" % (unsmoothed_record[0],unsmoothed_record[1],xG))

#closing database connection.
if(connection):
    cursor.close()
    connection.close()
    print("PostgreSQL connection is closed")
