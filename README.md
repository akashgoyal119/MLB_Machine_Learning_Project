# MLB_Machine_Learning_Project

This project parses data from Retrosheet and MLB's PITCHf/x, which can subsequently be used for data analysis and predictive modeling. I will obtain the data utilizing Python and then store it in a MySQL database.

 As an example of the information that you can analyze, see <a href="http://gd2.mlb.com/components/game/mlb/year_2017/month_07/day_09/gid_2017_07_09_detmlb_clemlb_1/inning/inning_all.xml">this XML file.</a>

Below are the steps needed to convert all the information from Retrosheet and Pitch F/X into a database.

1) Go to Retrosheet and download the <a href="http://www.retrosheet.org/game.htm">regular season event files</a> (whichever period of time you wish to analyze. Also download the <a href= "http://www.retrosheet.org/gamelogs/index.html"> game log files</a>. Make sure you download the folder into the same directory as the Python file.

2) Create the MySQL database by following the steps provided <a href="https://www.a2hosting.com/kb/developer-corner/mysql/managing-mysql-databases-and-users-from-the-command-line">here.</a>

3) Run pitch.py to extract all the "inning/inning_all.xml" information (velocity, location, movement etc) from Pitch F/X  and players.py to extract all the "/players.xml" information from Pitch F/X (starting lineup information). Note that with 30 teams in the MLB and a total of 81 home games for each team, there are typically 2,430 games per regular season. Depending on how many seasons you are looking at and your internet speed, this process can take a while (i.e. it took me ~ 1.5 hours to download 8 seasons worth of data per script).

4) Run ballpark.py and gamelog.py to extract information about ballparks and general information about the game (windspeed, attendance, temperature, etc). This will not take more than 10 seconds as you have already downloaded the relevant files in step 1.

5) Run the create.sql file in MySQL to create the database, and run the populate.sql in order to load data into the databases. Make sure to change the file paths in the populate.sql file.

6) Now you have everything you need to do analysis! To see what attributes are available, take a look at the create.sql file to see the tables and attributes.


Now that we have our database setup, we can run the statistical analysis. We'll focus on predicting the type of pitch a given pitcher is going to throw in a certain scenario. For example, let's say we're the Red Sox and we're in the 5th inning of a game in July down 3 runs facing Masahiro Tanaka, and it's currently a 1-1 count with 1 out and no runners on base. What kind of pitch is he most likely to throw next, and with what probabilities? (i.e. maybe he'll throw a slider with 50% probability, a splitter with 30% probability and a four-seam fastball with 20% probability).

It makes sense that the type of pitch a player is going to throw depends on a great deal of factors. The question of whether to pitch to him or whether to pitch around him could be contingent on the strength of the other players in the lineup, the leverage of the situation (i.e. a pitcher might toy around with his worst pitches in a blowout or might stick with his guns in a close game), and many other factors.

In order to run this analysis, we'll make use of logistic regression with an L1-normalized loss function. Additionally we'll use K-Means in order to cluster pitchers into certain classifications. By doing this, we can find pitchers who are very similar to each other and "crowd-source" the data so that we can use comparable pitchers' tendencies to gain more accurate predictions.



