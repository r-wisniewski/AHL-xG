# AHL-xG

# Purpose
Hockey analytics are a hot topic these days and with the incrediblty rich publically available data for each NHL game, its incredible to see what information is can be extracted. With the AHL and CHL, an analyst unfortunately does not have access to public databases containing vast amounts of rich data. With that limitation in mind, my goal with this project is to see how accurately I could predict the expected goals (xG) for a shot in the AHL, or in the CHL, based on the x and y location of that shot combined with the strength. 

This project will focus on the AHL; however, the CHL website stores game information in the exact same format. With very slight modification to the code in this project, one could modify the scripts to work for the CHL as well.

# Getting started

Packages required and SQL DB setup.

## Prerequisites 

1. Python3 with packages requests, psycopg2, datascience, matplotlib, numpy
```
pip install -r requirements.txt
```
2. Install tkinter
```
sudo apt-get install python-tk
```
3. A postgres [SQL Database](https://www.postgresql.org/download/linux/) is required.

## SQL DB Setup

Before you begin, step a SQL database. Note the lines 
```
    connection = psycopg2.connect(user = <insert username>,
                                  password = <insert password>,
                                  host = <insert sql server addr>,
                                  port = <insert sql server port number>,
                                  database = <insert database name>)
```
are commented out in the python scripts. Replace the angle brackets in the above statement with your SQL DB’s information.

# Usage

1. The first step is scraping data from the AHL website.
The ahl_xgf_sql_scrape.py script gets all x,y shot & goal locations at a certain strength from the AHL website and puts it into a sql table named 'ahlxgf'. On the first run of the script, I’d recommend commentting out the lines that drop the table.
```
command: python ahl_xgf_sql_scrape.py <latestGameID#>
```
Where the <latestGameID#> can be found by going to theahl.com website, finding the most recent completed game and extracting the game ID from the URL
```
for example, the game ID for this URL: https://theahl.com/stats/game-center/1019145 is 1019145
```

2. With the data in a SQL database, we can calulate the xG of individual x,y locations for each strength. The ahl_xgf_sql_smoothing.py script calculates xG based on that particular x,y point. To reduce peaks and bring valleys up in the xG calculations, a smoothing box of size x +/- var,y +/- var (with var > 1) parses each x,y coordinate. On the first run of the script, I’d recommend commentting out the lines that drop the table.
```
command: python ahl_xgf_sql_smoothing.py
```
| Table Name    | Strengths (numerical) | Strenghts represented |
| ------------- | --- | --------------------- |
| ahlxgcalc0   | -2 | 3v5, down by 2 players  |
| ahlxgcalc1   | -1 | 4v5, down by 1 player |
| ahlxgcalc2   | 0 | 5v5, even strength  |
| ahlxgcalc3   | +1 | 5v4 or 4v3, up by 1 player |
| ahlxgcalc4   | +2 | 5v3, up by 2 players  |

3. This step is OPTIONAL, use the xg_plot.py to display the results of step 2. The heat map will visually show the xG values for each strength. 
```
command: python xg_plot.py
```
Here's what an example heatmap looks like:
![Heatmap](https://i.imgur.com/wwf9Zyf.png)

4. The fourth, last, and most important step. Run the ahl_xgf_sql_accuracy.py script to compare the actual game score vs what the xG predicts it to be. On the first run of the script, I’d recommend commentting out the lines that drop the table.
```
command: python ahl_xgf_sql_accuracy.py <latestGameID#>
```
E.g., All four scripts can be run back to back
```
python ahl_xgf_sql_scrape.py <latestGameID#>; python ahl_xgf_sql_smoothing.py; python xg_plot.py; python ahl_xgf_sql_accuracy.py <latestGameID#>
```

# Results

## In Sample Error

The tests to reduce error were simple tests ran against a 76 game in sample dataset. From these tests the average goals per game error and the mean squared error were calculcated to determine which smoothing swath combination was the most adequate. The table below lists the results of those tests:

| swath size (-2) | swath size (-1) | swath size (0) | swath size (+1) | swath size (+2) |Avg Error | MSE |
| ---- | --------- | ---------- | --------- | ---------- | ---------- | --------- |
| 50x50 | 80x80 | 100x100 | 60x60 | 50x50 | 6.864 | 52.23 |
| 160x160 | 120x120 | 80x80 | 70x70 | 80x80 | 6.986 | 54.14 |
| 80x80 | 100x100 | 80x80 | 70x70 | 80x80 | 6.995 | 52.27 |
| 160x160 | 100x100 | 80x80 | 70x70 | 80x80 | 6.991 | 54.23 |
| 10x10 | 60x60 | 78x78 | 56x56 | 16x16 | 7.034 | 54.84 |
| 160x160 | 120x120 | 50x50 | 70x70 | 80x80 | 7.192 | 57.42 |


Note: The first 5 columns (from the left) represent the smooth swath sizes for a particular strength. e.g., the furthest column to the left titled “swath size (-2)” represents the swath size for strength -2 on a particular test run.

## Out of Sample Prediction

In progress.

# Future Work

I would greatly appreciate feedback regarding this code. This project is far from perfect and could definitely be fine tuned in many many ways. 

# Contact

Robin Wisniewski – [LinkedIn](https://www.linkedin.com/in/robin-wisniewski/) –  [wisniewski.ro@gmail.com](mailto:wisniewski.ro@gmail.com)
