from . import TestCase
from plaid_ledger import ledger


class TestCase(TestCase):
    def test_parse(self):
        lines = self.load_fixture('test_parse.ledger', lines=True)
        ledger_items = ledger.parse(lines)

        assert len(ledger_items) == 4
        items = sorted(ledger_items.values(),
                       key=lambda t: (t['date'], t['description'], t['id']))

        for item in items[:3]:
            assert 'Transaction-Id' in item['meta']
            assert len(item['sources']) == 1
            assert isinstance(item['sources'][0]['amount'], float)
            assert isinstance(item['target']['amount'], float)

        assert len(items[3]['sources']) == 2

    def test_is_headline(self):
        lines = self.load_fixture('test_parse.ledger', lines=True)

        assert ledger.parser.is_headline(lines[0])
        for line in lines[1:4]:
            assert not ledger.parser.is_headline(line)

    def test_is_comment(self):
        lines = self.load_fixture('test_parse.ledger', lines=True)
        comment = lines.pop(1)

        assert ledger.parser.is_comment(comment)
        for line in lines[0:4]:
            assert not ledger.parser.is_comment(line)

    def test_is_meta(self):
        lines = self.load_fixture('test_parse.ledger', lines=True)
        l = lines.pop(1)
        m = ledger.parser.parse_comment(l)
        assert ledger.parser.is_meta(m['comment'])

    def test_parse_comment(self):
        lines = self.load_fixture('test_parse.ledger', lines=True)
        m = ledger.parser.parse_comment(lines.pop(1))
        assert m['comment'] == "Transaction-Id: Lowg3NgAvnTKxR6QkyPAcVBDvYwrQ3fxyDdOJ"

    def test_parse_meta(self):
        lines = self.load_fixture('test_parse.ledger', lines=True)
        l = lines.pop(1)
        comment = ledger.parser.parse_comment(l)['comment']
        m = ledger.parser.parse_meta(comment)

        assert m['key'] == 'Transaction-Id'
        assert m['value'] == "Lowg3NgAvnTKxR6QkyPAcVBDvYwrQ3fxyDdOJ"
