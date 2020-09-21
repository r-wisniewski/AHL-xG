import matplotlib.pyplot as plt 
import numpy as np
import tkinter
import matplotlib
matplotlib.use('TkAgg')
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

#Grab every xG row/datapoint from the database
cursor.execute("SELECT * FROM ahlxgCalc;")
records = cursor.fetchall()

#Create numpy array that will be populated by our records
#shape = (rows,columns) in our case rows are the y's and columns are the x's
rows = 297
cols = 301
A = np.ndarray(shape=(rows,cols), dtype=float)

for record in records:
    #A[x][y] = xG
    A[record[0],record[1]] = record[2]
    print("Array element (%i,%i) is %6.5f" % (record[0],record[1],record[2]))
    
plt.xlabel('Distance between the boards')
plt.ylabel('Distance from net')
title = 'xGF for AHL shot location'
plt.title(title)
im = plt.imshow(A, cmap='hot')
plt.colorbar(im)
plt.show()
    
#closing database connection.
if(connection):
    cursor.close()
    connection.close()
    print("PostgreSQL connection is closed")