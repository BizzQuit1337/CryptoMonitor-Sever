import config_ocar, time
import pandas as pd
import shared_Functions as sf
import totalBalance_Binance, totalBalance_Kraken, totalBalance_OKX, totalBalance_Huobi, totalBalance_Bitmex, totalBalance_Gate, totalBalance_Bittrex, totalBalance_Bybit
#print("Number of processors: ", mp.cpu_count())
print('Monitor script is running')
start = time.time()
#results = [pool.apply(howmany_within_range, args=(row, 4, 8)) for row in data]

###Pre loading all assets to try and make the boi zoomy
#if __name__ == "__main__":
#    with Pool(5) as p:
#        binanceBalance = p.map(totalBalance_Binance.total_binance_balance, [config_ocar.binance_key, config_ocar.binance_secret, 'Binance'])
binanceBalance = totalBalance_Binance.total_binance_balance(config_ocar.binance_key, config_ocar.binance_secret, 'Binance', False)
binanceSubBalance = totalBalance_Binance.total_binance_balance(config_ocar.binance_sub_key, config_ocar.binance_sub_secret, 'Binance-sub', False)
bitmexBalance = totalBalance_Bitmex.bitmex_wallet(config_ocar.bitmex_key, config_ocar.bitmex_secret, False)
bittrexBalance = totalBalance_Bittrex.bittrex_balance(config_ocar.bittrex_key, config_ocar.bittrex_secret, False)
bybitBalance = totalBalance_Bybit.total_bybit_balance(config_ocar.bybit_key, config_ocar.bybit_secret, 'Bybit', False)
bybitSubBalance = totalBalance_Bybit.total_bybit_balance(config_ocar.bybit_sub_key, config_ocar.bybit_sub_secret, 'Bybit-sub', False)
gateBalance = totalBalance_Gate.gate_total_balance(config_ocar.gate_key, config_ocar.gate_secret, False)
huobiBalance = totalBalance_Huobi.total_huobi_balance(config_ocar.huobi_key, config_ocar.huobi_secret, config_ocar.huobi_spot_id, 'Huobi', False)
huobiSubBalance = totalBalance_Huobi.total_huobi_balance(config_ocar.huobi_key_sub, config_ocar.huobi_secret_sub, config_ocar.huobi_spot_id_sub, 'Huobi-sub', False)
krakenBalance = totalBalance_Kraken.total_kraken_balance(config_ocar.kraken_futures_key, config_ocar.kraken_futures_secret, config_ocar.kraken_key, config_ocar.kraken_secret, False)
okxBalance = totalBalance_OKX.okx_wallet_total(config_ocar.okx_key, config_ocar.okx_secret, config_ocar.okx_passphrase, 'OKX', False)
okxSubBalance = totalBalance_OKX.okx_wallet_total(config_ocar.okx_key_sub, config_ocar.okx_secret_sub, config_ocar.okx_pass_sub, 'OKX-sub', False)

binancePosition = totalBalance_Binance.all_positions(config_ocar.binance_key, config_ocar.binance_secret, 'Binance')
bitmexPosition = totalBalance_Bitmex.get_usdt_pos(config_ocar.bitmex_key, config_ocar.bitmex_secret, 'Bitmex')
bybitPosition = totalBalance_Bybit.get_usdt_pos(config_ocar.bybit_key, config_ocar.bybit_secret, 'Bybit')
gatePosition = totalBalance_Gate.get_usdt_pos(config_ocar.gate_key, config_ocar.gate_secret, 'Gate')
huobiPosition = totalBalance_Huobi.get_all_positions(config_ocar.huobi_key, config_ocar.huobi_secret, 'Huobi')
krakenPosition = totalBalance_Kraken.get_usdt_pos(config_ocar.kraken_futures_key, config_ocar.kraken_futures_secret, 'Kraken')
okxPosition = totalBalance_OKX.get_usdt_pos(config_ocar.okx_key, config_ocar.okx_secret, config_ocar.okx_passphrase, 'OKX')
binanceSubPosition = totalBalance_Binance.all_positions(config_ocar.binance_sub_key, config_ocar.binance_sub_secret, 'Binance-sub')
bybitSubPosition = totalBalance_Bybit.get_usdt_pos(config_ocar.bybit_sub_key, config_ocar.bybit_sub_secret, 'Bybit-sub')
okxSubPosition =totalBalance_OKX.get_usdt_pos(config_ocar.okx_key_sub, config_ocar.okx_secret_sub, config_ocar.okx_pass_sub, 'OKX-sub')
huobiSubPosition = totalBalance_Huobi.get_all_positions(config_ocar.huobi_key_sub, config_ocar.huobi_secret_sub, 'Huobi-sub')

