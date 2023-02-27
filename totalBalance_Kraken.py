import pandas as pd
import shared_Functions as sf
import requests
import hmac
import hashlib
import base64
import time
from uuid import uuid1
import urllib.parse
import sys
from typing import List
import config_ocar
import re



def rest_kraken_wallet(chiave_kraken, segreta_kraken):
    resp = kraken_request('/0/private/Balance', {
        "nonce": str(int(1000 * time.time()))
    }, chiave_kraken, segreta_kraken)
    r = resp.json()
    return r

def kraken_request(uri_path, data, api_key, api_sec):
    api_url = "https://api.kraken.com"
    headers = {}
    headers['API-Key'] = api_key
    # get_kraken_signature() as defined in the 'Authentication' section
    headers['API-Sign'] = get_kraken_signature(uri_path, data, api_sec)
    req = requests.post((api_url + uri_path), headers=headers, data=data)
    return req

def get_kraken_signature(urlpath, data, secret):
    postdata = urllib.parse.urlencode(data)
    encoded = (str(data['nonce']) + postdata).encode()
    message = urlpath.encode() + hashlib.sha256(encoded).digest()
    mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    sigdigest = base64.b64encode(mac.digest())
    return sigdigest.decode()

def get_kraken_current_price(base, quote):
    symbol = base + '/' + quote
    resp = requests.get('https://api.kraken.com/0/public/Ticker?pair=' + symbol)
    r = resp.json()
    sy = list(r['result'].keys())[0]
    pr = float(r['result'][sy]['c'][0])
    return pr

try:
    from exceptions import KrakenExceptions
except ModuleNotFoundError:
    print('USING LOCAL MODULE')
    sys.path.append('/Users/benjamin/repositories/Trading/python-kraken-sdk')
    from exceptions import KrakenExceptions

class KrakenErrorHandler():
    '''Class used to raise an Error or return the response'''

    def __init__(self):
        self.__kexceptions = KrakenExceptions()

    def __get_exception(self, msg):
        return self.__kexceptions.get_exception(msg)

    def check(self, data: dict) -> dict:
        '''Check if the error message is a known Kraken error response
            than raise a custom exception or return the data containing the 'error'
        '''
        if len(data.get('error', [])) == 0 and 'result' in data: return data['result']

        exception = self.__get_exception(data['error'])
        if exception: raise exception(data)
        return data

    def check_send_status(self, data: dict) -> dict:
        '''Used for futures REST responses'''
        if 'sendStatus' in data and 'status' in data['sendStatus']:
            exception = self.__get_exception(data['sendStatus']['status'])
            if exception: raise exception(data)
            return data
        return data

    def check_batch_status(self, data: List[dict]) -> dict:
        '''Used for futures REST batch order responses'''
        if 'batchStatus' in data:
            batch_status = data['batchStatus']
            for status in batch_status:
                if 'status' in status:
                    exception = self.__get_exception(status['status'])
                    if exception: raise exception(data)
        return data

