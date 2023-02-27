import config_ocar
import pandas as pd
import shared_Functions as sf
import requests, base64, hmac
from datetime import datetime



def okx_get_header(endpoint, api_key, api_secret, api_pass):
    body = {}
    current_time = current_time_okx()
    header = {
        'CONTENT_TYPE':'application/json',
        'OK-ACCESS-KEY':api_key,
        'OK-ACCESS-SIGN':okx_signature(current_time, endpoint, body, api_secret),
        'OK-ACCESS-TIMESTAMP':current_time,
        'OK-ACCESS-PASSPHRASE':api_pass
    }
    return header

def okx_signature(timestamp, request_path, body, api_secret):
    if str(body) == '{}' or str(body) == 'None':
        body = ''
    message = str(timestamp) + 'GET' + request_path + str(body)
    mac = hmac.new(bytes(api_secret, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod='sha256')
    d = mac.digest()
    return base64.b64encode(d)

def current_time_okx():
    now = datetime.utcnow()
    t = now.isoformat("T", "milliseconds")
    return t + "Z"

def get_okx_trading_wallet(api_key, api_secret, api_pass):
    ## Trading wallet
    url = '/api/v5/account/balance'
    header = okx_get_header(url, api_key, api_secret, api_pass)
    response = requests.get('http://www.okex.com' + url, headers=header)
    r = response.json()
    return r

def get_okx_funding_wallet(api_key, api_secret, api_pass):
    url = '/api/v5/asset/balances'
    header = okx_get_header(url, api_key, api_secret, api_pass)
    response = requests.get('http://www.okex.com' + url, headers=header)
    r = response.json()
    w = pd.DataFrame(columns=['Qty', 'USDValue'])
    return r

def okx_send_unsigned_request(url_path, payload={}):
    BASE_URL = 'https://www.okx.com'
    url = BASE_URL + url_path
    response = requests.get(url)
    return response.json()

def get_okx_current_price(base, quote):
    res = okx_send_unsigned_request("/api/v5/market/ticker?instId=" + base+'-'+quote, payload={})
    return float(res['data'][0]['last'])

def trying():
    url = '/api/v5/finance/staking-defi/orders-active'
    header = okx_get_header(url, 'b31868f6-5da1-4632-807a-5c11461fb885', 'DBE05EDEF38A320C9DBE64CD91BFE651', 'qju2wgy6dkqRZM7qyt')
    response = requests.get('http://www.okex.com' + url, headers=header)
    r = response.json()
    w = pd.DataFrame(columns=['Qty', 'USDValue'])
    return response

def get_positions(api_key, api_secret, api_pass):
    url = '/api/v5/account/positions'
    header = okx_get_header(url, api_key, api_secret, api_pass)
    response = requests.get('http://www.okex.com' + url, headers=header)
    r = response.json()
    return r

def get_contract(api_key, api_secret, api_pass, instType):
    url = '/api/v5/public/instruments?instType='+instType
    header = okx_get_header(url, api_key, api_secret, api_pass)
    response = requests.get('http://www.okex.com' + url, headers=header)
    r = response.json()
    return r

def get_earn(api_key, api_secret, api_pass):
    url = '/api/v5/finance/staking-defi/orders-active'
    header = okx_get_header(url, api_key, api_secret, api_pass)
    response = requests.get('http://www.okex.com' + url, headers=header)
    r = response.json()
    return r






def okx_funding_wallet_balance(api_key, api_secret, api_pass, exchange):
    funding_wallet = get_okx_funding_wallet(api_key, api_secret, api_pass)
    total_balance = 0
    assets = []
    
    for i in range(0, len(funding_wallet['data'])):
        try:
            coin_price = get_okx_current_price(funding_wallet['data'][i]['ccy'], 'USDT')
            total = float(funding_wallet['data'][i]['bal'])*float(coin_price)
            total_balance += total
            if round(total,2) != 0:
                asset = {
                    'Coin':funding_wallet['data'][i]['ccy'], 
                    'Contract':funding_wallet['data'][i]['ccy'],
                    'QTY':round(float(funding_wallet['data'][i]['bal']),6), 
                    'USDValue':round(total,2),
                    'Exchange':exchange, 
                    'Account':'SPOT'}
                assets.append(asset)
        except:
            total_balance += funding_wallet['data'][i]['bal']
            if round(float(funding_wallet['data'][i]['bal']),2) != 0:
                asset = {
                    'Coin':funding_wallet['data'][i]['ccy'], 
                    'Contract':funding_wallet['data'][i]['ccy'],
                    'QTY':round(float(funding_wallet['data'][i]['bal']),6), 
                    'USDValue':round(float(funding_wallet['data'][i]['eqUsd']),2),
                    'Exchange':exchange, 
                    'Account':'SPOT'}
                assets.append(asset)

    return [total_balance, 'SPOT', assets]

def okx_trading_wallet_balance(api_key, api_secret, api_pass, exchange):
    trading_wallet = get_okx_trading_wallet(api_key, api_secret, api_pass)
    total_balance = 0
    assets = []

    #print('trading: ', trading_wallet['data'][0]['details'])

    for i in range(0, len(trading_wallet['data'][0]['details'])):
        total_balance += float(trading_wallet['data'][0]['details'][i]['eqUsd'])
        #print(trading_wallet['data'][0]['details'][i]['ccy'],trading_wallet['data'][0]['details'][i]['eqUsd'])
        if round(float(trading_wallet['data'][0]['details'][i]['eqUsd']),2) != 0:
            asset = {
                'Coin':trading_wallet['data'][0]['details'][i]['ccy'], 
                'Contract':trading_wallet['data'][0]['details'][i]['ccy'],
                'QTY':round(float(trading_wallet['data'][0]['details'][i]['cashBal']),6), 
                'USDValue':round(float(trading_wallet['data'][0]['details'][i]['eqUsd']),2),
                'Exchange':exchange, 
                'Account':'USDT-M'}
            assets.append(asset)

    return [total_balance, 'USDT-M', assets]

def get_earn_balance(api_key, api_secret, api_pass, exchange):
    earn_wallet = get_earn(api_key, api_secret, api_pass)
    total_balance = 0
    assets = []

    for i in earn_wallet['data']:
        qty =float(i['investData'][0]['amt'])
        try:
            coin_price = get_okx_current_price(i['investData'][0]['ccy'], 'USDT')
            usd = qty*float(coin_price)
            asset = {
                    'Coin':i['investData'][0]['ccy'], 
                    'Contract':i['investData'][0]['ccy'],
                    'QTY':round(qty,6), 
                    'USDValue':round(usd, 2),
                    'Exchange':exchange, 
                    'Account':'Earn'}
            assets.append(asset)
            total_balance += usd
        except:
            usd = qty*1
            asset = {
                    'Coin':i['investData'][0]['ccy'], 
                    'Contract':i['investData'][0]['ccy'],
                    'QTY':round(qty,6), 
                    'USDValue':round(usd, 2),
                    'Exchange':exchange, 
                    'Account':'Earn'}
            assets.append(asset)
            total_balance += usd

    return [total_balance, 'Earn', assets]


def okx_wallet_total(api_key, api_secret, api_pass, exchange, breakdown):
    all_asset = []
    total_balance = 0
    coin_assets = []
    b = {'Exchange':exchange, 'USDT-M':0, 'SPOT':0, 'Margin':0, 'Earn':0, 'Coin-M':0, 'Total':0}

    for i in [okx_trading_wallet_balance(api_key, api_secret, api_pass, exchange), okx_funding_wallet_balance(api_key, api_secret, api_pass, exchange), get_earn_balance(api_key, api_secret, api_pass, exchange)]:
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
        
        sf.displayDataFrame(newList, True, False)
        print('Total',f"{total_balance:,.2f}")
    okx = {'total':total_balance, 'coins':coin_assets, 'breakdown':newList}


    #print(pd.DataFrame(okx['coins'][2]))
    #print(total_balance)

    return okx

def okxLeaverage(api_key, api_secret, api_pass, exchange):
    leverageValue = []

    for i in [okx_trading_wallet_balance(api_key, api_secret, api_pass, exchange)]:
        for j in i[2]:
            if j['Coin'] == 'USDT':
                lever = {'USDValue':j['USDValue'], 'Account':'USDT-M', 'exchange':'OKX'}
                leverageValue.append(lever)
    return leverageValue

def get_usdt_pos(api_key, api_secret, api_pass, exchange):
    usdtPos = get_positions(api_key, api_secret, api_pass)
    contract_size = get_contract(api_key, api_secret, api_pass, 'SWAP')

    assets = []

    posAbsolute = 0
    posUSDValue = 0

    for i in usdtPos['data']:
        for j in contract_size['data']:
            if j['instId'] == i['instId']:
                position = float(j['ctVal'])*float(i['pos'])
                USD_Value = position*float(i['markPx'])
                liq = i['liqPx']
                try:
                    
                    if i['pos'][:-(len(i['pos'])-1)] == '-':
                        asset = {
                            'Coin':i['instId'].split('-')[0],
                            'Contract':i['instId'],
                            'QTY':round(position,6),
                            'USDValue':round(USD_Value,2),
                            'Exchange':exchange,
                            'Account':'USDT-M',
                            'Leverage':i['lever'],
                            'MarkPrice':round(float(i['markPx']),2),
                            'LiqPrice':round(float(i['liqPx']),2),
                            'LiqRisk':(float(liq)-float(i['markPx']))/float(i['markPx'])
                        }
                    else:
                        asset = {
                            'Coin':i['instId'].split('-')[0],
                            'Contract':i['instId'],
                            'QTY':round(position,6),
                            'USDValue':round(USD_Value,2),
                            'Exchange':exchange,
                            'Account':'USDT-M',
                            'Leverage':i['lever'],
                            'MarkPrice':round(float(i['markPx']),2),
                            'LiqPrice':round(float(i['liqPx']),2),
                            'LiqRisk':(float(i['markPx'])-float(liq))/float(i['markPx'])
                        }
                    assets.append(asset)

                    posAbsolute += abs(USD_Value)
                    posUSDValue += USD_Value
                except:
                    asset = {
                        'Coin':i['instId'].split('-')[0],
                        'Contract':i['instId'],
                        'QTY':round(position,6),
                        'USDValue':round(USD_Value,2),
                        'Exchange':exchange,
                        'Account':'USDT-M',
                        'Leverage':i['lever'],
                        'MarkPrice':round(float(i['markPx']),2),
                        'LiqPrice':'Null',
                        'LiqRisk':'Null'
                    }
                    assets.append(asset)

                    posAbsolute += abs(USD_Value)
                    posUSDValue += USD_Value

    OKX = {'assets':assets, 'posValue':[posAbsolute, posUSDValue, 'Earn']}

    return OKX

def leverValues(api_key, api_secret, api_pass, exchange):
    leverValue = []

    for i in [get_usdt_pos(api_key, api_secret, api_pass, exchange)]:
        lever = {'absolute':i['posValue'][0], 'USDValue':i['posValue'][1], 'Account':'USDT-M', 'exchange':'OKX'}
        leverValue.append(lever)

    return leverValue

#print(leverValues(config.okx_key, config.okx_secret, config.okx_passphrase, 'OKX'))
