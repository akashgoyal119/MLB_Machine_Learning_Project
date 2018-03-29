import os
import csv
import xml.etree.ElementTree as ET
import sys
from urllib.request import urlopen
import time 


#This looks at Retrosheet event files and creates a Dictionary with gameID as key and URL as value
#http://gd2.mlb.com/components/game/mlb/year_2017/month_03/day_31/gid_2017_03_31_colmlb_seamlb_1/inning/inning_all.xml
startTime = time.time()
gameDict = {} #global variable
pathName = 'retrosheet files/2010eve/'
for file in os.listdir(pathName):
    fileInput = os.fsdecode(file)
    gameNum = '1'

    #step is necessary on the mac since system may have unvisible parent directory files
    if fileInput[0]=='.' or fileInput[-3:]=='ROS':   
        continue 
    fname = open(pathName+fileInput,'r')
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
            new_path = new_path+visitTeam+'_'+homeTeam+'_'+gameNum+'/inning/inning_all.xml'
            gameDict[gameID] = 'http://gd2.mlb.com/components/game/mlb/'+new_path
    fname.close()


#now that we've stored all the gameID to URL in a dictionary, let's extract the information...
print ('now onto the long part')
print (time.time()-startTime)

def getPitchAttributes(subtree,args):
    l1 = []
    for arg in args:
        try:
            l1.append(subtree.attrib[arg])
        except:
            #this is the MySQL method of making a null
            l1.append(chr(92)+'N')
    return l1

gameNum = 1
myOutput = open('gd2Data-2010-2017-test.txt','w')
error_writer = csv.writer(error_file,delimiter=',')
csv_writer = csv.writer(myOutput,delimiter=',')

for item in gameDict:
    file = urlopen(gameDict[item])
    data = file.readline()
    game = ET.fromstring(data)
    pitcherDict = {} #use to track pitch count
    batterVpitcher= {}
    home_team_runs = 0
    away_team_runs = 0 
    ctr = 0

    for inning in game:
        for half in inning:
            atBats = half.findall('atbat')
            prevOuts = 0 
            for at_bat in atBats:
                pitches= at_bat.findall("pitch")
                abInfo = [item] #make the gameID the first item in the list
                abInfo.extend(getPitchAttributes(at_bat,['num','batter','pitcher','stand',
                    'p_throws','event_num','event']))

                #this will be used to find number of times through the order. 
                current_matchup = str(at_bat.attrib['pitcher'])+str(at_bat.attrib['batter'])
                if not batterVpitcher.get(current_matchup):
                    batterVpitcher[current_matchup] = 1
                else:
                    batterVpitcher[current_matchup]+=1

                current_pitcher = at_bat.attrib['pitcher']
                for pitch in pitches:
                    #if there's a new pitcher, set his total pitches to 1, otherwise add 1
                    if not pitcherDict.get(current_pitcher):
                        pitcherDict[current_pitcher] = 1
                    else:
                        pitcherDict[current_pitcher]+=1

                    #copy all the AB information over to pitch_info
                    pitch_info = abInfo[:]
                    pitchCharacteristics = getPitchAttributes(pitch,['id','pitch_type',
                        'des','type','zone','x','y','start_speed','end_speed','sz_top',
                        'sz_bot','pfx_x','pfx_z','break_y','break_angle','on_1b','on_2b','on_3b'])
                    pitch_info.extend(pitchCharacteristics)
                    pitch_info.append(prevOuts) #current number of outs before ball is in play
                    pitch_info.append(pitcherDict[current_pitcher]) #cumulative pitches by pitcher
                    pitch_info.append(batterVpitcher[current_matchup]) #number times faced prior to current AB

                    pitch_info.append(home_team_runs)
                    pitch_info.append(away_team_runs)
                    csv_writer.writerow(pitch_info)

                if prevOuts >2:
                    print (abInfo)
                prevOuts = int(at_bat.attrib['o']) #update the outs so that the next for loop can utilize this info
                try: 
                    home_team_runs = int(at_bat.attrib['home_team_runs'])
                    away_team_runs = int(at_bat.attrib['away_team_runs'])
                    ctr +=1
                except:
                    pass
    if ctr == 0:
        print (gameDict[item])
    print (gameNum) #just used to keep track of progress while running.
    gameNum +=1

print (str(time.time()-startTime)+' seconds is how long this took')

