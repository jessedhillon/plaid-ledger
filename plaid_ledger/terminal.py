import json
import pprint
from datetime import datetime
from json import JSONEncoder

import pygments
from pygments import lexers, formatters
from pygments.token import Token
from pygments.style import Style


class Encoder(JSONEncoder):
    def default(self, v):
        if isinstance(v, datetime):
            return v.strftime('%Y-%m-%d')
        return super(JSONEncoder, self).default(v)


class TerminalStyle(Style):
    styles ={
        Token.Punctuation: '#ansiblack',
        Token.Name.Tag: '#ansiteal',
        Token.Literal.String.Double: '#ansibrown',
        Token.Keyword.Constant: '#ansipurple',
        Token.Number: '#ansilightgray',
    }


def format_json(obj):
    serialized = json.dumps(obj, cls=Encoder, sort_keys=True, indent=2)
    return pygments.highlight(serialized, lexers.JsonLexer(),
            formatters.Terminal256Formatter(style=TerminalStyle))
