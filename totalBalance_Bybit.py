import pandas as pd
import shared_Functions as sf
import config_ocar
import requests, hmac, hashlib, time
from urllib.parse import quote_plus

def bybit_signature(segreta_bybit, params):
    #timestamp = int(time.time() * 10 ** 3)
    param_str = ''
    for key in sorted(params.keys()):
        v = params[key]
        if isinstance(params[key], bool):
            if params[key]:
                v = 'true'
            else :
                v = 'false'
        param_str += key + '=' + v + '&'
    param_str = param_str[:-1]
    hash = hmac.new(segreta_bybit.encode("utf-8"), param_str.encode("utf-8"), hashlib.sha256)
    signature = hash.hexdigest()
    sign_real = {
        "sign": signature
    }
    param_str = quote_plus(param_str, safe="=&")
    full_param_str = f"{param_str}&sign={sign_real['sign']}"
    return full_param_str

def get_bybit_current_price(symbol):
    BASE_URL = 'https://api.bybit.com'
    enpoint = '/v2/public/tickers'
    params = {'symbol':symbol}
    url = BASE_URL + enpoint
    response = requests.get(url, params=params)
    r = response.json()
    return float(r['result'][0]['last_price'])

def signed_request(chiave_bybit, segreta_bybit, endpoint):
    BASE_URL = 'https://api.bybit.com'
    enpoint = endpoint
    timestamp = int(time.time() * 10 ** 3)
    params={'api_key':chiave_bybit,
                'timestamp': str(timestamp),
                'recv_window': '5000'}
    full_param_str = bybit_signature(segreta_bybit, params)
    url = BASE_URL + enpoint + '?' + full_param_str
    response = requests.get(url)
    r = response.json()
    return r

def bybit_futures_wallet(api_key, api_secret, exchange):
    futures_wallet = signed_request(api_key, api_secret, '/v2/private/wallet/balance')
    total_balance = 0
    assets = []

    #sf.saveExcel('bybit_fut.xlsx', futures_wallet['result'])

    for i in futures_wallet['result']:
        if futures_wallet['result'][i]['equity'] != 0:
            coin_price = 1
            total = float(futures_wallet['result'][i]['equity'])*float(coin_price)
            total_balance += futures_wallet['result'][i]['equity']
            if round(total,2) != 0:
                coin_asset = {
                    'Coin':i, 
                    'Contract':i,
                    'QTY':round(float(futures_wallet['result'][i]['equity']),6), 
                    'USDValue':round(total,2),
                    'Exchange':exchange, 
                    'Account':'USDT-M'}
                assets.append(coin_asset)

    return [total_balance, 'USDT-M', assets]

def bybit_spot_wallet(api_key, api_secret, exchange):
    spot_wallet = signed_request(api_key, api_secret, '/spot/v3/private/account')
    total_balance =0 
    assets = []

    for i in range(0, len(spot_wallet['result']['balances'])):
        try:
            coin_price = get_bybit_current_price(symbol=(spot_wallet['result']['balances'][i]['coin']+'USDT'))
            total = float(spot_wallet['result']['balances'][i]['total'])*float(coin_price)
            total_balance += total
            if round(total,2) != 0:
                coin_asset = {
                    'Coin':spot_wallet['result']['balances'][i]['coin'], 
                    'Contract':spot_wallet['result']['balances'][i]['coin'],
                    'QTY':round(float(spot_wallet['result']['balances'][i]['total']),6), 
                    'USDValue':round(total,2),
                    'Exchange':exchange, 
                    'Account':'SPOT'}
                assets.append(coin_asset)
        except:
            total_balance += float(spot_wallet['result']['balances'][i]['total'])
            if round(float(spot_wallet['result']['balances'][i]['total']),2) != 0:
                coin_asset = {
                    'Coin':spot_wallet['result']['balances'][i]['coin'], 
                    'Contract':spot_wallet['result']['balances'][i]['coin'],
                    'QTY':round(float(spot_wallet['result']['balances'][i]['total']),6), 
                    'USDValue':round(float(spot_wallet['result']['balances'][i]['total']),2),
                    'Exchange':exchange, 
                    'Account':'SPOT'}
                assets.append(coin_asset)

    
    return [total_balance, 'SPOT', assets]

