import os
import csv
import pymysql as mc 
import time
import webbrowser
import sys
#%matplotlib inline
import numpy as np
import pandas as pd
import getpass
from sqlalchemy import create_engine
from sqlalchemy.types import VARCHAR

pw = getpass.getpass()

cnx = mc.connect(user='akashgoyal',password=pw,
                 host='stromberg.cs.uchicago.edu',db='mlb_practicum',port=3306)

#reclassify all the pitch_types
def reclassify_pitches(df):
    #takes a current DF and returns a new DF with additional column 
    four_seam = ['FF','FA']
    slider = ['SL']
    two_seam = ['FT']
    change_up = ['CH']
    sinker = ['SI','FS']
    knuckleball = ['KN']
    curve = ['CU','KC']
    cutter = ['FC']
    na = ['IN','PO','FO','EP','SC','UN','AB']
    l = []
    i = 2
    
    for row in df.itertuples():
        if row[i] in four_seam:
            l.append('four_seam')
        elif row[i] in slider:
            l.append('slider')
        elif row[i] in two_seam:
            l.append('two_seam')
        elif row[i] in change_up:
            l.append('change_up')
        elif row[i] in sinker:
            l.append('sinker')
        elif row[i] in knuckleball:
            l.append('knuckleball')
        elif row[i] in curve:
            l.append('curve')
        elif row[i] in cutter:
            l.append('cutter')
        else:
            l.append(None)
    df['new_pitch_type']=l 
    return df

query = 'SELECT pitcherID, pitchType,Pitch2.gameID,gameDate FROM Pitch2 INNER JOIN Game ON Game.gameID=Pitch2.gameID'
df = pd.read_sql_query(query,cnx)
print ('finished running the query')
df2 = df.copy() 
df = None #this was originally done in jupyter...
df2 = reclassify_pitches(df2)

distinct_games = df2.gameDate.unique()
distinct_games = distinct_games[10:]
full_df = 'FILLER'
original_type = type(full_df)

password = pw
user='akashgoyal'
host='stromberg.cs.uchicago.edu'
db_name = 'mlb_practicum'

cnx2 = create_engine('mysql+pymysql://'+user+':'+password+'@'+host+':3306/'+db_name,echo=False)

for z,day in enumerate(distinct_games):
    start_time = time.time()
    
    temp_df = df2[df2['gameDate']<day]
    temp_df = temp_df.drop(columns=['gameDate','gameID']) #really just to match existing interface
    if len(temp_df)==0:
        continue
    #this will take in a dataframe and return a new Dataframe with
    #pitcherID, totalPitches, %fastballs, %sliders, %changeup, etc
    table = pd.pivot_table(temp_df,values=['new_pitch_type'],columns=['new_pitch_type'],
                       index=['pitcherID'],aggfunc='count')
    table.fillna(value=0,inplace=True)
    #convert counts to percentages and create a new dataframe
    players = {}
    for row in table.itertuples():
        total = 0
        freqList = []
        for i in range(1,9):
            total+=row[i]

        for i in range(1,9):
            freqList.append(row[i]/total)
        freqList.append(total)
        players[row[0]] = freqList
        
        #prepare the new dataframe for KMeans 
    player_df = pd.DataFrame.from_dict(players,orient='index')
    player_df.columns=["change_up","curve","cutter","four_seam",
                       "knuckleball","sinker","slider","two_seam","total_pitches"]
    condensed_df = player_df[player_df['total_pitches']>100]
    condensed_df = condensed_df.drop('total_pitches',axis=1)
    condensed_df['gameDate'] = day #add in the current date

    if type(full_df)==original_type:
        full_df = condensed_df
    else:
        full_df = full_df.append(condensed_df)
    print ('finished up df work')    
    #condensed_df.to_sql(name='pitcher_classifications_5_25_18',con=cnx2,if_exists='append',
    #           index=True,index_label='playerID',dtype={None:VARCHAR(20)})
    print ('added df to sql')
    if z%10==0:
        print (z,time.time()-start_time)

full_df.to_csv('new_pitcher_percentages_5_29_18.csv')


print ('all done!')
