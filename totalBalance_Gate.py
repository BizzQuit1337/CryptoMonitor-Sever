import config_ocar
import pandas as pd
import shared_Functions as sf
import time, hashlib, hmac, requests



def signature(method, url, chiave_gate, segreta_gate, query_string=None, payload_string=None):
    key = chiave_gate
    secret = segreta_gate
    t = time.time()
    m = hashlib.sha512()
    m.update((payload_string or "").encode('utf-8'))
    hashed_payload = m.hexdigest()
    s = '%s\n%s\n%s\n%s\n%s' % (method, url, query_string or "", hashed_payload, t)
    sign = hmac.new(secret.encode('utf-8'), s.encode('utf-8'), hashlib.sha512).hexdigest()
    return {'KEY': key, 'Timestamp': str(t), 'SIGN': sign}
    

def send_signed_request(url, chiave_gate, segreta_gate):
    host = "https://api.gateio.ws"
    prefix = "/api/v4"
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

    query_param = ''
    # for `gen_sign` implementation, refer to section `Authentication` above
    sign_headers = signature('GET', prefix + url, chiave_gate, segreta_gate, query_param)
    headers.update(sign_headers)
    r = requests.request('GET', host + prefix + url, headers=headers)
    return r.json()

def current_price(base, quote):
    host = "https://api.gateio.ws"
    prefix = "/api/v4"
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

    url = '/spot/tickers'
    query_param = 'currency_pair=' + base + '_' + quote
    r = requests.request('GET', host + prefix + url + "?" + query_param, headers=headers)
    return float(r.json()[0]['last'])

exchange = 'Gate'


def gate_swap_balance(api_key, api_secret):
    gate_wallet = send_signed_request('/futures/usdt/accounts', api_key, api_secret)
    unrealPnL = gate_wallet['unrealised_pnl'] 
    total_balance = float(gate_wallet['total']) + float(unrealPnL)
    #sf.saveExcel('hh.xlsx',gate_wallet)
    asset = {'Account':'Futures', 'USDValue':total_balance}
    if round(total_balance,2) != 0:
        coin_asset = {
            'Coin':gate_wallet['currency'], 
            'Contract':gate_wallet['currency'], 
            'QTY':round(float(gate_wallet['total']),6), 
            'USDValue':round(total_balance,2),
            'Exchange':exchange, 
            'Account':'USDT-M'}
        return [total_balance, 'USDT-M', coin_asset]
    else:
        coin_asset = {
            'Coin':gate_wallet['currency'], 
            'Contract':gate_wallet['currency'], 
            'QTY':round(float(gate_wallet['total']),6), 
            'USDValue':round(total_balance,2),
            'Exchange':exchange, 
            'Account':'USDT-M'}
        return [total_balance, 'USDT-M', coin_asset]

def gate_spot_balance(api_key, api_secret):
    gate_wallet = send_signed_request('/spot/accounts', api_key, api_secret)
    total_balance = 0
    assets = []

    #sf.saveExcel('d.xlsx', gate_wallet)

    for i in range(0, len(gate_wallet)):
        try:
            coin_price = current_price(gate_wallet[i]['currency'], 'USDT')
            total_pre_price = float(gate_wallet[i]['available'])+float(gate_wallet[i]['locked'])
            total = total_pre_price * coin_price
            total_balance += total
            if round(total,2) != 0:
                asset = {
                    'Coin':gate_wallet[i]['currency'], 
                    'Contract':gate_wallet[i]['currency'], 
                    'QTY':round(float(gate_wallet[i]['available']),6), 
                    'USDValue':round(total,2),
                    'Exchange':exchange, 
                    'Account':'SPOT'}
                assets.append(asset)
        except:
            if gate_wallet[i]['currency'] == 'BTTOLD':
                total = float(gate_wallet[i]['available'])+float(gate_wallet[i]['locked'])
                total_balance += 0
                usd = 0
                if usd != 0:
                    asset = {
                        'Coin':gate_wallet[i]['currency'], 
                        'Contract':gate_wallet[i]['currency'],
                        'QTY':round(float(gate_wallet[i]['available']),6), 
                        'USDValue':0,
                        'Exchange':exchange, 
                        'Account':'SPOT'}
                    assets.append(asset)
            else:
                total = float(gate_wallet[i]['available'])+float(gate_wallet[i]['locked'])
                total_balance += total
                if round(total,2) != 0:
                    asset = {
                        'Coin':gate_wallet[i]['currency'], 
                        'Contract':gate_wallet[i]['currency'], 
                        'QTY':round(float(gate_wallet[i]['available']),6), 
                        'USDValue':round(total,2),
                        'Exchange':exchange, 
                        'Account':'SPOT'}
                    assets.append(asset)

    return [total_balance, 'SPOT', assets]

