import os
import csv
import xml.etree.ElementTree as ET
import sys
from urllib.request import urlopen
import time 

startTime = time.time()
#This looks at Retrosheet event files and creates a Dictionary with gameID as key and URL as value
gameDict = {} #global variable
pathName = 'retrosheet files/2010eve/'
for file in os.listdir(pathName):
    fileInput = os.fsdecode(file)
    gameNum = '1'

    #step is necessary on the mac since system may have unvisible parent directory files
    if fileInput[0]=='.' or fileInput[-3:]=='ROS':   
        continue 
    with open(pathName+fileInput,'r') as fname:
        eachLine = fname.readlines() 


        for line in range(len(eachLine)):
            lineArray = eachLine[line].split(',')
            if lineArray[0]=='id':
                gameID = lineArray[1][:-1]
                theYear = gameID[3:7]
                theMonth = gameID[7:9]
                theDate = gameID[9:11]
                gameNum = '1'
        
                #check for doubleheaders
                if gameID[11]=='2':
                    gameNum = '2'
                new_path = 'year_'+theYear+'/month_'+theMonth + '/day_'+theDate+'/gid_'+theYear+'_'+theMonth +'_'+theDate+'_'
                
                #get the visiting team and home team
                visitTeam = eachLine[line+2].split(',')[2][:-1].lower()+'mlb'
                homeTeam = eachLine[line+3].split(',')[2][:-1].lower()+'mlb'
                new_path = new_path+visitTeam+'_'+homeTeam+'_'+gameNum+'/players.xml'
                gameDict[gameID] = 'http://gd2.mlb.com/components/game/mlb/'+new_path

#now that we've stored all the gameID to URL in a dictionary, let's extract the information...
print ('now onto the long part')
print (time.time()-startTime)

#just a helper function that returns the value or null (SQL-styled null)
def getAttributes(subtree,args):
    l1 = []
    for arg in args:
        try:
            l1.append(subtree.attrib[arg])
        except:
            l1.append(chr(92)+'N')
    return l1


gameNum = 1
with open('gd2Data-players-2010-2017.txt','w') as myOutput:
    csv_writer = csv.writer(myOutput,delimiter=',')

    for item in gameDict:
        file = urlopen(gameDict[item])
        game = ET.parse(file).getroot()
        teams = game.findall('team')

        for team in teams:
            players = team.findall('player')
            for player in players:
                abInfo = [item] #make the gameID the first item in the list
                abInfo.extend(getAttributes(player,['id','first','last','rl','bats','position',
                    'current_position','status','team_abbrev','team_id','parent_team_abbrev','parent_team_id',
                    'bat_order','game_position','avg','hr','rbi','wins','losses','era']))
                csv_writer.writerow(abInfo)

        print (gameNum)
        gameNum +=1

print (str(time.time()-startTime)+' seconds is how long this took')

