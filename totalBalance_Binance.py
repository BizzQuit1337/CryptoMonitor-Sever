import config_ocar
import pandas as pd
import shared_Functions as sf
import requests
from urllib.parse import urlencode
import time
import hmac
import hashlib
import numpy as np

def binance_send_signed_request(BASE_URL, http_method, url_path, chiave_binance, segreta_binance, payload={}):
    query_string = urlencode(payload, True)
    if query_string:
        query_string = "{}&timestamp={}".format(query_string, binance_get_timestamp())
    else:
        query_string = "timestamp={}".format(binance_get_timestamp())

    url = (
        BASE_URL + url_path + "?" + query_string + "&signature=" + binance_hashing(query_string, segreta_binance)
    )
    params = {"url": url, "params": {}}
    response = binance_dispatch_request(http_method, chiave_binance)(**params)
    return response.json()

def binance_dispatch_request(http_method, chiave_binance=''):
    session = requests.Session()
    session.headers.update(
        {"Content-Type": "application/json;charset=utf-8", "X-MBX-APIKEY": chiave_binance}
    )
    return {
        "GET": session.get,
        "DELETE": session.delete,
        "PUT": session.put,
        "POST": session.post,
    }.get(http_method, "GET")

def get_binance_current_price(base, quote):
    BASE_URL = "https://api.binance.com"
    pr = binance_send_public_request(BASE_URL, '/api/v3/ticker/price', payload={'symbol':base+quote})['price']
    return float(pr)

def binance_get_timestamp():
    return int(time.time() * 1000)

def binance_hashing(query_string, segreta_binance):
    return hmac.new(
        segreta_binance.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256
    ).hexdigest()

def binance_send_public_request(BASE_URL, url_path, payload={}):
    query_string = urlencode(payload, True)
    url = BASE_URL + url_path
    if query_string:
        url = url + "?" + query_string
    response = binance_dispatch_request("GET")(url=url)
    return response.json()

def binance_future_wallet_balance(api_key, api_secret, exchange):
    futures_wallet = binance_send_signed_request("https://fapi.binance.com", 'GET', '/fapi/v2/balance', api_key, api_secret, payload={})
    total_balance = 0
    assets = []

    

    for i in range(0, len(futures_wallet)):
        if futures_wallet[i]['balance'] != '0.00000000':
            try:
                coin_price = binance_send_public_request("https://api.binance.com", '/api/v3/ticker/price', payload={'symbol': (futures_wallet[i]['asset']+'USDT')})
                total = (float(futures_wallet[i]['balance']) + float(futures_wallet[i]['crossUnPnl']))*float(coin_price['price'])
                total_balance += total
                if round(total,2) != 0:
                    asset={
                        'Coin':futures_wallet[i]['asset'],
                        'Contract':futures_wallet[i]['asset'],
                        'QTY':round((float(futures_wallet[i]['balance']) + float(futures_wallet[i]['crossUnPnl'])), 6),
                        'USDValue':round(total,2),
                        'Exchange':exchange, 
                        'Account':'USD-M'
                        }
                    assets.append(asset)
            except:
                total = float(futures_wallet[i]['balance']) + float(futures_wallet[i]['crossUnPnl'])
                total_balance += total
                if round(total,2) != 0:
                    asset={
                        'Coin':futures_wallet[i]['asset'], 
                        'Contract':futures_wallet[i]['asset'],
                        'QTY':round(total, 6), 
                        'USDValue':round(total,2),
                        'Exchange':exchange, 
                        'Account':'USD-M'}
                    assets.append(asset)

    return [total_balance, 'USDT-M', assets]

def binance_m_wallet_balance(api_key, api_secret, exchange):
    m_wallet = binance_send_signed_request('https://dapi.binance.com', "GET", '/dapi/v1/balance', api_key, api_secret, payload={})
    total_balance = 0
    assets = []

    for i in range(0, len(m_wallet)):
        if  float(m_wallet[i]['balance']) != 0:
            try:
                coin_price = binance_send_public_request("https://api.binance.com", '/api/v3/ticker/price', payload={'symbol': (m_wallet[i]['asset']+'USDT')})
                total = (float(m_wallet[i]['balance'])+ float(m_wallet[i]['crossUnPnl']))*float(coin_price['price'])
                total_balance += total
                if round(total,2) != 0:
                    asset={
                        'Coin':m_wallet[i]['asset'], 
                        'Contract':m_wallet[i]['asset'],
                        'QTY':round((float(m_wallet[i]['balance'])+ float(m_wallet[i]['crossUnPnl'])),6), 
                        'USDValue':round(total,2),
                        'Exchange':exchange, 
                        'Account':'Coin-M'}
                    assets.append(asset)
            except:
                total = float(m_wallet[i]['balance']) + float(m_wallet[i]['crossUnPnl'])
                total_balance += total
                if round(total,2) != 0:
                    asset={
                        'Coin':m_wallet[i]['asset'], 
                        'Contract':m_wallet[i]['asset'],
                        'QTY':round(total,6), 
                        'USDValue':round(total,2),
                        'Exchange':exchange, 
                        'Account':'Coin-M'}
                    assets.append(asset)

    return [total_balance, 'Coin-M', assets]

