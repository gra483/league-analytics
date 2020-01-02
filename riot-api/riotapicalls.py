import requests
import json
import os
import time       
import sqlite3
        
API_KEY = ""
API_RATE_LIMIT = 120    #a standard API_KEY refreshes every 2 minutes, or 120 seconds
P_DB = sqlite3.connect("summoners/accounts.db") #connect to our account database

def saveFile(fileName, data):
    overwrite = False
    if(os.path.exists(fileName)):
        overwrite = True
    elif(fileName.rfind('/') > 0):
        path = fileName[0:fileName.rfind('/')]
        if(not os.path.exists(path)):
            os.makedirs(path)
    with open(fileName,'w') as outfile:
        wrapperList = []
        wrapperList.append(data)
        json.dump(wrapperList,outfile)
    if(overwrite):
        print(fileName + " saved and overwritten successfully.")
    else:
        print(fileName + " saved successfully.")

def loadFile(fileName):
    """
    When saved, our output is a list of [data], so we 
    need to return an empty list to be certain it 
    worked and doesn't break.
    """
    wrapperList = [] 
    if(os.path.exists(fileName)):
        tempStr = ""
        openFile = open(fileName,'r')
        for line in openFile:
            tempStr += line
        if(len(tempStr) > 0):
            wrapperList = json.loads(tempStr)  
        else:
            print(fileName + " is an empty file.")
        openFile.close()
    else:
        print("Could not find a file named " + fileName + ".")
    return wrapperList

def getApiKey():
    """
    Either loads in the API_KEY or just returns the value if already loaded.
    """
    global API_KEY
    if(len(API_KEY) == 0):
        fileName = "apikey.txt"
        if(os.path.exists("apikey.txt")):
            openFile = open(fileName,'r')
            API_KEY = openFile.read()
        else:
            print("apikey.txt does not exist. Make one using your own apikey from https://developer.riotgames.com/")
    return "?api_key=" + API_KEY

def makeApiCall(url):
    """
    Given a url/endpoint, it will make the call, and handle any error messages
    """
    try:    #sometimes we get a handshake error. if this happens, try it again
        request = requests.get(url)
    except:
        print("Exception of request of url, trying again in 5 seconds. Failed url: " + (url))
        time.sleep(5)
        return makeApiCall(url)
    d = json.loads(request.text)
    
    if(type(d) is dict):
        if(not d.get("status") == None):    #if we have a status on our hands
            RATE_LIMIT_EXCEEDED = 429
            FORBIDDEN = 403
            NOTFOUND = 404
            UNAVAILABLE = 503
            statusCode = d["status"]["status_code"]
            if(statusCode == RATE_LIMIT_EXCEEDED):
                global API_RATE_LIMIT
                print("Rate limit exceeded, waiting for " + (str)(API_RATE_LIMIT) + " seconds.")
                time.sleep(API_RATE_LIMIT)
                request = requests.get(url)
                d = json.loads(request.text)
            elif(statusCode == FORBIDDEN):
                print("API_KEY is incorrect. Please update your apikey.txt from https://developer.riotgames.com")
            elif(statusCode == NOTFOUND):
                print("No data was found using the following url: " + url)
            elif(statusCode == UNAVAILABLE):
                print("Service unavailable, trying again in 5 seconds.")
                time.sleep(5)
                return makeApiCall(url)
            else:
                print("Unknown status code: " + (str)(statusCode))
    
    return d

def getSeasons():
    d = makeApiCall("http://static.developer.riotgames.com/docs/lol/seasons.json")
    return d
    
def getVersion():
    d = makeApiCall("https://ddragon.leagueoflegends.com/realms/na.json")
    return d["n"]

def updateChamps(version):
    f = loadFile("constants/champs.txt")
    if(len(f) > 0 and f[0]["version"] == version):
        print("champs.txt version up to date")
    else:
        d = makeApiCall("http://ddragon.leagueoflegends.com/cdn/" + version + "/data/en_US/champion.json" + getApiKey())
        saveFile("constants/champs.txt",{"data":d,"version":version})
        print("champs.txt updated")
        
def updateItems(version):
    f = loadFile("constants/items.txt")
    if(len(f) > 0 and f[0]["version"] == version):
        print("items.txt version up to date")
    else:
        d = makeApiCall("http://ddragon.leagueoflegends.com/cdn/" + version + "/data/en_US/item.json" + getApiKey())
        saveFile("constants/items.txt",{"data":d,"version":version})
        print("items.txt updated")
        
