from django.db import models
from django.contrib.auth.models import User
import datetime


class Holding(models.Model):
    name = models.CharField('Holding name', max_length=100)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    def make_reports(self, start_date, end_date):
        for factory in self.factory_set.all():
            factory.make_reports(start_date, end_date)


class Factory(models.Model):
    name = models.CharField('Factory name', max_length=100)
    requisites = models.CharField('Factory requisites', max_length=100)
    symbol = models.CharField('Factory requisites', max_length=10)
    phone = models.CharField('Phone number', max_length=13)
    manager = models.ForeignKey(User, on_delete=models.CASCADE)
    holding = models.ForeignKey(Holding, on_delete=models.CASCADE)
    is_reported_already = models.BooleanField(default=False)

    def make_reports(self, start_date, end_date):
        income_statement_report = IncomeStatementReport(factory=self,
                                                        start_date=start_date, end_date=end_date)
        income_statement_report.save()
        net_income = income_statement_report.make_report(self.__data_for_incomestatementreport())
        cash_flow_statement_report = CashFlowStatementReport(factory=self,
                                                             start_date=start_date, end_date=end_date)
        cash_flow_statement_report.save()
        cash_flow_statement_report.make_report({'data': self.__data_for_cashflowstatementreport(),
                                             'net_income': net_income})
        balance_report = BalanceReport(factory=self,
                                       start_date=start_date, end_date=end_date)
        balance_report.save()
        balance_report.make_report(self.__data_for_balancereport())

    def __data_for_incomestatementreport(self):
        if self.digitalindex_set:
            return self.digitalindex_set.all().filter(name__startswith='I')
        else:
            return None

    def __data_for_cashflowstatementreport(self):
        if self.digitalindex_set:
            return self.digitalindex_set.all().filter(name__startswith='C')
        else:
            return None

    def __data_for_balancereport(self):
        if self.assets_set or self.liabilities_set:
            return self.get_assets(), self.get_liabilities()
        else:
            return None

    def get_assets(self):
        return self.assets_set.all()

    def get_liabilities(self):
        return self.liabilities_set.all()


class Index(models.Model):
    INDEX_UNITS = [
        ('USD', 'USD'),
        ('EUR', 'EUR'),
        ('BLR', 'BLR'),
    ]
    value = models.FloatField('Value', default=0)
    units = models.CharField('Units', choices=INDEX_UNITS, max_length=3, default='BLR')
    date = models.DateField('Report calculation date', default=datetime.date.today)


class DigitalIndex(Index):
    INDEX_NAMES = [
        ('Ivolume of sold', 'volume of sold(объем продаж)'),
        ('Iaverage check', 'average check(средний чек)'),
        ('Icost price', 'cost price(себестоимость)'),
        ('Iselling expenses', 'selling expenses(упаковка, доставка, аренда, зарплата)'),
        ('Iother operating expenses', 'other operating expenses'),
        ('Iother expenses', 'other expenses(проценты по кредитам, штрафы)'),
        ('Iother income', 'other income(проценты по вкладам, безвозмездное получение активов)'),
        ('Iincome tax', 'income tax'),
        ('Cnon-cash expenses', 'non-cash expenses'),
        ('Cnon-cash income', 'non-cash income'),
        ('Cstock acquisition', 'stock acquisition(приобретение запасов)'),
        ('Cadvances paid', 'advances paid(оплата услуг раньше срока)'),
        ('Cadvances received', 'advances received(получение за услуги до срока)'),
    ]
    factory = models.ForeignKey(Factory, on_delete=models.CASCADE)
    name = models.CharField('Name', choices=INDEX_NAMES, max_length=100)


class Assets(Index):
    factory = models.ForeignKey(Factory, on_delete=models.CASCADE)
    name = models.CharField('Name', max_length=100)
    description = models.CharField('Description', max_length=200, default='')


class Liabilities(Index):
    factory = models.ForeignKey(Factory, on_delete=models.CASCADE)
    name = models.CharField('Name', max_length=100)
    description = models.CharField('Description', max_length=200, default='')


class ReportInterface:
    def make_report(self, data):
        pass


class Report(models.Model, ReportInterface):
    start_date = models.DateField('Stare report calculation date', default=datetime.date.today)
    end_date = models.DateField('End report calculation date', default=datetime.date.today)


class IncomeStatementReport(Report):
    factory = models.ForeignKey(Factory, on_delete=models.CASCADE)
    name = 'Income Statement Report'
    revenue = models.FloatField('Revenue', default=0)
    gross_profit = models.FloatField('Gross profit', default=0)
    operating_income = models.FloatField('Operating income', default=0)
    income_before_tax = models.FloatField('Income before tax', default=0)
    net_income = models.FloatField('Net income', default=0)

    def make_report(self, data):
        if data is not None:
            data = data.filter(date__range=[self.start_date, self.end_date])
            for i in range(0, len(data.filter(name='Ivolume of sold'))):
                self.revenue += data.filter(name='Ivolume of sold')[i].value *\
                                data.filter(name='Iaverage check')[i].value
            self.gross_profit = self.revenue - sum(c.value for c in data.filter(name='Icost price'))
            self.operating_income = self.gross_profit - sum(c.value for c in data.filter(name='Iselling expenses')) -\
                                    sum(c.value for c in data.filter(name='Iother operating expenses'))
            self.income_before_tax = self.operating_income + sum(c.value for c in data.filter(name='Iother income')) -\
                                     sum(c.value for c in data.filter(name='Iother expenses'))
            self.net_income = self.income_before_tax - sum(c.value for c in data.filter(name='Iincome tax'))
            self.save()
            return self.net_income


class BalanceReport(Report):
    factory = models.ForeignKey(Factory, on_delete=models.CASCADE)
    name = 'Balance Report'
    assets = models.FloatField('Assets cost', default=0)
    liabilities = models.FloatField('Liabilities cost', default=0)

    def make_report(self, data):
        if data is not None:
            assets, liabilities = data
            for a in assets.filter(date__range=[self.start_date, self.end_date]):
                self.assets += a.value
            for l in liabilities.filter(date__range=[self.start_date, self.end_date]):
                self.liabilities += l.value
            self.save()


class CashFlowStatementReport(Report):
    factory = models.ForeignKey(Factory, on_delete=models.CASCADE)
    name = 'Cash Flow Statement Report'
    operating_cash_flow = models.FloatField('Operating cash flow', default=0)
    cash_from_operations = models.FloatField('Cash from operations', default=0)
    cash_net_income = models.FloatField('Cash net income', default=0)

    def make_report(self, data):
        d = data['data'].filter(date__range=[self.start_date, self.end_date])
        net_income = data['net_income']
        if data is not None:
            self.operating_cash_flow = net_income
            self.cash_net_income = self.operating_cash_flow -\
                                   sum(c.value for c in d.filter(name='Cnon-cash expenses')) +\
                                   sum(c.value for c in d.filter(name='Cnon-cash income'))
            self.cash_from_operations = self.cash_net_income -\
                                        sum(c.value for c in d.filter(name='Cstock acquisition')) -\
                                        sum(c.value for c in d.filter(name='Cadvances paid')) +\
                                        sum(c.value for c in d.filter(name='Cadvances received'))

            self.save()
