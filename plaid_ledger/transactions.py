import glob
import json
import math
from datetime import datetime

from plaid.errors import ItemError

from plaid_ledger import config


def load():
    transaction_store = {}
    for path in glob.glob('transactions-*.json'):
        with open(path, 'r') as f:
            config.logger.debug("{}: loading".format(path))
            ts = json.loads(f.read())
            for k, txn in ts.items():
                assert k not in transaction_store
                transaction_store[k] = txn
                txn['date'] = datetime.strptime(txn['date'], '%Y-%m-%d')
    return transaction_store


def store(store):
    transactions_by_quarter = {}
    for k, txn in store.items():
        quarter = math.floor(txn['date'].month / 4)
        qk = "{:%Y}q{}".format(txn['date'], quarter + 1)
        t = txn.copy()
        t['date'] = t['date'].strftime('%Y-%m-%d')
        transactions_by_quarter.setdefault(qk, {})[k] = t

    for qk, s in transactions_by_quarter.items():
        fn = "transactions-{}.json".format(qk)
        with open(fn, 'w') as f:
            config.logger.debug("{}: storing {} transactions".format(fn, len(s)))
            f.write(json.dumps(s, sort_keys=True))

    return transactions_by_quarter


def merge(store, transactions):
    for txn in transactions:
        key = txn['transaction_id']
        assert key not in store or store[key]['date'] == txn['date']
        store[key] = txn
    return store


def fetch(item):
    access_token = item['access_token']
    name = item['name']
    transactions = []

    config.logger.info("{id} ({name}): fetching transactions".format(**item))

    try:
        # transactions
        start_date = '2017-01-01'
        end_date = datetime.now().strftime('%Y-%m-%d')
        response = config.client.Transactions.get(
            access_token,
            start_date=start_date,
            end_date=end_date)

        transactions.extend(response['transactions'])
        while len(transactions) < response['total_transactions']:
            response = config.client.Transactions.get(
                access_token,
                start_date=start_date,
                end_date=end_date,
                offset=len(transactions))
            transactions.extend(response['transactions'])

    except ItemError as exc:
        config.logger.error("{id} ({name}): {}".format(exc, **item))
        return transactions

    for txn in transactions:
        txn['date'] = datetime.strptime(txn['date'], '%Y-%m-%d')

    return transactions