def binance_spot_wallet_balance(api_key, api_secret, exchange):
    spot_wallet = binance_send_signed_request('https://api.binance.com', "GET", "/sapi/v1/capital/config/getall", api_key, api_secret, payload={'type': 'SPOT'})
    total_balance = 0
    assets = []

    for i in range(0, len(spot_wallet)):
        if spot_wallet[i]['free'] != '0':#'USDT':
            try:
                total = float(spot_wallet[i]['free'])+float(spot_wallet[i]['locked'])
                coin_price = binance_send_public_request("https://api.binance.com", '/api/v3/ticker/price', payload={'symbol': (spot_wallet[i]['coin']+'USDT')})
                total_usd = float(coin_price['price']) * total
                total_balance += total_usd
                if round(total_usd,2) != 0:
                    asset={
                        'Coin':spot_wallet[i]['coin'],
                        'Contract':spot_wallet[i]['coin'], 
                        'QTY':round(total,6), 
                        'USDValue':round(total_usd,2),
                        'Exchange':exchange, 
                        'Account':'SPOT'}
                    assets.append(asset)       
            except:
                try:
                    total = float(spot_wallet[i]['free'])+float(spot_wallet[i]['locked'])
                    coin_price = binance_send_public_request("https://api.binance.com", '/api/v3/ticker/price', payload={'symbol': (spot_wallet[i]['coin']+'BUSD')})
                    total_usd = float(coin_price['price']) * total
                    total_balance += total_usd
                    if round(total_usd,2) != 0:
                        asset={
                            'Coin':spot_wallet[i]['coin'], 
                            'Contract':spot_wallet[i]['coin'], 
                            'QTY':round(total,6), 
                            'USDValue':round(total_usd,2),
                            'Exchange':exchange, 
                            'Account':'SPOT'}
                        assets.append(asset)
                except:
                    total = float(spot_wallet[i]['free'])+float(spot_wallet[i]['locked'])
                    total_balance += total
                    if round(total,2) != 0:
                        asset={
                            'Coin':spot_wallet[i]['coin'], 
                            'Contract':spot_wallet[i]['coin'],
                            'QTY':round(total,6), 
                            'USDValue':round(total,2),
                            'Exchange':exchange, 
                            'Account':'SPOT'}
                        assets.append(asset)
                    
    return [total_balance, 'SPOT', assets]

