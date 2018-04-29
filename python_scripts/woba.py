#!/usr/bin/python3
import os
import csv
import pymysql as mc
import time
import webbrowser
import sys
from sklearn.cluster import KMeans
import numpy as np
import pandas as pd
import getpass
import pickle
'''
Here is how this file is structured
1) Take in a connection, a yr and a month and query the DB for
 gameID, current inning, abNum, pitchID, event, runners on base, outs,
 current runs for each team, end of game runs for each team, and game date

2) Read all this stuff into a Pandas dataframe.

3) Go through all possible game/inning combinations, and for each game create a smaller
dataframe, and then for each inning take an even smaller dataframe from that
and pass it into the Inning Class.

4) The sole purpose of the inning class is to get the score at the end of the inning so that
I can use it in the at-bats to find the runs created during an inning.

5) Go through the inning dataframe and for each row, find the last pitch of the at-bat.
This will be the "Action Pitch" which I want to create a class from. Note that the data
contains certain issues such as ejections which result in my data classifying certain rows
as having 3 outs prior to the AB, so I will discard those.

6) Choose the action pitch and create an AB class from it. The AB class will first calculate
which of the 24 states we are in (as defined by Tom Tango in The Book). Then it will calculate
the runs generated from the current AB to the end of the inning. (This is all in generate_ab_list)

7) Call calculate_run_expectancies which generates the average runs generated in each of the
24 situations.

8) Call add_run_expectancies which updates the start and end run expectancies 
for every bat in self.ab_list. This will allow us to generate a "value add above replacement" 
for each batter.

9) We're done! We've now calculated the value above replacement for each at-bat in the sample.
Now we can calculate the weights for each type of hit and perform analysis
'''

class REMatrix:
    def __init__(self,cnx,startTime,yr=None,mo=None):
        query1=''
        query2=''
        if yr and mo:   #this takes 0.35 seconds 
            query1 = """SELECT Pitch2.gameID AS gameID ,curr_inn FROM Pitch2 
                        INNER JOIN Game ON Pitch2.gameID = Game.gameID
                        WHERE YEAR(gameDate)='{}' AND MONTH(gameDate)='{}'
                        GROUP BY gameID,curr_inn""".format(yr,mo)
                        #this takes 0.30 seconds
            query2 = """SELECT Game.gameID AS gameID,abNum,pitchID,the_event,
                        firstBaseRunner,secondBaseRunner, thirdBaseRunner,outs,
                        home_team_runs,away_team_runs,curr_inn, homeTeamScore,
                        awayTeamScore,gameDate
                        FROM Pitch2 INNER JOIN Game ON Pitch2.gameID = Game.gameID
                        WHERE YEAR(gameDate)='{}' AND MONTH(gameDate)='{}'""".format(yr,mo)
        elif yr:        #this takes 0.91 seconds
            query1 = """SELECT Pitch2.gameID AS gameID ,curr_inn 
                        FROM Pitch2 INNER JOIN Game ON Pitch2.gameID = Game.gameID 
                        WHERE YEAR(gameDate)='{}'
                        GROUP BY gameID,curr_inn""".format(yr)
                        #this takes 1.36 seconds
            query2 = """SELECT Game.gameID AS gameID,abNum,pitchID,
                        the_event,firstBaseRunner,secondBaseRunner, 
                        thirdBaseRunner,outs,home_team_runs, 
                        away_team_runs,curr_inn, homeTeamScore,
                        awayTeamScore,gameDate 
                        FROM Pitch2 INNER JOIN Game 
                        ON Pitch2.gameID = Game.gameID 
                        WHERE YEAR(gameDate)='{}'""".format(yr)
        else:           #this took 7.10 seconds
            query1 = """SELECT Pitch2.gameID AS gameID ,curr_inn
                        FROM Pitch2
                        GROUP BY gameID,curr_inn"""
                        #this took 10.45 seconds
            query2 = """SELECT Pitch2.gameID AS gameID,abNum,pitchID,
                        the_event,firstBaseRunner,secondBaseRunner, 
                        thirdBaseRunner,outs,home_team_runs, away_team_runs,
                        curr_inn, homeTeamScore,awayTeamScore,gameDate 
                        FROM Pitch2 INNER JOIN Game on Pitch2.gameID = Game.gameID"""
        
        self.game_inn_df = pd.read_sql_query(query1,cnx)
        self.df = pd.read_sql_query(query2,cnx)
        self.all_combos = [(item[1],item[2]) for item in self.game_inn_df.itertuples()] 
        self.inning_list = []
        self.ab_list = []
        self.expect_dict = {}
        self.generate_ab_list()
        self.calculate_run_expectancies() #generate 24 expectancies for 24 situations
        self.add_run_expectancies()  
    
    #takes the given run expectancies for each of the 24 situations and assigns a value to each at-bat
    #based off this value
    def add_run_expectancies(self):
        #this loop adds the start run expectancies and next at-bats
        for i,ab in enumerate(self.ab_list):
            start_sit = ab.situation 
            ab.start_run_expectancy = self.expect_dict[start_sit]
            try:
                #if ab's are consecutive and in the same inning, mark a next AB
                if (ab.abNum == self.ab_list[i+1].abNum-1 and
                        ab.inning.inning_number == self.ab_list[i+1].inning.inning_number):
                    ab.next_ab = self.ab_list[i+1]
                else:
                    ab.next_ab = None
            except IndexError as e: #special case for the last item
                ab.next_ab = None
        
        #this adds the end run expectancies
        for i, ab in enumerate(self.ab_list):
            if ab.next_ab and ab.abNum == ab.next_ab.abNum-1:
                #this will generally work except for when a player gets picked off
                #to end the inning (or caught stealing to end inning)
                ab.end_run_expectancy = ab.next_ab.start_run_expectancy
            else:
                ab.end_run_expectancy = 0
        
        #finally calculate the value each batter added per AB
        for ab in self.ab_list:
            ab.calculate_adjusted_runs_created() 

    #create a dataframe of each gameID from self.all_combos, and then within those small dataframes
    #look up the individual innings to get those stats. 
    def generate_ab_list(self):
        previous_game_id = None
        curr_df = None
        for j,item in enumerate(self.all_combos):

            curr_time = time.time()
            if item[0] != previous_game_id:
                previous_game_id = item[0]
                curr_df = self.df[self.df['gameID']==item[0]]
                #print ('this combo took {} seconds'.format(time.time()-curr_time))

            #I separated inn_df and curr_df because of performance issues
            #allows me to look up current inning on a dataframe of just one game (~300Pitches)
            #as opposed to looking at all 5.5 million pitches 
            inn_df = curr_df[curr_df['curr_inn']==item[1]]
            inning_object = Inning(curr_df,item[1],item[0])
            
            self.inning_list.append(inning_object)
            
            for i in range(len(inn_df)):
                try:
                    #if ab number is not the same as the next one, it's last pitch of AB
                    if inn_df.iloc[i,1]<inn_df.iloc[i+1,1]:    
                        try:
                            ab_object = AB(inn_df.iloc[i,:],inning_object)
                            self.ab_list.append(ab_object)
                        #i.e. this is the condition where there's sometimes more than 3 outs...
                        except ValueError as e:
                            print ('there were more than 3 outs or less than 0 outs')
                            continue

                #index error happens on last pitch of inning so this is an "action pitch"
                except IndexError as e:
                    try:
                        ab_object = AB(inn_df.iloc[i,:],inning_object)
                        self.ab_list.append(ab_object)
                    except ValueError as e:
                        print (str(item[0])+' had an AB with less than 0 or more than 3 outs')
                        continue
            

    def calculate_run_expectancies(self):
        situations = [item.situation for item in self.ab_list]
        runs_created = [item.runs_created for item in self.ab_list]
        run_expectancy_df = pd.DataFrame({'situation':situations,'runs_created':runs_created})
        for i in range(24):
            self.expect_dict[i] = round(run_expectancy_df[run_expectancy_df.situation==i].mean()['runs_created'],3)

