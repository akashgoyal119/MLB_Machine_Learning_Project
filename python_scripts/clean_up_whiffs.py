import csv

input_file = '/Users/t2/Desktop/github/MLB_Machine_Learning_Project/python_scripts/hitter whiff rates.csv'
output_file = '/Users/t2/Desktop/github/MLB_Machine_Learning_Project/python_scripts/new hitter whiff rates.csv'
with open(input_file,'r') as csv_file:
	with open(output_file,'w') as csv_out:
		csv_reader = csv.reader(csv_file)
		csv_writer = csv.writer(csv_out,delimiter=',')
		for i,row in enumerate(csv_reader):
			l = [col if len(col)!=0 else chr(92)+'N' for col in row]
			csv_writer.writerow(l)
			if i %50000 == 0:
				print (i)