def binance_margin_wallet_balance(api_key, api_secret, exchange):
        margin_wallet = binance_send_signed_request('https://api.binance.com', "GET", "/sapi/v1/margin/account", api_key, api_secret, payload={})
        total_balance = 0
        assets = []

        isolated_margin = binance_send_signed_request("https://api.binance.com", 'GET', '/sapi/v1/margin/isolated/account', api_key, api_secret, payload={})

        for i in isolated_margin['assets']:
            if i['baseAsset']['borrowed'] != 0:
                try:
                    coin_price = binance_send_public_request("https://api.binance.com", '/api/v3/ticker/price', payload={'symbol': (i['baseAsset']['asset']+'USDT')})
                    total = (float(i['baseAsset']['netAsset'])*float(coin_price['price']))
                    asset={
                            'Coin':i['baseAsset']['asset'], 
                            'Contract':i['baseAsset']['asset'],
                            'QTY':i['baseAsset']['netAsset'], 
                            'USDValue':total,
                            'Exchange':exchange, 
                            'Account':'Margin-Isolated'}
                    if float(i['baseAsset']['netAsset']) != 0:
                        assets.append(asset)
                        total_balance += total
                except:
                    asset={
                            'Coin':i['baseAsset']['asset'], 
                            'Contract':i['baseAsset']['asset'],
                            'QTY':i['baseAsset']['netAsset'], 
                            'USDValue':i['baseAsset']['netAsset'],
                            'Exchange':exchange, 
                            'Account':'Margin-Isolated'}
                    if float(i['baseAsset']['netAsset']) != 0:
                        assets.append(asset)
                        total_balance += float(i['baseAsset']['netAsset'])

        for i in isolated_margin['assets']:
            if i['quoteAsset']['netAsset'] != 0:
                try:
                    coin_price = binance_send_public_request("https://api.binance.com", '/api/v3/ticker/price', payload={'symbol': (i['quoteAsset']['asset']+'USDT')})
                    total = (float(i['baseAsset']['netAsset'])*float(coin_price['price']))
                    asset={
                            'Coin':i['quoteAsset']['asset'], 
                            'Contract':i['quoteAsset']['asset'],
                            'QTY':i['quoteAsset']['netAsset'], 
                            'USDValue':total,
                            'Exchange':exchange, 
                            'Account':'Margin-Isolated-quote'}
                    if float(i['quoteAsset']['netAsset']) != 0:
                        assets.append(asset)
                        total_balance += total
                except:
                    asset={
                            'Coin':i['quoteAsset']['asset'], 
                            'Contract':i['quoteAsset']['asset'],
                            'QTY':i['quoteAsset']['netAsset'], 
                            'USDValue':i['quoteAsset']['netAsset'],
                            'Exchange':exchange, 
                            'Account':'Margin-Isolated-quote'}
                    if float(i['baseAsset']['netAsset']) != 0:
                        assets.append(asset)
                        total_balance += float(i['quoteAsset']['netAsset'])

        for i in range(0, len(margin_wallet['userAssets'])):
            if margin_wallet['userAssets'][i]['free'] != '0':
                try:
                    coin_price = binance_send_public_request("https://api.binance.com", '/api/v3/ticker/price', payload={'symbol': (margin_wallet['userAssets'][i]['asset']+'USDT')})
                    total = (float(margin_wallet['userAssets'][i]['free'])+float(margin_wallet['userAssets'][i]['locked']))*float(coin_price['price'])
                    total_balance += total
                    if round(total,2) != 0:
                        asset={
                            'Coin':margin_wallet['userAssets'][i]['asset'], 
                            'Contract':margin_wallet['userAssets'][i]['asset'],
                            'QTY':round((float(margin_wallet['userAssets'][i]['free'])+float(margin_wallet['userAssets'][i]['locked'])),6), 
                            'USDValue':round(total,2),
                            'Exchange':exchange, 
                            'Account':'Margin'}
                        assets.append(asset)
                except:
                    total = float(margin_wallet['userAssets'][i]['free'])+float(margin_wallet['userAssets'][i]['locked'])
                    total_balance += total
                    if round(total,2) != 0:
                        asset={
                            'Coin':['userAssets'][i]['asset'], 
                            'Contract':['userAssets'][i]['asset'],
                            'QTY':round(total,6), 'USDValue':round(total,2),
                            'Exchange':exchange, 
                            'Account':'Margin'}
                        assets.append(asset)

        return [total_balance, 'Margin', assets]

def binance_earn_wallet_balance(api_key, api_secret, exchange):
    total_balance = 0
    staking = binance_send_signed_request('https://api.binance.com', "GET", "/sapi/v1/staking/position",api_key, api_secret, payload={'product': 'STAKING'})
    saving = binance_send_signed_request('https://api.binance.com', "GET", "/sapi/v1/lending/union/account", api_key, api_secret)
    assets = []

    for i in range(0, len(staking)):
        if staking[i]['amount'] != '0':
            coin_price = binance_send_public_request("https://api.binance.com", '/api/v3/ticker/price', payload={'symbol': (staking[i]['asset']+'USDT')})
            total = float(staking[i]['amount'])*float(coin_price['price'])
            total_balance += total
            if round(float(staking[i]['amount']),2) != 0:
                asset={
                    'Coin':staking[i]['asset'], 
                    'Contract':staking[i]['asset'],
                    'QTY':round(float(staking[i]['amount']),6), 
                    'USDValue':round(total,2),
                    'Exchange':exchange, 
                    'Account':'Earn'}
                assets.append(asset)

    for j in range(0, len(saving['positionAmountVos'])):
        if saving['positionAmountVos'][j]['amountInUSDT'] != '0':
            total = saving['positionAmountVos'][j]['amountInUSDT']
            total_balance += total
            if round(total,2) != 0:
                asset={
                    'Coin':saving['positionAmountVos'][j]['asset'], 
                    'Contract':saving['positionAmountVos'][j]['asset'],
                    'QTY':round(total,6), 
                    'USDValue':round(total,2),
                    'Exchange':exchange, 
                    'Account':'Earn'}
                assets.append(asset)
        else:
            total_balance += 0

    return [total_balance, 'Earn', assets]