print('Assets Loaded.')

#end = time.time()
#print('Assets loaded: ', (end-start))

def allBalanceBreak():
    binanceBreakdown = binanceBalance['breakdown']
    binanceSubBreakdown = binanceSubBalance['breakdown']
    bitmexBreakdown = bitmexBalance['breakdown']
    bittrexBreakdown = bittrexBalance['breakdown']
    bybitBreakdown = bybitBalance['breakdown']
    bybitSubBreakdown = bybitSubBalance['breakdown']
    gateBreakdown = gateBalance['breakdown']
    huobiBreakdown = huobiBalance['breakdown']
    huobiSubBreakdown = huobiSubBalance['breakdown']
    krakenBreakdown = krakenBalance['breakdown']
    okxBreakdown = okxBalance['breakdown']
    okxSubBreakdown = okxSubBalance['breakdown']

    breakList = [binanceBreakdown, binanceSubBreakdown, bitmexBreakdown, bittrexBreakdown, bybitBreakdown, bybitSubBreakdown, gateBreakdown, huobiBreakdown, huobiSubBreakdown, krakenBreakdown, okxBreakdown, okxSubBreakdown]
    newList = sf.condense(breakList)
    
    return newList



def get_all_positions_bak():
    positions = []
    errorCount = 0
    total_USD = 0
    for i in [binancePosition, bitmexPosition['assets'], bybitPosition['assets'], gatePosition['assets'], huobiPosition, krakenPosition, binanceSubPosition, okxPosition['assets'], okxSubPosition]:
        if str(type(i)) == "<class 'dict'>":
            total_USD += i['USDValue']
            positions.append(i)
        else:
            for j in i:
                if str(type(j)) == "<class 'dict'>":
                    total_USD += j['USDValue']
                    positions.append(j)
                else:
                    for k in j:
                        if str(type(k)) == "<class 'dict'>":
                            total_USD += k['USDValue']
                            positions.append(k)
                        else:
                            errorCount += 1
    #print(pd.DataFrame(positions))
    return positions

def get_leverageValue():
    all_positions = []
    for i in [totalBalance_Binance.leverValues(config_ocar.binance_key, config_ocar.binance_secret, 'Binance'), totalBalance_Huobi.leverValues(config_ocar.huobi_key, config_ocar.huobi_secret, 'Huobi'), totalBalance_OKX.leverValues(config_ocar.okx_key, config_ocar.okx_secret, config_ocar.okx_passphrase, 'OKX'), totalBalance_Bybit.leverValues(config_ocar.bybit_key, config_ocar.bybit_secret, 'Bybit'), totalBalance_Gate.leverValues(config_ocar.gate_key, config_ocar.gate_secret, 'Gate'), totalBalance_Bitmex.leverValues(config_ocar.bitmex_key, config_ocar.bitmex_secret, 'Bitmex')]:
        df = sf.displayDataFrame(i, False, True)
        all_positions.append(df)
    return all_positions

def leaverageAssets():
    all_assets = []
    for i in [totalBalance_Binance.binanceLeaverage(config_ocar.binance_key, config_ocar.binance_secret, 'Binance'), totalBalance_Huobi.huobiLeaverage(config_ocar.huobi_key, config_ocar.huobi_secret, 'Huobi'), totalBalance_OKX.okxLeaverage(config_ocar.okx_key, config_ocar.okx_secret, config_ocar.okx_passphrase, 'OKX'), totalBalance_Bybit.bybitLeaverage(config_ocar.bybit_key, config_ocar.bybit_secret, 'Bybit'), totalBalance_Gate.gateLeaverage(config_ocar.gate_key, config_ocar.gate_secret), totalBalance_Bitmex.bitmexLeaverage(config_ocar.bitmex_key, config_ocar.bitmex_secret)]:
        df = sf.displayDataFrame(i, False, True)
        all_assets.append(df)
    
    return all_assets

