import pandas as pd
import pymysql as mc 
import os
import sys
import time
import numpy as np

cnx = mc.connect(user='akashgoyal',password=os.environ['DB_PASSWORD'],
                 host='stromberg.cs.uchicago.edu',db='mlb_practicum',port=3306)

query = """SELECT gameDate,Pitch2.gameID AS gameID, batterID, batterHand,pitcherHand,
        the_event,pitchID, pitchType,pitchDes,zone FROM Pitch2 INNER JOIN Game
        ON Game.gameID = Pitch2.gameID WHERE pitchType NOT IN
        ('IN','PO','FO','EP','SC','UN','AB')"""
df = pd.read_sql_query(query,cnx)
print ('made it here')
sys.exit()

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

df2 = df.copy()
df2 = reclassify_pitches2(df2)
sorted_df = df2.sort_values(['gameDate','gameID','pitchID'],ascending=[True,True,True])

# aggregation 2:
# alternate approach: more columns
# replace this list with your own

swinging_outcomes = [
    'Swinging Strike', 'Foul', 'In play, no out', 'In play, out(s)', 'In play, run(s)',
    'Swinging Strike (Blocked)','Swinging Pitchout','Missed Bunt','Foul Tip',
    'Foul Bunt','Foul (Runner Going)']

whiff_outcomes = ['Swinging Strike','Swinging Strike (Blocked)','Swinging Pitchout',
                 'Missed Bunt']

pitch_types = ['four_seam','slider','two_seam','change_up','sinker','knuckleball','curve','cutter']
grouping_columns = ['batterID','pitcherHand']

def aggregation2(df, trailing_ab):
    summing_columns = []
    for pt in pitch_types:
        summing_columns.extend([f'swing_{pt}', f'whiff_{pt}', f'ball_{pt}', f'is_{pt}'])
        df[f'is_{pt}'] = df['pitchType'] == pt
        df[f'swing_{pt}'] = df['pitchDes'].isin(swinging_outcomes) & (df['pitchType'] == pt)
        df[f'whiff_{pt}'] = df['pitchDes'].isin(whiff_outcomes) & (df['pitchType'] == pt)
        df[f'ball_{pt}'] = (df['pitchDes'] == 'Ball') & (df['pitchType'] == pt)
    
    #need to have groupedby, then tail, then grouped by again as tail will return a dataframe, and groupby
    #will return the last trailing abs back as another group by object
    grouped = df.groupby(grouping_columns).tail(trailing_ab).groupby(grouping_columns)
    agg_operations = {c: 'sum' for c in summing_columns} #creates a dictionary here to get the sum of all
    agg_operations['batterID'] = 'count' #just for the batterID create a count
    aggregated = grouped.agg(agg_operations) #this will return a dataframe for the aggregated operation
    
    #make sure the values aren't booleans....
    for col in aggregated.columns:
        aggregated[col] = np.where(aggregated[col]==False,0,aggregated[col])
        
    aggregated.rename(index=str, columns={'batterID': 'pitch_count'}) 
    for pt in pitch_types:
        aggregated[f'whiff_{pt}_rate'] = np.where(aggregated[f'swing_{pt}']<=20,None,
        										  aggregated[f'whiff_{pt}'] / aggregated[f'swing_{pt}'])
        aggregated[f'swing_{pt}_rate'] = np.where(aggregated[f'is_{pt}']<=20,None,
        										  aggregated[f'swing_{pt}'] / aggregated[f'is_{pt}'])
        aggregated[f'ball_{pt}_rate'] = np.where(aggregated[f'is_{pt}']<=20,None,
        										 aggregated[f'ball_{pt}'] / aggregated[f'is_{pt}'])
    return aggregated


start = time.time()
unique_dates = sorted_df.gameDate.unique()
copy_df = sorted_df.copy()
new_dataframe = None 
for i,day in enumerate(unique_dates):
    sub_dataframe = copy_df[copy_df['gameDate']<day].copy()
    if len(sub_dataframe)==0:
        continue
    sub_dataframe = aggregation2(sub_dataframe,1000)
    sub_dataframe['gameDate'] = day #add this is in for the specific game
    
    if new_dataframe is not None:
        new_dataframe = new_dataframe.append(sub_dataframe)
    else:
        new_dataframe = sub_dataframe
    
    if i % 10 == 0:
        print (f'weve gone through {i} iterations in {time.time()-start} secs')
        start = time.time()

new_dataframe.to_csv('whiff_rates.csv')