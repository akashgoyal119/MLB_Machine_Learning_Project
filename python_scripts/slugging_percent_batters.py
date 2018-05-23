import pandas as pd
import pymysql as mc 
import os
import sys
import time
import numpy as np

cnx = mc.connect(user='akashgoyal',password=os.environ['DB_PASSWORD'],
                 host='stromberg.cs.uchicago.edu',db='mlb_practicum',port=3306)
cnx = mc.connect(user='root',password=os.environ['DB_PASSWORD'],host='localhost',db='mlb',port=3306)

def reclassify_pitches2(df):
        four_seam = ['FF','FA']
        slider = ['SL']
        two_seam = ['FT']
        change_up = ['CH']
        sinker = ['SI','FS']
        knuckleball = ['KN']
        curve = ['CU','KC']
        cutter = ['FC']
        df['pitchType'][df['pitchType'].isin(four_seam)] = 'four_seam'
        df['pitchType'][df['pitchType'].isin(slider)] = 'slider'
        df['pitchType'][df['pitchType'].isin(two_seam)] = 'two_seam'
        df['pitchType'][df['pitchType'].isin(change_up)] = 'change_up'
        df['pitchType'][df['pitchType'].isin(sinker)] = 'sinker'
        df['pitchType'][df['pitchType'].isin(knuckleball)] = 'knuckleball'
        df['pitchType'][df['pitchType'].isin(curve)] = 'curve'
        df['pitchType'][df['pitchType'].isin(cutter)] = 'cutter'
        return df

class slugging_pct:
    def __init__(self,df,trailing_ab,min_abs):
        self.df = df
        self.min_abs = min_abs
        self.trailing_ab = trailing_ab
        self.mapped_df = self.aggregation_helper(df)
        
        
    def aggregation_helper(self,df):
        possible_pitches = ['four_seam','slider','two_seam','change_up','sinker',
                        'knuckleball','curve','cutter']

        grouped = df.groupby(['gameID','abNum']).tail(1) #this gets the action pitch of the at bat
        grouped = grouped[grouped['pitchType'].notnull()] #get rid of pitches which we dont know the type
        ball_in_play = ['In play, out(s)','In play, run(s)','In play, no out'] #valid balls in play
        grouped = grouped[grouped.pitchDes.isin(ball_in_play)] #only get balls in play

        #create a dictionary mapping bases to each event
        ball_in_play_outs = ['Groundout','Flyout','Pop Out','Lineout','Sac Fly',
                        'Grounded Into DP','Forceout','Double Play', 'Field Error',
                        'Bunt Groundout','Sac Bunt','Fielders Choice Out','Bunt Pop Out',
                        'Fielders Choice','Bunt Lineout','Sac Fly DP','Triple Play',
                        'Sacrifice Bunt DP','Batter Interference','Fan interference',
                        'Catcher Interference']
        in_play_dict = {i:0 for i in ball_in_play_outs}
        in_play_dict['Home Run'] = 4
        in_play_dict['Triple'] = 3
        in_play_dict['Double'] = 2
        in_play_dict['Single'] = 1
        grouped['bases'] = grouped['the_event'].map(in_play_dict)
        return grouped
    
    def create_pivot(self,gameDate,df):
        grouped = df.groupby(['batterID','pitcherHand']).tail(self.trailing_ab)
    
        def pivot_helper(df):
            total = df.sum()
            if len(df)>self.min_abs:
                return total/len(df)
            return '\\N'
    
        #now calculate the slugging percent
        pivot_table = pd.pivot_table(grouped,values=['bases'],columns=['pitchType'],
                                     index=['batterID','pitcherHand'], aggfunc=pivot_helper,
                                    fill_value='\\N')

        pivot_table['gameDate'] = gameDate
        return pivot_table


query = """SELECT gameDate,Pitch2.gameID AS gameID, abNum,batterID, batterHand,pitcherHand,
        the_event,pitchID, pitchType,pitchDes,zone FROM Pitch2 INNER JOIN Game
        ON Game.gameID = Pitch2.gameID WHERE ((pitchType
        NOT IN ('IN','PO','FO','EP','SC','UN','AB')) OR pitchType is NULL)"""

df = pd.read_sql_query(query,cnx)
df2 = df.copy()
df2 = reclassify_pitches2(df2)
df2 = df2.sort_values(['gameDate','gameID','pitchID'],ascending=[True,True,True])

a = slugging_pct(df2,500,20)
distinct_dates = df2.gameDate.unique()
full_pivot_table = 'FILLER'
start_type = type(full_pivot_table)

for i,day in enumerate(distinct_dates):
	df = a.mapped_df[a.mapped_df['gameDate']<day] 
	if len(df)==0:
		continue

	piv = a.create_pivot(day,df)
	print (piv)
	if type(full_pivot_table)!=start_type and len(full_pivot_table)>0:
		full_pivot_table = full_pivot_table.append(piv)
	
	elif len(piv)!=0:
		full_pivot_table = piv 

	if i % 2 == 0:
		print (i,day)

full_pivot_table.to_csv('batter_slugging_percentages.txt')
