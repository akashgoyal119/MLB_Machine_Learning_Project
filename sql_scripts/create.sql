USE mlb;

DROP TABLE IF EXISTS Ballpark;
CREATE TABLE Ballpark(
	parkID VARCHAR(50) PRIMARY KEY,
    parkName VARCHAR(50),
    openDate DATE NOT NULL,
    closeDate DATE#,
);

DROP TABLE IF EXISTS Game;
CREATE TABLE Game (
	gameID VARCHAR(50) PRIMARY KEY,
    homeTeam CHAR(3),
    awayTeam CHAR(3),
    homeTeamScore INT NOT NULL,
    awayTeamScore INT NOT NULL,
    lengthGameOuts INT,
    dayNight VARCHAR(10), 
    gameDate DATE,
    windDirection VARCHAR(10),
    windSpeed REAL,
    temperature REAL,
    isDoubleHeader INT DEFAULT 0,
    attendance INT DEFAULT NULL,
    umpHP VARCHAR(50),
    parkID VARCHAR(50),
    FOREIGN KEY (parkID) REFERENCES Ballpark(parkID)
);

DROP TABLE IF EXISTS Player;
CREATE TABLE Player(
	gameID VARCHAR(50),
    playerID VARCHAR(50),
    firstName VARCHAR(50),
    lastName VARCHAR(50),
    rl CHAR(1),
    bats CHAR(1),
    fieldingPosition VARCHAR(5),
    currentPosition VARCHAR(5),
    theStatus VARCHAR(10),
    teamAbbreviation VARCHAR(5),
    teamID VARCHAR(5),
    parentTeamAbbreviation VARCHAR(5),
    parentTeamID VARCHAR(5),
    batPosition INT,
    gamePosition VARCHAR(5),
    battingAverage FLOAT,
    hr INT,
    rbi INT,
    wins INT,
    losses INT,
    era FLOAT,
    PRIMARY KEY (gameID, playerID)
);
CREATE INDEX firstnameIndex ON Player(firstName);
CREATE INDEX lastnameIndex ON Player(lastName);

DROP TABLE IF EXISTS Pitch;
CREATE TABLE Pitch(
	gameID varchar(50),
    abNum INT,
    pitcherID varchar(50) NOT NULL,
    batterID varchar(50) NOT NULL,
    batterHand varchar(5),
    pitcherHand varchar(5),
    event_num INT,
    the_event VARCHAR(50),
    pitchID INT,
    pitchType VARCHAR(5),
	pitchDes VARCHAR(50),
	pitchTypeShort VARCHAR(10), #either S,B,X 
    zone VARCHAR(10),
    x FLOAT,
    y FLOAT,
    initialVelocity FLOAT,
    endVelocity FLOAT,
    szTop FLOAT,
    szBottom FLOAT,
    pfx_x FLOAT,
    pfx_y FLOAT,
    break_y FLOAT,
    break_angle FLOAT,
	firstBaseRunner VARCHAR(50),
    secondBaseRunner VARCHAR(50),
    thirdBaseRunner VARCHAR(50),
    outs INT,
    cumulativePitches INT,
    timesFaced INT,
    home_team_runs INT,
    away_team_runs INT,
    PRIMARY KEY (gameID,pitchID)
    );

#SHOW ENGINE INNODB STATUS;