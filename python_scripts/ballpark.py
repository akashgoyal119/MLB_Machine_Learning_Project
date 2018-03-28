#make the ballpark file
#http://www.retrosheet.org/parkcode.txt
import sys 

def convertDate(aDate):
    if len(aDate) == 0:
        return chr(92)+'N'
    else:
        return aDate[-4:]+'-'+aDate[:2]+'-'+aDate[3:5]

myOutput = open('ballparkOutput.txt','w')
bp = open('ballparkInput.txt','r')
lines = bp.readlines()
for line in lines:
    try:
        arr = line.split(',')
        myStr = arr[0]+','+arr[1]+','+convertDate(arr[5])+','+convertDate(arr[6])
        myOutput.write(myStr+'\n')
    except:
        print (arr)
        sys.exit()

myOutput.close()
bp.close()
