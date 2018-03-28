# MLB_Machine_Learning_Project

This project parses data from Retrosheet and MLB's PITCHf/x, which can subsequently be used for data analysis and predictive modeling. I will obtain the data utilizing Python and then store it in a MySQL database.

 As an example of the information that you can analyze, see this XML file (http://gd2.mlb.com/components/game/mlb/year_2017/month_07/day_09/gid_2017_07_09_detmlb_clemlb_1/inning/inning_all.xml) 

Below are the steps needed to convert all the information from Retrosheet and Pitch F/X into a database.

1) Go to <a href="http://www.retrosheet.org/game.htm">Retrosheet</a> and download the regular season event files (whichever period of time you wish to analyze. Make sure you download the folder into the same directory as the Python file.

2) Create the MySQL database by following the steps provided <a href="https://www.a2hosting.com/kb/developer-corner/mysql/managing-mysql-databases-and-users-from-the-command-line">here.</a>

3) Run pitch.py to extract all the "inning/inning_all.xml" information from Pitch F/X. Note that with 30 teams in the MLB and a total of 81 home games for each team, there are typically 2,430 games per regular season. Depending on how many seasons you are looking at and your internet speed, this process can take a while (i.e. it took me ~ 1.5 hours to download 8 seasons worth of data).

4) Run the create.sql file in MySQL to create the database, and run the populate.sql in order to load data into the databases. Make sure to change the file paths in the populate.sql file.

5) Now you have everything you need to do analysis. To see what attributes are available, take a look at the create.sql file to see the tables and attributes.
