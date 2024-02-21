
import sys
from json import loads
from re import sub

columnSeparator = "|"

# Dictionary of months used for date transformation
MONTHS = {'Jan':'01','Feb':'02','Mar':'03','Apr':'04','May':'05','Jun':'06',\
        'Jul':'07','Aug':'08','Sep':'09','Oct':'10','Nov':'11','Dec':'12'}

# Global variable used to keep count of highest category within the dataset (TEST -> set to 10 to see if we can insert)
categoryCount = 0

# Global list used to keep track of the category class objects for building the dat file
categoryList = []

#for the given bid, associate an id num (primary key constraint)
bidNum = 0

"""
Category Class. Object to hold the datas categories. We hold the associated itemID, number of categories, and a list
of each category used
"""
class catObj:
    def __init__(self, itemNum, numCat, category):
        self.itemNum = itemNum
        self.numCat = numCat
        self.category = category

"""
Given a string for the table we need to insert, we'll ensure the following:
1. Every string surrounded by double quotes
2. Replace any single double quotes with two double quotes (" -> "")
"""
def updateString(s):
    #first, look for any single quotes and add double quotes
    s = s.replace('"', '""')

    #add double quotes to string value
    s = '"' + s + '"'

    return s


"""
Returns true if a file ends in .json
"""
def isJson(f):
    return len(f) > 5 and f[-5:] == '.json'

"""
Converts month to a number, e.g. 'Dec' to '12'
"""
def transformMonth(mon):
    if mon in MONTHS:
        return MONTHS[mon]
    else:
        return mon

"""
Transforms a timestamp from Mon-DD-YY HH:MM:SS to YYYY-MM-DD HH:MM:SS
"""
def transformDttm(dttm):
    dttm = dttm.strip().split(' ')
    dt = dttm[0].split('-')
    date = '20' + dt[2] + '-'
    date += transformMonth(dt[0]) + '-' + dt[1]
    return date + ' ' + dttm[1]

"""
Transform a dollar value amount from a string like $3,453.23 to XXXXX.xx
"""

def transformDollar(money):
    if money == None or len(money) == 0:
        return money
    return sub(r'[^\d.]', '', money)

"""
CS564 - AGUINA
For a given item, build the category class object given the Category key's contents. We'll be tracking the item with 
the most categories so we'll create this dat file (categories) last.
"""
def createCat(item):
    id = int(item['ItemID'])
    categoryRaw = item['Category']

    catList = []
    [catList.append(x) for x in categoryRaw if x not in catList]

    lenCat = len(catList)

    tmpObj = catObj(id, lenCat, catList)

    global categoryList

    categoryList.append(tmpObj)

    global categoryCount

    #if the catCount is < lenCat then update
    if categoryCount < lenCat:
        categoryCount = lenCat

"""
CS564 - AGUINA
For a given item, build the Item relation and build the correct dat file (items)
"""
def createItemFile(item):
    #create file for return
    f = open('items.dat', 'a', encoding="utf-8")

    id = int(item['ItemID'])
    itemName = updateString(str(item['Name']))
    price = transformDollar(item['Currently'])
    firstBid = transformDollar(item['First_Bid'])
    totalBids = int(item['Number_of_Bids'])
    startDate = transformDttm(item['Started'])
    endDate = transformDttm(item['Ends'])
    location = updateString(str(item['Location']))
    country = updateString(str(item['Country']))

    #grab the userID from the Seller obj
    sellerDat = item['Seller']

    userID = updateString(str(sellerDat['UserID']))

    desc = updateString(str(item['Description']))

    line = "{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}\n".format(
        id, itemName, price, firstBid, totalBids, startDate, endDate, location, country, userID, desc
    )

    f.write(line)

"""
CS564 - AGUINA
For a given item, build the User relation and build the correct dat file (users)
"""
def createSellerFile(item):
    #create file for insertion of UserDB
    f = open('sellers.dat', 'a', encoding="utf-8")

    #grab the seller array from the item
    sellerDat = item['Seller']

    sellerID = updateString(str(sellerDat['UserID']))
    rating = int(sellerDat['Rating'])

    itemID = item['ItemID']

    line = "{}|{}|{}\n".format(sellerID, rating, itemID)

    f.write(line)

    f.close()

"""
CS564 - AGUINA
For a given item, build the bidder relation data and create the correct dat file (bidders)
"""
def createBidderFile(item):
    #create file for insertion of BidderDB
    f = open('bidders.dat', 'a', encoding="utf-8")

    #set up the itemID for use to associate the bidders
    itemID = item['ItemID']

    #grab the bidder dict
    bids = item['Bids']

    for bid in bids:
        #get the inner bid dict
        bidDict = bid['Bid']

        #grab the bidder dict within the bid dict
        bidderInfo = bidDict['Bidder']

        #get all the information from the bidder dict
        userID = updateString(str(bidderInfo['UserID']))

        rating = bidderInfo['Rating']

        if 'Location' not in bidderInfo:
            location = "null"
        else:
            location = updateString(str(bidderInfo['Location']))

        if 'Country' not in bidderInfo:
            country = "null"
        else:
            country = updateString(str(bidderInfo['Country']))

        #finalize the last options
        timeBid = transformDttm(bidDict['Time'])

        amtBid = transformDollar(bidDict['Amount'])

        #before insertion update the bidNum
        global bidNum
        bidNum += 1

        #create the line to store
        line = '{}|{}|{}|{}|{}|{}|{}|{}\n'.format(bidNum, userID, rating, location, country, timeBid, amtBid, itemID)

        f.write(line)

    #once finished close the document
    f.close()

"""
CS 564 - AGUINA
Once we're finished with other relations, we'll come back to categories and build out the category dat file
"""
def createCatFile():
    #create the file to use
    f = open('categories.dat', 'a', encoding="utf-8")

    empty = 'null'

    global categoryList

    for categoryItem in categoryList:
        #associate the values to the class members
        id = categoryItem.itemNum

        count = categoryItem.numCat

        categories = categoryItem.category

        #create line and append initial items
        line = str(id)
        line += '|{}'.format(str(count))

        global categoryCount

        i = len(categories)

        for catStr in categories:
            catStr = updateString(str(catStr))
            line += '|{}'.format(catStr)

        if (i < categoryCount):
            difference = categoryCount - i
            emptyStr = '"' + empty + '"'
            j = 0

            while j < difference:
                line += '|{}'.format(emptyStr)
                j += 1


        #before continuing add \n to line and insert
        line += '\n'

        f.write(line)

    f.close()
"""
Parses a single json file. Currently, there's a loop that iterates over each
item in the data set. Your job is to extend this functionality to create all
the necessary SQL tables for your database.
"""
def parseJson(json_file):
    with open(json_file, 'r') as f:
        items = loads(f.read())['Items'] # creates a Python dictionary of Items for the supplied json file
        for item in items:
            #First, get the category object created for later
            createCat(item)

            #Create our biggest/first relation (ITEMS)
            createItemFile(item)

            #Create the seller relation
            createSellerFile(item)

            #if the bidders is not empty
            if item['Bids'] is not None:
                #create the bidder relation
                createBidderFile(item)

        #create our category relation
        createCatFile()

    pass

"""
Loops through each json files provided on the command line and passes each file
to the parser
"""
def main(argv):
    if len(argv) < 2:
        print >> sys.stderr, 'Usage: python aguina_parser.py <path to json files>'
        sys.exit(1)
    # loops over all .json files in the argument
    for f in argv[1:]:
        if isJson(f):
            parseJson(f)
            print("Success parsing " + f)
if __name__ == '__main__':
    main(sys.argv)
