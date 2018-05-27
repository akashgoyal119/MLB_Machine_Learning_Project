import pandas as pd
import pymysql as mc 
import os
import time 

start = time.time()
cnx = mc.connect(user='akashgoyal',password=os.environ['DB_PASSWORD'],
                 host='stromberg.cs.uchicago.edu',database='mlb_practicum')

query = """SELECT gameID, pitchID, batterID, pitcherID, akash, curr_inn
		   FROM Pitch2 INNER JOIN Pitch_type_mapping ptm ON ptm.original = Pitch2.pitchType"""

query2 = """SELECT gameID, batterID FROM Pitch2 
			GROUP BY gameID, batterID"""

df = pd.read_sql_query(query,cnx)
print ('got this far')
df2 = pd.read_sql_query(query2,cnx)
print ('got this far')
print ('queries took '+str(time.time()-start)+' seconds')

types = ['four_seam','curve','slider','two_seam','cutter','kunckleball','sinker',
	        'change_up']
def initialize():
	return {'four_seam':0, 'curve':0,'slider':0,'two_seam':0,
							'cutter':0, 'knuckleball':0, 'sinker':0, 'change_up':0,'total':0}

def initialize2():
	return {'four_seam':0, 'curve':0,'slider':0,'two_seam':0,
							'cutter':0, 'knuckleball':0, 'sinker':0, 'change_up':0,'total':0}

#initialize conditions for each batter and game
player_game_dict = {}
for i in df2.itertuples():
	game = i[1]
	player = i[2]
	player_game_dict[game+player] = initialize2()

#all these lists will ultimately be used to add to the end dataframe
ff1=[]
cb1=[]
sl1=[]
two1=[]
cut1=[]
kn1=[]
si1=[]
cu1=[]
all_lists = [ff1,cb1,sl1,two1,cut1,kn1,si1,cu1]

ff2=[]
cb2=[]
sl2=[]
two2=[]
cut2=[]
kn2=[]
si2=[]
cu2=[]
all_lists2 = [ff2,cb2,sl2,two2,cut2,kn2,si2,cu2]

#create a mapping to help out with for loops below
pt_number_map = {0:'four_seam', 1:'curve',2:'slider',3:'two_seam',
					4:'cutter', 5:'knuckleball', 6:'sinker', 7:'change_up'}
prevGame = 'phony game'
prevPitcher = {'home':'home phony pitcher','away':'away phony pitcher'}

in_game_total = initialize()
w = 0
curr = time.time()
for i in df.itertuples():
	
	w = w + 1

	curr_game = i[1]
	curr_pitcher = i[4]
	curr_batter = i[3]
	pitch_type = i[5]
	inning = i[6] #used to distinguish home and away
	home_or_away = 'away'
	if inning*2%2==1: #it's the home team
		home_or_away = 'home'

	#if we are in a new game or see a new pitcher, reset the values 
	if curr_game!=prevGame or prevPitcher[home_or_away]!=curr_pitcher:
		in_game_total = initialize()
		player_game_dict[curr_game+curr_batter] = initialize()

	#in_game_total has pitch % of each type that all batters have seen against particular pitcher
	#pt _number_map maps the number to the pitch type. thus in_game_total['pitchType'] gives you
	#the total % of each type of pitch. 
	for i,item in enumerate(all_lists):
		pt = pt_number_map[i]
		if in_game_total['total'] == 0: #beginning condition case prevent divde by 0
			item.append(0)
		else:
			item.append(in_game_total[pt]/in_game_total['total'])
		#prepare for next iteration
		if pt == pitch_type:
			in_game_total[pt]+=1
	in_game_total['total']+=1


	#do same for % of pitch types seen by just the current hitter
	for i,item in enumerate(all_lists2):
		player_dict = player_game_dict[curr_game+curr_batter]
		pt = pt_number_map[i]
		if player_dict['total']==0:
			item.append(0)
		else:
			item.append(player_dict[pt]/player_dict['total']) #print the % of each type to the list
		if pt == pitch_type:
			player_dict[pt]+=1
	player_dict['total']+=1

	#update values
	prevGame = curr_game
	prevPitcher[home_or_away] = curr_pitcher
	if w %10000 == 0:
		print('this iteration {} took {} seconds'.format(w,time.time()-curr))
		curr = time.time()

for i,pt in enumerate(types):
	df[f'pct_{pt}_seen_team'] = all_lists[i]

for i,pt in enumerate(types):
	df[f'pct_{pt}_seen_individual'] = all_lists2[i]

df.to_csv('prior_pitches_full_game.csv')




