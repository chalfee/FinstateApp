import copy

import requests
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.utils.encoding import force_text, force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.auth import login as lgn
from django.contrib.auth.models import User


from .forms import RegisterForm, UploadFileForm, HoldingRegistrationForm, FactoryRegistrationForm
from .models import *
import pandas as pd
import datetime
import logging

from .token import account_activation_token

logger = logging.getLogger(__name__)


def main(request):
    if request.user.is_authenticated:
        data = {}
        try:
            holding_data = Holding.objects.get(owner=request.user.id)
        except:
            holding_data = None
        if holding_data:
            data['holding'] = holding_data
            data['factories'] = []
            for f in holding_data.factory_set.all():
                if f.digitalindex_set.all():
                    factory_data = __make_data_for_facrory(f)
                    data['factories'].append([f, factory_data])
                else:
                    data['factories'].append([f, False])
            return render(request, 'finstateapp/main.html', {'data': data})
        else:
            data['holding_registration_form'] = HoldingRegistrationForm()
            return render(request, 'finstateapp/main.html', {'data': data})
    else:
        if request.method == 'POST':
            form = UploadFileForm(request.POST, request.FILES)
            if form.is_valid():
                factory = __create_fiction_factory(request)
                __parse_excel_file(request, factory)
                return redirect('reports')
        else:
            form = UploadFileForm()
        return render(request, 'finstateapp/main.html', {'form': form})


@login_required
def holding_registration(request):
    if request.method == 'POST':
        user = User.objects.get(id=request.user.id)
        holding_obj = Holding()
        holding_obj.name = request.POST['name']
        holding_obj.owner = user
        holding_obj.save()
    return redirect('/')


@login_required
def add_factory(request, holding_id):
    if request.method == 'POST':
        holding_obj = Holding.objects.get(id=holding_id)
        factory_obj = _create_factory(request, holding_obj)
        start_date = factory_obj.digitalindex_set.filter(name='Ivolume of sold').order_by('date')[0].date
        end_date = list(factory_obj.digitalindex_set.filter(name='Ivolume of sold').order_by('date'))[-1].date
        factory_obj.make_reports(start_date, end_date)
        return redirect('/')
    else:
        factory_registration_form = FactoryRegistrationForm(initial={'symbol': 'None'})
        return render(request, 'finstateapp/create_factory.html',
                      {'factory_registration_form': factory_registration_form})


def reports(request):
    try:
        factory_obj = Factory.objects.get(name='fictionFactory')
        start_date = factory_obj.digitalindex_set.filter(name='Ivolume of sold').order_by('date')[0].date
        end_date = list(factory_obj.digitalindex_set.filter(name='Ivolume of sold').order_by('date'))[-1].date
        factory_obj.holding.make_reports(start_date, end_date)
        data = __create_data_for_reports_page(factory_obj, start_date, end_date)
        factory_obj.holding.delete()
        return render(request, 'finstateapp/reports.html', {'data': data})
    except:
        return redirect('/')


def factory(request):
    return render(request, 'finstateapp/factory.html')


def login(request):
    return render(request, 'finstateapp/login.html')


def register(response):
    if response.method == 'POST':
        form = RegisterForm(response.POST)
        if form.is_valid():
            form.save()
            user_data = User.objects.get(username=form.cleaned_data.get('username'))
            user_data.is_active = False
            user_data.save()
            logger.info("User {} successfully registered".format(user_data.username))
            _send_mail_to(response, user_data)
            return redirect('/')
    else:
        form = RegisterForm()
    return render(response, 'finstateapp/registration.html', {'form': form})


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        print(uid)
        user_data = User.objects.get(pk=uid)
        print(user_data.username)
    except:
        user_data = None

    if user_data is not None and account_activation_token.check_token(user_data, token):
        user_data.is_active = True
        user_data.save()
        lgn(request, user_data, backend='django.contrib.auth.backends.ModelBackend')
        return redirect('/')
    else:
        return redirect('/register/')


