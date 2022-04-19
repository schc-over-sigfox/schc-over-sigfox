from unittest import TestCase

from Entities.Rule import Rule


class TestRule(TestCase):

    def test_str(self):
        rule_0 = Rule(0, 0)
        self.assertEqual('000', str(rule_0))
        rule_1 = Rule(1, 0)
        self.assertEqual('001', str(rule_1))
        rule_2 = Rule(2, 0)
        self.assertEqual('010', str(rule_2))
        rule_3 = Rule(3, 0)
        self.assertEqual('011', str(rule_3))
        rule_4 = Rule(4, 1)
        self.assertEqual('000100', str(rule_4))
        rule_5 = Rule(5, 2)
        self.assertEqual('00000101', str(rule_5))
