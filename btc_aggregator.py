# # Imports
# -----------------------------------------------------|
import sys
import argparse
from orderbook_tooling.components import *


# # Arg Parsing
# -----------------------------------------------------|
def parse_args():
    about_app = 'This app aggregates CoinBase Pro, Kraken and Gemini exchanges \
                    to determine purchase/sell prices for BTC'
    parser = argparse.ArgumentParser(description=about_app)
    parser.add_argument('--amt', '-A',
                        type=str,
                        required=False,
                        default='',
                        help='Amount of BTC to buy/sell')

    args = parser.parse_args()
    return args


# # Main Entry
# -----------------------------------------------------|
if __name__ == '__main__':
    exit_code = 1
    try:
        #parse amount from cmd line
        args = parse_args()
        amount = args.amt
        amount = float(amount) if amount else 10

        # get and merge order books
        bids, asks = merge_order_books()

        # calculate buy/sell based on amount input
        sold, sell_price = txn_price(bids, amount)
        print(f'{sold} BTC sellable for: ${sell_price}')

        purchased, buy_price = txn_price(asks, amount)
        print(f'{purchased} BTC purchasable for: ${buy_price}')

    except Exception as ex:
        print(ex)
    sys.exit(exit_code)