def total_binance_balance(api_key, api_secret, exchange, breakdown):
    all_asset = []
    coin_assets = []
    total_balance = 0

    b = {'Exchange':exchange, 'USDT-M':0, 'SPOT':0, 'Margin':0, 'Earn':0, 'Coin-M':0, 'Total':0}

    for i in [binance_future_wallet_balance(api_key, api_secret, exchange), binance_spot_wallet_balance(api_key, api_secret, exchange), binance_margin_wallet_balance(api_key, api_secret, exchange), binance_earn_wallet_balance(api_key, api_secret, exchange), binance_m_wallet_balance(api_key, api_secret, exchange) ]:
        asset = {'Account':i[1],'USDValue':i[0]}
        all_asset.append(asset)
        total_balance += i[0]
        coin_assets.append(i[2])
        for j in b:
            if i[1] == j:
                b[j] = i[0]

    b['Total'] = total_balance            
    newList = [b]
    if breakdown:
        sf.displayDataFrame(newList, False, True)
        print('Total',f"{total_balance:,.2f}")
    binance = {'total':total_balance, 'coins':coin_assets, 'breakdown':newList}
    
    return binance
def binanceLeaverage(api_key, api_secret, exchange):
    leverageValue = []

    for i in [binance_future_wallet_balance(api_key, api_secret, exchange), binance_m_wallet_balance(api_key, api_secret, exchange)]:
        lever = {'USDValue':i[0], 'Account':i[1], 'exchange':'Binance'}
        leverageValue.append(lever)
        
    return leverageValue



def get_usdt_pos(api_key, api_secret, exchange):
    usdtPos = binance_send_signed_request("https://fapi.binance.com", 'GET', '/fapi/v2/positionRisk', api_key, api_secret, payload={})

    assets = []

    posAbsolute = 0
    posUSDValue = 0

    for i in usdtPos:
        if float(i['positionAmt']) != 0.0:
            position = float(i['positionAmt'])
            USD_Value = position*float(i['markPrice'])
            try:
                if i['pos'][:-(len(i['pos'])-1)] == '-':
                    liq_risk = (float(i['liquidationPrice'])-float(i['markPrice']))/float(i['markPrice'])
                else:
                    liq_risk = (float(i['markPrice'])-float(i['liquidationPrice']))/float(i['markPrice'])
                if i['symbol'][:4] == '1000':  
                    asset = {
                            'Coin':i['symbol'][4:-4],
                            'Contract':i['symbol'],
                            'QTY':round(position*1000,6),
                            'USDValue':round(USD_Value,2),
                            'Exchange':exchange,
                            'Account':'USDT-M',
                            'Leverage':i['leverage'],
                            'MarkPrice':round(float(i['markPrice']),2),
                            'LiqPrice':round(float(i['liquidationPrice']),2),
                            'LiqRisk':liq_risk
                        }
                    assets.append(asset)

                    posAbsolute += abs(USD_Value)
                    posUSDValue += USD_Value
                else:
                    asset = {
                            'Coin':i['symbol'].split('_')[0][:-4],
                            'Contract':i['symbol'],
                            'QTY':round(position,6),
                            'USDValue':round(USD_Value,2),
                            'Exchange':exchange,
                            'Account':'USDT-M',
                            'Leverage':i['leverage'],
                            'MarkPrice':round(float(i['markPrice']),2),
                            'LiqPrice':round(float(i['liquidationPrice']),2),
                            'LiqRisk':round(float(i['liquidationPrice']),2)
                        }
                    assets.append(asset)

                    posAbsolute += abs(USD_Value)
                    posUSDValue += USD_Value
            except:
                try:
                    liq = round(float(i['liquidationPrice']),2)
                    liqRisk = (liq-float(i['markPrice']))/float(i['markPrice'])
                except:
                    liq = 'Null'
                if i['symbol'][:4] == '1000':  
                    asset = {
                            'Coin':i['symbol'][4:-4],
                            'Contract':i['symbol'],
                            'QTY':round(position*1000,6),
                            'USDValue':round(USD_Value,2),
                            'Exchange':exchange,
                            'Account':'USDT-M',
                            'Leverage':i['leverage'],
                            'MarkPrice':round(float(i['markPrice']),2),
                            'LiqPrice':liq,
                            'LiqRisk':liq
                        }
                    assets.append(asset)

                    posAbsolute += abs(USD_Value)
                    posUSDValue += USD_Value
                else:
                    asset = {
                            'Coin':i['symbol'].split('_')[0][:-4],
                            'Contract':i['symbol'],
                            'QTY':round(position,6),
                            'USDValue':round(USD_Value,2),
                            'Exchange':exchange,
                            'Account':'USDT-M',
                            'Leverage':i['leverage'],
                            'MarkPrice':round(float(i['markPrice']),2),
                            'LiqPrice':liq,
                            'LiqRisk':liqRisk
                        }
                    assets.append(asset)

                    posAbsolute += abs(USD_Value)
                    posUSDValue += USD_Value

    binance = {'assets':assets, 'posValue':[posAbsolute, posUSDValue, 'USDT-M']}

    return binance

