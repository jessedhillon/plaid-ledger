import re as regex
from datetime import datetime

from plaid_ledger.lib import Constants


Patterns = Constants(
    comment=regex.compile('\s+[;#%|*]+\s*(?P<comment>.*)'),
    metadata=regex.compile('(?P<key>[\w_-]+): (?P<value>.*)'),
    posting_with_amount=regex.compile('(?P<account>.*)\s\s+\$(?P<amount>[ -][0-9,\.]+)$'))


def is_headline(line):
    # the only line which can have a digit at position 0 is the headline
    return line[0].isdigit()


def is_comment(line):
    return Patterns.comment.match(line) is not None


def is_meta(comment):
    return Patterns.metadata.match(comment) is not None


def is_posting_with_amount(line):
    return Patterns.posting_with_amount.match(line) is not None


def parse_amount(s):
    return float(s.strip().replace(',', ''))


def parse_posting(line):
    line = line.strip()
    if is_posting_with_amount(line):
        m = Patterns.posting_with_amount.match(line).groupdict()
        amount = m['amount'].strip().replace(',', '')
        return {
            'account': m['account'].strip(),
            'amount': parse_amount(amount)
        }

    return {
        'account': line,
        'amount': None
    }


def parse_comment(line):
    return Patterns.comment.match(line).groupdict()


def parse_meta(comment):
    return Patterns.metadata.match(comment).groupdict()


def parse_headline(line):
    date, description = line.split(None, 1)
    return {
        'date': datetime.strptime(date, '%Y-%m-%d'),
        'description': description.strip()
    }