def _create_factory(request, holding_obj):
    factory_obj = Factory()
    factory_obj.name = request.POST['name']
    factory_obj.symbol = request.POST['symbol']
    factory_obj.requisites = request.POST['requisites']
    factory_obj.phone = request.POST['phone']
    factory_obj.manager = holding_obj.owner
    factory_obj.holding = holding_obj
    factory_obj.save()
    __parse_excel_file(request, factory_obj)
    return factory_obj


def __create_fiction_factory(request):
    user = User.objects.get(username='a')
    holding = Holding(name='fictionHolding', owner=user)
    holding.save()
    factory = Factory(name='fictionFactory', requisites='', phone='', manager=user, holding=holding)
    factory.save()
    return factory


def __parse_data_to_objects(data, factory):
    for i in range(0, data['average check'].size):
        date = __parse_date(data['date'][i])
        index = DigitalIndex(value=data['average check'][i], name='Iaverage check',
                             factory=factory, date=date)
        index.save()
        index = DigitalIndex(value=data['volume of sold'][i], name='Ivolume of sold',
                             factory=factory, date=date)
        index.save()
        index = DigitalIndex(value=data['cost price'][i], name='Icost price',
                             factory=factory, date=date)
        index.save()
        index = DigitalIndex(value=data['selling expenses'][i], name='Iselling expenses',
                             factory=factory, date=date)
        index.save()
        index = DigitalIndex(value=data['other operating expenses'][i], name='Iother operating expenses',
                             factory=factory, date=date)
        index.save()
        index = DigitalIndex(value=data['other expenses'][i], name='Iother expenses',
                             factory=factory, date=date)
        index.save()
        index = DigitalIndex(value=data['other income'][i], name='Iother income',
                             factory=factory, date=date)
        index.save()
        index = DigitalIndex(value=data['income tax'][i], name='Iincome tax',
                             factory=factory, date=date)
        index.save()
        index = DigitalIndex(value=data['non-cash expenses'][i], name='Cnon-cash expenses',
                             factory=factory, date=date)
        index.save()
        index = DigitalIndex(value=data['non-cash income'][i], name='Cnon-cash income',
                             factory=factory, date=date)
        index.save()
        index = DigitalIndex(value=data['stock acquisition'][i], name='Cstock acquisition',
                             factory=factory, date=date)
        index.save()
        index = DigitalIndex(value=data['advances paid'][i], name='Cadvances paid',
                             factory=factory, date=date)
        index.save()
        index = DigitalIndex(value=data['advances received'][i], name='Cadvances received',
                             factory=factory, date=date)
        index.save()


def __parse_semicolon_statement(data):
    d = {}
    data = data.split(';')
    for i in data:
        d[i.split(':')[0]] = float(i.split(':')[1])
    return d


def __parse_assets(data, factory):
    data = __parse_semicolon_statement(data)
    for key in data.keys():
        assets = Assets(name=key, value=data[key], factory=factory)
        assets.save()


def __parse_liabilities(data, factory):
    data = __parse_semicolon_statement(data)
    for key in data.keys():
        liabilities = Liabilities(name=key, value=data[key], factory=factory)
        liabilities.save()


def __parse_excel_file(request, factory):
    data = pd.read_excel(request.FILES['file'])
    __parse_data_to_objects(data, factory)
    for i in range(data['assets'].size):
        __parse_assets(data['assets'][i], factory)
    for i in range(data['liabilities'].size):
        __parse_liabilities(data['liabilities'][i], factory)
    logger.info("File uploaded successfully")