def get_coinM_pos(api_key, api_secret, exchange):
    coinMPos = binance_send_signed_request("https://dapi.binance.com", 'GET', '/dapi/v1/positionRisk', api_key, api_secret, payload={})

    assets = []

    posAbsolute = 0
    posUSDValue = 0

    for i in coinMPos:
        if float(i['positionAmt']) != 0:
            position = float(i['notionalValue'])
            USD_Value = position*float(i['markPrice'])
            try:
                if i['pos'][:-(len(i['pos'])-1)] == '-':
                    asset = {
                            'Coin':i['symbol'].split('_')[0][:-3],
                            'Contract':i['symbol'],
                            'QTY':round(position,6),
                            'USDValue':round(USD_Value,2),
                            'Exchange':exchange,
                            'Account':'COIN-M',
                            'Leverage':i['leverage'],
                            'MarkPrice':round(float(i['markPrice']),2),
                            'LiqPrice':round(float(i['liquidationPrice']),2),
                            'LiqRisk':(float(i['liquidationPrice'])-float(i['markPrice']))/float(i['markPrice'])
                        }
                else:
                    asset = {
                            'Coin':i['symbol'].split('_')[0][:-3],
                            'Contract':i['symbol'],
                            'QTY':round(position,6),
                            'USDValue':round(USD_Value,2),
                            'Exchange':exchange,
                            'Account':'COIN-M',
                            'Leverage':i['leverage'],
                            'MarkPrice':round(float(i['markPrice']),2),
                            'LiqPrice':round(float(i['liquidationPrice']),2),
                            'LiqRisk':(float(i['markPrice'])-float(i['liquidationPrice']))/float(i['markPrice'])
                        }
                assets.append(asset)

                posAbsolute += abs(USD_Value)
                posUSDValue += USD_Value
            except:
                try:
                    liq = round(float(i['liquidationPrice']),2)
                    liqRisk = (liq-float(i['markPrice']))/float(i['markPrice'])
                except:
                    liq = 'Null'
                asset = {
                        'Coin':i['symbol'].split('_')[0][:-3],
                        'Contract':i['symbol'],
                        'QTY':round(position,6),
                        'USDValue':round(USD_Value,2),
                        'Exchange':exchange,
                        'Account':'COIN-M',
                        'Leverage':i['leverage'],
                        'MarkPrice':round(float(i['markPrice']),2),
                        'LiqPrice':liq,
                        'LiqRisk':liqRisk
                    }
                assets.append(asset)

                posAbsolute += abs(USD_Value)
                posUSDValue += USD_Value

    binance = {'assets':assets, 'posValue':[posAbsolute, posUSDValue, 'Coin-M']}

    return binance

def all_positions(api_key, api_secret, exchange):
    assets = []

    for i in [get_coinM_pos(api_key, api_secret, exchange), get_usdt_pos(api_key, api_secret, exchange)]:
        assets.append(i['assets'])

    return assets

def leverValues(api_key, api_secret, exchange):
    leverValue = []

    for i in [get_coinM_pos(api_key, api_secret, exchange), get_usdt_pos(api_key, api_secret, exchange)]:
        lever = {'absolute':i['posValue'][0], 'USDValue':i['posValue'][1], 'Account':i['posValue'][2], 'exchange':'Binance'}
        leverValue.append(lever)

    return leverValue