def total_bybit_balance(api_key, api_secret, exchange, breakdown):
    total_balance = 0
    assets = []
    coin_assets = []
    b = {'Exchange':exchange, 'USDT-M':0, 'SPOT':0, 'Margin':0, 'Earn':0, 'Coin-M':0, 'Total':0}
    for i in [bybit_spot_wallet(api_key, api_secret, exchange), bybit_futures_wallet(api_key, api_secret, exchange)]:
        assets.append(i)
        total_balance += i[0]
        coin_assets.append(i[2])
        for j in b:
            if i[1] == j:
                b[j] = i[0]

    
    #print(coin_assets)
    #print(pd.DataFrame(assets), '\nTotal Bybit balance: ', total_balance)
    b['Total'] = total_balance
    newList = [b]
    if breakdown:
        
        sf.displayDataFrame(newList, True, False)
        print('Total',f"{total_balance:,.2f}")
    bybit = {'total':total_balance, 'coins':coin_assets, 'breakdown':newList}


    return bybit
def bybitLeaverage(api_key, api_secret, exchange):
    leverageValue = []

    for i in [bybit_futures_wallet(api_key, api_secret, exchange)]:
        lever = {'USDValue':i[0], 'Account':'USDT-M', 'exchange':'Bybit'}
        leverageValue.append(lever)

    return leverageValue



def get_usdt_pos(api_key, api_secret, exchange):
    usdtPos = signed_request(api_key, api_secret, '/private/linear/position/list')

    assets = []

    posAbsolute = 0
    posUSDValue = 0

    for i in usdtPos['result']:
        if i['data']['size'] != 0:
            currentPrice = get_bybit_current_price(i['data']['symbol'])
            position = float(i['data']['size'])
            USD_Value = position*float(currentPrice)
            try:
                if i['data']['side'] == 'Sell':
                    asset = {
                            'Coin':i['data']['symbol'][:-4],
                            'Contract':i['data']['symbol'],
                            'QTY':round(position*-1,6),
                            'USDValue':round(USD_Value*-1,2),
                            'Exchange':exchange,
                            'Account':'USDT-M',
                            'Leverage':i['data']['leverage'],
                            'MarkPrice':round(currentPrice,2),
                            'LiqPrice':round(float(i['data']['liq_price']),2),
                            'LiqRisk':(float(i['data']['liq_price'])-float(currentPrice))/float(currentPrice)
                        }
                    assets.append(asset)

                    posAbsolute += abs(USD_Value)
                    posUSDValue += USD_Value*-1
                else:
                    asset = {
                            'Coin':i['data']['symbol'][:-4],
                            'Contract':i['data']['symbol'],
                            'QTY':round(position,6),
                            'USDValue':round(USD_Value,2),
                            'Exchange':exchange,
                            'Account':'USDT-M',
                            'Leverage':i['data']['leverage'],
                            'MarkPrice':round(currentPrice,2),
                            'LiqPrice':round(float(i['data']['liq_price']),2),
                            'LiqRisk':(float(currentPrice)-float(i['data']['liq_price']))/float(currentPrice)
                        }
                    assets.append(asset)

                    posAbsolute += abs(USD_Value)
                    posUSDValue += USD_Value
            except:
                if i['data']['side'] == 'Sell':
                    asset = {
                            'Coin':i['data']['symbol'][:-4],
                            'Contract':i['data']['symbol'],
                            'QTY':round(position*-1,6),
                            'USDValue':round(USD_Value*-1,2),
                            'Exchange':exchange,
                            'Account':'USDT-M',
                            'Leverage':i['data']['leverage'],
                            'MarkPrice':round(currentPrice,2),
                            'LiqPrice':'Null',
                            'LiqRisk':'Null'
                        }
                    assets.append(asset)

                    posAbsolute += abs(USD_Value)
                    posUSDValue += USD_Value*-1
                else:
                    asset = {
                            'Coin':i['data']['symbol'][:-4],
                            'Contract':i['data']['symbol'],
                            'QTY':round(position,6),
                            'USDValue':round(USD_Value,2),
                            'Exchange':exchange,
                            'Account':'USDT-M',
                            'Leverage':i['data']['leverage'],
                            'MarkPrice':round(currentPrice,2),
                            'LiqPrice':'Null',
                            'LiqRisk':'Null'
                        }
                    assets.append(asset)

                    posAbsolute += abs(USD_Value)
                    posUSDValue += USD_Value

    bybit = {'assets':assets, 'posValue':[posAbsolute, posUSDValue, 'Trading']}

    return bybit

def leverValues(api_key, api_secret, exchange):
    leverValue = []

    for i in [get_usdt_pos(api_key, api_secret, exchange)]:
        lever = {'absolute':i['posValue'][0], 'USDValue':i['posValue'][1], 'Account':'USDT-M', 'exchange':'Bybit'}
        leverValue.append(lever)

    return leverValue

#get_usdt_pos(config.bybit_key, config.bybit_secret, 'terd waffle')
