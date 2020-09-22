# AHL-xG

# Purpose
Hockey analytics are a hot topic these days and with the incrediblty rich publically available data for each NHL game, its incredible to see what information is able to be extracted. With the AHL and CHL, an analyst unfortunately does not have access to databases containing vast amounts of data. With that limitation in mind, my goal with this project is to see how accurately I could predict the expected goals (xG) for a shot in the AHL, or in the CHL, based only off of the x and y location of that shot. 

This project will focus on the AHL; however, the CHL website store game information in the exact same format. With very slight modification, one could modify the scripts to work for the CHL as well.

# Method
Before you begin, step your SQL database. Note the lines 
```
    connection = psycopg2.connect(user = <insert username>,
                                  password = <insert password>,
                                  host = <insert sql server addr>,
                                  port = <insert sql server port number>,
                                  database = <insert database name>)
```
are commented out in the *_sql.py scripts.

1. The first step is scraping data from the AHL website.
The ahl_xgf_sql_scrape.py script gets all x,y shot & goal locations from the AHL website and puts it into a sql table named 'ahlxgf'. This table needs to be created in the sql database you connect to as it is initially dropped. Conversely, you could comment out the lines that drop the table the first run of the script.
command: python ahl_xgf_sql_scrape.py <latestGameID#>

2. With the data in a SQL database, we can calulate the xG of individual x,y locations. The ahl_xgf_sql_smoothing.py script ONLY calculates xG based on that particular x,y point. Subsequently, a smoothing box of size x +/- var,y +/- var (with var > 1) parses each x,y coordinate. This results in lower peaks but
higher valleys. The 'ahlxgfCalc' table needs to be created in the sql database you connect to as it is initially dropped. Conversely, you could comment out the lines that drop the table the first run of the script.
```
command: python ahl_xgf_sql_smoothing.py <latestGameID#>
```
3. This step is OPTIONAL, use the xg_plot.py to display the results of step 2. The heat map will visually show the xG values. 
```
command: python xg_plot.py
```
Here's what an example heatmap looks like:
![Heatmap](https://i.imgur.com/wwf9Zyf.png)

4. The fourth, last, and most important step. Run the ahl_xgf_sql_accuracy.py script to compare the actual game score vs what the xG predicts it to be. The 'ahlxgfaccuracy' table needs to be created in the sql database you connect to as it is initially dropped. Conversely, you could comment out the lines that drop the table the first run of the script.
```
command: python ahl_xgf_sql_accuracy.py <latestGameID#>
```
E.g., All four scripts can be run back to back
```
python ahl_xgf_sql_scrape.py <latestGameID#>; python ahl_xgf_sql_smoothing.py <latestGameID#>; python xg_plot.py; python ahl_xgf_sql_accuracy.py <latestGameID#>
```

# Dependencies

1. Python3 with packages requests, json, psycopg2, sys, datascience, matplotlib, numpy, ktniker
```
pip install requests, json, psycopg2, sys, datascience, matplotlib, numpy, ktniker
```
2. A postgres SQL Database is required.
3. A SQL GUI such as [Sqlectron](https://sqlectron.github.io/).


# Future Work

I would greatly appreciate feedback regarding this code. This project is far from perfect and could definitely be fine tuned in many many ways. 
