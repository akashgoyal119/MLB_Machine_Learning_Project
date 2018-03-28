USE mlb;

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
	LOCAL INFILE "Users/t2/Desktop/github/MLB_Machine_Learning_Project/txt_output_files/gd2Data-game-2010-2017.txt"
    REPLACE INTO TABLE Pitch
    FIELDS TERMINATED BY ','
    OPTIONALLY ENCLOSED BY '"'
    LINES TERMINATED BY '\n';

LOAD DATA
	LOCAL INFILE "Users/t2/Desktop/github/MLB_Machine_Learning_Project/txt_output_files/patched-players-2010-2017.txt"
    REPLACE INTO TABLE Player
    FIELDS TERMINATED BY ','
    OPTIONALLY ENCLOSED BY '"'
    LINES TERMINATED BY '\r\n';


