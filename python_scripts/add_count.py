import os
import csv
import mysql.connector as mc 
import time
import webbrowser
import sys
from sklearn.cluster import KMeans
import numpy as np
import pandas as pd
import numexpr

#this will query the existing database and add a ball-strike count to each pitch. 

cnx = mc.connect(user='root',password='******',host='localhost',database='mlb')
query1 = 'SELECT gameID,abNum,pitchID,pitchDes FROM Pitch2'
df = pd.read_sql_query(query1,cnx)

valid_dict =  {'Ball':True,'Called Strike':False,'Swinging Strike':False,
                           'Ball in Dirt':True, 'Swinging Strike (Blocked)':False,
                           'Intent Ball':True, 'Missed Bunt':True,
                           'Automatic Ball':True, 'Pitchout':True, 'Swinging Pitchout':False,
                           'Automatic Strike':True}
extend_dict = {'Foul':0,'Foul Tip':0,'Foul (Runner Going)':0,'Foul Pitchout':0}

class Pitch:
    def __init__(self,pid,gid,ab,event):
        self.pid = pid 
        self.gid = gid 
        self.ab = ab
        self.event = event 
        self.strikes=0
        self.balls=0
   
    def calc_balls_strikes(self,prevPitch=None):
        if not prevPitch:
            self.balls = 0
            self.strikes = 0
        #if the previous pitch had a different at-bat number, then your starting count was 0-0
        elif self.ab != prevPitch.ab: 
            self.balls = 0
            self.strikes = 0

        #we're in the same at-bat
        else:
            #if the previous pitch wasn't a ball, update the strike count
            if prevPitch.event in valid_dict: 
                
                if valid_dict[prevPitch.event] == True: #if ball
                    self.balls=prevPitch.balls+1
                    self.strikes=prevPitch.strikes
                
                else: #if strike
                    self.strikes=prevPitch.strikes+1
                    self.balls = prevPitch.balls

            #the pitch was a foul, so if there were 2 strikes, keep it the same, otherwise add a strike
            elif prevPitch.strikes!=2:
                self.strikes = prevPitch.strikes+1
                self.balls = prevPitch.balls

            else:
                self.strikes = prevPitch.strikes
                self.balls = prevPitch.balls 
        return 

#query1 = 'SELECT gameID,abNum,pitchID,the_event FROM Pitch2'
l = [(item[1],item[2],item[3],item[4]) for item in df.itertuples()]
pitchL = []
for i,item in enumerate(l):
    newPitch = Pitch(item[2],item[0],item[1],item[3])
    if i==0:
        newPitch.calc_balls_strikes()
        pitchL.append(newPitch)
    else:
        newPitch.calc_balls_strikes(prevPitch=pitchL[i-1])
        pitchL.append(newPitch)

with open('ball_strike.csv','w') as outfile:
    csv_writer = csv.writer(outfile,delimiter=',')
    for item in pitchL:
        csv_writer.writerow([item.gid,item.pid,item.balls,item.strikes])