def updateSpells(version):
    f = loadFile("constants/spells.txt")
    if(len(f) > 0 and f[0]["version"] == version):
            print("spells.txt version up to date")
    else:
        d = makeApiCall("http://ddragon.leagueoflegends.com/cdn/" + version + "/data/en_US/summoner.json" + getApiKey())
        saveFile("constants/spells.txt",{"data":d,"version":version})
        print("spells.txt updated")

def updateConstants():
    versions = getVersion()
    updateChamps(versions["champion"])
    updateItems(versions["item"])
    updateSpells(versions["summoner"])
    
"""
Summoner entpoints. Get an account's information by different methods.
"""
    
def getAccountByName(name):
    d = makeApiCall("https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/" + name + getApiKey())
    return d

def getAccountByAccId(accId):
    d = makeApiCall("https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-account/" + accId + getApiKey())
    return d

def getAccountByPPUID(ppuid):
    d = makeApiCall("https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-ppuid/" + ppuid + getApiKey())
    return d

def getAccountBySummId(summId):
    d = makeApiCall("https://na1.api.riotgames.com/lol/summoner/v4/summoners/" + summId + getApiKey())
    return d

"""
Match endpoints. Do different things with matches.
"""

def getMatchList(accId,queries):
    d = makeApiCall("https://na1.api.riotgames.com/lol/match/v4/matchlists/by-account/" + accId + getApiKey() + queries)
    return d

def getMatchTimeline(matchId):
    d = makeApiCall("https://na1.api.riotgames.com/lol/match/v4/timelines/by-match/" + (str)(matchId) + getApiKey())
    return d

def getMatch(matchId):
    d = makeApiCall("https://na1.api.riotgames.com/lol/match/v4/matches/" + (str)(matchId) + getApiKey())
    return d

"""
Important methods built on top of riotapicalls that use the above endpoints to do useful things.
"""

def getMostRecentSeasonId():
    seasons = getSeasons()
    season = seasons[len(seasons)-1]
    return season["id"]

def getAllMatches(matchList):
    """
    Get all of the matches from a matchList. Defaults to the most recent season.
    """
    if(len(matchList) == 0):
        return []
    seasonId = getMostRecentSeasonId()
    matches = []
    count = 0
    for match in matchList["matches"]:
        if((int)(match["season"]) == (int)(seasonId)):
            m = getMatch(match["gameId"])
            matches.append(m)
            count += 1
    return matches

def getMatchListByName(name,queries):
    summoner = getAccountByName(name)
    return getMatchList(summoner["accountId"],queries)

def getAllRankedMatchesByAccount(account):
    matches = []
    accId = account["accountId"]
    name = account["name"]
    seasonId = getMostRecentSeasonId()
    fileName = "summoners/"+name+"S"+(str)(seasonId)+".txt"
    
    f = loadFile(fileName)
    lastGameId = 0
    if(len(f) > 0 and f[0]["seasonId"] == seasonId):
        lastGameId = f[0]["matches"][0]["gameId"]
        print((str)(len(f[0]["matches"])) + " ranked matches already downloaded.")
    
    prevSize = 0
    queries = "&queue=420"
    matchList = getMatchList(accId,queries)
    totalGames = matchList["totalGames"]    #need to find the real amount of total games (accounting for season changes)
    
    print((str)(totalGames) + " total ranked games possible to download.")
    for num in range(0,(int)(totalGames/100)): #need the +1 because of integer division (truncation)
        matchList = checkGameIds(matchList,lastGameId)
        matches.extend(getAllMatches(matchList))
        if(not len(matches) == 100 + prevSize): #if we didn't add 100 matches, it's because we reached the end of the season, a duplicate match, or the last set of games
            break
        else:
            prevSize = len(matches)
            
        queries = "&queue=420&beginIndex=" + (str)((num+1)*100)
        matchList = getMatchList(accId,queries)
        
    matchesDownloaded = len(matches)
    if(len(matches) == 0):
        print("No ranked matches downloaded.")
        return f[0]["matches"]
    else:
        print((str)(matchesDownloaded) + " ranked matches actually downloaded.")
        if(len(f) > 0 and f[0]["seasonId"] == seasonId):
            matches.extend(f[0]["matches"])    #add back the matches we loaded in at the beginning
        
    saveFile(fileName,{"matches":matches,"seasonId":seasonId})
    return matches

def checkGameIds(matchList,lastGameId):
    newMatchList = {"matches":[]}
    for match in matchList["matches"]:
        if(match["gameId"] == lastGameId):  #found the last match that is the same, we don't need to keep going, so we're done
            break
        else:
            newMatchList["matches"].append(match)
    return newMatchList

def getAccountsByNames(names):
    accounts = []
    for name in names:
        accounts.append(getAccountByName(name))
    return accounts