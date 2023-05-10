import requests

def get_coinbase_btc_orderbook():
    response = requests.get('https://api.pro.coinbase.com/products/BTC-USD/book?level=2').json()

    return response['bids'][:50], response['asks'][:50]

def get_gemini_btc_orderbook():
    
    response = requests.get('https://api.gemini.com/v1/book/BTCUSD').json()

    return response['bids'], response['asks']

def get_kraken_btc_orderbook():

    response = requests.get('https://api.kraken.com/0/public/Depth?pair=XBTUSD').json()
    order_book = response['result']['XXBTZUSD']

    return order_book['bids'][:50], order_book['asks'][:50]


# Get order books from exchanges, normalize, clean and aggregate
def merge_order_books():
    cb_bids, cb_asks = get_coinbase_btc_orderbook()
    #CoinBase Pro Bids/Asks Structure: [[BTC price, BTC amount, ___], [BTC price, BTC amount, ___]]
    cb_bids = [[float(bid[0]), float(bid[1])] for bid in cb_bids]
    cb_asks = [[float(ask[0]), float(ask[1])] for ask in cb_asks]


    gm_bids, gm_asks = get_gemini_btc_orderbook()
    # Gemini Bids/Asks Structure: [{'price': 'X', 'amount': 'Y', 'timestamp': 'Z'}, {'price': 'X', 'amount': 'Y', 'timestamp': 'Z'}]
    gm_bids = [[float(bid['price']), float(bid['amount'])] for bid in gm_bids]
    gm_asks = [[float(ask['price']), float(ask['amount'])] for ask in gm_asks]

    
    kr_bids, kr_asks = get_kraken_btc_orderbook()
    # Kraken Bids/Asks Structure: [[BTC price, BTC amount, timestamp], [BTC price, BTC amount, timestamp]]
    kr_bids = [[float(bid[0]), float(bid[1])] for bid in kr_bids]
    kr_asks = [[float(ask[0]), float(ask[1])] for ask in kr_asks]

    # Merged orderbook Bids/Asks Structure: [[BTC price, BTC amount], [BTC price, BTC amount]] we don't care about timestamps
    bids = cb_bids + gm_bids + kr_bids
    asks = cb_asks + gm_asks + kr_asks

    bids = sorted(bids, key=lambda x: x[0], reverse=True)
    asks = sorted(asks, key=lambda x: x[0])

    return bids, asks

# Grab next listing, combine with moving sum
def txn_price(book, amount=10):
    total = amount
    i, price = 0, 0

    while book[i][1] < amount:
        amount -= book[i][1]
        price += (book[i][0] * book[i][1])
        i += 1
        if i == 150:
            return total - amount, price
    price += (amount * book[i][0])
    return total, price

