import os
import yaml
import logging
import logging.config

import colorlog
from plaid import Client


accounts = None
items = None
client = None
filters = None
mappings = None

logger = logging.getLogger('ledger')


def initialize(path=None, verbose=False):
    global plaid, accounts, items, client, filters, mappings

    configure_logging(verbose)
    plaid = {
        'client_id': os.environ.get('PLAID_CLIENT_ID'),
        'secret': os.environ.get('PLAID_SECRET'),
        'public_key': os.environ.get('PLAID_PUBLIC_KEY'),
        'environment': os.environ.get('PLAID_ENV'),
    }

    with open(path, 'r') as f:
        config = yaml.load(f.read())
        if 'plaid' in config:
            plaid.update(config.get('plaid', {}))

    client = Client(**plaid)
    accounts = {a['id']: a for a in config['accounts']}
    items = {i['id']: i for i in config['items']}
    filters = config.get('filters', [])
    mappings = config.get('mappings', [])

    for a in accounts.values():
        item = get_item(a['item_id'])
        item.setdefault('accounts', []).append(a)
        a['item'] = item


def get_item(item_id):
    return items[item_id]


def get_account(account_id):
    if account_id not in accounts:
        logger.warn("unknown account {}".format(account_id))
    return accounts[account_id]


def configure_logging(verbose):
    log_level = 'DEBUG' if verbose else 'INFO'

    formatters = {
        'standard': {
            'class': 'colorlog.ColoredFormatter',
            'format':
                '[%(asctime)s %(name)s] %(log_color)s%(levelname)-8s%(reset)s %(message)s',
            'datefmt': '%H:%M:%S',
        }
    }

    handlers = {
        'default': {
            'level': 'NOTSET',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        }
    }

    loggers = {
        'ledger': {
            'handlers': ['default'],
            'level': log_level,
            'propagate': True,
        },
    }

    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': formatters,
        'handlers': handlers,
        'loggers': loggers,
    })

    logger.debug("logging initialized")