class KrakenBaseFuturesAPI():
    ''' Base class for all Spot clients

        Handles un/signed requests and returns exception handled results

        ====== P A R A M E T E R S ======
        key: str, defualt: ''
            Spot API public key
        secret: str, default: ''
            Spot API secret key
        url: str, default: 'https://api.kraken.com'
            optional url
        sandbox: bool, default: False
            not used so far
    '''

    URL = 'https://api.kraken.com'
    API_V = '/0'


    def __init__(self, key: str='', secret: str='', url: str='', sandbox: bool=False):
        if sandbox: raise ValueError('Sandbox not availabel for Kraken Spot trading.')
        if url != '': self.url = url
        else: self.url = self.URL
        
        self.__nonce = 0
        self.__key = key
        self.__secret = secret
        self.__err_handler = KrakenErrorHandler()
        self.__session = requests.Session()
        self.__session.headers.update({'User-Agent': 'python-kraken-sdk'})

    def _request(self,
        method: str,
        uri: str,
        timeout: int=10,
        auth: bool=True,
        params: dict=None,
        do_json: bool=False,
        return_raw: bool=False
    ) -> dict:
        if params is None: params = {}
        method = method.upper()
        data_json = ''
        if method in ['GET', 'DELETE']:
            if params:
                strl = []
                for key in sorted(params): strl.append(f'{key}={params[key]}')
                data_json += '&'.join(strl)
                uri += f'?{data_json}'.replace(' ', '%20')

        headers = { }
        if auth:
            if not self.__key or self.__key == '' or not self.__secret or self.__secret == '': raise ValueError('Missing credentials.')
            self.__nonce = (self.__nonce + 1) % 1
            params['nonce'] = str(int(time.time() * 1000)) + str(self.__nonce).zfill(4)
            headers.update({
                'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
                'API-Key': self.__key,
                'API-Sign': self.get_kraken_signature(f'{self.API_V}{uri}', params)
            })

        url = f'{self.url}{self.API_V}{uri}'
        if method in ['GET', 'DELETE']:
            return self.__check_response_data(
                self.__session.request(method=method, url=url, headers=headers, timeout=timeout),
                return_raw
            )
        if do_json:
            return self.__check_response_data(
                self.__session.request(method=method, url=url, headers=headers, json=params, timeout=timeout),
                return_raw
            )
        return self.__check_response_data(
            self.__session.request(method=method, url=url, headers=headers, data=params, timeout=timeout),
            return_raw
        )

    def get_kraken_signature(self, urlpath: str, data: dict) -> str:
        '''Returns the signed data'''
        return base64.b64encode(
            hmac.new(
                base64.b64decode(self.__secret),
                urlpath.encode() + hashlib.sha256((str(data['nonce']) + urllib.parse.urlencode(data)).encode()).digest(),
                hashlib.sha512
            ).digest()
        ).decode()

    def __check_response_data(self, response_data, return_raw: bool=False) -> dict:
        '''checkes the response, handles the error and returns the data'''
        if response_data.status_code in [ '200', 200 ]:
            if return_raw: return response_data
            try: data = response_data.json()
            except ValueError as exc: raise ValueError(response_data.content) from exc
            else:
                if 'error' in data: return self.__err_handler.check(data)
                return data
        raise Exception(f'{response_data.status_code} - {response_data.text}')

    @property
    def return_unique_id(self) -> str:
        '''Returns a unique id str'''
        return ''.join(str(uuid1()).split('-'))

    def _to_str_list(self, value) -> str:
        '''Converts a list to a comme separated str'''
        if isinstance(value, str): return value
        if isinstance(value, list): return ','.join(value)
        raise ValueError('a must be type of str or list of strings')

