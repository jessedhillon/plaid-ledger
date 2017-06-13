import re as regex

from plaid_ledger import config


def match_transaction(transaction, transaction_type=None, item_id=None,
        account_id=None, name=None, amount=None, date=None):
    account = config.get_account(transaction['account_id'])
    item = account['item']

    matches = {}
    if item_id is not None:
        matches['item_id'] = regex_match(item['id'], item_id)
    if account_id is not None:
        matches['account_id'] = regex_match(account['id'], account_id)
    if transaction_type is not None:
        matches['transaction_type'] = regex_match(transaction['transaction_type'], transaction_type)
    if name is not None:
        matches['name'] = regex_match(transaction['name'], name)
    if amount is not None:
        matches['amount'] = numerical_match(transaction['amount'], amount)
    if date is not None:
        dm = {}
        td = transaction['date']
        if 'day' in date:
            dm['day'] = numerical_match(td.day, date['day'])
        if 'month' in date:
            dm['month'] = numerical_match(td.month, date['month'])
        if 'year' in date:
            dm['year'] = numerical_match(td.year, date['year'])
        matches['date'] = all(dm.values())

    if all(matches.values()):
        return matches
    return None


def regex_match(s, patterns):
    if isinstance(patterns, str):
        patterns = [patterns]

    for p in patterns:
        m = regex.match(p, s, regex.IGNORECASE)
        if m:
            return m


def numerical_match(n, values):
    if isinstance(values, (int, float)):
        return (n == values)
    elif isinstance(values, str):
        low, high = [float(s.strip()) for s in values.split('-')]
        return low <= n <= high
    else:  # list
        return any(numerical_match(n, v) for v in values)
