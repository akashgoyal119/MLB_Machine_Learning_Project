#!/Library/Frameworks/Python.framework/Versions/3.6/bin/python3
import os
import csv
import xml.etree.ElementTree as ET
import sys
import time 
from multiprocessing import Pool
from urllib.request import urlopen
from urllib.error import HTTPError
import urllib
import requests 
import datetime 
import pymysql
import getpass
import pandas as pd 
from sqlalchemy import create_engine
import sqlalchemy
import credentials as cred
import zipfile,urllib.request,shutil
from tqdm import tqdm

'''
	This file is intended to update the Pitch3 Database by grabbing the games from the previous date
	and then filling in all the information into the table. Note that the majority of the work is for the wRC calculation
'''
pw = getpass.getpass()

# https://github.com/panzarino/mlbgame/blob/master/mlbgame/data.py
BASE_URL = ('http://gd2.mlb.com/components/game/mlb/'
            'year_{0}/month_{1:02d}/day_{2:02d}/')
GAME_URL = BASE_URL + 'gid_{3}/{4}'

def get_schedule(tup):
	"""Return the game file for a certain day matching certain criteria."""

	year = tup[0]
	month = tup[1]
	day = tup[2]
	try:
		data = requests.get(BASE_URL.format(year, month, day) + 'scoreboard.xml')
		games = ET.fromstring(data.text)
		game_list = []
		for game in games:
			home_score = game.findall('team')[0].find('gameteam').attrib['R']
			away_score = game.findall('team')[1].find('gameteam').attrib['R']
			if home_score == away_score:
				continue
			game_list.append(game.find('game').attrib['id'])
		print (year,month,day)
		return game_list

	except Exception as e:
		print (e)
		with open('roster_errors.txt','a') as f:
			f.write(f'no games were played on {month},{day},{year}')
		return []

def get_date_from_game_id(game_id):
	''' From 2018_03_31_pitmlb_detmlb_1, return the date '''
	year, month, day, _discard = game_id.split('_', 3)
	return int(year), int(month), int(day)

def get_all_urls_from_retrosheet():
	# this part extracts all the files
	cwd = os.getcwd()
	url = "https://www.retrosheet.org/events/2010seve.zip"
	file_name = '2010zip.zip'
	with urllib.request.urlopen(url) as response, open(file_name,'wb') as out_file:
    		shutil.copyfileobj(response,out_file)
    		with zipfile.ZipFile(file_name) as zf:
        		zf.extractall(cwd+'/retrosheet_files')
	# this part traverses through each of the files and creates a list of all the URLS
	url_list = []
	pathName = cwd+'/retrosheet_files/'
	for file_name in os.listdir(pathName):
		fileInput = os.fsdecode(file_name)
		gameNum='1'
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
				url_list.append((gameID,'http://gd2.mlb.com/components/game/mlb/'+new_path))
		fname.close()
	return url_list

#look at the inning_all xml files
def get_game_data(tup):
	#year, month, day = get_date_from_game_id(gameID)
	#url = GAME_URL.format(year,month,day,gameID,'inning/inning_all.xml')
	gameID = tup[0]
	url = tup[1]
	relevant_info = main(gameID,url)
	return relevant_info

def getPitchAttributes(subtree,args):
	''' helper function for main '''
	l1 = []
	for arg in args:
		try:
			l1.append(subtree.attrib[arg])
		except KeyError as e:
			l1.append(None)
	return l1