class KrakenBaseFuturesAPI():
    ''' Base class for all Futures clients

        Handles un/signed requests and returns exception handled results

        ====== P A R A M E T E R S ======
        key: str, defualt: ''
            Futures API public key
        secret: str, default: ''
            Futures API secret key
        url: str, default: 'https://futures.kraken.com'
            optional url
        sandbox: bool, default: False
            if set to true the url will be 'https://demo-futures.kraken.com'

        ====== N O T E S ======
        If the sandbox environment is chosen, the keys must be generated here:
            https://demo-futures.kraken.com/settings/api
    '''

    URL = 'https://futures.kraken.com'
    SANDBOX_URL = 'https://demo-futures.kraken.com'

    def __init__(self, key: str='', secret: str='', url: str='', sandbox: bool=False):

        self.sandbox = sandbox
        if url: self.url = url
        elif self.sandbox: self.url = self.SANDBOX_URL
        else: self.url = self.URL

        self.__key = key
        self.__secret = secret
        self.__nonce = 0

        self.__err_handler = KrakenErrorHandler()
        self.__session = requests.Session()
        self.__session.headers.update({'User-Agent': 'python-kraken-sdk'})

    def _request(self,
        method: str,
        uri: str,
        timeout: int=10,
        auth: bool=True,
        post_params: dict=None,
        query_params: dict=None,
        return_raw: bool=False
    ) -> dict:
        method = method.upper()

        post_string: str = ''
        if post_params is not None:
            strl: List[str] = []
            for key in sorted(post_params): strl.append(f'{key}={post_params[key]}')
            post_string = '&'.join(strl)
        else: post_params = {}

        query_string: str = ''
        if query_params is not None:
            strl: List[str] = []
            for key in sorted(query_params): strl.append(f'{key}={query_params[key]}')
            query_string = '&'.join(strl).replace(' ', '%20')
        else: query_params = {}

        headers = { }
        if auth:
            if not self.__key or self.__key == '' or not self.__secret or self.__secret == '': raise ValueError('Missing credentials')
            self.__nonce = (self.__nonce + 1) % 1
            nonce = str(int(time.time() * 1000)) + str(self.__nonce).zfill(4)
            headers.update({
                'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
                'Nonce': nonce,
                'APIKey': self.__key,
                'Authent': self.get_kraken_futures_signature(uri, query_string + post_string, nonce)
            })

        if method in ['GET', 'DELETE']:
            return self.__check_response_data(
                self.__session.request(
                    method=method,
                    url=f'{self.url}{uri}' if query_string == '' else f'{self.url}{uri}?{query_string}',
                    headers=headers,
                    timeout=timeout
                ),
                return_raw
            )
        if method == 'PUT':
            return self.__check_response_data(
                self.__session.request(
                method=method,
                url=f'{self.url}{uri}',
                params=str.encode(query_string),
                headers=headers,
                timeout=timeout
                ),
                return_raw
            )

        return self.__check_response_data(
            self.__session.request(
                method=method,
                url=f'{self.url}{uri}?{post_string}',
                data=str.encode(post_string),
                headers=headers,
                timeout=timeout
            ), return_raw
        )

    def get_kraken_futures_signature(self, endpoint: str, data: str, nonce: str) -> str:
        '''
            Returns the signed data/message
            reference: https://github.com/CryptoFacilities/REST-v3-Python/blob/ee89b9b324335d5246e2f3da6b52485eb8391d50/cfRestApiV3.py#L295-L296
        '''
        if endpoint.startswith('/derivatives'): endpoint = endpoint[len('/derivatives'):]
        sha256_hash = hashlib.sha256()
        sha256_hash.update((data + nonce + endpoint).encode('utf8'))
        return base64.b64encode(
            hmac.new(
                base64.b64decode(self.__secret),
                sha256_hash.digest(),
                hashlib.sha512
            ).digest()
        )

    def __check_response_data(self, response_data, return_raw: bool=False) -> dict:
        if response_data.status_code in [ '200', 200 ]:
            if return_raw: return response_data
            try: data = response_data.json()
            except ValueError as exc: raise ValueError(response_data.content) from exc
            else:
                if 'error' in data: return self.__err_handler.check(data)
                if 'sendStatus' in data: return self.__err_handler.check_send_status(data)
                if 'batchStatus' in data: return self.__err_handler.check_batch_status(data)
                return data
        else: raise Exception(f'{response_data.status_code} - {response_data.text}')


exchange = 'Kraken'

