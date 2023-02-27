### This is were all the shared and common function will be stored 
### This will also hold the function that will call and unlock the files for the keys 
import os, time
import pandas as pd
from tabulate import tabulate

#This function will take a file path and the name of an exchange and will return both the api_key and the secret_key in hat order
def getKeySecret(filePath, exchange): 
    keySecret = []                                              #List to store keys
    with open(filePath, 'r') as f:                              
        for line in f:
            if line.split(' ')[0] == exchange:                  #Seperating the  required key from others
                keySecret.append(line.split(' ')[2][:-1])       #Pushing the wanted keys into List keySecret
    return keySecret                                            #Returns a list containing the the key position 0 and secret position 1
##Obselte function

#This function will save data to excel
def saveExcel(fileName, dict):
    try:
        df = pd.DataFrame.from_dict(dict)                           #Converts the dictionary to a pandas data frame
        df.to_excel(fileName)   
        print('#######################\n# file has been saved #\n#' + fileName + '#\n#######################')                                    #Pushes the pandas data frame into an excel worksheet
    except:
        df = pd.DataFrame(dict)                                     #Converts the list to a pandas data frame
        df.to_excel(fileName)  
        print('#######################\n# file has been saved #\n#######################')     
##To be used when needed not all the time


def displayDataFrame(List, printState, returnList):
    positions = []
    errorCount = 0
    try:
        for i in List:
            if str(type(i)) == "<class 'dict'>":
                positions.append(i)
            else:
                for j in i:
                    if str(type(j)) == "<class 'dict'>":
                        positions.append(j)
                    else:
                        for k in j:
                            if str(type(k)) == "<class 'dict'>":
                                positions.append(k)
                            else:
                                errorCount += 1
    except:
        for i in List:
            if str(type(i)) == "<class 'float'>":
                positions.append(i)
            else:
                for j in i:
                    if str(type(j)) == "<class 'float'>":
                        positions.append(j)
                    else:
                        for k in j:
                            if str(type(k)) == "<class 'float'>":
                                positions.append(k)
                            else:
                                errorCount += 1
    
    df = pd.DataFrame(positions)

    if printState:
        pd.options.display.float_format = '{:,.5f}'.format
        #display(df)
        print(df)
    if returnList:
        return positions

def singleDict(list):
    newList = {'Exchange':''}
    for i in list:
        for j in i.items():
            if j[0] != 'Exchange':
                newList.update({j[0]:j[1]})
            else:
                newList['Exchange'] = j[1] 
    return [newList]

#List = [{'Exchange': 'Binance', 'USDT-M': 11924.88948775}, {'Exchange': 'Binance', 'SPOT': 52106.25838933826}, {'Exchange': 'Binance', 'Margin': 0.76176}, {'Exchange': 'Binance', 'Earn': 1486.96894324}, {'Exchange': 'Binance', 'Coin-M': 1486.05643450145}]
#singleDict(List)

def timer(start, msg, stop):
    end = time.time()
    print('###\n', msg, '. overall time: ', (end-start), '\n###')
    if stop:
        return end

def tableFormatFloat(valueList):
    for i in valueList:
        for j in i:
            if str(type(i[j])) == "<class 'float'>":
                i[j] = '{:,.2f}'.format(i[j])
    return valueList

def condense(list):
    newList = []
    for i in list:
        for j in i:
            newList.append(j)
    return newList
