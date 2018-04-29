use mlb_practicum;

DROP TABLE IF EXISTS Pitch;
CREATE TABLE Pitch2(
	gameID varchar(50),
    abNum INT,
	batterID varchar(50) NOT NULL,
    pitcherID varchar(50) NOT NULL,
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
    pfx_z FLOAT,
    px FLOAT,
    pz FLOAT,
    x0 FLOAT,
    y0 FLOAT,
    z0 FLOAT,
    vx0 FLOAT,
    vy0 FLOAT,
    vz0 FLOAT,
    ax FLOAT,
    ay FLOAT,
    az FLOAT,
    break_y FLOAT,
    break_angle FLOAT,
    break_length FLOAT,
    type_confidence FLOAT,
    nasty FLOAT,
    spin_dir FLOAT,
    spin_rate FLOAT,
	firstBaseRunner VARCHAR(50),
    secondBaseRunner VARCHAR(50),
    thirdBaseRunner VARCHAR(50),
    outs INT,
    cumulativePitches INT,
    timesFaced INT,
    home_team_runs INT,
    away_team_runs INT,
    curr_inn FLOAT,
    PRIMARY KEY (gameID,pitchID)
    );


LOAD DATA
	LOCAL INFILE "Users/t2/Desktop/github/MLB_Machine_Learning_Project/txt_output_files/updated_txt_pitch_files_with_all_attributes/joint.csv"
    REPLACE INTO TABLE Pitch2
    FIELDS TERMINATED BY ','
    OPTIONALLY ENCLOSED BY '"'
    LINES TERMINATED BY '\r\n';
    


#This is the patch that will add the ball/strike count
ALTER TABLE Pitch2 ADD balls INT;
ALTER TABLE Pitch2 ADD strikes INT;
CREATE TABLE pitchHelper (
	gameId VARCHAR(20),
    pitchId INT,
    balls INT,
    strikes INT,
    PRIMARY KEY(gameId,pitchId)
    );

LOAD DATA
	LOCAL INFILE "Users/t2/Desktop/github/MLB_Machine_Learning_Project/txt_output_files/updated_txt_pitch_files_with_all_attributes/ball_strike.csv"
    REPLACE INTO TABLE pitchHelper
    FIELDS TERMINATED BY ','
    OPTIONALLY ENCLOSED BY '"'
    LINES TERMINATED BY '\n';

#turn it to 0 to turn off safe mode, 1 to keep it on. Turning it off allows me to update values in columns
SET SQL_SAFE_UPDATES = 1;
#ADD balls and strikes to my pitch helper table
UPDATE Pitch2 
INNER JOIN pitchHelper ON pitchHelper.gameId = Pitch2.gameID 
AND pitchHelper.pitchId = Pitch2.pitchID 
SET Pitch2.balls = pitchHelper.balls, Pitch2.strikes = pitchHelper.strikes;


