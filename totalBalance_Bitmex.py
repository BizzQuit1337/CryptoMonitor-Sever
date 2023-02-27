import config_ocar
import pandas as pd
import shared_Functions as sf
import hmac, hashlib
from datetime import datetime, timedelta
import requests

def signature(endpoint, expires, api_secret):
    query_string = 'GET' + endpoint + str(expires)
    sign = hmac.new(
            api_secret.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256
        ).hexdigest()
    return sign


def signed_request(endpoint,api_key, api_secret):
    base_url = 'https://www.bitmex.com'
    verb = 'GET'
    now = datetime.now()+timedelta(minutes=1)
    expires = int(datetime.timestamp(now))
    s = signature(endpoint, expires, api_secret)
    headers = {'api-expires':str(expires),
         'api-key':api_key,
         'api-signature':s}
    url = base_url + endpoint
    response = requests.get(url, headers=headers)
    return response.json()

def get_current_price(symbol):
    payload={'symbol':symbol, 'reverse':True}
    response = requests.get('https://www.bitmex.com/api/v1/trade', params=payload)
    r = response.json()
    return r[0]['price']


def get_bitmex_wallet(api_key, api_secret):
    endpoint = '/api/v1/user/margin?currency=all'
    r = signed_request(endpoint,api_key, api_secret)
    return r
    

exchange = 'Bitmex'

def bitmex_wallet(api_key, api_secret, breakdown):
    wallet = get_bitmex_wallet(api_key, api_secret)
    total_balance = 0
    total_unrealisedPnL = 0
    assets = []
    coin_assets = []

    for i in range(0, len(wallet)):
        if wallet[i] != 0:
            if wallet[i]['currency'].upper() == 'XBT':
                coin_price = get_current_price(wallet[i]['currency'].upper())
                satoshi_convert = float(wallet[i]['walletBalance'])*0.00000001
                total = satoshi_convert*coin_price
                total_balance += total
                if round(total,2) != 0:
                    asset={
                        'Coin':'BTC', 
                        'Contract':'BTC', 
                        'QTY':round(satoshi_convert,6), 
                        'USDValue':round(total,2),
                        'Exchange':exchange, 
                        'Account':'SPOT'}
                    coin_assets.append(asset)
                #print(wallet[i]['unrealisedPnl'])
            elif wallet[i]['currency'] == 'BMEx':
                coin_price = get_current_price(wallet[i]['currency'].upper())
                satoshi_convert = float(wallet[i]['walletBalance'])*0.000001
                total = satoshi_convert*coin_price
                total_balance += satoshi_convert
                total_unrealisedPnL += wallet[i]['unrealisedPnl']
                if round(total,2) != 0:
                    asset={
                        'Coin':'BMEX', 
                        'Contract':'BMEX',
                        'QTY':round(satoshi_convert,6), 
                        'USDValue':round(total,2),
                        'Exchange':exchange, 
                        'Account':'SPOT'}
                    coin_assets.append(asset)

    asset = {'Account':'SPOT', 'USDValue':total_balance}
    pnl = {'Account':'UnrealPnL', 'USDValue': total_unrealisedPnL}
    b = {'Exchange':exchange, 'USDT-M':0, 'SPOT':total_balance, 'Margin':0, 'Earn':0, 'Coin-M':0, 'Total':0}
    assets.append(asset)
    assets.append(pnl)
    #print(pd.DataFrame(coin_assets))
    #sf.saveExcel('bitmex.xlsx', coin_assets)
    #print(pd.DataFrame(assets), '\nTotal Bitmex balance: ', total_balance)

    b['Total'] = total_balance
    newList = [b]
    if breakdown:
        
        sf.displayDataFrame(newList, True, False)
        print('Total',f"{total_balance:,.2f}")
    bitmex = {'total':total_balance, 'coins':coin_assets, 'breakdown':newList}
    
     
    return bitmex

def bitmexLeaverage(api_key, api_secret):
    leverageValue = []

    for i in [bitmex_wallet(api_key, api_secret, False)]:
        lever = {'USDValue':i['total'], 'Account':'USDT', 'exchange':'Bitmex'}
        leverageValue.append(lever)

    return leverageValue


def get_usdt_pos(api_key, api_secret, exchange):
    usdtPos = signed_request('/api/v1/position', api_key, api_secret)

    assets = []

    posAbsolute = 0
    posUSDValue = 0

    for i in usdtPos:
        if float(i['homeNotional']) != 0:
            position = float(i['homeNotional'])
            USD_Value = position*float(i['markPrice'])
            try:
                asset = {
                        'Coin':i['underlying'],
                        'Contract':i['symbol'],
                        'QTY':round(position,6),
                        'USDValue':round(USD_Value,2),
                        'Exchange':exchange,
                        'Account':i['currency'],
                        'Leverage':i['leverage'],
                        'MarkPrice':round(float(i['markPrice']),2),
                        'LiqPrice':round(float(i['liquidationPrice']),2),
                        'LiqRisk':(float(i['liquidationPrice'])-float(i['markPrice']))/float(i['markPrice'])
                    }
                assets.append(asset)

                posAbsolute += abs(USD_Value)
                posUSDValue += USD_Value
            except:
                asset = {
                        'Coin':i['underlying'],
                        'Contract':i['symbol'],
                        'QTY':round(position,6),
                        'USDValue':round(USD_Value,2),
                        'Exchange':exchange,
                        'Account':i['currency'],
                        'Leverage':i['leverage'],
                        'MarkPrice':round(float(i['markPrice']),2),
                        'LiqPrice':'Null',
                        'LiqRisk':'Null'
                    }
                assets.append(asset)

                posAbsolute += abs(USD_Value)
                posUSDValue += USD_Value

    bitmex = {'assets':assets, 'posValue':[posAbsolute, posUSDValue, 'USDT']}

    return bitmex

def leverValues(api_key, api_secret, exchange):
    leverValue = []

    for i in [get_usdt_pos(api_key, api_secret,exchange)]:
        lever = {'absolute':i['posValue'][0], 'USDValue':i['posValue'][1], 'Account':i['posValue'][2], 'exchange':'Bitmex'}
        leverValue.append(lever)

    return leverValue
