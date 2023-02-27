
import pandas as pd
import shared_Functions as sf
import requests, hmac, config_ocar, hashlib, base64
from urllib.parse import urlencode
from datetime import datetime
import numpy as np



def get_huobi_current_price(base, quote):
    symbol = base+quote
    endpoint = '/market/detail/merged'
    base_uri = 'api.huobi.pro'
    method = 'GET'
    url = 'https://' + base_uri + endpoint + '?symbol=' + symbol.lower()
    response = requests.request(method, url)
    r = response.json()
    pr = (r['tick']['bid'][0] + r['tick']['ask'][0])/2
    return pr

def huobi_send_signed_request(chiave_huobi, segreta_huobi, endpoint, method, base_uri):
    timestamp = str(datetime.utcnow().isoformat())[0:19]
    params = urlencode({'AccessKeyId': chiave_huobi,
                        'SignatureMethod': 'HmacSHA256',
                        'SignatureVersion': '2',
                        'Timestamp': timestamp
                       })
    pre_signed_text = method + '\n' + base_uri + '\n' + endpoint + '\n' + params
    hash_code = hmac.new(segreta_huobi.encode(), pre_signed_text.encode(), hashlib.sha256).digest()
    signature = urlencode({'Signature': base64.b64encode(hash_code).decode()})
    url = 'https://' + base_uri + endpoint + '?' + params + '&' + signature
    response = requests.request(method, url)
    return response.json()

def huobi_send_signed_request_usdM(chiave_huobi, segreta_huobi, endpoint, method, base_uri):
    timestamp = str(datetime.utcnow().isoformat())[0:19]
    params = urlencode({'AccessKeyId': chiave_huobi,
                        'SignatureMethod': 'HmacSHA256',
                        'SignatureVersion': '2',
                        'Timestamp': timestamp,
                       })
    pre_signed_text = method + '\n' + base_uri + '\n' + endpoint + '\n' + params
    hash_code = hmac.new(segreta_huobi.encode(), pre_signed_text.encode(), hashlib.sha256).digest()
    signature = urlencode({'Signature': base64.b64encode(hash_code).decode()})
    url = 'https://' + base_uri + endpoint + '?' + params + '&' + signature
    response = requests.request(method, url, json={'valuation_asset': 'USDT'})
    return response.json()

def get_contract_size(symbol):
    endpoint = '/swap-api/v1/swap_contract_info?contract_code='+symbol
    base_uri = 'api.hbdm.com'
    method = 'GET'
    url = 'https://' + base_uri + endpoint
    response = requests.request(method, url)
    resp = response.json()
    r = resp['data'][0]['contract_size']
    return r

def huobi_usdM_wallet_balance(api_key, api_secret, exchange):
    huobi_usdM_wallet = huobi_send_signed_request_usdM(api_key, api_secret, '/linear-swap-api/v1/swap_balance_valuation', 'POST', 'api.hbdm.com')
    total_balance = 0                                             
    assets = []

    #print(huobi_usdM_wallet)
    #sf.saveExcel('huobi_btc.xlsx', huobi_usdM_wallet['data'])

    for i in range(0, len(huobi_usdM_wallet['data'])):
        if huobi_usdM_wallet['data'][i]['balance'] != 0:
            total_balance += float(huobi_usdM_wallet['data'][i]['balance'])
            if round(float(huobi_usdM_wallet['data'][i]['balance']),2) != 0:
                asset = {
                    'Coin':huobi_usdM_wallet['data'][i]['valuation_asset'].upper(), 
                    'Contract':huobi_usdM_wallet['data'][i]['valuation_asset'].upper(), 
                    'QTY':round(float(huobi_usdM_wallet['data'][i]['balance']),6), 
                    'USDValue':round(float(huobi_usdM_wallet['data'][i]['balance']),2),
                    'Exchange':exchange, 
                    'Account':'USD-M'}
                assets.append(asset)

    return [total_balance, 'USDT-M', assets]