# item is the gameID 
def main(item,url):
	''' this will go into the inning_all xml files and do the heavy lifting '''
	error_writer = []
	csv_writer = []

	try:
		data = urlopen(url).readline()
	except HTTPError as e: #likely got rained out
		print ('no game '+url)
		return []

	try:
	    game = ET.fromstring(data)
	except ET.ParseError as e:
	    print ('THIS GAME GOT MESSED UP PLEASE SEE THE ERROR LOG FOR GAME',item)
	    return []
	    error_writer.extend([item])
	except Exception as e2:
	    print (e2)
	    error_writer.extend([item,str(e2)])
	    return []

	pitcherDict = {} #use to track pitch count
	batterVpitcher= {}
	home_team_runs = 0
	away_team_runs = 0 

	for inning in game:
	    current_inning = inning.attrib['num']
	    for half in inning:
	        atBats = half.findall('atbat')
	        prevOuts = 0
	        curr_inn = int(current_inning)
	        if half.tag == 'bottom':
	            curr_inn+=0.5
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

	            # new at-bat so re-set the count 
	            strikes = 0
	            balls = 0 

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
	                    'sz_bot','pfx_x','pfx_z','px','pz','x0','y0','z0','vx0','vy0',
	                    'vz0','ax','ay','az','break_y','break_angle','break_length','type_confidence',
	                    'nasty','spin_dir','spin_rate','on_1b','on_2b','on_3b'])
	                pitch_info.extend(pitchCharacteristics)
	                pitch_info.append(prevOuts) #current number of outs before ball is in play
	                pitch_info.append(pitcherDict[current_pitcher]) #cumulative pitches by pitcher
	                pitch_info.append(batterVpitcher[current_matchup]) #number times faced prior to current AB
	                pitch_info.append(home_team_runs)
	                pitch_info.append(away_team_runs)
	                pitch_info.append(curr_inn)
	                pitch_info.append(balls)
	                pitch_info.append(strikes)
	                csv_writer.append(pitch_info) #write

	                # now that we've appended the result to csv_writer, let's update the count 
	                balls, strikes = update_count(pitch.attrib['des'],balls,strikes)

	            if prevOuts >2:
	                print (abInfo)
	                error_writer.append(str(abInfo))
	            prevOuts = int(at_bat.attrib['o']) #update the outs so that the next for loop can utilize this info
	            try: 
	            	home_team_runs = int(at_bat.attrib['home_team_runs'])
	            	away_team_runs = int(at_bat.attrib['away_team_runs'])
	            except Exception as e:
	            	error_writer.append(str(e))
	            	pass
	add_runs_created_to_list(csv_writer)

	db_name = cred.db_name
	user = cred.user
	password = pw
	host = cred.host
	cnx = create_engine('mysql+pymysql://'+user+':'+password+'@'+host+':3306/'+db_name,echo=False)

	columns = ['gameID','abNum','batterID','pitcherID','batterHand','pitcherHand',
				'event_num','the_event','pitchID','pitchType','pitchDes','pitchTypeShort',
				'zone','x','y','initialVelocity','endVelocity','szTop','szBottom','pfx_x',
				'pfx_z','px','pz','x0','y0','z0','vx0','vy0','vz0','ax','ay','az','break_y',
				'break_angle','break_length','type_confidence','nasty','spin_dir','spin_rate',
				'firstBaseRunner','secondBaseRunner','thirdBaseRunner','outs','cumulativePitches',
				'timesFaced','home_team_runs','away_team_runs','curr_inn','balls','strikes','runs_created']

	df = pd.DataFrame(data=csv_writer, columns=columns)
	print (item,url)
	try:
		df.to_sql('Pitch',cnx,if_exists='append',index=False)
	except sqlalchemy.exc.IntegrityError as e:
		print (e)
		print ('already inserted these in',item,url)
		error_writer.append(str(e))
	return csv_writer 
	
def add_runs_created_to_list(csv_writer):
	# append the runs created in the at-bat
	for i,line in enumerate(csv_writer):
		is_home_team = False if float(line[47])==int(line[47]) else True
		current_team_runs = line[45] if is_home_team else line[46]
		current_outs = line[42] 
		current_1b_runner = line[39]
		current_2b_runner = line[40]
		current_3b_runner = line[41]
		score_indx = 45 if is_home_team else 46
		try:

			#print (line[0],line[1],line[2],line[47],current_team_runs,csv_writer[i][45],csv_writer[i+1][45],csv_writer[i][46],csv_writer[i+1][46],is_home_team)
			team_runs_next_ab = csv_writer[i+1][score_indx]

			if line[47] == csv_writer[i+1][47]: #if within same inning
				next_outs = csv_writer[i+1][42]
				next_1b_runner = csv_writer[i+1][39]
				next_2b_runner = csv_writer[i+1][40]
				next_3b_runner = csv_writer[i+1][41]
			else:
				next_outs = None
				next_1b_runner = None
				next_2b_runner = None
				next_3b_runner = None

		except IndexError as e:
			team_runs_next_ab = line[score_indx]
			next_outs = None
			next_1b_runner = None
			next_2b_runner = None
			next_3b_runner = None

		rc = calculate_runs_created(current_team_runs, team_runs_next_ab,
								    current_outs,next_outs,
								    current_1b_runner, next_1b_runner,
								    current_2b_runner, next_2b_runner,
								    current_3b_runner, next_3b_runner)
		line.append(rc)

	# now adjust the current game to fix the problem where the runs-created for a given at-bat
	# are different based off different pitches in the AB
	for i,line in reversed(list(enumerate(csv_writer))):
		if i == len(csv_writer)-1: #if we're at the last line, do nothing
			continue
		else:
			if line[1]==csv_writer[i+1][1]: #if same at-bat
				line[50] = csv_writer[i+1][50]
			else:
				continue

