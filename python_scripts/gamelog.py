import os
import csv
import sys
#gameID
#awayTeam
#hometeam
#awayTeamScore      
#homeTeamScore      
#lengthGameOuts     
#dayNight
#gameDate
#windSpeed
#windDirection
#temperature
#isDoubleHeader     
#attendance
#umpHP
#parkID

gameDict = {}
#this part will handle the information gathering in event files
eventFolder = 'retrosheet files/2010eve/'
for file in os.listdir(eventFolder):
    teamFile = os.fsdecode(file)
    if teamFile[0]=='.': # annoying check if its .DS_STORE
        continue
    
    fname = open(eventFolder+teamFile,'r')
    fullDocument = fname.readlines()
    
    firstLine = fullDocument[0].split(',')
    gameID = firstLine[1][:-1]

    for a in fullDocument:
        line = a.split(',')
        if line[1] == 'visteam':
            gameDict[gameID].append(line[2][:-1])
        elif line[1] =='hometeam':
            gameDict[gameID].append(line[2][:-1])
        elif line[1] == 'date':
            gameDict[gameID].append(line[2][:-1].replace('/','-'))
        elif line[1] == 'daynight':
            gameDict[gameID].append(line[2][:-1])
        elif line[1] == 'winddir':
            gameDict[gameID].append(line[2][:-1])
        elif line[1] == 'windspeed':
            gameDict[gameID].append(float(line[2][:-1]))
        elif line[1] == 'temp':
            gameDict[gameID].append(float(line[2][:-1]))
        elif line[1] == 'umphome':
            gameDict[gameID].append(line[2][:-1])
        elif line[1] == 'attendance':
            gameDict[gameID].append(int(line[2][:-1]))
        elif line[1] == 'site': #parkID
            gameDict[gameID].append(line[2][:-1])

        #change the gameID as we are onto a new game
        elif line[0] == 'id':
            gameID = line[1][:-1]
            gameDict[gameID] = [gameID]
    fname.close()



#awayTeamScore      
#homeTeamScore      
#lengthGameOuts      
#isDoubleHeader    
#http://www.retrosheet.org/gamelogs/glfields.txt

#get rid of the quotes in the gamelog file...
def h1(aStr):
    if not isinstance(aStr,str):
        return aStr 
    elif chr(34) in aStr:
        return aStr.replace(chr(34),'')
    return aStr

print ('onto gamelogs part')
gamelogFolder = 'retrosheet files/gl2010_17/'
for file in os.listdir(gamelogFolder):
    yearFile = os.fsdecode(file)
    if yearFile[0] == '.':
        continue

    fname = open(gamelogFolder+yearFile,'r')
    fullDocument = fname.readlines()

    for game in fullDocument:
        line = game.split(',')
        gameID = h1(line[6])+h1(line[0])+h1(line[1])
        gameDict[gameID].extend([h1(line[9]),h1(line[10]), h1(line[11]),h1(line[1])])

#finally print all the data out
with open('gamelogOutput.csv','w') as csv_file:
    writer = csv.writer(csv_file)
    for key, value in gameDict.items():
        writer.writerow(value)
