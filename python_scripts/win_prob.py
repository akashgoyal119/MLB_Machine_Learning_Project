import os
import csv
import pymysql as mc 
import time
import webbrowser
import sys
from sklearn.cluster import KMeans
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import KFold, learning_curve
from sklearn.preprocessing import scale, PolynomialFeatures, LabelEncoder
from sklearn.neural_network import MLPClassifier
from pitcher_classification import Cluster_Data 

class WinProb:
    '''
        cnx is the SQL connection, sql_attrs is a list of items in either Pitch2 or
        Pitcher_Run_Expectancy. Enter a year between 2010 and 2017. you must enter
        at least one item in the list or else it will mess up. 
    '''
    def __init__(self,cnx,year=None):
        self.cnx = cnx
        self.year = year
        self.sql_attrs = ['300_avg','500_avg','1000_avg','2000_avg',
                          'timesFaced','cumulativePitches']
        self.df = self.run_sql_query()
        print ('done running query')
        self.add_wins_and_current_lead()
        self.classify_count()
        self.add_runners_on_base()
        self.X,self.Y = self.prepare_logistic_regression()
        print ('done preparing new df for regression')
        self.add_pythagorean_wins()
        print ('done adding pythagorean wins')
        print ('you can manually run the neural net now if you like by calling self.create_neural_net(number_nodes)')
        self.nn = None

    def run_sql_query(self):
        query = ''
        if not self.year:
            query = """SELECT Game.gameID AS gameID,homeTeamScore,awayTeamScore,curr_inn,balls,strikes,
                        firstBaseRunner, secondBaseRunner,thirdBaseRunner,home_team_runs,away_team_runs,{}
                        FROM Pitch2 INNER JOIN Pitcher_Run_Expectancy ON 
                        (Pitcher_Run_Expectancy.gameID = Pitch2.gameID AND
                        Pitcher_Run_Expectancy.playerID = Pitch2.pitcherID).""".format(','+','.join(self.sql_attrs))
        else:
            query = """SELECT Game.gameID AS gameID,homeTeamScore,awayTeamScore,curr_inn,balls,strikes,
                        firstBaseRunner, secondBaseRunner,thirdBaseRunner,home_team_runs,away_team_runs,{}
                        FROM Pitch2 INNER JOIN Game ON Pitch2.gameID = Game.gameID
                        INNER JOIN Pitcher_Run_Expectancy ON 
                        (Pitcher_Run_Expectancy.gameID = Pitch2.gameID 
                        AND Pitcher_Run_Expectancy.playerID = Pitch2.pitcherID)
                        WHERE YEAR(gameDate) IN ({})""".format(','.join(self.sql_attrs),','.join(self.year))
            df = pd.read_sql_query(query,self.cnx)
            return df 
    
    def add_wins_and_current_lead(self):
        #define whether or not the team batting now won or lost the game 
        self.df['win'] = pd.Series([(1 if (x[0]<x[1] and x[2]*2%2==0) or (x[0]>x[1] and x[2]*2%2==1) else 0)
                        for x in self.df[['homeTeamScore','awayTeamScore','curr_inn']].values])

        #add the current lead 
        l = []
        for x in self.df[['home_team_runs','away_team_runs','curr_inn']].values:
            #if home team
            if x[2]*2%2==1:
                l.append(x[0]-x[1])
            else:
                l.append(x[1]-x[0])
        self.df['current_lead'] = l
        #drop the homeTeamScore,awayTeamScore since we don't know the final outcome at the current pitch 
        self.df.drop(columns=['homeTeamScore','awayTeamScore','home_team_runs','away_team_runs'],inplace=True)
    
    #create 12 variables for each type of count 
    def classify_count(self):
        s = pd.Series([(x[0],x[1]) for x in self.df[['balls','strikes']].values])
        s = pd.get_dummies(s)
        self.df = self.df.join(s,how='outer')
        self.df.drop(columns=['balls','strikes']) 

    #KILL THIS AND JUST MAKE ITS OWN 
    def classify_count_deprecated(self):
        #add count classification (bad,neutral,favorable)
        l = []
        errs= []
        good = [(3,0),(3,1),(2,0),(3,2)]
        neutral = [(0,0),(1,0),(2,1),(1,1),(2,2)]
        bad = [(1,2),(0,2),(0,1)] 
        for x in self.df[['balls','strikes']].values:
            count = (x[0],x[1])
            if count in good:
                l.append(2)
            elif count in neutral:
                l.append(1)
            elif count in bad:
                l.append(0)
            else:
                errs.append(count)
        self.df['count_type'] = l
        
    def add_runners_on_base(self):
        #indicator variables if runners on base
        firstRunner = []
        secondRunner = []
        thirdRunner = []
        mod_inning = []
        home_away = []
        for x in self.df[['firstBaseRunner','secondBaseRunner','thirdBaseRunner','curr_inn']].values:
            firstRunner.append(1 if x[0] else 0)
            secondRunner.append(1 if x[1] else 0)
            thirdRunner.append(1 if x[2] else 0)
            if (2*x[3])%2 == 1:
                mod_inning.append(x[3]-0.5)
                home_away.append(0)
            else:
                mod_inning.append(x[3])
                home_away.append(1)
        self.df['1b runner'] = firstRunner
        self.df['2b runner'] = secondRunner
        self.df['3b runner'] = thirdRunner
        self.df['mod inning'] = mod_inning
        self.df['home_away'] = home_away
        self.df.drop(columns=['curr_inn','firstBaseRunner','secondBaseRunner',
                              'thirdBaseRunner'],inplace=True)
        
    def prepare_logistic_regression(self):
        Y = self.df['win']
        X = self.df.drop(columns=['win'])
        return X,Y

    def add_pythagorean_wins(self):
        qry = 'SELECT * FROM Pythagorean_Wins'
        wins_df = pd.read_sql_query(qry,self.cnx)
        self.X = self.X.merge(wins_df,how='inner',left_on='gameID',right_on='gameID')

        #this part just takes the difference of the pythagorean win expectancy
        c10 = []
        c30 = []
        c50 = []
        c100 = []
        for (indx,row) in self.X.iterrows():
            x10 = row['away10']-row['home10']
            x30 = row['away30'] - row['home30']
            x50 = row['away50'] - row['home50']
            x100 = row['away100'] - row['home100']
            if row['home_away'] == 1: #if away
                c10.append(x10)
                c30.append(x30)
                c50.append(x50)
                c100.append(x100)
            else:
                c10.append(-x10)
                c30.append(-x30)
                c50.append(-x50)
                c100.append(-x100)
        self.X['p10'] = c10 
        self.X['p30'] = c30
        self.X['p50'] = c50
        self.X['p100'] = c100
        self.X = self.X.drop(columns=['home10','away10','home30','away30','home50',
                                      'away50','home100','away100','gameID'])

    #for now I'll support just one hidden layer
    def create_neural_net(self,hidden_nodes):
        nn = MLPClassifier(solver='lbfgs',alpha=0.001,hidden_layer_sizes=(hidden_nodes,),random_state=1)
        nn.fit(self.X,self.Y)
        self.nn = nn 
        print ('Your in sample Neural Network Score was {}'.format(nn.score(self.X,self.Y))) 


