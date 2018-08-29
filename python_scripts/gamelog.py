import os
import csv
import sys
import pandas as pd 
from urllib.request import urlopen
from urllib.error import HTTPError
import urllib
import requests
import getpass
from sqlalchemy import create_engine
import sqlalchemy
#import credentials as cred
import zipfile,urllib.request,shutil
from tqdm import tqdm
import pymysql

'''
    This script gets the following info ... 
        gameID
        awayTeam
        hometeam
        awayTeamScore      
        homeTeamScore      
        lengthGameOuts     
        dayNight
        gameDate
        windSpeed
        windDirection
        temperature
        isDoubleHeader     
        attendance
        umpHP
        parkID
'''

def extract_zip(url,output_folder):
    # this part extracts all the files
    cwd = os.getcwd()
    file_name = url.split('/')[-1]
    with urllib.request.urlopen(url) as response, open(file_name,'wb') as out_file:
        shutil.copyfileobj(response,out_file)
        with zipfile.ZipFile(file_name) as zf:
            print ('made it here2')
            zf.extractall(cwd+'/'+output_folder)

#get rid of the quotes in the gamelog file...
def h1(aStr):
    if not isinstance(aStr,str):
        return aStr 
    elif chr(34) in aStr:
        return aStr.replace(chr(34),'')
    return aStr

if __name__ == '__main__':

    gamelog_zip_url = 'https://www.retrosheet.org/gamelogs/gl2010_17.zip'
    play_by_play_url = 'https://www.retrosheet.org/events/2010seve.zip'
    extract_zip(play_by_play_url,'play_by_play')
    print ('made it here')
    sys.exit()

    gameDict = {}
    eventFolder = os.getcwd()+'/play_by_play/'
    for file in os.listdir(eventFolder):
        teamFile = os.fsdecode(file)
        if teamFile[0]=='.': # annoying check if its .DS_STORE
            continue
        with open(eventFolder+teamFile,'r') as fname:
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

    #awayTeamScore      
    #homeTeamScore      
    #lengthGameOuts      
    #isDoubleHeader    
    #http://www.retrosheet.org/gamelogs/glfields.txt
    extract_zip(gamelog_zip_url,'gamelog')
    gamelogFolder = os.getcwd()+'/gamelog/'
    for file in os.listdir(gamelogFolder):
        yearFile = os.fsdecode(file)
        if yearFile[0] == '.':
            continue

        with open(gamelogFolder+yearFile,'r') as fname:
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
