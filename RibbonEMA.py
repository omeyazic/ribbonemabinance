from types import BuiltinFunctionType
import ccxt, config
from numpy import short
import pandas as pd
from ta.trend import EMAIndicator
from datetime import datetime
from smtplib import SMTP
import talib

import pygame
pygame.init()
pygame.mixer.init()
pygame.mixer.music.load("dumbelek.mp3")

# import pygame
# pygame.init()
# pygame.mixer.init()
# #duration = 1000 #milliseconds
# #freq = 440 #Hz

symbolName = input("Sembol Adi Girin(BTC, ETH, LTC, ...")
leverage = input("Kaldirac buyuklugu: ")
zamanAraligi = input("Zaman Araligi: (1m,3m,5m,15m,30m,45m,1h,2h,4h,6h,8h,12h,1d): ")
symbol = str(symbolName) + "/USDT"
# slowEMAValue = input("Yavas EMA: ")
# fastEMAValue = input("Hizli EMA: ")
kesisim = False
longPozisyonda = False
shortPozisyonda = False
pozisyondami = False
alinacak_miktar = 0

ema20 = 20
ema55 = 55

#API CONNECT
exchange = ccxt.binance({
"apiKey": config.apiKey,
"secret": config.secretKey,

'options': {
'defaultType': 'future'
},
'enableRateLimit': True
})


while True:
    try:

        balance = exchange.fetch_balance()
        free_balance = exchange.fetch_free_balance()
        positions = balance['info']['positions']
        newSymbol = symbolName+"USDT"
        current_positions = [position for position in positions if float(position['positionAmt']) != 0 and position['symbol'] == newSymbol]
        position_bilgi = pd.DataFrame(current_positions, columns=["symbol", "entryPrice", "unrealizedProfit", "isolatedWallet", "positionAmt", "positionSide"])
        
        #Pozisyonda olup olmadığını kontrol etme
        if not position_bilgi.empty and position_bilgi["positionAmt"][len(position_bilgi.index) - 1] != 0:
            pozisyondami = True
        else: 
            pozisyondami = False
            shortPozisyonda = False
            longPozisyonda = False
        
        # Long pozisyonda mı?
        if pozisyondami and float(position_bilgi["positionAmt"][len(position_bilgi.index) - 1]) > 0:
            longPozisyonda = True
            shortPozisyonda = False
        # Short pozisyonda mı?
        if pozisyondami and float(position_bilgi["positionAmt"][len(position_bilgi.index) - 1]) < 0:
            shortPozisyonda = True
            longPozisyonda = False


        #LOAD BARS
        bars = exchange.fetch_ohlcv(symbol, timeframe=zamanAraligi, since = None, limit = 500)
        df = pd.DataFrame(bars, columns=["timestamp", "open", "high", "low", "close", "volume"])

        # LOAD RSI & EMA20 & EMA55
        rsi = talib.RSI(df["close"]) # kapanis degerlerinden rsi degerlerini hesapla
        df['rsi14'] = rsi
        df['ema20'] = talib.EMA(rsi, timeperiod = ema20)
        df['ema55'] = talib.EMA(rsi, timeperiod = ema55)  
        df['time_stamp'] = pd.to_datetime(df['timestamp'], unit='ms') + pd.Timedelta(hours=3) 


        # LONG ENTER
        def longEnter(alinacak_miktar):
            order = exchange.create_market_buy_order(symbol, alinacak_miktar)
            pygame.mixer.music.play(0)
            
        # LONG EXIT
        def longExit():
            order = exchange.create_market_sell_order(symbol, float(position_bilgi["positionAmt"][len(position_bilgi.index) - 1]), {"reduceOnly": True}) # SELL ORDER | SEMBOL | NE KADAR SATILACAGI | ACIK POZU KAPATMASI ICIN (YENI POZISYON ACILMAYACAK)
            pygame.mixer.music.play(0)

        # SHORT ENTER
        def shortEnter(alincak_miktar):
            order = exchange.create_market_sell_order(symbol, alincak_miktar)
            pygame.mixer.music.play(0)
            
        # SHORT EXIT
        def shortExit():
            order = exchange.create_market_buy_order(symbol, (float(position_bilgi["positionAmt"][len(position_bilgi.index) - 1]) * -1), {"reduceOnly": True})
            pygame.mixer.music.play(0)

        # CONDITION LONG ENTER \ SHORT EXIT 
        if (df['rsi14'][len(df.index)-3]  < df['ema55'][len(df.index)-3] and df['rsi14'][len(df.index)-2] > df['ema55'][len(df.index)-2] and longPozisyonda == False):
            if shortPozisyonda:
                print(df['time_stamp'][len(df.index)-1], 'SHORT EXIT',df['close'][len(df.index)-1],df['rsi14'][len(df.index)-3], df['ema55'][len(df.index)-3],df['rsi14'][len(df.index)-2],df['ema55'][len(df.index)-2])
                shortExit()
                #shortPozisyonda = False
            # alinacak_miktar = (((float(free_balance["USDT"]) / 100 ) * 50) * float(leverage)) / float(df["close"][len(df.index) - 1])
            alinacak_miktar = 5
            print(df['time_stamp'][len(df.index)-1], 'LONG ENTER',df['close'][len(df.index)-1], ) 
            longEnter(alinacak_miktar)
            # baslik = symbol
            # message = "LONG ENTER\n" + "Toplam Para: " + str(balance['total']["USDT"])
            # content = f"Subject: {baslik}\n\n{message}"
            # mail = SMTP("smtp.gmail.com", 587)
            # mail.ehlo()
            # mail.starttls()
            # mail.login(config.mailAddress, config.password)
            # mail.sendmail(config.mailAddress, config.sendTo, content.encode("utf-8"))


        # CONDITION SHORT ENTER \ LONG EXIT 
        if (df['rsi14'][len(df.index)-3] > df['ema20'][len(df.index)-3] and df['rsi14'][len(df.index)-2] < df['ema20'][len(df.index)-2] and shortPozisyonda == False):
            if longPozisyonda:
                print(df['time_stamp'][len(df.index)-1], 'LONG EXIT',df['close'][len(df.index)-1],df['rsi14'][len(df.index)-3], df['ema20'][len(df.index)-3],df['rsi14'][len(df.index)-2], df['ema20'][len(df.index)-2] )
                longExit()
            alinacak_miktar = 5
            # alinacak_miktar = (((float(free_balance["USDT"]) / 100 ) * 50) * float(leverage)) / float(df["close"][len(df.index) - 1])
            print(df['time_stamp'][len(df.index)-1], 'SHORT ENTER',df['close'][len(df.index)-1])
            shortEnter(alinacak_miktar)
            # baslik = symbol
            # message = "LONG ENTER\n" + "Toplam Para: " + str(balance['total']["USDT"])
            # content = f"Subject: {baslik}\n\n{message}"
            # mail = SMTP("smtp.gmail.com", 587)
            # mail.ehlo()
            # mail.starttls()
            # mail.login(config.mailAddress, config.password)
            # mail.sendmail(config.mailAddress, config.sendTo, content.encode("utf-8"))

        if pozisyondami == False:
            print("POZİSYON ARANIYOR...")

        if shortPozisyonda:
            print("SHORT POZİSYONDA BEKLİYOR")
        if longPozisyonda:
            print("LONG POZİSYONDA BEKLİYOR")
        
    except ccxt.BaseError as Error:
        print ("[ERROR]", Error )
        continue
