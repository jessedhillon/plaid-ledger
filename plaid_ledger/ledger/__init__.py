import glob
import logging
import math
import re as regex
from collections import namedtuple

from plaid_ledger import config, predicate

from . import parser


def parse(s):
    ledger = {}
    t = {}
    for line in s + ['']:  # append empty str to trigger parsing of final txn
        if not line.strip() and t:
            ledger[t['id']] = t
            t = {}

        elif parser.is_headline(line):
            t.update(parser.parse_headline(line))

        elif parser.is_comment(line):
            m = parser.parse_comment(line)
            comment = m['comment']

            if parser.is_meta(comment):
                m = parser.parse_meta(comment)
                k, v = m['key'], m['value']

                t.setdefault('meta', {})
                t['meta'][k] = v

                if k == 'Transaction-Id':
                    t['id'] = v

        else:
            posting = parser.parse_posting(line)

            if 'target' not in t:
                t['target'] = posting
            else:
                t.setdefault('sources', []).append(posting)

    return ledger


def load():
    ledger = {}
    for path in glob.glob('*.ledger'):
        with open(path, 'r') as f:
            config.logger.debug("{}: loading".format(path))
            lines = f.readlines()
            ledger.update(parse(lines))
    return ledger


def merge_transactions(ledger, store):
    filters = config.filters

    pending = []
    for txn in store.values():
        if txn['pending']:
            continue

        exclude = False
        for f in filters:
            p = {
                'item_id': f.get('item_id'),
                'account_id': f.get('account_id'),
                'transaction_type': f.get('transaction_type'),
                'name': f.get('name')
            }
            if predicate.match_transaction(txn, **p):
                config.logger.debug("txn {txn[transaction_id]}: matches filter item_id: {item_id}, "
                    "account_id: {account_id},transaction_type: {transaction_type}, "
                    "name: {name}".format(txn=txn, **p))
                if f['action'] == 'exclude':
                    config.logger.debug("txn {transaction_id}: excluded transaction".\
                            format(**txn))
                    exclude = True
                    break

        if exclude:
            continue

        t_id = txn['transaction_id']
        if txn['pending_transaction_id']:
            pending.append(txn['pending_transaction_id'])

        if t_id not in ledger:
            t = {
                'id': t_id,
                'date': txn['date'],
                'description': txn['name'],
                'amount': txn['amount'],
                'meta': {
                    'Transaction-Id': t_id,
                },
            }

            t['target'] = get_target(txn)
            t['sources'] = get_source(txn)

            config.logger.debug("txn {transaction_id}: merging new transaction".format(**txn))
            ledger[t_id] = t

    for t_id in pending:
        if t_id in ledger:
            del ledger[t_id]


def store(ledger):
    transactions = sorted(ledger.values(), key=lambda t: (t['date'], t['description'], t['id']))

    items = {}
    for t in transactions:
        l = []
        l.append("{date:%Y-%m-%d} {description}".format(**t))

        indent = " " * 4
        keys = list(t['meta'].keys())
        keys.remove('Transaction-Id')
        for k in ['Transaction-Id'] + keys:
            v = t['meta'][k]
            l.append("{}; {}: {}".format(indent, k, v))

        for a in [t['target']] + t['sources']:
            if a['amount'] is None:
                l.append("{}{}".format(indent, a['account']))
            else:
                if a['amount'] >= 0:
                    amount_s = "$ {:,.2f}".format(a['amount'])
                else:
                    amount_s = "$-{:,.2f}".format(-1 * a['amount'])
                l.append("{}{:50} {: >12}".format(indent, a['account'], amount_s))

        quarter = math.floor(t['date'].month / 4)
        qk = "{:%Y}q{}".format(t['date'], quarter + 1)
        items.setdefault(qk, []).append('\n'.join(l))
    
    for qk, items in items.items():
        fn = "{}.ledger".format(qk)
        with open(fn, 'w') as f:
            config.logger.debug("{}: storing ledger".format(fn))
            f.write('\n\n'.join(items))
            f.write('\n')


def get_target(transaction):
    account = config.get_account(transaction['account_id'])
    amount = transaction['amount']

    target = []
    target.append(account.get('target', 'Expenses'))
    target.append(account['name'])
    amount *= -1

    return {
        'account': ':'.join(target),
        'amount': amount
    }


def get_source(transaction):
    account = config.get_account(transaction['account_id'])
    amount = transaction['amount']

    source = []
    for m in config.mappings:
        p = {
            'account_id': m.get('account_id'),
            'name': m.get('name'),
            'amount': m.get('amount'),
            'date': m.get('date')
        }
        matches = predicate.match_transaction(transaction, **p)
        if matches:
            nm = matches['name']
            source_mappings = m['source']
            if isinstance(source_mappings, str):
                source_mappings = [{
                    'source': m['source'],
                    'portion': 1.00
                }]

            last = len(source_mappings) - 1
            for i, sm in enumerate(source_mappings):
                s = {
                    'account': sm['source'].format(*nm.groups(),
                        **nm.groupdict(), account=account),
                }
                if last > 0 and i == last:
                    s['amount'] = None
                else:
                    if 'portion' in sm:
                        s['amount'] = amount * sm['portion']
                    elif 'floor' in sm:
                        base = sm['floor']
                        rounded = base * math.floor(float(transaction['amount'])/base)
                        s['amount'] = int(rounded)

                source.append(s)
            break

    if not source:
        if account['type'] in ('depository',):
            if amount < 0:
                base = 'Income'
            else:
                base = 'Expenses'
        elif account['type'] in ('credit',):
            base = 'Expenses'
        name = regex.sub('\s+', ' ', transaction['name'])
        source.append({
            'account': '{}:{}'.format(base, name),
            'amount': amount
        })

    return source
