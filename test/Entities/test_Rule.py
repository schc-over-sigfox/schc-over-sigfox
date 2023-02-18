from unittest import TestCase

from Entities.Rule import Rule


class TestRule(TestCase):

    def test_str(self):
        rule_0 = Rule('000')
        self.assertEqual('000', rule_0.STR)
        rule_1 = Rule('001')
        self.assertEqual('001', rule_1.STR)
        rule_2 = Rule('010')
        self.assertEqual('010', rule_2.STR)
        rule_3 = Rule('011')
        self.assertEqual('011', rule_3.STR)
        rule_4 = Rule('111100')
        self.assertEqual('111100', rule_4.STR)
        rule_5 = Rule('11111101')
        self.assertEqual('11111101', rule_5.STR)