def __create_data_for_reports_page(factory_obj, start_data, end_data):
    assets, liabilities = __combine_assets_and_liabilities(factory_obj,
                                                           start_data, end_data)
    return {
        'start_date': factory_obj.incomestatementreport_set.all()[0].start_date,
        'end_date': factory_obj.incomestatementreport_set.all()[0].end_date,
        'revenue': factory_obj.incomestatementreport_set.all()[0].revenue,
        'gross_profit': factory_obj.incomestatementreport_set.all()[0].gross_profit,
        'operating_income': factory_obj.incomestatementreport_set.all()[0].operating_income,
        'income_before_tax': factory_obj.incomestatementreport_set.all()[0].income_before_tax,
        'net_income': factory_obj.incomestatementreport_set.all()[0].net_income,
        'operating_cash_flow': factory_obj.cashflowstatementreport_set.all()[0].operating_cash_flow,
        'cash_from_operations': factory_obj.cashflowstatementreport_set.all()[0].cash_from_operations,
        'cash_net_income': factory_obj.cashflowstatementreport_set.all()[0].cash_net_income,
        'assets': factory_obj.balancereport_set.all()[0].assets,
        'liabilities': factory_obj.balancereport_set.all()[0].liabilities,
        'assets_dict': assets,
        'liabilities_dict': liabilities,
    }


def __combine_assets_and_liabilities(factory, start_date, end_date):
    data = ({}, {})
    for assets in factory.get_assets().filter(date__range=[start_date, end_date]):
        if assets.name in data[0]:
            data[0][assets.name] += assets.value
        else:
            data[0][assets.name] = assets.value
    for liabilities in factory.get_liabilities().filter(date__range=[start_date, end_date]):
        if liabilities.name in data[1]:
            data[1][liabilities.name] += liabilities.value
        else:
            data[1][liabilities.name] = liabilities.value
    return data


def __parse_date(date):
    return datetime.datetime.strptime(date, '%d.%m.%Y').date()


def _send_mail_to(request, user_data):
    current_site = get_current_site(request)
    subject = 'Please Activate Your Account'
    message = render_to_string('email.html', {
        'user': user_data,
        'domain': current_site.domain,
        'uid': urlsafe_base64_encode(force_bytes(user_data.pk)),
        'token': account_activation_token.make_token(user_data),
    })
    logger.info("Successful sent message to {}".format(user_data))
    user_data.email_user(subject, message)


def __get_stock_price(symbol):
    url = "https://alpha-vantage.p.rapidapi.com/query"

    querystring = {"symbol": symbol, "function": "GLOBAL_QUOTE"}

    headers = {
        'x-rapidapi-host': "alpha-vantage.p.rapidapi.com",
        'x-rapidapi-key': "b5034b71afmshf6154bd4cd6fdc1p18f532jsndf498b614c3a"
    }

    response = requests.request("GET", url, headers=headers, params=querystring)

    # return response.json()['Global Quote']['02. open']


def __make_data_for_facrory(f):
    factory_data = {
        'dates': '',
        'revenue': '',
        'net_income': '',
        'assets': '',
        'liabilities': '',
        'cash_from_operations': '',
        'cash_net_income': '',
    }
    for index in f.digitalindex_set.filter(name='Ivolume of sold').order_by('date'):
        factory_data['dates'] += ',' + str(index.date)
        f.make_reports(index.date, index.date)

        report = copy.copy(list(f.incomestatementreport_set.order_by('id'))[-1])
        list(f.incomestatementreport_set.order_by('id'))[-1].delete()
        factory_data['revenue'] += ',' + str(report.revenue)
        factory_data['net_income'] += ',' + str(report.net_income)

        report = copy.copy(list(f.balancereport_set.order_by('id'))[-1])
        list(f.balancereport_set.order_by('id'))[-1].delete()
        factory_data['assets'] += ',' + str(report.assets)
        factory_data['liabilities'] += ',' + str(report.liabilities)

        report = copy.copy(list(f.cashflowstatementreport_set.order_by('id'))[-1])
        list(f.cashflowstatementreport_set.order_by('id'))[-1].delete()
        factory_data['cash_from_operations'] += ',' + str(report.cash_from_operations)
        factory_data['cash_net_income'] += ',' + str(report.cash_net_income)
    for k in factory_data.keys():
        factory_data[k] = factory_data[k][1:]
    return factory_data