def kraken_spot_wallet_balance(api_key, api_secret):
    spot_wallet = rest_kraken_wallet(api_key, api_secret)
    total_balance = 0
    assets = []
    account = 'SPIT'

    for i in spot_wallet['result']:
        try:
            if len(i.split('.')) == 2:
                i == i.split('.')[0]
            coin_price = get_kraken_current_price(i, 'USD')
            #print(i, spot_wallet['result'][i], 'cp')
            total = float(spot_wallet['result'][i])*float(coin_price)
            total_balance += total
            if round(total,2) != 0:
                account = 'SPOT'
                asset = {
                    'Coin':i, 
                    'Contract':i,
                    'QTY':round(float(spot_wallet['result'][i]),2), 
                    'USDValue':round(total,2),
                    'Exchange':exchange, 
                    'Account':account}
                assets.append(asset)
        except:
            #print(i, spot_wallet['result'][i])
            total_balance += float(spot_wallet['result'][i])
            if round(float(spot_wallet['result'][i]),2) != 0:
                if len(i.split('.')) > 1:
                    x = i.split('.')
                    pattern = r'[0-9]'
                    y = re.sub(pattern, '', x[0])
                    try:
                        account = 'Earn'
                        coin_price = get_kraken_current_price(y, 'USD')
                        total = float(spot_wallet['result'][i])*float(coin_price)
                        asset = {
                        'Coin':y, 
                        'Contract':i,
                        'QTY':round(float(spot_wallet['result'][i]),2), 
                        'USDValue':total,
                        'Exchange':exchange, 
                        'Account':account}
                        assets.append(asset)
                    except:
                        account = 'Earn'
                        asset = {
                            'Coin':y, 
                            'Contract':i,
                            'QTY':round(float(spot_wallet['result'][i]),2), 
                            'USDValue':round(float(spot_wallet['result'][i]),2),
                            'Exchange':exchange, 
                            'Account':account}
                        assets.append(asset)
                else:
                    account = 'SPOT'
                    asset = {
                        'Coin':i, 
                        'Contract':i,
                        'QTY':round(float(spot_wallet['result'][i]),2), 
                        'USDValue':round(float(spot_wallet['result'][i]),2),
                        'Exchange':exchange, 
                        'Account':account}
                    assets.append(asset)

    return [total_balance, 'SPOT', assets]

def kraken_futures_wallet_balance(api_key, api_secret):
    client = KrakenBaseFuturesAPI(api_key, api_secret, "https://futures.kraken.com")
    futures_wallet = client._request('get', '/derivatives/api/v3/accounts')
    flex_wallet = futures_wallet['accounts']['flex']
    total_balance = 0
    assets = []

    #sf.saveExcel('futures Kraken.xlsx', futures_wallet['accounts'])

    ###

    for i in futures_wallet['accounts']['cash']['balances']:
        if futures_wallet['accounts']['cash']['balances'][i] != 0:
            try:
                coin_price = get_kraken_current_price(i, 'USD')
                total = float(futures_wallet['accounts']['cash']['balances'][i])*float(coin_price)
                #print(i, total)
                total_balance += total
                if round(total,2) != 0:
                    asset = {
                        'Coin':i, 
                        'Contract':i,
                        'QTY':round(float(futures_wallet['accounts']['cash']['balances'][i]),2), 
                        'USDValue':round(total,2),
                        'Exchange':exchange, 
                        'Account':'USD-Margin'}
                    assets.append(asset)
            except:
                total = float(futures_wallet['accounts']['cash']['balances'][i])
                #print(i, futures_wallet['accounts']['cash']['balances'][i])
                total_balance += total
                if round(float(futures_wallet['accounts']['cash']['balances'][i]),2) != 0:
                    asset = {
                        'Coin':i, 
                        'Contract':i, 
                        'QTY':round(float(futures_wallet['accounts']['cash']['balances'][i]),2), 
                        'USDValue':round(float(futures_wallet['accounts']['cash']['balances'][i]),2),
                        'Exchange':exchange, 
                        'Account':'USD-Margin'}
                    assets.append(asset)

    for i in flex_wallet['currencies']:
        QTY = flex_wallet['currencies'][i]['quantity']
        try:
            coin_price = coin_price = get_kraken_current_price(i, 'USD')
        except:
            coin_price = 1
        total_balance += float(QTY)*float(coin_price)
        asset = {
            'Coin':i, 
            'Contract':i,
            'QTY':round(QTY,6), 
            'USDValue':round(float(QTY)*float(coin_price),2),
            'Exchange':exchange, 
            'Account':'USD-Margin'}
        assets.append(asset)

        
    return [total_balance, 'USD-Margin', assets]

