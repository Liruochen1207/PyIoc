from test.dao.paydao import Paydao


class PayImp(Paydao):
    def __init__(self, discount, c=2):
        self.discount = discount
        self.c = c
