DROP TABLE IF EXISTS Ballpark;
CREATE TABLE Ballpark(
	parkID VARCHAR(50) PRIMARY KEY,
    parkName VARCHAR(50),
    #altitude REAL DEFAULT 0,
    openDate DATE NOT NULL,
    closeDate DATE#,
    #dimensions REAL
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
    PRIMARY KEY (gameID,pitchID)
    );

#just used for debugging below
CREATE TABLE mlbAB (
	gameID VARCHAR(20) PRIMARY KEY,
    mlbABs int
    );

DROP TABLE IF EXISTS RetrosheetAB;
CREATE TABLE RetrosheetAB (
	gameID VARCHAR(20) PRIMARY KEY,
    rsheetABs INT
    );
    

#this isn't useful anymore
DROP TABLE IF EXISTS Player;
CREATE TABLE Player(
    playerID VARCHAR(50) PRIMARY KEY,
    playerName VARCHAR(50),
    batHand CHAR(1),
    throwHand CHAR(1),
    #sz_top REAL,
    #sz_bottom REAL,
    dob DATE
);
CREATE INDEX playerNameIndex ON Player(playerName);

#SHOW ENGINE INNODB STATUS;