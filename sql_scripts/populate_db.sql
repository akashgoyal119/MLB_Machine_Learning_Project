USE mlb;

#run these 3 below
LOAD DATA
	LOCAL INFILE "Users/t2/Desktop/github/GD2_Baseball_Project/practicum/txt_output_files/ballparkOutput.txt"
    REPLACE INTO TABLE Ballpark
    FIELDS TERMINATED BY ','
    LINES TERMINATED BY '\n'
    (parkID,parkName,openDate,closeDate);

LOAD DATA
	LOCAL INFILE "Users/t2/Desktop/github/GD2_Baseball_Project/practicum/txt_output_files/gamelogOutput.txt"
    REPLACE INTO TABLE Game
    FIELDS TERMINATED BY ','
    LINES TERMINATED BY '\n'
    (gameID,awayTeam,homeTeam,parkID,gameDate,dayNight,umpHP,temperature,windDirection,
    windSpeed,attendance,awayTeamScore,homeTeamScore,lengthGameOuts,isDoubleHeader);

LOAD DATA
	LOCAL INFILE "Users/t2/Desktop/github/GD2_Baseball_Project/practicum/gd2Data-2010-2017-test.txt"
    REPLACE INTO TABLE Pitch
    FIELDS TERMINATED BY ','
    OPTIONALLY ENCLOSED BY '"'
    LINES TERMINATED BY '\n';


#just for testing. delete later
LOAD DATA
	LOCAL INFILE "Users/t2/Desktop/github/GD2_Baseball_Project/practicum/retroABs.txt"
    REPLACE INTO TABLE RetrosheetAB
    FIELDS TERMINATED BY ','
    LINES TERMINATED BY '\n';

LOAD DATA
	LOCAL INFILE "Users/t2/Desktop/github/GD2_Baseball_Project/practicum/mlbABs.txt"
    REPLACE INTO TABLE mlbAB
    FIELDS TERMINATED BY ','
    LINES TERMINATED BY '\n';

LOAD DATA
	LOCAL INFILE "Users/t2/Desktop/github/GD2_Baseball_Project/practicum/txt_output_files/2010-2017-Players.txt"
    REPLACE INTO TABLE Player
    FIELDS TERMINATED BY ','
    LINES TERMINATED BY '\n'
    (playerID,playerName,batHand,throwHand,DOB);