def huobi_coinM_wallet_balance(api_key, api_secret, exchange):
    coinM_wallet = huobi_send_signed_request(api_key, api_secret, '/swap-api/v1/swap_account_info', 'POST', 'api.hbdm.com')
    total_balance = 0 
    assets = []

    for i in range(0, len(coinM_wallet['data'])):
        if coinM_wallet['data'][i]['margin_balance'] != 0:
            try:
                coin_price = get_huobi_current_price(coinM_wallet['data'][i]['symbol'], 'USDT')
                total = float(coinM_wallet['data'][i]['margin_balance'])*float(coin_price)
                total_balance += total
                if round(total,2) != 0:
                    asset = {
                        'Coin':coinM_wallet['data'][i]['symbol'].upper(), 
                        'Contract':coinM_wallet['data'][i]['symbol'].upper(), 
                        'QTY':round(float(coinM_wallet['data'][i]['margin_balance']),6), 
                        'USDValue':round(total,2),
                        'Exchange':exchange, 
                        'Account':'Coin-M'}
                    assets.append(asset)
            except:
                total_balance += coinM_wallet['data'][i]['margin_balance']
                if round(float(coinM_wallet['data'][i]['margin_balance']),2) != 0:
                    asset = {
                        'Coin':coinM_wallet['data'][i]['symbol'].upper(), 
                        'Contract':coinM_wallet['data'][i]['symbol'].upper(), 
                        'QTY':round(float(coinM_wallet['data'][i]['margin_balance']),6), 
                        'USDValue':round(float(coinM_wallet['data'][i]['margin_balance']),2),
                        'Exchange':exchange, 
                        'Account':'Coin-M'}
                    assets.append(asset)
    
    return [total_balance, 'Coin-M', assets]

def rest_huobi_spot_wallet(chiave_huobi, segreta_huobi, huobi_spot_account_id, exchange):
    endpoint = '/v1/account/accounts/{}/balance'.format(huobi_spot_account_id)
    r = huobi_send_signed_request(chiave_huobi, segreta_huobi, endpoint, 'GET', 'api.huobi.pro')
    total_balance = 0
    assets = []

    for i in r['data']['list']:
        if i['balance'] != '0':
            if 'usd' in i['currency']:
                total_balance += float(i['balance'])
                if round(float(i['balance']),2) != 0:
                    asset = {
                        'Coin':i['currency'].upper(), 
                        'Contract':i['currency'].upper(), 
                        'QTY':round(float(i['balance']),6), 
                        'USDValue':round(float(i['balance']),2),
                        'Exchange':exchange, 
                        'Account':'SPOT'}
                    assets.append(asset)
            else:
                coin_price = get_huobi_current_price(i['currency'], 'usdt')
                total_balance += float(i['balance'])*coin_price
                if round((float(i['balance'])*float(coin_price)),2) != 0:
                    asset = {
                        'Coin':i['currency'].upper(), 
                        'Contract':i['currency'].upper(), 
                        'QTY':round(float(i['balance']),6), 
                        'USDValue':round((float(i['balance'])*float(coin_price)),2),
                        'Exchange':exchange, 
                        'Account':'SPOT'}
                    assets.append(asset)

    return [total_balance, 'SPOT', assets]

def total_huobi_balance(api_key, api_secret, api_id, exchange, breakdown):
    total_balance = 0
    assets = []
    coin_assets = []
    b = {'Exchange':exchange, 'USDT-M':0, 'SPOT':0, 'Margin':0, 'Earn':0, 'Coin-M':0, 'Total':0}

    for i in [huobi_coinM_wallet_balance(api_key, api_secret, exchange), huobi_usdM_wallet_balance(api_key, api_secret, exchange), rest_huobi_spot_wallet(api_key, api_secret, api_id, exchange)]:
        total_balance += i[0]
        asset = {'Account':i[1], 'USDValue':i[0]}
        assets.append(asset)
        coin_assets.append(i[2])
        for j in b:
            if i[1] == j:
                b[j] = i[0]

    #print(coin_assets)
    #print(pd.DataFrame(assets), '\nTotal Huobi balance: ', total_balance)
    b['Total'] = total_balance
    newList = [b]
    if breakdown:
        
        sf.displayDataFrame(newList, True, False)
        print('Total',f"{total_balance:,.2f}")
    huobi = {'total':total_balance, 'coins':coin_assets, 'breakdown':newList}


    return huobi
