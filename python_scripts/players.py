import os
import csv
import xml.etree.ElementTree as ET
import sys
from urllib.request import urlopen
import time 
from tqdm import tqdm
import requests
import zipfile,urllib.request, shutil
from sqlalchemy import create_engine
import sqlalchemy
import credentials as cred 
import getpass

password = getpass.getpass()
db_name = cred.db_name 
user = cred.user
host = cred.host 

def extract_retrosheet_zip():
    cwd = os.getcwd()
    url = "https://www.retrosheet.org/events/2010seve.zip"
    file_name = '2010zip.zip'

    with urllib.request.urlopen(url) as response, open(file_name,'wb') as out_file:
        shutil.copyfileobj(response,out_file)
        with zipfile.ZipFile(file_name) as zf:
            zf.extractall(cwd+'/retrosheet_files')

def get_urls_from_files():
    pathName = os.getcwd()+'/retrosheet_files/'
    game_urls = []
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
                    game_urls.append((gameID,'http://gd2.mlb.com/components/game/mlb/'+new_path))
    return game_urls

#just a helper function that returns the value or null (SQL-styled null)
def getAttributes(subtree,args):
    l1 = []
    for arg in args:
        try:
            l1.append(subtree.attrib[arg])
        except:
            l1.append(chr(92)+'N')
    return l1

def get_game_info(tup):
    item = tup[0]
    url = tup[1]
    file = urlopen(url)
    game = ET.parse(file).getroot()
    teams = game.findall('team')

    columns = ['id','first','last','rl','bats','position',
                'current_position','status','team_abbrev','team_id','parent_team_abbrev','parent_team_id',
                'bat_order','game_position','avg','hr','rbi','wins','losses','era']
    for team in teams:
        players = team.findall('player')
        for player in players:
            abInfo = [item] #make the gameID the first item in the list
            abInfo.extend(getAttributes(player,columns))

    other_cols = ['gameID']
    other_cols.extend(columns)
    df = pd.DataFrame(data=abInfo,columns=other_cols)
    cnx = create_engine('mysql+pymysql://'+user+':'+password+'@'+host+':3306/'+db_name,echo=False)
    try:
        df.to_sql('Lineup',cnx,if_exists='append',index=False)
    except sqlalchemy.exc.IntegrityError as e:
        print ('already inserted these in ',item,url)
    cnx.dispose()
    return True

if __name__ == '__main__':
    extract_retrosheet_zip()
    urls = get_urls_from_files()
    p = Pool(processes=10)
    info = p.map(get_game_info,urls)