def get_all_assets_bak():
    all_coins = []

    for i in [okxSubBalance['coins'], binanceBalance['coins'], binanceSubBalance['coins'], krakenBalance['coins'], huobiBalance['coins'], huobiSubBalance['coins'], bitmexBalance['coins'], gateBalance['coins'], bittrexBalance['coins'], bybitBalance['coins'], bybitSubBalance['coins'], okxBalance['coins']]:
        if str(type(i)) == "<class 'dict'>":
            all_coins.append(i)
        else:
            for j in i:
                if str(type(j)) == "<class 'dict'>":
                    all_coins.append(j)
                else:
                    for k in j:
                        if str(type(k)) == "<class 'dict'>":
                            all_coins.append(k)
                        else:
                            print('gone to deep bud')

    

    return all_coins

def get_all_positions():
    get_all_positions.total_asset_value = 0
    #total_assets_value = 0
    positions = []
    errorCount = 0
    total_USD = 0
    for i in [binancePosition, bitmexPosition['assets'], bybitPosition['assets'], gatePosition['assets'], huobiPosition, krakenPosition, binanceSubPosition, okxSubPosition['assets'], huobiSubPosition, okxPosition['assets'], bybitSubPosition['assets']]:
        if str(type(i)) == "<class 'dict'>":
            total_USD += i['USDValue']
            positions.append(i)
        else:
            for j in i:
                if str(type(j)) == "<class 'dict'>":
                    total_USD += j['USDValue']
                    positions.append(j)
                else:
                    for k in j:
                        if str(type(k)) == "<class 'dict'>":
                            total_USD += k['USDValue']
                            positions.append(k)
                        else:
                            errorCount += 1
    sorted_positions = sorted(positions, key=lambda d: d['Coin'])  

    #for i in sorted_positions:
        #get_all_positions.total_asset_value += float(i['USDValue'])
    for i in sorted_positions:
        if float(i['USDValue']) < 0:
            get_all_positions.total_asset_value += abs(i['USDValue'])#i['USDValue'] 

   #sf.saveExcel('positions.xlsx', sorted_positions)
   
    return sorted_positions

def get_total_balance():
    balances = []
    total_total_balance = 0
    sub_total_balance = 0
    total_total_balance +=  binanceBalance['total']
    sub_total_balance +=  binanceSubBalance['total']
    total_total_balance += bybitBalance['total']
    sub_total_balance += bybitSubBalance['total']
    total_total_balance += bitmexBalance['total']
    total_total_balance += huobiBalance['total']
    sub_total_balance += huobiSubBalance['total']
    total_total_balance += bittrexBalance['total']
    total_total_balance += gateBalance['total']
    total_total_balance += krakenBalance['total']
    total_total_balance += okxBalance['total']
    sub_total_balance += okxSubBalance['total']
    overall_total = sub_total_balance + total_total_balance
    total_investment = usdt_Value()[2]
    total = [{'Total':round(total_total_balance, 2), 'Totalsub':round(sub_total_balance, 2),'Totaloverall':round(overall_total, 2), 'Totalinvestment':round(total_investment,2)}]
    return total

def get_all_assets():
    all_coins = []

    for i in [okxSubBalance['coins'], binanceBalance['coins'], binanceSubBalance['coins'], krakenBalance['coins'], huobiBalance['coins'], huobiSubBalance['coins'], bitmexBalance['coins'], gateBalance['coins'], bittrexBalance['coins'], bybitBalance['coins'], bybitSubBalance['coins'], okxBalance['coins']]:
        if str(type(i)) == "<class 'dict'>":
            all_coins.append(i)
        else:
            for j in i:
                if str(type(j)) == "<class 'dict'>":
                    all_coins.append(j)
                else:
                    for k in j:
                        if str(type(k)) == "<class 'dict'>":
                            all_coins.append(k)
                        else:
                            print('gone to deep bud')
                            
    sorted_assets = sorted(all_coins, key=lambda d: d['Coin'])

    #sf.saveExcel('assets.xlsx', sorted_assets)

    return sorted_assets

