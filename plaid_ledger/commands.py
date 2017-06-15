from plaid_ledger import config, ledger, transactions, terminal

import click


@click.group()
@click.option('--conf', '-C', default='ledger.yml')
@click.option('--verbose', '-v', is_flag=True)
def main(conf, verbose):
    config.initialize(conf, verbose)


@main.group()
def fetch():
    """Fetch data from Plaid"""
    pass


@main.group()
def dump():
    """Dump object"""
    pass


@fetch.command(name='transactions')
@click.argument('item_ids', required=False, nargs=-1)
@click.option('--full', '-F', is_flag=True)
def fetch_transactions(item_ids, full):
    ts = transactions.load()
    new = 0

    items = config.items.values()
    if item_ids:
        items = [i for i in items if i['id'] in item_ids]

    for item in items:
        if not item.get('enabled', True):
            config.logger.debug("{id} ({name}): disabled, skipping".format(**item))
            continue

        fetched = transactions.fetch(item, full_history=full)
        config.logger.debug("{id} ({name}): fetched {} transactions)".format(len(fetched), **item))

        count = len(ts.keys())
        transactions.merge(ts, fetched)
        count = len(ts.keys()) - count
        assert count >= 0

        new += count

        if count > 0:
            config.logger.info("{id} ({name}): {} new transaction(s)".format(count, **item))

    if new > 0:
        transactions.store(ts)


@fetch.command(name='accounts')
@click.argument('item_id')
def fetch_accounts(item_id):
    item = config.get_item(item_id)
    config.logger.info("{id} ({name}): fetching accounts".format(**item))

    response = config.client.Accounts.get(item['access_token'])
    print(terminal.format_json(response['accounts']))


@dump.command(name='transaction')
@click.argument('transaction_key')
def dump_transaction(transaction_key):
    ts = transactions.load()
    if transaction_key in ts:
        print(terminal.format_json(ts[transaction_key]))


@main.command()
def update():
    """
    Merge transactions into the ledger
    """
    try:
        ts = transactions.load()
        l = ledger.load()

        count = len(l)
        ledger.merge_transactions(l, ts)
        count = len(l) - count

        if count > 0:
            config.logger.info("merging {} new transactions".format(count))
            ledger.store(l)
    except:
        import traceback
        import pdb
        traceback.print_exc()
        pdb.post_mortem()
