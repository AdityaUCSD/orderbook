import requests
from orderbook_tooling.error_messages import *

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
    """
    Get exchange orderbooks, combine and sort by price
    :return: sorted bids orderbook, sorted asks orderbook

    """
    cb_bids, cb_asks = get_coinbase_btc_orderbook()
    #CoinBase Pro Bids/Asks Structure: [[BTC price, BTC amount, ___], [BTC price, BTC amount, ___]]
    cb_bids = [[float(bid[0]), float(bid[1]), 'CoinBase'] for bid in cb_bids]
    cb_asks = [[float(ask[0]), float(ask[1]), 'CoinBase'] for ask in cb_asks]


    gm_bids, gm_asks = get_gemini_btc_orderbook()
    # Gemini Bids/Asks Structure: [{'price': 'X', 'amount': 'Y', 'timestamp': 'Z'}, {'price': 'X', 'amount': 'Y', 'timestamp': 'Z'}]
    gm_bids = [[float(bid['price']), float(bid['amount']), 'Gemini'] for bid in gm_bids]
    gm_asks = [[float(ask['price']), float(ask['amount']), 'Gemini'] for ask in gm_asks]

    
    kr_bids, kr_asks = get_kraken_btc_orderbook()
    # Kraken Bids/Asks Structure: [[BTC price, BTC amount, timestamp], [BTC price, BTC amount, timestamp]]
    kr_bids = [[float(bid[0]), float(bid[1]), 'Kraken'] for bid in kr_bids]
    kr_asks = [[float(ask[0]), float(ask[1]), 'Kraken'] for ask in kr_asks]

    # Merged orderbook Bids/Asks Structure: [[BTC price, BTC amount], [BTC price, BTC amount]] we don't care about timestamps
    bids = cb_bids + gm_bids + kr_bids
    asks = cb_asks + gm_asks + kr_asks

    bids = sorted(bids, key=lambda x: x[0], reverse=True)
    asks = sorted(asks, key=lambda x: x[0])

    return bids, asks

def parse_amt(amount):
    try:
        amount = float(amount) if amount else 10 
    except:
        raise Exception(invalid_type_amount)
    if amount < 0:
        raise Exception(negative_amount)
    return amount

# Grab next listing, combine with moving sum
def txn_price(book, amount=10):
    """
    Calculate lowest buy and highest sell across major exchanges
        As exchanges do, this function allows fractions of orders
    :param book: aggregated order book of live exchange prices
    :param amount: amount of btc to buy/sell
    :return: amount purchased, price in dollars

    """
    total = amount
    i, price = 0, 0

    while book[i][1] < amount:
        amount -= book[i][1]
        price += (book[i][0] * book[i][1])
        i += 1
        # if total requested BTC > available in orderbook, only include avaialable
        if i == len(book):
            return total - amount, price

    # fractional amount of last order
    price += (amount * book[i][0])
    return total, price

def gen_limit_order(book, amount=10)->str:
    """
    Generate the optimal market order
        As exchanges do, this function allows fractions of orders
    :param book: aggregated order book of live exchange prices
    :param amount: amount of btc to buy/sell
    :return: (str) optimal buy/sell pattern for each exchange
    """
    total = amount
    i, price = 0, 0
    limit_order = {}

    # iterate orderbook, aggregate total by exchange
    while book[i][1] < amount:
        if book[i][2] in limit_order:
            limit_order[book[i][2]] = {
                'price': book[i][0],
                'amount': limit_order[book[i][2]]['amount'] + book[i][1]
            }
        else: 
            limit_order[book[i][2]] = {
                'price': book[i][0],
                'amount': book[i][1]
            }
        amount -= book[i][1]
        price += (book[i][0] * book[i][1])
        i += 1
        # if total requested BTC > available in orderbook, only include avaialable
        if i == len(book):
            total = total - amount
            break

    # fractional amount of last order
    if book[i][2] in limit_order:
        limit_order[book[i][2]] = {
            'price': book[i][0],
            'amount': limit_order[book[i][2]]['amount'] + amount
        }
    else: 
        limit_order[book[i][2]] = {
            'price': book[i][0],
            'amount': amount
        }
    price += (amount * book[i][0])

    # return strategy string
    return gen_strat_str(limit_order, amount)

def gen_strat_str(limit_order, amount):
    strat_str = ""
    for ex, nums in limit_order.items():
        amount = round(nums.get('amount'), 5)
        price = nums.get('price')
        strat_str += (f'{ex} Limit Order:\t{amount}BTC at\t${price}\tTotal = ${price * amount}\n')
    # remove trailing newline + return
    return strat_str[:-2]


def print_strat(bids, asks, amount):
    print('')
    print('To achieve the sell price, submit market order sells to the following exchanges for the shown btc amounts')
    strat = gen_limit_order(bids, amount)
    print(strat)

    print('')
    print('To achieve the buy price, submit market order buys to the following exchanges for the shown btc amounts')
    strat = gen_limit_order(asks, amount)
    print(strat)