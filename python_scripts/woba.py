#Baseball wOBA class
from functools import reduce

class Woba:
	def __init__(self,df):
		self.df = df

		#steps... 
		#1) look through the database and calculate the run expectancies for all 24 states (outs/runners). 
		# Do this by choosing a select where XYZ runner is not on first second or third... and calculate
		# the number of outs until the end of the inning

		#2) calculate the average starting run expectancy for each type of event (i.e. do a lookup of the above situation)
		# before the AB in question

		#3) calculate the run expectancy from right before the batter gets on base to the end of the inning.

		# 4) Take the difference between 3 and 2 for the run value of an event. You can thus have negative values since
		# you are comparing the expectancy now versus before (whcih could drop if you had a bad at-bat)

		#5) adjust home runs by looking at the state in Step 1 at the beginning vs. end of the at-bat + runs scored from the HR
		# then take the weighted average of each of the 24 situations to calculate the run value. do this for all events

		#6) calculate the run expectancy of an out and then add those to all the situations where you reach base to 
		# update the run expectancy



		#7) He attempts to match the calculations to league-average OBP so he increases each factor by 15%
		
		#8) calculation is just a hitter's sum of these weights divided by (AB + BB - IBB + SF + HBP)

		#9) average hitter should be around 0.340, great hitter is above 0.400 and bad hitter below 0.300

		#10) to calculate the run value per PA above average, simply take wOBA_player-wOBA_league_avg/1.15

		#could also do the same calculation for win expectancy 

class AB:
	#I could also just pass a dataframe and extract values that way
	def __init__(self,gameID,abNum,outs, runner_scenario, inning,event,start_runs):
		self.gameID = gameID
		self.abNum = abNum
		self.outs = outs
		self.runner_scenario = runner_scenario
		
		self.event = None
		self.inning = inning
		self.start_run_expectancy = None
		self.end_run_expectancy = None
		self.runs_created  = None

	def calculate_runs_created(self):
		return self.inning.endScore - self.df.loc[last_pitch,home_away_score]

	def calculate_end_run_expectancy(self,nextAB=None):
		if not nextAB:
			return 0
		elif nextAB.abNum > self.abNum+1:
			return 0
		else:
			return nextAB.start_run_expectancy

	def calculate_runs_created(self,nextAB=None):
		if not nextAB:
			return 0
		else:
			return self.end_run_expectancy-self.start_run_expectancy+nextAB.start_runs - self.start_runs 


class Inning:
	def __init__(self,df):
		self.inning_number = df.loc[:,'inning'].mode()
		self.gameID = df.loc[:,'gameID'].mode()
		self.home_or_away = self.get_home_or_away()
		self.endScore = self.get_end_score(df)

	def get_home_or_away(self):
		if self.inning_number*2%2 == 1:
			return 'Home'
		else:
			return 'Away'

	def get_end_score(self,df):
		#just look at the last row of the dataframe
		if self.home_or_away == 'Home':
			return df[-1:'home_team_runs']
		else:
			return df[-1:'away_team_runs']
		#this should look at the dataframe and return the score of the last 
		#AB in the inning of the (away team if inning ends in 0.0 or home team if it ends in 0.5)
		#note I will deal with getting rid of 9.5+ in the AB class

#uses the chmod scheme in order to map scenarios from 1 to 8
def calculate_runner_situation(aRow):
	total = 0
	if aRow['runner_1b']:
		total+=1
	if aRow['runner_2b']:
		total+=2
	if aRow['runner_3b']:
		total+=4
	return total

#add 8 and 16 if outs are 1,2 respectively
def calculate_situation(runner_sit,outs):
	newSit = runner_sit
	if outs >= 3 or outs <0:
		raise ValueError('You cannot start the AB with 3 or less outs. There was probably an error w the data')
	if outs == 0:
		return newSit
	elif outs ==1:
		return newSit+8
	elif outs ==2:
		return newSit+16


massive_df = pd.read_sql('SELECT * FROM Pitch')
df_helper = 'SELECT gameID, inning, COUNT(*) FROM Pitch GROUP BY gameID, inning'
all_combos = ['some_list_comprehnsion to extract all these']
inning_list = []
ab_list = []

for item in all_combos:
	inning_df = massive_df[massive_df.loc[:,'gameID']==item.gameID and massive_df.loc[:,'inning']==item.inning]
	inning_df.sort(columns=['pitchID'],inplace=True,kind='mergesort')
	inning_object = Inning(inning_df)
	#sort the dataframe on pitchNumberAscending
	

	#now traverse through each line and determine if the current row's abNum is different from the next one, or
	#if we hit a row out of bounds: if so create an AB oject
	for indx,row in enumerate(inning_df.iterrows()):
		try:
			#I can further hash this out so that I really don't need the inning_object and don't have to worry
			#about the reference getting deleted as I further traverse
			if inning_df[indx:'abNum'] == inning_df[indx+1,'abNum']:
				ab_object = AB(row['gameID'],row['abNum'],row['outs'],inning_object)
				abList.append(ab_object)
		except IndexOutOfBoundsError as e:
			ab_object = AB(row['gameID'],row['abNum'],row['outs'],inning_object)
			ab_list.append(ab_object)

#now I can discard the the massive_df pandas array from memory since I have all the objects I need in my ab_list/inning_list

#now initialize the list of outcomes
avg_run_scored_dict = {}
for i in range(24):
	avg_run_scored_dict[i] = []

for at_bat in ab_list:
	try:
		current_scenario = calculate_situation(at_bat.runner_scenario, at_bat.outs)
		avg_run_scored_dict[current_scenario].append(at_bat.runs_created)
	except ValueError as e:
		print (at_bat.gameID,at_bat.abNum)
		continue 

for i in range(24):
	avg = reduce(lambda x,y: x+y, avg_run_scored_dict[i])/5.0
	print ('there were {} observations for category {}, and the average runs scored was {}'.format(len(avg_run_scored_dict[i]),i,avg))