class Inning:
    def __init__(self,df,inn,gameID):
        self.inning_number = inn
        self.gameID = gameID
        self.home_or_away = self.get_home_or_away()
        self.endScore = self.get_end_score(df)

    def get_home_or_away(self):
        if self.inning_number*2%2 == 1:
            return 'Home'
        else:
            return 'Away'

    def get_end_score(self,df):
        #just look at the last row of the dataframe
        inning_df = df[df['curr_inn']==self.inning_number]
        if self.home_or_away == 'Home':
            return inning_df['home_team_runs'].tail(1).iloc[0]
        else:
            return inning_df['away_team_runs'].tail(1).iloc[0]


class AB:
    #passing in a series here. 
    def __init__(self,df,inning):
        
        self.gameID = df['gameID']
        self.abNum = df['abNum']
        self.outs = df['outs']
        self.runners = (df['firstBaseRunner'],df['secondBaseRunner'],df['thirdBaseRunner'])
        self.event = df['the_event']
        self.inning = inning
        self.starting_runs = None
        self.situation = self.calculate_state()
        self.runs_created  = self.calculate_runs_created(df)
        self.start_run_expectancy = 0
        self.end_run_expectancy = 0
        self.next_ab = None
        self.adjusted_runs_created = None
    
    def calculate_adjusted_runs_created(self):
        if not self.next_ab:
            self.adjusted_runs_created = self.end_run_expectancy - self.start_run_expectancy
        else:
            self.adjusted_runs_created = (self.end_run_expectancy - self.start_run_expectancy + 
                                          self.next_ab.starting_runs -self.starting_runs)
            
    def calculate_runs_created(self,df):
        if self.inning.home_or_away == 'Home':
            self.starting_runs = df['home_team_runs']
            return self.inning.endScore - df['home_team_runs']
        else:
            self.starting_runs = df['away_team_runs']
            return self.inning.endScore - df['away_team_runs']

    #determines which of the 24 runner on base/outs circumstance
    def calculate_state(self):
        total = 0
        if self.runners[0]:
            total+=1
        if self.runners[1]:
            total+=2
        if self.runners[2]:
            total+=4

        if self.outs == 1:
            total+=8
        elif self.outs ==2:
            total+=16
        elif self.outs>=3 or self.outs<0:
            raise ValueError("cant start AB with less than 0 or > 3 outs")
        return total

if __name__=="__main__":
 	cnx = mc.connect(user='akashgoyal',password=os.environ['DB_PASSWORD'],host='stromberg.cs.uchicago.edu',db='mlb_practicum',port=3306)
 	startTime= time.time()
 	re_obj = REMatrix(cnx,startTime,yr=2017,mo=5)
 	print (time.time()-startTime)
 	pickle_out = open('pickler201705','wb')
 	pickle.dump(re_obj,pickle_out)
 	#pickle_out.close()
	#pickle_in = open('pickler201705','rb')
	#val = pickle.load(pickle_in)
	#print (val.expect_dict)
    pass