def huobiLeaverage(api_key, api_secret, exchange):
    leverageValue = []

    for i in [huobi_usdM_wallet_balance(api_key, api_secret, exchange), huobi_coinM_wallet_balance(api_key, api_secret, exchange)]:
        lever = {'USDValue':i[0], 'Account':i[1], 'exchange':'Huobi'}
        leverageValue.append(lever)

    return leverageValue



def get_usdtM_pos(api_key, api_secret, exchange):
    usdtMPos = huobi_send_signed_request(api_key, api_secret, '/linear-swap-api/v1/swap_cross_position_info', 'POST', 'api.hbdm.com')
    get_cont_size=huobi_send_signed_request(api_key, api_secret, '/linear-swap-api/v1/swap_contract_info', 'GET', 'api.hbdm.com')
    liq_price = huobi_send_signed_request(api_key, api_secret, '/linear-swap-api/v1/swap_cross_account_info', 'POST', 'api.hbdm.com')
    
    assets = []    

    posAbsolute = 0
    posUSDValue = 0  

    for i in usdtMPos['data']:
        for j in get_cont_size['data']:
            for k in liq_price['data'][0]['contract_detail']:
                if j['symbol'] == i['symbol'] and i['symbol'] == k['symbol']:
                    position = j['contract_size']*i['volume']
                    USD_Value = position*i['last_price']
                    try:
                        liq = float(k['liquidation_price'])
                        if i['direction'] == 'sell':
                            asset = {
                                'Coin':i['symbol'],
                                'Contract':i['contract_code'],
                                'QTY':round(position*-1,6),
                                'USDValue':round(USD_Value*-1,2),
                                'Exchange':exchange,
                                'Account':'USDT-M',
                                'Leverage':i['lever_rate'],
                                'MarkPrice':round(float(i['last_price']),2),
                                'LiqPrice':round(liq,2),
                                'LiqRisk':(liq-float(i['last_price']))/float(i['last_price'])
                            }
                            assets.append(asset)

                            posAbsolute += abs(USD_Value)
                            posUSDValue += (USD_Value*-1)
                        else:
                            asset = {
                                'Coin':i['symbol'],
                                'Contract':i['contract_code'],
                                'QTY':round(position,6),
                                'USDValue':round(USD_Value,2),
                                'Exchange':exchange,
                                'Account':'USDT-M',
                                'Leverage':i['lever_rate'],
                                'MarkPrice':round(float(i['last_price']),2),
                                'LiqPrice':round(liq,2),
                                'LiqRisk':(float(i['last_price'])-liq)/float(i['last_price'])
                            }
                            assets.append(asset)

                            posAbsolute += abs(USD_Value)
                            posUSDValue += USD_Value
                    except:
                        liq = 'Null'
                        if i['direction'] == 'sell':
                            asset = {
                                'Coin':i['symbol'],
                                'Contract':i['contract_code'],
                                'QTY':round(position*-1,6),
                                'USDValue':round(USD_Value*-1,2),
                                'Exchange':exchange,
                                'Account':'USDT-M',
                                'Leverage':i['lever_rate'],
                                'MarkPrice':round(float(i['last_price']),2),
                                'LiqPrice':liq,
                                'LiqRisk':liq
                            }
                            assets.append(asset)

                            posAbsolute += abs(USD_Value)
                            posUSDValue += (USD_Value*-1)
                        else:
                            asset = {
                                'Coin':i['symbol'],
                                'Contract':i['contract_code'],
                                'QTY':round(position,6),
                                'USDValue':round(USD_Value,2),
                                'Exchange':exchange,
                                'Account':'USDT-M',
                                'Leverage':i['lever_rate'],
                                'MarkPrice':round(float(i['last_price']),2),
                                'LiqPrice':liq,
                                'LiqRisk':liq
                            }
                            assets.append(asset)

                            posAbsolute += abs(USD_Value)
                            posUSDValue += USD_Value
    huobi = {'assets':assets, 'posValue':[posAbsolute, posUSDValue, 'USDT-M']}

    return huobi

