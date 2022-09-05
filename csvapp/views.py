from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from .models import Amount
from django.http import HttpResponse , HttpResponseRedirect
from .models import Amount
import csv , io , os
from datetime import datetime
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.seasonal import STL
import pmdarima as pmd
import joblib
import math
import numpy as np


# Create your views here.
#@permission_required('admin.can_add_log_entry')

def decomposition(series):
    stl = STL(series)
    results = stl.fit()
    trend = results.trend
    return trend

def arraryResempling(array):
    dataAarray  = []
    for i,j in zip(np.array(array.index),array.values):
        t = [str(i).split('T')[0],j]
        dataAarray.append(t)
    return dataAarray 

def Auto_arima(series):
    df = decomposition(series)
    autoarima_model = pmd.auto_arima(df, 
                              start_p=2, 
                              start_q=2,
                              max_p=7,
                              max_q=8,
                              d=1,
                            trace=True)
    return autoarima_model.order
def ARIMA_MODEL(series , order):
    df = decomposition(series)
    model= ARIMA(df,order= order)
    model = model.fit()
    return model

def upload(request):
    template = "upload.html"
    data = Amount.objects.all()
    try:
        prompt = {
        'order': 'Order of the CSV should be : [ date , amount ]',
        'Amount': data}
        if request.method == "GET":
            return render(request, template, prompt)

        csv_file = request.FILES['file']
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'THIS IS NOT A CSV FILE')
            return  render(request, template, prompt)
        data_set = csv_file.read().decode('UTF-8')
    except:
        prompt = {
        'order': 'There must be some kind of Error try again with correct format. Order of the CSV should be : [ date , amount ]',
        'Amount': data}
        return render(request, template, prompt)
        
    io_string = io.StringIO(data_set)
    next(io_string)
    for column in csv.reader(io_string, delimiter=',', quotechar="|"):
        _, created = Amount.objects.update_or_create(
        date= pd.to_datetime(column[0]),
        amount=column[1])

    df = pd.DataFrame(list(Amount.objects.all().values('date', 'amount')))
    df['date'] = pd.to_datetime(df['date'])
    df1 = df.fillna(0,axis=0).set_index('date')['amount'].resample('D').sum()

    order =  Auto_arima(df1)
    model = ARIMA_MODEL(df1 , order)

    filename = "models/ARIMA.joblib"
    joblib.dump(model, filename )
    context = {'order':order,
                'AIC':math.floor(model.aic),
                'LogLiklyHood':math.floor(model.llf),
                'mae':math.floor(model.mae),
                'AICC':math.floor(model.aicc),
                'BIC':math.floor(model.bic)}
    
    
    return render(request , 'after_upload.html', context)

    

def forecast(request):
    filename = "models/ARIMA.joblib"
    model = joblib.load(filename)

    if request.method == "GET":
        fc = model.forecast(60)
        fc_dict = {'date':fc.index , 'Amount':fc.values}
        fc_df = pd.DataFrame(fc_dict)
        Daily  =  arraryResempling(fc.resample("D").sum())
        weekly =  arraryResempling(fc.resample("W").sum())
        monthly =  arraryResempling(fc.resample("M").sum())
        # Moving Averages
        day4 = arraryResempling(fc.rolling(4,min_periods=1).mean())
        week = arraryResempling(fc.rolling(7,min_periods=1).mean())
        week2 = arraryResempling(fc.rolling(14,min_periods=1).mean())
        month = arraryResempling(fc.rolling(30,min_periods=1).mean())
        context = {'columns':fc_df.columns,
                   'values': fc_df.values,
                   'Amount': fc_df['Amount'],
                   'date':fc_df['date'],
                   "weekly":weekly,"daily": Daily, "monthly":monthly,
                   "day4":day4,"week":week,"week2":week2,"month":month,
                   
                   
                   }
        return render(request , 'forecast.html' ,context )
    days = request.POST.get('days')
    fc = model.forecast(int(days))
    Daily  =  arraryResempling(fc.resample("D").sum())
    weekly =  arraryResempling(fc.resample("W").sum())
    monthly =  arraryResempling(fc.resample("M").sum())

    # Moving Averages

    day4 = arraryResempling(fc.rolling(4,min_periods=1).mean())
    week = arraryResempling(fc.rolling(7,min_periods=1).mean())
    week2 = arraryResempling(fc.rolling(14,min_periods=1).mean())
    month = arraryResempling(fc.rolling(30,min_periods=1).mean())
    fc_dict = {'date':fc.index , 'Amount':fc.values}
    fc_df = pd.DataFrame(fc_dict)
    context = {'columns':fc_df.columns,
               'values': fc_df.values,
               'Amount': fc_df['Amount'],
               'date':fc_df['date'],
               "weekly":weekly,"daily": Daily, "monthly":monthly,
               "day4":day4,"week":week,"week2":week2,"month":month,}
    return render(request , 'forecast.html' ,context ) 
    



    return render(request , 'test.html')