"""
Usage: python ahl_xgf_sql_smoothing.py 
Take the ahlxgf database & table. Find the shots that are in the vicinity of 
the datapoint. Use the k nearest neighbors to find the xG for each strength

How it works
This is a simple k nearest neighbors algorithm where we find the k nearest neighbors 
and then classify our point accordingly. xG = k nearest neighbors that resulted in a goal / k
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


#### Drop the 5 tables if they already exist ####
#### Save code with using a for loop + formatted string (potential security issue)
for i in range(0,5):
    #set the table name here
    table_name = "ahlxgcalc"+str(i)

    try:
        cursor.execute("DROP TABLE %s;" % table_name)
        connection.commit()
        print("Table %s has been dropped" % table_name)
    except (Exception, psycopg2.DatabaseError) as error :
        print ("Error while deleting PostgreSQL table", error)

############# Create the 5 tables in ahlxgf that contain the calculated xG for each datapoint for each strength (-2 through +2) #########
#ahlxgCalc0 == table for strength -2, ahlxgCalc1 == table for strength -1 ... ahlxgCalc4 == table for strength +2
for i in range(0,5):
    #set the table name here
    table_name = "ahlxgcalc"+str(i)

    try:
        create_table = '''CREATE TABLE %s ( 
            XLocation INT,
            YLocation INT,
            xG FLOAT )'''
        cursor.execute(create_table % table_name)
        connection.commit()
    except (Exception, psycopg2.DatabaseError) as error :
        print ("Error while creating PostgreSQL table", error)

# events is a csv file containing all X Location and Y Location values
# based on the database it will calculate an xG value
events = Table.read_table("input_simple.csv")

#populate each ahlxgCalc table w/ datapoints from CSV
for i in range(0,5):
    #set the table name here
    table_name = "ahlxgcalc"+str(i)
    print("Populating %s with all x,y points" % table_name)
    for event_row in events.rows:
        values = """INSERT INTO %s (XLocation, YLocation) VALUES (%%s,%%s)"""
        cursor.execute(values % table_name, [int(event_row[0]),int(event_row[1])])

#variable sized smoothing swaths for different strengths
smoothing_swath = [5,30,39,28,8]

for i in range(0,5):
    #set the table name here
    table_name = "ahlxgcalc"+str(i)

    #Grab every datapoint from the database and run the calculation for each stregnth
    query = cursor.execute("SELECT * FROM %s;" % table_name)
    records = cursor.fetchall()

    var = smoothing_swath[i]
    xG = 0
    #Smooth out each calculated data point with a averaging function that takes values around the point.
    #The swath is var*2 wide and high
    for record in records:
        goal = 0
        query = '''SELECT * FROM ahlxgf WHERE XLocation BETWEEN %s AND %s INTERSECT SELECT * FROM ahlxgf WHERE YLocation BETWEEN %s AND %s INTERSECT SELECT * FROM ahlxgf WHERE Strength = %s;'''
        cursor.execute(query % (record[0]-var,record[0]+var,record[1]-var,record[1]+var,i-2))
        matching_records = cursor.fetchall()
        num_rows = len(matching_records)
        if num_rows == 0:
            xG = 0
        else:
            for row in matching_records:
                # if this row is a goal, add one to the goal variable
                if row[2] == 1:
                    goal += 1
            xG = goal/num_rows
        inserting = '''UPDATE %s SET xG = %%s WHERE (XLocation) = (%%s) AND (YLocation) = (%%s);'''
        cursor.execute(inserting % table_name, [xG,record[0],record[1]])
        connection.commit()
        print("Smoothed Expected goals for (%i , %i) is %6.5f at strength %i" % (record[0],record[1],xG,i-2))
        
#closing database connection.
if(connection):
    cursor.close()
    connection.close()
    print("PostgreSQL connection is closed")