def usdt_Value():
    total_assets = []
    total_asset_value = 0

    assets = get_all_assets()
    positions = get_all_positions()

    position_value = get_all_positions.total_asset_value
    

    #sf.saveExcel('positionings.xlsx', positions)

    for i in positions:
        total_assets.append(i)
    for i in assets:
        total_assets.append(i)

    sorted_assets = sorted(total_assets, key=lambda d: d['Coin'])

    #sf.displayDataFrame(sorted_assets)

    #for i in sorted_assets:
    #    if i['Exchange'] == 'OKX-sub':
    #        print(i)

    breakAsset = {
        'Coin':'BREAK',
        'USDValue':0,
        'QTY':0
    }

    sorted_assets.append(breakAsset)
    #for i in sorted_assets:
    #    if i['Coin'] == 'sc':
    #        print(i)

    #sf.saveExcel('sorted_assets.xlsx', sorted_assets)


    coinUSD = 0
    coinQTY = 0
    cond_assets = []
    cond_currency = []

    for i in sorted_assets:
        try:
            if preCoin == i['Coin']:
                coinUSD += float(i['USDValue'])
                coinQTY += float(i['QTY'])
            else:
                if preCoin == 'USD' or preCoin == 'USDT' or preCoin == 'USDC' or preCoin == 'EUR' or preCoin == 'BUSD' or preCoin == 'ZUSD':
                    currency = {
                        'Coin':preCoin,
                        'QTY':coinQTY,
                        'USDValue':round(coinUSD,2)
                    }
                    cond_currency.append(currency)
                else:
                    asset = {
                        'Coin':preCoin,
                        'QTY':coinQTY,
                        'USDValue':coinUSD
                    }
                    cond_assets.append(asset)
                #total_asset_value += float(coinUSD)
                preCoin = i['Coin']
                coinUSD = i['USDValue']
                coinQTY = i['QTY']
        except:
            preCoin = i['Coin']
            coinUSD += float(i['USDValue'])
            coinQTY += float(i['QTY'])

    #sf.saveExcel('cond_assets.xlsx', cond_assets)

    for i in assets:
        if i['Coin'] == 'USD':
            break
        if i['Coin'] != 'EUR' and i['Coin'] != 'BUSD':
            total_asset_value += abs(float(i[ 'USDValue']))


    calc_value = abs((float(total_asset_value) + float(position_value))/2)

    return [cond_assets, cond_currency, calc_value]


def Leverage():
    
    asset_bal = leaverageAssets()
    bbdf = sf.displayDataFrame(asset_bal, False, True)
    asset_pos = get_leverageValue()
    bpdf = sf.displayDataFrame(asset_pos, False, True)

    levers = []

    for i in bbdf:
        for j in bpdf:
            if i['Account'] == j['Account'] and i['exchange'] == j['exchange']:
                try:
                    lever = {
                        'Exchange':i['exchange'],
                        'Account':i['Account'],
                        'WalletUSDValue':i['USDValue'],
                        'PositionAbsolute':j['absolute'],
                        'PositionUSDValue':j['USDValue'],
                        'Leverage':round((float(j['absolute'])/float(i['USDValue'])),2)
                    }
                    levers.append(lever)
                except:
                    lever = {
                        'Exchange':i['exchange'],
                        'Account':i['Account'],
                        'WalletUSDValue':i['USDValue'],
                        'PositionAbsolute':j['absolute'],
                        'PositionUSDValue':j['USDValue'],
                        'Leverage':0
                    }
                    levers.append(lever)
    return levers

print('Functions loaded')

leaverage = Leverage()
Balance = get_total_balance()
assets = usdt_Value()
risks = get_all_positions()
total_assets = get_all_assets()
breakdown = allBalanceBreak()

print('Data loaded')

with open('tmp.py', 'w') as f:
    lever = 'leverage = '+str(sf.tableFormatFloat(leaverage))
    bal = 'balance = '+str(sf.tableFormatFloat(Balance))
    ass = 'asset = '+str(sf.tableFormatFloat(assets[0]))
    ass_usd = 'asset_usd = '+str(sf.tableFormatFloat(assets[1]))
    risk = 'risk = '+str(sf.tableFormatFloat(risks))
    tot_ass = 'total = '+str(sf.tableFormatFloat(total_assets))
    breakD = 'breakD = '+str(sf.tableFormatFloat(breakdown))
    f.write(lever)
    f.write('\n')
    f.write(bal)
    f.write('\n')
    f.write(ass)
    f.write('\n')
    f.write(risk)
    f.write('\n')
    f.write(ass_usd)
    f.write('\n')
    f.write(tot_ass)
    f.write('\n')
    f.write(breakD)
end = time.time()
print('Taken: ', (end-start))