def total_kraken_balance(api_key_f, api_secret_f, api_key_s, api_secret_s, breakdown):
    total_balance = 0
    assets = []
    coin_assets = []
    balance_break = []

    for i in [kraken_futures_wallet_balance(api_key_f, api_secret_f), kraken_spot_wallet_balance(api_key_s, api_secret_s)]:
        
        #print(i[2])
        #if i[2] == 'a':#['Account'] == 'Earn':
        #for j in i[2]:
        #    if j['Account'] == 'Earn':
        #        asset = {'Account':'Earn', 'USD_Value':i[0]}
        #        assets.append(asset)
        #        coin_assets.append(i[2])
        #        balance = {'Exchange':'Kraken', 'Earn':i[0]}
        #        balance_break.append(balance)
        #    else:
        #        asset = {'Account':i[1], 'USD_Value':i[0]}
        #        assets.append(asset)
        #        coin_assets.append(i[2])
        #        balance = {'Exchange':'Kraken', i[1]:i[0]}
        #        balance_break.append(balance)
        for j in i[2]:
            total_balance += j['USDValue']
            asset = {'Account':j['Account'], 'USD_Value':j['USDValue']}
            assets.append(asset)
            coin_assets.append(j)
            balance = {'Exchange':'Kraken', j['Account']:j['USDValue']}
            balance_break.append(balance)

    #print(pd.DataFrame(assets), '\nTotal kraken balance: ', total_balance)
    usd_margin = 0
    earn = 0
    spot = 0
    nothing = 0
    for i in balance_break:
        try:
            if i['USD-Margin']:
                usd_margin += float(i['USD-Margin'])
        except:
            nothing += 1
        try:
            if i['SPOT']:
                spot += float(i['SPOT'])
        except:
            nothing += 1
        try:
            if i['Earn']:
                earn += float(i['Earn'])
        except:
            nothing += 1
    b = {'Exchange':exchange, 'USDT-M':0, 'SPOT':spot, 'Margin':usd_margin, 'Earn':earn, 'Coin-M':0, 'Total':total_balance}
    newList = [b]



    if breakdown:
        sf.displayDataFrame(newList, True, False)
        print('Total',f"{total_balance:,.2f}")
    kraken = {'total':total_balance, 'coins':coin_assets, 'breakdown':newList}


    return kraken


def get_usdt_pos(api_key, api_secret, exchange):
    client = KrakenBaseFuturesAPI(api_key, api_secret, "https://futures.kraken.com")
    usdtPos = client._request('GET', '/derivatives/api/v3/openpositions')
    tickers = client._request('GET', '/derivatives/api/v3/tickers')

    assets = []

    for i in usdtPos['openPositions']:
        if i['size'] != 0:
            for j in tickers['tickers']:
                if i['symbol'] == j['symbol']:
                    coin_price = float(j['markPrice'])
                    coin = j['pair'].split(':')[0]
            position = float(i['size'])
            USD_Value = position*coin_price
            if i['side'] == 'short':
                asset = {
                        'Coin':coin,
                        'Contract':i['symbol'],
                        'QTY':round(position*-1,6),
                        'USDValue':round((USD_Value*-1),2),
                        'Exchange':exchange,
                        'Account':'USDT-M',
                        'Leverage':1,
                        'MarkPrice':1,
                        'LiqPrice':1,
                        'LiqRisk':1
                    }
                assets.append(asset)
            else:
                asset = {
                        'Coin':coin,
                        'Contract':i['symbol'],
                        'QTY':round(position*-1,6),
                        'USDValue':round((USD_Value*-1),2),
                        'Exchange':exchange,
                        'Account':'USDT-M',
                        'Leverage':1,
                        'MarkPrice':1,
                        'LiqPrice':1,
                        'LiqRisk':1
                    }
                assets.append(asset)

    return assets



