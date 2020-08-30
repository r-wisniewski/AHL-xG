# AHL-xG

# Purpose
Hockey analytics are a hot topic these days and with the incrediblty rich publically available data for each NHL game, its incredible to see what information is able to be extracted. With the AHL and CHL, an analyst unfortunately does not have access to databases containing vast amounts of data. With that limitation in mind, my goal with this project is to see how accurately I could predict the expected goals (xG) for a shot in the AHL, or in the CHL, based only off of the x and y location of that shot. 

# Method
1. The first step is scraping data from the AHL website.
The ahl_xgf_scrape.py script gets all x,y shot & goal locations from the AHL website
command: python ahl_xgf_scrape.py <latestGameID#>

2. With the data in a SQL database, we can calulate the xG of individual x,y locations. The ahl_xgf_sql_smoothing.py script ONLY calculates xG based on that particular x,y point. Subsequently, a smoothing box of size x +/- var,y +/- var (with var > 1) parses each x,y coordinate. This results in lower peaks but
higher valleys.
command: python ahl_xgf_*.py <latestGameID#>

3. This step is OPTIONAL, use the xg_plot.py to display the results of step 2. The heat map will visually show the xG values
command: python xg_plot.py

4. The fourth, last, and most important step. Run the ahl_xgf_sql_accuracy.py script to compare the actual game score vs what the xG predicts it to be. 
command: python ahl_xgf_accuracy.py <latestGameID#>

E.g., All four scripts can be run back to back
```
python ahl_xgf_scrape.py <latestGameID#>; python ahl_xgf_*.py <latestGameID#>; python xg_plot.py; python ahl_xgf_accuracy.py <latestGameID#>
```

# Dependencies

