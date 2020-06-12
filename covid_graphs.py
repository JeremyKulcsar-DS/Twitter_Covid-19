# -*- coding: utf-8 -*-
"""
Created on Thu Apr 23 14:18:03 2020

@author: Jeremy
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

from statsmodels.tsa.arima_model import ARIMA

from selenium import webdriver
import time
import os

import tweepy

from datetime import datetime

import warnings
warnings.filterwarnings('ignore')

today = str(datetime.now().strftime('%d'))+'-'+str(datetime.now().strftime('%m'))+'-'+str(datetime.now().year)

# Waits for the given time
def download_wait(directory, timeout, nfiles=None):
    seconds = 0
    dl_wait = True
    while dl_wait and seconds < timeout:
        time.sleep(1)
        dl_wait = False
        files = os.listdir(directory)
        if nfiles and len(files) != nfiles:
            dl_wait = True

        for fname in files:
            if fname.endswith('.csv'):
                dl_wait = True

        seconds += 1
    return seconds

# Gets the source file
def open_direct_web(downloaded_file_dir):
    folder_path_slash = os.path.dirname(os.path.abspath(__file__)).replace("\\","/")
    
    print("Looking for previous datasource...")
    try:
        os.remove("timeseries.csv")
        print("Previous datasource removed")
    except:
        print("No previous datasource found")
    
    print("Reaching for the source URL...")
    url0 = "https://coronadatascraper.com/timeseries.csv"
    options = webdriver.ChromeOptions() 
    prefs = {"profile.default_content_settings.popups": 0,
    'download.default_directory' : downloaded_file_dir, "directory_upgrade": True}
    options.add_experimental_option('prefs', prefs)
    
    try:
        driver = webdriver.Chrome(executable_path=folder_path_slash+"/chromedriver.exe", chrome_options=options)
        driver.get(url0)
        download_wait(folder_path_slash,15,1)
        print("Downloaded the new datasource!")
    except:
        print("Couldn't download the new datasource :(")
    
    driver.quit()

# In case of emergency
def format_date(column):
    temp = column.str.split(pat = "/")
    temp2 = []
    for i in range(len(temp)):
        if len(temp[i][0]) == 1:
            temp[i][0] = '0' + temp[i][0]
        if len(temp[i][1]) == 1:
            temp[i][1] = '0' + temp[i][1]
        temp2.append(temp[i][0] + '/' + temp[i][1] + '/' + temp[i][2])
    return temp2

# Generates the graphs
def generate_graphs(country, threshold = 150):
    df = pd.read_csv('timeseries.csv')
    df_x = df[df['name'] == country].fillna(0)
    
    """
    #In case timeseries.csv is broken, here is another source
    df = pd.read_csv('covid_19_clean_complete.csv')
    df['Date'] = format_date(df['Date'])
    if country == "Hong Kong":
        df_x = df[df['Province/State'] == country].fillna(0)
    else:
        df_x = df[df['Country/Region'] == country].fillna(0)
    df_x = df_x.groupby('Date').agg(sum)[['Confirmed','Deaths','Recovered']]
    df_x['cases'] = df_x['Confirmed']
    df_x['recovered'] = df_x['Recovered']
    df_x['deaths'] = df_x['Deaths']
    df_x['date'] = df_x.reset_index('Date')['Date'].values
    """
    
    df_x['current'] = df_x['cases'] - df_x['recovered'] - df_x['deaths']
    df_x_drop = df_x[df_x['cases']>threshold]
    df_x_drop['diff'] = df_x_drop['cases'].diff()
    dates = df_x_drop['date']
    
    # --------------------------- Forecast with ARIMA ---------------------------
    try:
        confirmed_table = df_x_drop['cases'].values
        model = ARIMA(confirmed_table, order=(3,2,0))
        model_fit = model.fit(disp=0)
        output = model_fit.forecast()
        forecast_conf = output[0]
        confirmed_table = np.concatenate((confirmed_table, forecast_conf))
    except:
        forecast_conf = df_x_drop['cases'].values
        confirmed_table = np.append(df_x_drop['cases'].values, df_x_drop['cases'].values[0])
    
    try:
        current_table = df_x_drop['current'].values
        model = ARIMA(current_table, order=(3,2,0))
        model_fit = model.fit(disp=0)
        output = model_fit.forecast()
        forecast_curr = output[0]
        current_table = np.concatenate((current_table, forecast_curr))
    except:
        forecast_curr = df_x_drop['current'].values
        current_table = np.append(df_x_drop['current'].values, df_x_drop['current'].values[0])
    
    try:
        recovered_table = df_x_drop['recovered'].values
        model = ARIMA(recovered_table, order=(3,2,0))
        model_fit = model.fit(disp=0)
        output = model_fit.forecast()
        forecast_recov = output[0]
        recovered_table = np.concatenate((recovered_table, forecast_recov))
    except:
        forecast_recov = df_x_drop['recovered'].values
        recovered_table = np.append(df_x_drop['recovered'].values, df_x_drop['recovered'].values[0])
    
    try:
        deaths_table = df_x_drop['deaths'].values
        model = ARIMA(deaths_table, order=(3,2,0))
        model_fit = model.fit(disp=0)
        output = model_fit.forecast()
        forecast_death = output[0]
        deaths_table = np.concatenate((deaths_table, forecast_death))   
    except:
        forecast_death = df_x_drop['deaths'].values
        deaths_table = np.append(df_x_drop['deaths'].values, df_x_drop['deaths'].values[0])
        
    # --------------------------- Evolution of COVID-19 ---------------------------
    plt.figure()
    # # ----------- Figure 1 -----------
    fig, (ax1, ax2) = plt.subplots(nrows = 2, ncols = 1, figsize=(14,10))
    ax1.plot(confirmed_table, color = 'tab:blue', marker = 'o', lw=1)
    ax1.plot(current_table, color = 'tab:orange', marker = 'o', lw=1)
    ax1.plot(recovered_table, color = 'tab:green', marker = 'o', lw=1)
    ax1.plot(deaths_table, color = 'tab:red', marker = 'o', lw=1)
    df_x_drop.set_index('date')['cases'].plot(kind = 'line', label = 'Confirmed cases (people who tested positive)', legend = True, lw=4, color = 'tab:blue', ax=ax1)
    df_x_drop.set_index('date')['current'].plot(kind = 'line', label = 'Currently active cases (positive, not recovered nor dead)', legend = True, lw=4, color = 'tab:orange', ax=ax1)
    df_x_drop.set_index('date')['recovered'].plot(kind = 'line', label = 'Recovered (previously positive, now negative)', legend = True, lw=4, color = 'tab:green', ax=ax1)
    df_x_drop.set_index('date')['deaths'].plot(grid = True, kind = 'line', label = 'Deaths (died while being positive)', legend = True, title = "Evolution of COVID-19 in {} as of {}".format(country,today), lw=4, color = 'tab:red', ax=ax1).set_xlabel("")
    
    # # ----------- Figure 2 -----------
    df_x_drop.set_index('date')['diff'].shift(-1).plot(kind = 'bar', color = 'tab:blue', title = "New cases per day in {} as of {}".format(country,today), ax=ax2).set_xlabel("")
    ax2.set_ylim(ymin=0)
    
    ticklabels = ['']*len(df_x_drop)
    skip = len(df_x_drop)//7
    ticklabels[::skip] = df_x_drop['date'].astype("datetime64").iloc[::skip].dt.strftime('%Y-%m-%d')
    ax2.xaxis.set_major_formatter(mticker.FixedFormatter(ticklabels))
    def fmt(x, pos=0, max_i=len(ticklabels)-1):
        i = int(x) 
        i = 0 if i < 0 else max_i if i > max_i else i
        return dates[i]
    ax2.fmt_xdata = fmt
    ax2.tick_params(labelrotation=0)
    
    # # ----------- Save it -----------
    plt.savefig("evolution_{}_{}.png".format(country, today))
    
    return \
    int(df_x_drop['cases'].values[-1]), \
    int(df_x_drop['cases'].values[-1] - df_x_drop['cases'].values[-2]), \
    int(df_x_drop['current'].values[-1]), \
    int(df_x_drop['current'].values[-1] - df_x_drop['current'].values[-2]), \
    int(df_x_drop['recovered'].values[-1]), \
    int(df_x_drop['recovered'].values[-1] - df_x_drop['recovered'].values[-2]), \
    int(df_x_drop['deaths'].values[-1]), \
    int(df_x_drop['deaths'].values[-1] - df_x_drop['deaths'].values[-2]), \
    int(forecast_conf[0] - df_x_drop['cases'].values[-1]), \
    int(forecast_curr[0] - df_x_drop['current'].values[-1]), \
    int(forecast_recov[0] - df_x_drop['recovered'].values[-1]), \
    int(forecast_death[0] - df_x_drop['deaths'].values[-1])
    

# Posts the graphs
def post_graph(country, forecast_cases):
    
    # Consumer keys and access tokens
    consumer_key = 'mLhqSwCo0QzPetvyqXnuaqv9M'
    consumer_secret = 'HcOsJycgN9u8IKqct6k7OvTMR6Fjb0bfx1Y6AMOtOgxmtsdqOK'
    access_token = '1254380788281495552-QtJYhKhY8N9TKrsP8Z5ZNwYgZ31PY5'
    access_token_secret = '1vODLDbWXaY4UoMEqSWTvlQDK0nwXvHpZn1SkifhhpZ4d'
     
    # OAuth
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
     
    # Instance the API
    api = tweepy.API(auth)
    
    # Test authentication
    try:
        api.verify_credentials()
        print("Published the tweet for {}!".format(country))
    except:
        print("Error during authentication")
    
    # Load the image
    imagePath = "C:/Users/Jeremy/Desktop/COVID/Script/evolution_{}_{}.png".format(country, today)
    if forecast_cases[9] > 0:
        status = "#Data for #COVID19 in #{} on {} \n\nAs of today: \n{:,d} confirmed cases ({:+,d}) \n{:,d} currently active cases ({:+,d}) \n{:,d} recovered ({:+,d}) \n{:,d} deaths ({:+,d}) \n\nForecasts for tomorrow: \n{:,d} new cases \n{:,d} new active cases \n{:,d} recoveries \n{:,d} deaths".format(country.replace(" ", ""), today, forecast_cases[0], forecast_cases[1],forecast_cases[2],forecast_cases[3],forecast_cases[4],forecast_cases[5],forecast_cases[6],forecast_cases[7],forecast_cases[8],forecast_cases[9],forecast_cases[10],forecast_cases[11])
    else:
        status = "#Data for #COVID19 in #{} on {} \n\nAs of today: \n{:,d} confirmed cases ({:+,d}) \n{:,d} currently active cases ({:+,d}) \n{:,d} recovered ({:+,d}) \n{:,d} deaths ({:+,d}) \n\nForecasts for tomorrow: \n{:,d} new cases \n{:,d} less active cases \n{:,d} recoveries \n{:,d} deaths".format(country.replace(" ", ""), today, forecast_cases[0], forecast_cases[1],forecast_cases[2],forecast_cases[3],forecast_cases[4],forecast_cases[5],forecast_cases[6],forecast_cases[7],forecast_cases[8],np.absolute(forecast_cases[9]),forecast_cases[10],forecast_cases[11])
    
    # Send the tweet
    api.update_with_media(imagePath, status)
    
# Generate and post on Twitter
def generate_and_post():  
    # Italy
    try:
        forecast_italy = generate_graphs('Italy')
        post_graph('Italy', forecast_italy)
    except:
        pass

    # Spain
    try:
        forecast_spain = generate_graphs('Spain')
        post_graph('Spain', forecast_spain)
    except:
        pass

    # Thailand
    try:
        forecast_thailand = generate_graphs('Thailand')
        post_graph('Thailand', forecast_thailand)
    except:
        pass
    
    # Hong Kong
    try:
        forecast_hongkong = generate_graphs('Hong Kong')
        post_graph('Hong Kong', forecast_hongkong)
    except:
        pass
    
    # Germany
    try:
        forecast_germany = generate_graphs('Germany')
        post_graph('Germany', forecast_germany)
    except:
        pass
    
    # France
    try:
        forecast_france = generate_graphs('France')
        post_graph('France', forecast_france)
    except:
        pass
    
# Pipeline
def execute():
    folder_path = os.path.dirname(os.path.abspath(__file__))
    open_direct_web(r'{}'.format(folder_path))
    
    generate_and_post()