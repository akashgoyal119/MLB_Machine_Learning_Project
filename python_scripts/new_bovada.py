#!/Library/Frameworks/Python.framework/Versions/3.6/bin/python3
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By 
import sys
import os 
import time
import datetime
import csv
from bs4 import BeautifulSoup

def calculate_implied_probability(moneyline):
	""" calculate the Bovada-implied probability of winning """

	if moneyline == 'EVEN':
		return 0.5
	odds = int(moneyline[1:])
	#if team is underdog
	if moneyline[0]=='+':
		return round(100.0/(odds+100),3)
	#if team is favored to win
	else:
		to_win = ((100.0)/odds)*100
		return round(100.0/(to_win+100),3)


driver = webdriver.Chrome()
driver.get('https://www.bovada.lv/sports/baseball/mlb')
element = WebDriverWait(driver,10).until(EC.presence_of_element_located((By.CLASS_NAME,'bet-btn')))
time.sleep(1)

driver.execute_script("window.scrollTo(0,1000)")
time.sleep(2)
driver.execute_script("window.scrollTo(0,2000)")
time.sleep(2)
driver.execute_script("window.scrollTo(2000,6000)")
time.sleep(2)
driver.execute_script("window.scrollTo(6000,8000)")
time.sleep(2)
driver.execute_script("window.scrollTo(8000,10000)")
time.sleep(2)
driver.execute_script("window.scrollTo(10000,12000)")
time.sleep(2)


innerHTML = driver.execute_script("return document.body.innerHTML")
driver.quit()
soup = BeautifulSoup(innerHTML,'html.parser')

# get the team information 
teams = soup.find_all('h4')
the_teams = []
for team in teams:
	the_team = team.text
	all_stuff = the_team.split('\n')
	the_teams.append(all_stuff[1])


odds = soup.find_all('sp-outcome')
probabilities = []
for i,odd in enumerate(odds):
	odd.find_all('span', class_="bet-price")
	data = odd.text
	data_array = data.split('\n')
	indicator = True
	for data in data_array:
		for letter in data:
			if letter =='(' or letter == ')':
				indicator = False
	if indicator:
		probabilities.append(data_array[7].strip())


driver.quit()
today = datetime.datetime.now()
year = today.year
month = today.month
day = today.day 

win_probabilities = zip(the_teams,probabilities)

directory = os.path.dirname(os.path.realpath(__file__))
with open (f'{directory}/output/bovada_odds-{year}-{month}-{day}.txt','w') as f:
	csv_writer = csv.writer(f,delimiter=',')
	for item in win_probabilities:
		csv_writer.writerow([item[0],item[1],calculate_implied_probability(item[1])])


