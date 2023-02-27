import pandas as pd
import config_ocar
import shared_Functions as sf
import time, hashlib, hmac, requests

def bittrex_wallet_request(api_key, api_secret):
    url = "https://api.bittrex.com/v3/balances"
    method = "GET"
    nonce = int(time.time() * 1000)
    params = {}
    content = ""
    contenthash = hashlib.sha512(content.encode()).hexdigest()
    paramsstring = ""
    message = str(nonce) + url + paramsstring + method + contenthash
    signature = hmac.new(api_secret.encode(),
                         message.encode(), hashlib.sha512).hexdigest()
    headers = {
        'Accept': 'application/json',
        'Api-Key': api_key,
        'Api-Signature': signature,
        'Api-Timestamp': str(nonce),
        'Api-Content-Hash': contenthash
    }
    response = requests.request(method, url, headers=headers, params=params)
    r = response.json()
    return r

def get_price(symbol:str):
    url = 'https://api.bittrex.com/v3/markets/' + symbol + '/ticker'
    response = requests.get(url)
    r = response.json()
    return r


exchange = 'Bittrex'

def bittrex_balance(api_key, api_secret, breakdown):
    bittrex_wallet = bittrex_wallet_request(api_key, api_secret)
    total_balance = 0
    assets = []
    coin_assets = []

    for i in range(0, len(bittrex_wallet)):
        if bittrex_wallet[i]['currencySymbol'] == 'EUR':
            coin_price = get_price('USD-'+bittrex_wallet[i]['currencySymbol'])
            total = float(bittrex_wallet[i]['total'])/float(coin_price['lastTradeRate'])
            total_balance += total
            asset = {'Account':bittrex_wallet[i]['currencySymbol'], 'USDValue':total}
            assets.append(asset)
            if round(total,2) != 0:
                coin_asset = {
                    'Coin':bittrex_wallet[i]['currencySymbol'], 
                    'Contract':bittrex_wallet[i]['currencySymbol'],
                    'QTY':round(float(bittrex_wallet[i]['total']),6), 
                    'USDValue':round(total,2),'Exchange':exchange, 
                    'Account':'SPOT'}
                coin_assets.append(coin_asset)
        else:
            try:
                coin_price = get_price(bittrex_wallet[i]['currencySymbol']+'-USD')
                #print(coin_price)
                total = float(bittrex_wallet[i]['total'])*float(coin_price)
                total_balance += total 
                asset = {'Account':bittrex_wallet[i]['currencySymbol'], 'USDValue':total}
                assets.append(asset)
                if round(total,2) != 0:
                    coin_asset = {
                        'Coin':bittrex_wallet[i]['currencySymbol'], 
                        'Contract':bittrex_wallet[i]['currencySymbol'],
                        'QTY':round(float(bittrex_wallet[i]['total']),6), 
                        'USDValue':round(total,2),
                        'Exchange':exchange, 
                        'Account':'SPOT'}
                    coin_assets.append(coin_asset)
            except:
                total = float(bittrex_wallet[i]['total'])* 0
                total_balance += total 
                asset = {'Account':bittrex_wallet[i]['currencySymbol'], 'USDValue':total}
                assets.append(asset)
                if round(total,2) != 0:
                    coin_asset = {
                        'Coin':bittrex_wallet[i]['currencySymbol'], 
                        'Contract':bittrex_wallet[i]['currencySymbol'], 
                        'QTY':round(float(bittrex_wallet[i]['total']),6), 
                        'USDValue':round(total,2),
                        'Exchange':exchange, 
                        'Account':'SPOT'}
                    coin_assets.append(coin_asset)

    #print(pd.DataFrame(assets), '\nTotal Bittrex balance: ', total_balance)
    #print(pd.DataFrame(coin_assets))
    b = {'Exchange':exchange, 'USDT-M':0, 'SPOT':total_balance, 'Margin':0, 'Earn':0, 'Coin-M':0, 'Total':total_balance}
    newList = [b]
    if breakdown:
        
        sf.displayDataFrame(newList, True, False)
        print('Total',f"{total_balance:,.2f}")
    bittrex = {'total':total_balance, 'coins':coin_assets, 'breakdown':newList}


    return bittrex