def gate_total_balance(api_key, api_secret, breakdown):
    total_balance = 0
    assets = []
    coin_assets = []
    skips = 0
    b = {'Exchange':exchange, 'USDT-M':0, 'SPOT':0, 'Margin':0, 'Earn':0, 'Coin-M':0, 'Total':0}

    for i in [gate_swap_balance(api_key, api_secret), gate_spot_balance(api_key, api_secret)]:
        assets.append(i)
        try:
            total_balance += float(i[0])
            coin_assets.append(i[2])
            for j in b:
                if i[1] == j:
                    b[j] = i[0]
        except:
            total_balance += float(i[0])
            for j in b:
                if i[1] == j:
                    b[j] = i[0]
            skips += 1

    #print(coin_assets)
    #print(pd.DataFrame(assets), '\nTotal Gate balance: ', total_balance)
    b['Total'] = total_balance
    newList = [b]
    if breakdown:
        
        sf.displayDataFrame(newList, True, False)
        print('Total',f"{total_balance:,.2f}")
    gate = {'total':total_balance, 'coins':coin_assets, 'breakdown':newList}


    return gate
def gateLeaverage(api_key, api_secret):
    leverageValue = []

    for i in [gate_swap_balance(api_key, api_secret)]:
        lever = {'USDValue':i[0], 'Account':'USDT-M', 'exchange':'Gate'}
        leverageValue.append(lever)
        if lever['USDValue'] <= 0.01:
            lever['USDValue'] = 0

    return leverageValue



def get_usdt_pos(api_key, api_secret, exchange):
    usdtPos = send_signed_request('/futures/usdt/positions', api_key, api_secret)

    assets = []

    posAbsolute = 0
    posUSDValue = 0

    for i in usdtPos:
        if i['size'] != 0:
            position = float(i['value'])/float(i['mark_price'])
            USD_Value = float(i['value'])
            try:
                asset = {
                        'Coin':'When can see output add coin name here',
                        'Contract':'When can see output add contract name here',
                        'QTY':round(position,6),
                        'USDValue':round(USD_Value,2),
                        'Exchange':exchange,
                        'Account':'USDT-M',
                        'Leverage':i["leverage"],
                        'MarkPrice':round(float(i["mark_price"]),2),
                        'LiqPrice':round(float(i["liq_price"]),2),
                        'LiqRisk':(float(i["liq_price"])-float(i["mark_price"]))/float(i["mark_price"])
                    }
                assets.append(asset)

                posAbsolute += abs(USD_Value)
                posUSDValue += USD_Value
            except:
                asset = {
                        'Coin':'When can see output add coin name here',
                        'Contract':'When can see output add contract name here',
                        'QTY':round(position,6),
                        'USDValue':round(USD_Value,2),
                        'Exchange':exchange,
                        'Account':'USDT-M',
                        'Leverage':i["leverage"],
                        'MarkPrice':round(float(i["mark_price"]),2),
                        'LiqPrice':'Null',
                        'LiqRisk':'Null'
                    }
                assets.append(asset)

                posAbsolute += abs(USD_Value)
                posUSDValue += USD_Value

    Gate = {'assets':assets, 'posValue':[posAbsolute, posUSDValue, 'Future']}

    return Gate

def leverValues(api_key, api_secret, exchange):
    leverValue = []

    for i in [get_usdt_pos(api_key, api_secret, exchange)]:
        lever = {'absolute':i['posValue'][0], 'USDValue':i['posValue'][1], 'Account':i['posValue'][2], 'exchange':'Gate'}
        leverValue.append(lever)

    return leverValue
    
