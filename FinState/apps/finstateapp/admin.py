from django.contrib import admin

from . import models

admin.site.register(models.Holding)
admin.site.register(models.Factory)
admin.site.register(models.DigitalIndex)
admin.site.register(models.Assets)
admin.site.register(models.Liabilities)
admin.site.register(models.BalanceReport)
admin.site.register(models.CashFlowStatementReport)
admin.site.register(models.IncomeStatementReport)
