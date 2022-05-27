from unittest import TestCase

from Entities.Rule import Rule


class TestRule(TestCase):

    def test_str(self):
        rule_0 = Rule('000')
        self.assertEqual('000', str(rule_0))
        rule_1 = Rule('001')
        self.assertEqual('001', str(rule_1))
        rule_2 = Rule('010')
        self.assertEqual('010', str(rule_2))
        rule_3 = Rule('011')
        self.assertEqual('011', str(rule_3))
        rule_4 = Rule('111100')
        self.assertEqual('111100', str(rule_4))
        rule_5 = Rule('11111101')
        self.assertEqual('11111101', str(rule_5))