def get_coinM_pos(api_key, api_secret, exchange):
    coinMPos = huobi_send_signed_request(api_key, api_secret, '/swap-api/v1/swap_position_info', 'POST', 'api.hbdm.com')
    liqPrice = huobi_send_signed_request(api_key, api_secret, '/swap-api/v1/swap_account_info', 'POST', 'api.hbdm.com')

    assets = []     

    posAbsolute = 0
    posUSDValue = 0 

    for i in coinMPos['data']:
        if i['volume'] != 0:
            for j in liqPrice['data']:
                if j['symbol'] == i['symbol']:
                    cont_Size = get_contract_size(i['contract_code'])
                    USD_Value = float(i['volume'])*float(cont_Size)
                    position = USD_Value/float(i['last_price'])
                    try:
                        liq = float(j['liquidation_price'])
                        if i['direction'] == 'sell':
                            asset = {
                                    'Coin':i['symbol'],
                                    'Contract':i['contract_code'],
                                    'QTY':round(position*-1,6),
                                    'USDValue':round(USD_Value*-1,2),
                                    'Exchange':exchange,
                                    'Account':'Coin-M',
                                    'Leverage':i['lever_rate'],
                                    'MarkPrice':round(float(i['last_price']),2),
                                    'LiqPrice':round(liq,2), #Need to find this or an alternative
                                    'LiqRisk':(liq-float(i['last_price']))/float(i['last_price'])
                                }
                            assets.append(asset)

                            posAbsolute += abs(USD_Value)
                            posUSDValue += (USD_Value*-1)
                        else:
                            asset = {
                                    'Coin':i['symbol'],
                                    'Contract':i['contract_code'],
                                    'QTY':round(position,6),
                                    'USDValue':round(USD_Value,2),
                                    'Exchange':exchange,
                                    'Account':'Coin-M',
                                    'Leverage':i['lever_rate'],
                                    'MarkPrice':round(float(i['last_price']),2),
                                    'LiqPrice':round(liq,2), #Need to find this or an alternative
                                    'LiqRisk':(float(i['last_price'])-liq)/float(i['last_price'])
                                }
                            assets.append(asset)

                            posAbsolute += abs(USD_Value)
                            posUSDValue += USD_Value
                    except:
                        liq = 'Null'
                        if i['direction'] == 'sell':
                            asset = {
                                    'Coin':i['symbol'],
                                    'Contract':i['contract_code'],
                                    'QTY':round(position*-1,6),
                                    'USDValue':round(USD_Value*-1,2),
                                    'Exchange':exchange,
                                    'Account':'Coin-M',
                                    'Leverage':i['lever_rate'],
                                    'MarkPrice':round(float(i['last_price']),2),
                                    'LiqPrice':liq, #Need to find this or an alternative
                                    'LiqRisk':liq
                                }
                            assets.append(asset)

                            posAbsolute += abs(USD_Value)
                            posUSDValue += (USD_Value*-1)
                        else:
                            asset = {
                                    'Coin':i['symbol'],
                                    'Contract':i['contract_code'],
                                    'QTY':round(position,6),
                                    'USDValue':round(USD_Value,2),
                                    'Exchange':exchange,
                                    'Account':'Coin-M',
                                    'Leverage':i['lever_rate'],
                                    'MarkPrice':round(float(i['last_price']),2),
                                    'LiqPrice':liq, #Need to find this or an alternative
                                    'LiqRisk':liq
                                }
                            assets.append(asset)

                            posAbsolute += abs(USD_Value)
                            posUSDValue += USD_Value

    huobi = {'assets':assets, 'posValue':[posAbsolute, posUSDValue, 'Coin-M']}

    return huobi

def get_all_positions(api_key, api_secret, exchange):
    assets = []

    for i in [get_coinM_pos(api_key, api_secret, exchange), get_usdtM_pos(api_key, api_secret, exchange)]:
        assets.append(i['assets'])

    return assets

def leverValues(api_key, api_secret, exchange):
    leverValue = []

    for i in [get_coinM_pos(api_key, api_secret, exchange), get_usdtM_pos(api_key, api_secret, exchange)]:
        lever = {'absolute':i['posValue'][0], 'USDValue':i['posValue'][1], 'Account':i['posValue'][2], 'exchange':'Huobi'}
        leverValue.append(lever)

    return leverValue

#x = leverValues(config.huobi_key, config.huobi_secret, 'jj')

#sf.displayDataFrame(x, True)