def calculate_runs_created(current_team_runs, team_runs_next_ab,
						   current_outs,next_outs,
						   current_1b_runner, next_1b_runner,
						   current_2b_runner, next_2b_runner,
						   current_3b_runner, next_3b_runner):

	run_expectancies = {0: 0.47, 1:0.827, 2:1.089, 3:1.393, 4:1.364, 5:1.729, 6:1.952,
					    7:2.177, 8:0.248, 9:0.489, 10:0.639, 11:0.846, 12:0.927, 13:1.097, 
					    14:1.356, 15:1.491, 16:0.098, 17:0.205, 18:0.302, 19:0.403, 20:0.342,
					    21:0.433, 22:0.522, 23:0.692}
	#determines which of the 24 runner on base/outs circumstances we are currently in
	def calculate_state(runner1b,runner2b,runner3b,outs):
	    total = 0
	    if runner1b:
	        total+=1
	    if runner2b:
	        total+=2
	    if runner3b:
	        total+=4

	    if outs==1:
	        total+=8
	    elif outs ==2:
	        total+=16
	    elif outs>=3 or outs<0:
	        print ('Umpire ejected a player and things got screwed up')
	        return 16
	    return total

	situation = calculate_state(current_1b_runner,current_2b_runner,current_3b_runner,current_outs)
	expected_runs = run_expectancies[situation]

	if next_outs == None: #new inning 
		new_expected_runs = 0
	else:
		next_situation = calculate_state(next_1b_runner,next_2b_runner,next_3b_runner,next_outs)
		new_expected_runs = run_expectancies[next_situation]

	scored_in_at_bat = team_runs_next_ab - current_team_runs

	if scored_in_at_bat < 0:
		print ('messed up negative runs')
		raise Exception ('Cant Have Negative Runs!')
		sys.exit()
	return new_expected_runs - expected_runs + scored_in_at_bat

def update_count(event,prev_balls,prev_strikes):
	valid_dict =  {'Ball':'Ball','Called Strike':'Strike','Swinging Strike':'Strike',
                           'Ball In Dirt':'Ball', 'Swinging Strike (Blocked)':'Strike',
                           'Intent Ball':'Ball', 'Missed Bunt':'Strike',
                           'Automatic Ball':'Ball', 'Pitchout':'Ball', 'Swinging Pitchout':'Strike',
                           'Automatic Strike':'Strike','Foul Bunt':'Strike'}
	action_list = ['Hit By Pitch','In play, out(s)','In play, no out','In play, run(s)']
	extend_dict = {'Foul':0,'Foul Tip':0,'Foul (Runner Going)':0,'Foul Pitchout':0}

	# account for games where umpire screwed up
	if prev_balls>3:
		prev_balls = prev_balls - 1
		print ('this game had a messed up ball count (>=4)')
	if prev_strikes > 2:
		prev_strikes = prev_strikes - 1
		print ('this game had a messed up strike count (>=3)')

	# normal situation 
	if event in valid_dict:
		if valid_dict[event] == 'Ball':
			return prev_balls+1,prev_strikes 
		else:
			return prev_balls,prev_strikes+1 

	# the pitch was a foul, so if there two strikes, keep it same,
	# else add a strike. Note that if it was in-play the updated count wouldnt matter
	elif prev_strikes!=2:
		return prev_balls, prev_strikes+1
	else:
		return prev_balls, prev_strikes

if __name__ == '__main__':
	urls = get_all_urls_from_retrosheet()
	'''
	print ('starting job')
	year = 2018

	
	month_day_dict = {3:31,4:30,5:31,6:30,7:2}
	l = []
	# USE THIS FOR OLD WORK CATCHING UP
	
	p = Pool(processes=30)

	for month in month_day_dict:
		# don't include spring training 
		if month == 3:
			for i in range(29,32):
				l.append((year,month,i))
		else:
			for day in range(1,month_day_dict[month]+1):
				l.append((year,month,day))

	game_list = p.map(get_schedule,l)
	print ('done with first job')
	game_list = [item for sublist in game_list for item in sublist] # https://stackoverflow.com/questions/952914/making-a-flat-list-out-of-list-of-lists-in-python
	'''
	p = Pool(processes=10)
	relevant_info = p.map(get_game_data,urls)
	

	'''

	#basically gets the url for each game so that we can easily query in the next function
	game_list = get_schedule((previous_date.year,previous_date.month,previous_date.day))
	'''



	print ('done writing')