#This is not really meant to be used again... 
class Pythagorean_Wins:
    #looks through dataframe to find the ex-ante pythag win expectancy
    #this will take 5-10 minutes to run so be patient 
    def calculate_pythag_win(cnx,year,trailingGamesList):
        qry = '''SELECT gameID, homeTeam,awayTeam,homeTeamScore,awayTeamScore,
                     gameDate FROM Game WHERE YEAR(gameDate)<={}'''.format(year)
        game_df = pd.read_sql_query(qry,cnx)
        
        #adjust for Marlins team name:
        for (idx,row) in game_df.iterrows():
            if row['homeTeam'] == 'FLO':
                row['homeTeam'] = 'MIA'
            elif row['awayTeam'] == 'FLO':
                row['awayTeam'] = 'MIA'
        
        all_teams = game_df.homeTeam.unique()
        
        #create dataframes for all 31 teams
        team_game_dict = {} 
        for team in all_teams:
            team_game_dict[team] = game_df[(game_df['homeTeam']==team) |
                                           (game_df['awayTeam']==team)]
        
        #pWins will take a gameID as key and value will be a list of home and away team stats (alternating)
        pWins = {} 

        for game in game_df.itertuples():
            gameID = game[1]
            homeTeam = game[2]
            awayTeam = game[3]
            currentDate = game[6]
            
            home_df = team_game_dict[homeTeam]
            home_df = home_df[home_df['gameDate']<currentDate].sort_values(by="gameDate")
            away_df = team_game_dict[awayTeam]
            away_df = away_df[away_df['gameDate']<currentDate].sort_values(by="gameDate")
            

            for i,number in enumerate(trailingGamesList):
                temp = home_df.iloc[-number:,:]
                runs_for = 0
                runs_against = 0
                
                for (idx,row) in temp.iterrows():
                    if row['homeTeam'] == homeTeam:
                        runs_for+= row['homeTeamScore']
                        runs_against+=row['awayTeamScore']
                    else:
                        runs_for+=row['awayTeamScore']
                        runs_against+=row['homeTeamScore']
                
                #if no games have been played yet then just give them 50/50 chance of winning
                if len(temp) == 0: #special case for first iteration
                    if i==0:
                        pWins[gameID] = [0.5]
                    else:
                        pWins[gameID].append(0.5) 
                        
                #otherwise calculate pythagorean wins like normal 
                else:
                    pythag_wins = (runs_for)**1.81/(runs_for**1.81+runs_against**1.81)
                    if i ==0:
                        pWins[gameID] = [pythag_wins]
                    else:
                        pWins[gameID].append(pythag_wins)
                    
                    
                #now do the same calculation for the away team
                temp = away_df.iloc[-number:,:]
                runs_for = 0
                runs_against = 0
                for (idx,row) in temp.iterrows():
                    if row['homeTeam'] == awayTeam:
                        runs_for+= row['homeTeamScore']
                        runs_against+=row['awayTeamScore']
                    else:
                        runs_for+=row['awayTeamScore']
                        runs_against+=row['homeTeamScore']
                
                if len(temp)==0:
                    pWins[gameID].append(0.5)
                else:
                    pythag_wins = (runs_for)**1.81/(runs_for**1.81+runs_against**1.81)
                    pWins[gameID].append(pythag_wins)
        
        return pWins