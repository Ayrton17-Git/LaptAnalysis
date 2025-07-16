import pandas as pd
from pandas import DataFrame
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
from os import path
import matplotlib.image as mpimg
import tkinter as tk
from tkinter import filedialog
import datetime
from dash import Dash, dcc, html, dash_table, Input, Output, State,exceptions
import dash_bootstrap_components as dbc
import threading
import webbrowser
import plotly.io as pio
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import os
import subprocess
from dash.exceptions import PreventUpdate
import plotly.express as px

pd.options.mode.chained_assignment = None

# 1. Carica i dataframe
df = pd.read_csv("df.csv")
Results = pd.read_csv("results.csv")
info = pd.read_csv("info.csv")
Pit=pd.read_csv('PitStopFile.csv')

# DATA_DIR = 'C:/Users/Inca9/OneDrive - SRO/2025 Technical SRO/Events/2025/GT3/GTWCE/20250629 - R05 24h Spa/02_Results/05_R/24h'
# EL_DIR='C:/Users/Inca9/OneDrive - SRO/2025 Technical SRO/Events/2025/GT3/GTWCE/20250629 - R05 24h Spa/01_Documents'
# OUT_DIR='C:/Users/Inca9/OneDrive - SRO/2025 Technical SRO/Events/2025/GT3/GTWCE/_Documents'


# el= pd.read_csv(path.join(EL_DIR, 'EL.csv'))
# res_xls=pd.read_excel(path.join(DATA_DIR, 'ResultListXLS.xlsx'))
Results=Results.replace(['Silver Cup','Pro Cup', 'Bronze Cup', 'Gold Cup', 'Pro-AM Cup'], ['SILVER','PRO', 'BRONZE', 'GOLD','PRO-AM'])
el=Results[['Bib','Driver1', 'Driver2', 'Driver3', 'Driver4', 'CarName', 'TeamName','ClassName']]
el.columns=['Car No.','Driver1', 'Driver2', 'Driver3', 'Driver4', 'Car', 'Team','Category']

CarNumber=info['Car'].iloc[0]
Session_Selected=info['Sessione'].iloc[0]

#### creo lista risultati

def normalize_time_format(series):
    def normalize_single(t):
        parts = t.split(":")
        if len(parts) == 3:
            # hh:mm:ss.d
            h, m, s = parts
            s = f"{float(s):06.3f}"
            return f"{int(h):02d}:{int(m):02d}:{s}"
        elif len(parts) == 2:
            # mm:ss.d
            m, s = parts
            s = f"{float(s):06.3f}"
            return f"{int(m):02d}:{s}"
        else:
            raise ValueError(f"Formato non valido: {t}")

    return series.apply(normalize_single)

def convert_time_series_to_seconds(series):
    counts = series.str.count(':')
    
    result = pd.Series(index=series.index, dtype=float)

    # Formato hh:mm:ss.d (due ":")
    if (counts == 2).any():
        s_hms = series[counts == 2].str.split(':', expand=True)
        result.loc[counts == 2] = (
            s_hms[0].astype(int) * 3600 +
            s_hms[1].astype(int) * 60 +
            s_hms[2].astype(float)
        )

    # Formato mm:ss.d (uno ":")
    if (counts == 1).any():
        s_ms = series[counts == 1].str.split(':', expand=True)
        result.loc[counts == 1] = (
            s_ms[0].astype(int) * 60 +
            s_ms[1].astype(float)
        )

    return result

Results['TotalTime']=normalize_time_format(Results['TotalTime'])
Results['BestLapTime']=normalize_time_format(Results['BestLapTime'])

Results['TotalTimeS']=round(convert_time_series_to_seconds(Results['TotalTime']),3)
Results['BestLapS']=round(convert_time_series_to_seconds(Results['BestLapTime']),3)

# res_xls['TotalTimeS']=86400*res_xls['TotalTime']
# res_xls['BestLapS']=86400*res_xls['BestLapTime']

Diff_calc=[]
Gap_calc=[]

## Variabile che se è 0 significa FP o Q, se è 1 significa che è Race... DA CAMBIARE PRIMA DI GARA 1!!!

if Session_Selected=="Race":
    Session=1
else: 
    Session=0

## Inserire qui sotto il numero totale di Stint della gara!!
# StintNumber=2

if Session==0:  
    for i in range(0,len(Results)):
        if i==0:
            Diff=0
            Gap=0
        else:
            Gap=round((Results['BestLapS'].iloc[i]-Results['BestLapS'].iloc[i-1]),3)
            Diff=round((Results['BestLapS'].iloc[i]-Results['BestLapS'].iloc[0]),3)
        Gap_calc.append(Gap)
        Diff_calc.append(Diff)

else:
    for i in range(0,len(Results)):
        if i==0:
            Diff=0
            Gap=0
        else:
            if Results['LapCount'].iloc[i]-Results['LapCount'].iloc[i-1]==0:
                Gap=round((Results['TotalTimeS'].iloc[i]-Results['TotalTimeS'].iloc[i-1]),3)
                Diff=round((Results['TotalTimeS'].iloc[i]-Results['TotalTimeS'].iloc[0]),3)
                if Diff<0:
                    Diff='Lapped'
            else:
                Gap ='Lapped'
                Diff='Lapped'
        Gap_calc.append(Gap)
        Diff_calc.append(Diff)

Results['Gap Calc']=Gap_calc
Results['Diff Calc']=Diff_calc

res_OV=Results[['Rank', 'Bib', 'ClassName', 'Driver1', 'Driver2', 'Driver3', 'CarName', 'TeamName','LapCount','TotalTimeS', 'BestLapS','Gap Calc','Diff Calc']]
res_OV.columns=['Rank', 'Car No.', 'Category', 'Driver 1', 'Driver 2', 'Driver 3', 'Car', 'Team','Laps','TotalTimeS', 'BestLapS','Gap','Diff']

def ClassResultsDEF(db,Class):
    DiffinClass=[]
    GapinClass=[]
    if Session==0:
        res_OV_class=db[['Car No.','Category','Laps','BestLapS']]
        is_class=res_OV_class['Category']==Class
        ClassResults=res_OV_class[is_class].reset_index()
        DiffTotal=ClassResults['BestLapS']
        for i in range(0,len(ClassResults)):
            if i==0:
                Diff=0
                Gap=0
            else:
                Gap=round((DiffTotal.iloc[i]-DiffTotal.iloc[i-1]),3)
                Diff=round((DiffTotal.iloc[i]-DiffTotal.iloc[0]),3)
            GapinClass.append(Gap)
            DiffinClass.append(Diff)
    else:
        res_OV_class=db[['Car No.','Category','Laps','TotalTimeS']]
        is_class=res_OV_class['Category']==Class
        ClassResults=res_OV_class[is_class].reset_index()
        DiffTotal=ClassResults['TotalTimeS']
        for i in range(0,len(ClassResults)):
            if i==0:
                Diff=0
                Gap=0
            else:
                if ClassResults['Laps'].iloc[i]-ClassResults['Laps'].iloc[i-1]==0:
                    Gap=round((DiffTotal.iloc[i]-DiffTotal.iloc[i-1]),3)
                    Diff=round((DiffTotal.iloc[i]-DiffTotal.iloc[0]),3)
                    if Diff<0:
                        Diff='Lapped'
                else:
                    Gap ='Lapped'
                    Diff='Lapped'
            GapinClass.append(Gap)
            DiffinClass.append(Diff)

    ClassResults['Gap in Class']=GapinClass
    ClassResults['Diff in Class']=DiffinClass
    
    return ClassResults

ResultsPRO=ClassResultsDEF(res_OV,'PRO')
ResultsGOLD=ClassResultsDEF(res_OV,'GOLD')
ResultsSILVER=ClassResultsDEF(res_OV,'SILVER')
ResultsBRONZE=ClassResultsDEF(res_OV,'BRONZE')
ResultsPROAM=ClassResultsDEF(res_OV,'PRO-AM')

ResultsCLASS=pd.concat([ResultsPRO,ResultsGOLD,ResultsSILVER,ResultsBRONZE,ResultsPROAM],axis=0)
res_OV=pd.merge(res_OV,ResultsCLASS[['Car No.','Gap in Class','Diff in Class']],on='Car No.')

#### da qui in poi calcolo per tutte le macchine: BL, BT, B Sectors, B10 e B50%, Top Speed
#### il tutto sarà poi messo in un unica tabella chiamata "bl"

def BestLap_to_seconds(col_data):
    col_data = pd.to_datetime(col_data, format="%M:%S.%f", errors="coerce")
    
    # The above line adds the 1900-01-01 as a date to the time, so using subtraction to remove it
    col_data = col_data - datetime.datetime(1900,1,1)
    
    return col_data.dt.total_seconds()

if type(df['Time'].iloc[0]) is float or type(df['Time'].iloc[0])is str:
    df['Lap Time (s)']=BestLap_to_seconds(df['Time'])
else:
    df['Lap Time (s)']=df['Time'].apply(lambda x: x*86400 if x<1 else x)

def Sector_Convert(sector):
    Sector_Calc=[]
    for i in range(0,len(sector)): 
        if type(sector.iloc[i]) is float:
            Sector=sector.iloc[i]
        elif sector.iloc[i].find(':')>=1:
            Sector=BestLap_to_seconds(sector.iloc[i:i+1]).iloc[0]
        else:
            Sector=float(sector.iloc[i])
        Sector_Calc.append(Sector)
    return Sector_Calc

if type(df['Sector1Time'].iloc[0]) is float or type(df['Sector1Time'].iloc[0])is str:
    df['S1 (s)']=Sector_Convert(df['Sector1Time'])
else:
    df['S1 (s)']=df['Sector1Time']
    df['S1 (s)']=df['S1 (s)'].apply(lambda x: x*86400 if x<1 else x)
    df['S1 (s)']=df['S1 (s)'].apply(lambda x: x+1000 if x==0 else x)
if type(df['Sector2Time'].iloc[0]) is float or type(df['Sector2Time'].iloc[0])is str:
    df['S2 (s)']=Sector_Convert(df['Sector2Time'])
else:
    df['S2 (s)']=df['Sector2Time']
    df['S2 (s)']=df['S2 (s)'].apply(lambda x: x*86400 if x<1 else x)
    df['S2 (s)']=df['S2 (s)'].apply(lambda x: x+1000 if x==0 else x)
if type(df['Sector3Time'].iloc[0]) is float or type(df['Sector3Time'].iloc[0])is str:
    df['S3 (s)']=Sector_Convert(df['Sector3Time'])
else:
    df['S3 (s)']=df['Sector3Time']
    df['S3 (s)']=df['S3 (s)'].apply(lambda x: x*86400 if x<1 else x)
    df['S3 (s)']=df['S3 (s)'].apply(lambda x: x+1000 if x==0 else x)

df['S1 (s)']=round(df['S1 (s)'],3)
df['S2 (s)']=round(df['S2 (s)'],3)
df['S3 (s)']=round(df['S3 (s)'],3)

timeMS=df[['Bib', 'Lap Time (s)','S1 (s)','S2 (s)','S3 (s)']]

bl=timeMS.groupby('Bib').min()
bl=bl.reset_index()
bl['Theo']=round(bl['S1 (s)']+bl['S2 (s)']+bl['S3 (s)'],3)                      #calcolo theoretical lap
car=df[['Bib','Car']].drop_duplicates('Bib').reset_index()                                      # creo lista con il modello delle vetture
bl['Car']=car['Car']
bl.columns= ['Car No.','Best Lap', 'Best S1', 'Best S2', 'Best S3','Theo Lap', 'Car Model']    #rinomino e riordino (riga sotto) le colonne
bl=bl[['Car No.', 'Car Model','Best Lap', 'Theo Lap', 'Best S1', 'Best S2', 'Best S3']]

#Calcolo Top Speed per vettura
df_ts=df[['Bib', 'TopSpeed']]
ts=df_ts.groupby('Bib').max()
ts=ts.reset_index()
bl['Top Speed']=ts['TopSpeed']

#creo DB per calcolare poi il B10 e il B50
df_b10=df[['Bib', 'Lap Time (s)']]                                    
df_b10.columns=['Car No.','Laptime']
df_b10sorted=df_b10.sort_values(['Car No.','Laptime'])          #ordino il database per vettura e laptime (dal migliore al peggiore) 

el_car=bl['Car No.']
b10_arr=[]
b50_arr=[]
lapFifty=int(0.5*(df['Lap'].max()-df['Lap'].min()))
for i in el_car:                                            # questo ciclo for mi serve per filtrare una vettura alla volta e calcolare il rispettivo B10 e B50%
    is_car=df_b10sorted['Car No.'] ==i
    dfb10_car=df_b10sorted[is_car].reset_index()
    b10=round(dfb10_car.values[0:10,2].mean(),3)
    b10_arr.append(b10)
    b50=round(dfb10_car.values[0:lapFifty,2].mean(),3)
    b50_arr.append(b50)
    
bl['B10']=b10_arr
bl['B50']=b50_arr

def SectorBest10(database,entrylist,columnforbest):
    df_b=database[['Bib', columnforbest]]                                    
    df_b[columnforbest]=df_b[columnforbest]
    df_b.columns=['Car No.','Laptime']
    df_bsorted=df_b.sort_values(['Car No.','Laptime'])          #ordino il database per vettura e laptime (dal migliore al peggiore) 
    b10_array=[]
    for i in entrylist:                                            # questo ciclo for mi serve per filtrare una vettura alla volta e calcolare il rispettivo B10 e B50%
        is_car=df_bsorted['Car No.'] ==i
        dfb_car=df_bsorted[is_car].reset_index()
        b10=round(dfb_car.values[0:10,2].mean(),3)
        b10_array.append(b10)
    return b10_array

bl['B10 - S1']=SectorBest10(df,el_car,columnforbest='S1 (s)')
bl['B10 - S2']=SectorBest10(df,el_car,columnforbest='S2 (s)')
bl['B10 - S3']=SectorBest10(df,el_car,columnforbest='S3 (s)')


bl=pd.merge(bl,el[['Car No.','Category']],on='Car No.')

# funzione per calcolare la media dei best10 per ogni categoria. Prendo tutte le vetture eccetto le ultime 3 (valore casuale per eliminare gli spike e i Nan)
def SecAvg_GainLoss(database,sector,sector_outputname):
    
    db_car=database[['Car No.',sector]]
    db_car_sorted=db_car.sort_values(sector,na_position='last')
    sector_ave_class=round(db_car_sorted.values[0:len(db_car_sorted)-3,1].mean(),3)
    sector_GainLoss_class=db_car_sorted[sector]-sector_ave_class
    db_car_sorted[sector_outputname]=sector_GainLoss_class
    db_car_sorted['Perc '+sector_outputname]=sector_GainLoss_class/sector_ave_class*100
    
    return db_car_sorted

s1_ave=SecAvg_GainLoss(bl,sector='B10 - S1',sector_outputname='S1 Gain Loss')
s2_ave=SecAvg_GainLoss(bl,sector='B10 - S2',sector_outputname='S2 Gain Loss')
s3_ave=SecAvg_GainLoss(bl,sector='B10 - S3',sector_outputname='S3 Gain Loss')

bl=pd.merge(bl,s1_ave[['Car No.','S1 Gain Loss','Perc S1 Gain Loss']],on='Car No.')
bl=pd.merge(bl,s2_ave[['Car No.','S2 Gain Loss','Perc S2 Gain Loss']],on='Car No.')
bl=pd.merge(bl,s3_ave[['Car No.','S3 Gain Loss','Perc S3 Gain Loss']],on='Car No.')

bl['Best - Diff']=round(bl['Best Lap']-bl['Best Lap'].min(),3)
bl['Theo - Diff']=round(bl['Theo Lap']-bl['Theo Lap'].min(),3)
bl['S1 - Diff']=round(bl['Best S1']-bl['Best S1'].min(),3)
bl['S2 - Diff']=round(bl['Best S2']-bl['Best S2'].min(),3)
bl['S3 - Diff']=round(bl['Best S3']-bl['Best S3'].min(),3)
bl['Top Speed - Diff']=round(bl['Top Speed'].max()-bl['Top Speed'],3)

bl['B10 - Diff']=round(bl['B10']-bl['B10'].min(),3)
bl['B50 - Diff']=round(bl['B50']-bl['B50'].min(),3)
bl['B10 S1 - Diff']=round(bl['B10 - S1']-bl['B10 - S1'].min(),3)
bl['B10 S2 - Diff']=round(bl['B10 - S2']-bl['B10 - S2'].min(),3)
bl['B10 S3 - Diff']=round(bl['B10 - S3']-bl['B10 - S3'].min(),3)

#### da qui in poi calcolo raising average per laptime e top speed
#### utilizzo anche il DB creato prima per il calcolo del best10 e best 50%

mov_ave=[]
mov_ave_car=[]
Lap=[]
CarNo=[]
Lap_car=[]
CarNo_car=[]
topspeed=[]
topspeed_car=[]
#creo DB per top speed, S1, S2 e S3 (come fatto per B10 e B50)
df_ts_sorted=df_ts.sort_values(['Bib','TopSpeed'],ascending=False,ignore_index= True)
df_ts_sorted.columns=['Car No.','TopSpeed']  

df_s1=df[['Bib', 'S1 (s)']]                                    
df_s1.columns=['Car No.','S1']
df_s1sorted=df_s1.sort_values(['Car No.','S1'])

df_s2=df[['Bib', 'S2 (s)']]                                    
df_s2.columns=['Car No.','S2']
df_s2sorted=df_s2.sort_values(['Car No.','S2'])

df_s3=df[['Bib', 'S3 (s)']]                                    
df_s3.columns=['Car No.','S3']
df_s3sorted=df_s3.sort_values(['Car No.','S3'])

#funzione per calcolare raising avg (di modo da non doverla ripetere per tutte le colonne)
def raisingcalc(database,entrylist,dec_num,column_name):
    rais_ave=[]
    rais_ave_car=[]
    for i in entrylist:                                            
        is_car=database['Car No.'] ==i
        database_car=database[is_car].reset_index()
        for j in range(0,len(database_car)):
            rais_ave_loop=round(database_car.values[0:j+1,2].mean(),dec_num)
            if rais_ave_loop>0:
                rais_ave_car.append(float(rais_ave_loop))
            else:
                rais_ave_car.append(1000)
    rais_ave=pd.DataFrame(rais_ave_car,columns=[column_name])
    return rais_ave

for i in el_car:                                            
    is_car=df_b10sorted['Car No.'] ==i
    dfb10_car=df_b10sorted[is_car].reset_index()
    for j in range(0,len(dfb10_car)):
        Lap_car.append(j+1)
        CarNo_car.append(i)

Lap=pd.DataFrame(Lap_car, columns=['Lap'])
CarNo=pd.DataFrame(CarNo_car,columns=['Car No.'])

mov_ave=raisingcalc(df_b10sorted, el_car,3,column_name='Rais Avg')
topspeed=raisingcalc(df_ts_sorted, el_car,1,column_name='Sorted Top Speed')
s1_mov_ave=raisingcalc(df_s1sorted,el_car,3,column_name='S1 Rais Avg')
s2_mov_ave=raisingcalc(df_s2sorted,el_car,3,column_name='S2 Rais Avg')
s3_mov_ave=raisingcalc(df_s3sorted,el_car,3,column_name='S3 Rais Avg')

df_raisavg=pd.concat([CarNo,Lap,mov_ave,s1_mov_ave,s2_mov_ave,s3_mov_ave,topspeed,df_b10['Laptime']],axis=1)
df_raisavg=pd.merge(df_raisavg,el[['Car No.','Car']], on='Car No.')
# df_raisavg=pd.merge(df_raisavg,df_b10[['Car No.', 'Laptime']], on='Car No.')

#### Calcolo Stint

Stint=[]
Driver=[]
DriverID=[]
for CAR in el_car:
    is_car=df['Bib']==CAR
    db_Car=df[is_car]
    is_pit=Pit['Nr']==CAR
    Pit_Car=Pit[is_pit]
    Stint_number=1
    if len(Pit_Car)>0:
        DriverIN=Pit_Car['Driver in'].iloc[0]
    else:
        DriverIN=0
    for i in range(0,len(db_Car)):
        if Stint_number-1<len(Pit_Car['Lap In']):
            if db_Car['Lap'].iloc[i]==Pit_Car['Lap In'].iloc[Stint_number-1]+1:
                DriverIN=Pit_Car['Driver out'].iloc[Stint_number-1]
                Stint_number=Stint_number+1
        else:
            Stint_number=Stint_number
            DriverIN=DriverIN
        if DriverIN in el['Driver1'].to_list():
            DriverID_Car=1
        if DriverIN in el['Driver2'].to_list():
            DriverID_Car=2
        if DriverIN in el['Driver3'].to_list():
            DriverID_Car=3
        if DriverIN in el['Driver4'].to_list():
            DriverID_Car=4
        if DriverIN==0:
            DriverID_Car=0
        Stint.append(Stint_number)
        Driver.append(DriverIN)
        DriverID.append(DriverID_Car)
    
df['Stint']=Stint
df['Driver']=Driver
df['DriverHwId']=DriverID

#### calcolo best performance per pilota

def driverperf(database,DriverID,Stint):
    if DriverID==0 and Stint>0:
        df_dr=df[df['Stint']==Stint]
    else:
        df_dr=df[df['DriverHwId']==DriverID]
    dr=df_dr[['Bib','Lap Time (s)','S1 (s)','S2 (s)','S3 (s)']]
    dr_pf=dr.groupby('Bib').min()
    dr_pf=dr_pf.reset_index()
    dr_pf['Theo']=round(dr_pf['S1 (s)']+dr_pf['S2 (s)']+dr_pf['S3 (s)'],3)
    if DriverID==1:
        dr_name=df_dr[['Bib','Driver1']].drop_duplicates('Driver1').reset_index() 
        dr_pf['Driver']=dr_name['Driver1']
        dr_pf['DriverID']=DriverID
        dr_pf.columns=['Car No.','Laptime','S1','S2','S3','Theo','Driver','DriverID']
    if DriverID==2:
        dr_name=df_dr[['Bib', 'Driver2']].drop_duplicates('Driver2').reset_index()
        dr_pf['Driver']=dr_name['Driver2']
        dr_pf['DriverID']=DriverID
        dr_pf.columns=['Car No.','Laptime','S1','S2','S3','Theo','Driver','DriverID']
    if DriverID==3:
        dr_name=df_dr[['Bib', 'Driver3']].drop_duplicates('Driver3').reset_index()
        dr_pf['Driver']=dr_name['Driver3']
        dr_pf['DriverID']=DriverID
        dr_pf.columns=['Car No.','Laptime','S1','S2','S3','Theo','Driver','DriverID']
    if DriverID==0 and Stint>0:
        dr_pf['Driver']=0
        dr_pf['Stint']=Stint
        dr_pf.columns=['Car No.','Laptime','S1','S2','S3','Theo','Driver','Stint']
    if DriverID==0 and Stint==0:
        dr_pf['Driver']="N/A"
        dr_pf['DriverID']=DriverID
        dr_pf.columns=['Car No.','Laptime','S1','S2','S3','Theo','Driver','DriverID']
    if DriverID==4:
        dr_name=df_dr[['Bib', 'Driver4']].drop_duplicates('Driver4').reset_index()
        dr_pf['Driver']=dr_name['Driver4']
        dr_pf['DriverID']=DriverID
        dr_pf.columns=['Car No.','Laptime','S1','S2','S3','Theo','Driver','DriverID']
    return dr_pf

def driverperfpace(database,DriverID,Stint):
    dr_08=[]
    dr_08_car=[]
    dr_08_devstd_car=[]
    if DriverID==0 and Stint>0:
        df_dr=df[df['Stint']==Stint]
    else:
        df_dr=df[df['DriverHwId']==DriverID]
    dr=df_dr[['Bib','Lap Time (s)']]
    entrylist=df_dr['Bib'].drop_duplicates().reset_index()
    entrylist=entrylist['Bib']
    for i in entrylist:                                            
        is_car=dr['Bib'] ==i
        dr_car=dr[is_car].reset_index()
        dr_car=dr_car[['Bib','Lap Time (s)']].sort_values(['Bib','Lap Time (s)'])
        Lap=int(0.2*len(dr_car)+1)
        dr_b08_loop=round(dr_car.values[0:Lap,1].mean(),3)
        dr_08_car.append(float(dr_b08_loop))
        dr_b08_devstd_loop=round(dr_car.values[0:Lap,1].std(),3)
        dr_08_devstd_car.append(float(dr_b08_devstd_loop))
    dr_08_pace=pd.DataFrame(dr_08_car,columns=['Avg Pace'])
    dr_08_std=pd.DataFrame(dr_08_devstd_car,columns=['Dev Std'])
    dr_08=pd.concat([dr_08_pace,dr_08_std],axis=1)
    return dr_08


dr1_best=driverperf(df,1,0)
dr2_best=driverperf(df,2,0)
dr3_best=driverperf(df,3,0)
dr4_best=driverperf(df,4,0)
dr0_best=driverperf(df,0,0)
dr1_pace=driverperfpace(df,1,0)
dr2_pace=driverperfpace(df,2,0)
dr3_pace=driverperfpace(df,3,0)
dr4_pace=driverperfpace(df,4,0)
dr0_pace=driverperfpace(df,0,0)
    
StintArray=list(range(df['Stint'].max()))
stint_best=[]
for i in StintArray:
    stint_i_pace=driverperfpace(df,0,i+1)
    stint_i_best=driverperf(df,0,i+1)
    stint_i=pd.concat([stint_i_best,stint_i_pace],axis=1)
    if i==0:
        stint_best=stint_i
    else:
        stint_best=pd.concat([stint_best,stint_i],axis=0)
    
dr1=pd.concat([dr1_best,dr1_pace],axis=1)
dr2=pd.concat([dr2_best,dr2_pace],axis=1)
dr3=pd.concat([dr3_best,dr3_pace],axis=1)
dr4=pd.concat([dr4_best,dr4_pace],axis=1)
dr0=pd.concat([dr0_best,dr0_pace],axis=1)
    
dr_best=pd.concat([dr1,dr2,dr3,dr4,dr0],axis=0)

# dr_best.to_csv('Driver_Perf.csv')
# stint_best.to_csv('Stint_Perf.csv')

#### output to csv

# res_OV.to_csv(path.join(OUT_DIR, 'OverallResults.csv'), index=False)
# df_raisavg.to_csv(path.join(OUT_DIR, 'df_raisavg_no_index.csv'), index=False)
# bl.to_csv(path.join(OUT_DIR, 'Best_Perf_no_index.csv'), index=False)
# el.to_csv(path.join(OUT_DIR, 'EL.csv'), index=False)

# Colonne fisse e dinamiche
static_columns = ['Rank', 'Car No.', 'Category', 'Car', 'Team', 'BestLapS']

# Mappa per formattazione condizionale
color_map = {
    "mercedes": {"background": "#333333", "color": "white"},
    "mclaren": {"background": "#FFA500", "color": "black"},
    "lamborghini": {"background": "#90EE90", "color": "black"},
    "bmw": {"background": "#00008B", "color": "white"},
    "porsche": {"background": "#D3D3D3", "color": "black"},
    "aston": {"background": "#006400", "color": "white"},
    "audi": {"background": "#800080", "color": "white"},
    "ferrari": {"background": "#FF0000", "color": "black"},
    "corvette": {"background": "#000000", "color": "white"},
    "ford": {"background": "#87CEEB", "color": "black"},
}

# === DASH APP ===

app = Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.BOOTSTRAP])
# app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server

# Sidebar
sidebar = html.Div(
    [
        html.H4("TIMING ANALYSIS", className="display-7", style={"fontFamily": "Aptos"}),
        html.Hr(),
        dbc.Nav(
            [
                dbc.NavLink("RESULTS", href="/", active="exact"),
                dbc.NavLink("BEST PERF.", href="/best", active="exact"),
                dbc.NavLink("AVG. PERF", href="/avg-perf", active="exact"),
                dbc.NavLink("DRIVER PERF. BOXPLOT", href="/driver-perf", active="exact"),
            ],
            vertical=True,
            pills=True,
        ),
    ],
    style={
        "position": "fixed",
        "top": 0,
        "left": 0,
        "bottom": 0,
        "width": "16rem",
        "padding": "2rem 1rem",
        "backgroundColor": "#f8f9fa",
    },
)

# Layout generale con sidebar
content = html.Div(id="page-content", style={"marginLeft": "18rem", "padding": "2rem 1rem"})

app.layout = html.Div([
    dcc.Location(id="url"),
    sidebar,
    content
])

# Layout PAGE 1 - RESULTS
results_layout = html.Div([
    html.H3("Overall Results", style={"fontFamily": "Aptos", "fontSize": "18px"}),

    html.Div([
        dcc.Dropdown(id="category-filter", placeholder="Filter by Category", style={"width": "250px"}),
        dcc.Dropdown(id="car-filter", placeholder="Filter by Car", style={"width": "250px"}),
        dcc.Dropdown(id="team-filter", placeholder="Filter by Team", style={"width": "250px"}),
    ], style={"display": "flex", "gap": "15px", "marginBottom": "20px"}),

    dash_table.DataTable(
        id="results-table",
        page_size=100,
        style_table={"overflowX": "auto"},
        style_cell={
            "textAlign": "center",
            "fontFamily": "Aptos",
            "fontSize": "12px",
            "minWidth": "50px",
            "maxWidth": "100px",
        },
        style_cell_conditional=[
            {"if": {"column_id": "Car No."}, "minWidth": "40px", "maxWidth": "60px"},
            {"if": {"column_id": "Rank"}, "minWidth": "40px", "maxWidth": "60px"},
        ],
        style_header={"backgroundColor": "#f2f2f2", "fontWeight": "bold"},
        style_data_conditional=[],
    )
])

# Layout PAGE 2 - BEST PERF
best_perf_layout = html.Div([
    html.H3("Best Performances", style={"fontFamily": "Aptos", "fontSize": "18px"}),
    
    html.Div([
        dcc.Dropdown(id="bp-cat", placeholder="Filter by Category", style={"width": "250px"}),
        dcc.Dropdown(id="bp-car", placeholder="Filter by Car", style={"width": "250px"})
    ], style={"display": "flex", "gap": "15px", "marginBottom": "20px"}),

    # html.Div(id="bp-tables")
    html.Div([
    html.Div([
        dbc.RadioItems(
       id="toggle-diff",
       options=[
           {"label": "Standard", "value": "standard"},
           {"label": "Show Diff Columns", "value": "diff"},
       ],
       value="standard",
       inline=True,
       labelStyle={"marginRight": "15px"},
       style={"fontFamily": "Aptos", "marginBottom": "10px"}
   ),
    ], style={"marginBottom": "20px"}),
    html.Div(id="bp-tables", style={"display": "flex", "flexWrap": "wrap", "gap": "20px"})
    ])
])

# Routing
@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def render_page_content(pathname):
    if pathname == "/" or pathname == "/results":
        return results_layout
    elif pathname == "/best":
        return best_perf_layout
    elif pathname == "/avg-perf":
        return avg_perf_layout
    elif pathname == "/driver-perf":
        return driver_perf_layout
    return html.Div([html.H1("404 - Pagina non trovata")])

# Update dropdown filters - RESULTS
@app.callback(
    Output("category-filter", "options"),
    Output("car-filter", "options"),
    Output("team-filter", "options"),
    Input("url", "pathname")
)
def update_dropdown_options(_):
    return (
        [{"label": x, "value": x} for x in sorted(res_OV["Category"].unique())],
        [{"label": x, "value": x} for x in sorted(res_OV["Car"].unique())],
        [{"label": x, "value": x} for x in sorted(res_OV["Team"].unique())]
    )

# CALLBACK pagina RESULTS
@app.callback(
    Output("results-table", "data"),
    Output("results-table", "columns"),
    Output("results-table", "style_data_conditional"),
    Input("category-filter", "value"),
    Input("car-filter", "value"),
    Input("team-filter", "value")
)
def update_table(category, car, team):
    df_filtered = res_OV.copy()
    if category: df_filtered = df_filtered[df_filtered["Category"] == category]
    if car: df_filtered = df_filtered[df_filtered["Car"] == car]
    if team: df_filtered = df_filtered[df_filtered["Team"] == team]
    
    dynamic_cols = ["Gap", "Diff"] if not category else ["Gap in Class", "Diff in Class"]
    columns = ["Rank", "Car No.", "Category", "Car", "Team", "BestLapS"] + dynamic_cols
    dash_columns = [{"name": col, "id": col} for col in columns]

    style_data_conditional = []
    for brand, style in color_map.items():
        matched = df_filtered[df_filtered["Car"].str.lower().str.contains(brand)].Car.unique()
        for val in matched:
            style_data_conditional.append({
                "if": {"filter_query": f'{{Car}} = "{val}"', "column_id": "Car No."},
                "backgroundColor": style["background"],
                "color": style["color"]
            })

    style_data_conditional.append({
        "if": {"filter_query": f'{{Car No.}} = {CarNumber}'},
        "backgroundColor": "#ffff66",
        "color": "black"
    })

    return df_filtered[columns].to_dict("records"), dash_columns, style_data_conditional

# Callback per popolare i filtri della pagina BEST PERF.
@app.callback(
    Output("bp-cat", "options"),
    Output("bp-car", "options"),
    Input("url", "pathname")
)
def populate_best_perf_filters(pathname):
    if pathname and "/best" in pathname:
        cat_options = [{"label": x.strip(), "value": x.strip()} for x in sorted(bl["Category"].dropna().unique())]
        car_options = [{"label": x.strip(), "value": x.strip()} for x in sorted(bl["Car Model"].dropna().unique())]
        return cat_options, car_options
    return [], []

# CALLBACK pagina BEST PERF
@app.callback(
    Output("bp-tables", "children"),
    Input("bp-cat", "value"),
    Input("bp-car", "value"),
    Input("toggle-diff", "value")
)
def update_best_perf(cat, car_model, mode):
    df = bl.copy()

    # Pulizia e filtri
    df["Category"] = df["Category"].astype(str).str.strip()
    df["Car Model"] = df["Car Model"].astype(str).str.strip()

    if cat:
        df = df[df["Category"] == cat.strip()]
    if car_model:
        df = df[df["Car Model"] == car_model.strip()]

    if mode == "diff":
        tables_info = [
            ("Best Lap Diff", "Best - Diff", False),
            ("Theo Lap Diff", "Theo - Diff", False),
            ("S1 Diff", "S1 - Diff", False),
            ("S2 Diff", "S2 - Diff", False),
            ("S3 Diff", "S3 - Diff", False),
            ("Top Speed Diff", "Top Speed - Diff", False),
        ]
    else:
        tables_info = [
            ("Best Lap", "Best Lap", False),
            ("Theo Lap", "Theo Lap", False),
            ("Best S1", "Best S1", False),
            ("Best S2", "Best S2", False),
            ("Best S3", "Best S3", False),
            ("Top Speed", "Top Speed", True),
        ]

    table_elements = []
    for title, col, descending in tables_info:
        if col not in df.columns:
            continue

        dff = df[["Car No.", "Car Model", col]]
        dff = dff[dff[col].notna()]
        dff = dff.sort_values(by=col, ascending=not descending)

        style_data_conditional = []
        for brand, style in color_map.items():
            matched = dff[dff["Car Model"].str.lower().str.contains(brand.lower(), na=False)]
            for val in matched["Car Model"].unique():
                style_data_conditional.append({
                    "if": {"filter_query": f'{{Car Model}} = "{val}"', "column_id": "Car No."},
                    "backgroundColor": style["background"],
                    "color": style["color"]
                })

        style_data_conditional.append({
            "if": {"filter_query": f'{{Car No.}} = {CarNumber}'},
            "backgroundColor": "#ffff66",
            "color": "black"
        })

        table_elements.append(html.Div([
            html.H5(title, style={"fontFamily": "Aptos", "fontSize": "14px", "textAlign": "center"}),
            dash_table.DataTable(
                columns=[
                    {"name": "Car No.", "id": "Car No."},
                    {"name": col, "id": col}
                ],
                data=dff[["Car No.", col, "Car Model"]].to_dict("records"),
                style_table={"overflowX": "auto", "width": "100%"},
                style_cell={
                    "textAlign": "center",
                    "fontFamily": "Aptos",
                    "fontSize": "12px",
                    "minWidth": "60px",
                    "maxWidth": "70px",
                },
                sort_action="native",
                style_data_conditional=style_data_conditional
            )
        ], style={"width": "15%", "minWidth": "140px", "display": "inline-block", "verticalAlign": "top", "marginRight": "10px"}))

    return html.Div(table_elements, style={"display": "flex", "flexWrap": "wrap"})

# Layout PAGE 3 - AVG PERF

avg_perf_layout = html.Div([
    html.H3("Average Performances", style={"fontFamily": "Aptos", "fontSize": "18px"}),

    html.Div([
        dcc.Dropdown(id="avg-cat", placeholder="Filter by Category", style={"width": "250px"}),
        dcc.Dropdown(id="avg-car", placeholder="Filter by Car", style={"width": "250px"}),
    ], style={"display": "flex", "gap": "15px", "marginBottom": "20px"}),

    html.Div([
        dbc.RadioItems(
            id="toggle-diff-avg",
            options=[
                {"label": "Standard", "value": "standard"},
                {"label": "Show Diff Columns", "value": "diff"},
            ],
            value="standard",
            inline=True,
            labelStyle={"marginRight": "15px"},
            style={"fontFamily": "Aptos", "marginBottom": "10px"}
        ),
    ], style={"marginBottom": "20px"}),

    html.Div(id="avg-tables", style={"display": "flex", "flexWrap": "wrap", "gap": "20px"})
])


@app.callback(
    Output("avg-tables", "children"),
    Input("avg-cat", "value"),
    Input("avg-car", "value"),
    Input("toggle-diff-avg", "value")
)
def update_avg_perf(cat, car_model, mode):
    df = bl.copy()

    df["Category"] = df["Category"].astype(str).str.strip()
    df["Car Model"] = df["Car Model"].astype(str).str.strip()

    if cat:
        df = df[df["Category"] == cat.strip()]
    if car_model:
        df = df[df["Car Model"] == car_model.strip()]

    if mode == "diff":
        tables_info = [
            ("B10 Diff", "B10 - Diff", False),
            ("B50 Diff", "B50 - Diff", False),
            ("B10 S1 Diff", "B10 S1 - Diff", False),
            ("B10 S2 Diff", "B10 S2 - Diff", False),
            ("B10 S3 Diff", "B10 S3 - Diff", False),
        ]
    else:
        tables_info = [
            ("Best 10 Laps", "B10", False),
            ("Best 50% Laps", "B50", False),
            ("Best 10 - S1", "B10 - S1", False),
            ("Best 10 - S2", "B10 - S2", False),
            ("Best 10 - S3", "B10 - S3", False),
        ]

    table_elements = []
    for title, col, descending in tables_info:
        if col not in df.columns:
            continue

        dff = df[["Car No.", "Car Model", col]].dropna()
        dff = dff.sort_values(by=col, ascending=not descending)

        style_data_conditional = []
        for brand, style in color_map.items():
            matched = dff[dff["Car Model"].str.lower().str.contains(brand.lower(), na=False)]
            for val in matched["Car Model"].unique():
                style_data_conditional.append({
                    "if": {"filter_query": f'{{Car Model}} = "{val}"', "column_id": "Car No."},
                    "backgroundColor": style["background"],
                    "color": style["color"]
                })

        style_data_conditional.append({
            "if": {"filter_query": f'{{Car No.}} = {CarNumber}'},
            "backgroundColor": "#ffff66",
            "color": "black"
        })

        table_elements.append(html.Div([
            html.H5(title, style={"fontFamily": "Aptos", "fontSize": "14px", "textAlign": "center"}),
            dash_table.DataTable(
                columns=[
                    {"name": "Car No.", "id": "Car No."},
                    {"name": col, "id": col}
                ],
                data=dff[["Car No.", col, "Car Model"]].to_dict("records"),
                style_table={"overflowX": "auto", "width": "100%"},
                style_cell={
                    "textAlign": "center",
                    "fontFamily": "Aptos",
                    "fontSize": "12px",
                    "minWidth": "60px",
                    "maxWidth": "70px",
                },
                sort_action="native",
                style_data_conditional=style_data_conditional
            )
        ], style={"width": "15%", "minWidth": "140px", "display": "inline-block", "verticalAlign": "top", "marginRight": "10px"}))

    return html.Div(table_elements, style={"display": "flex", "flexWrap": "wrap"})

@app.callback(
    Output("avg-cat", "options"),
    Output("avg-car", "options"),
    Input("url", "pathname")  # oppure Input("avg-tables", "children") se non usi multipagina con URL
)
def populate_avg_filters(pathname):
    df = bl.copy()

    cat_options = [{"label": c, "value": c} for c in sorted(df["Category"].dropna().unique())]
    car_options = [{"label": c, "value": c} for c in sorted(df["Car Model"].dropna().unique())]

    return cat_options, car_options

# layout DRIVER PERFORMANCE BOXPLOT

driver_perf_layout = html.Div([
    html.H3("Driver Performance - Boxplot", style={
        "fontFamily": "Aptos", 
        "fontSize": "18px", 
        "marginBottom": "20px"
    }),

    html.Div([
        html.Label("X-axis Min"),
        dcc.Input(id="xaxis-min", type="number", debounce=True),

        html.Label("X-axis Max", style={"marginLeft": "20px"}),
        dcc.Input(id="xaxis-max", type="number", debounce=True),
    ], style={
        "padding": "10px", 
        "fontFamily": "Aptos", 
        "fontSize": "14px"
    }),

    html.Div(id="driver-boxplots", style={
        "display": "flex", 
        "flexDirection": "column", 
        "gap": "40px"
    })
])

import plotly.graph_objects as go

@app.callback(
    Output("driver-boxplots", "children"),
    Input("url", "pathname"),
    Input("xaxis-min", "value"),
    Input("xaxis-max", "value")
)
def render_driver_perf(pathname, x_min, x_max):
    if pathname != "/driver-perf":
        raise PreventUpdate

    min_df = (
        df.groupby("Driver")["Lap Time (s)"]
        .min()
        .sort_values()
        .reset_index()
    )
    sorted_drivers = min_df["Driver"].tolist()
    df["Driver"] = pd.Categorical(df["Driver"], categories=sorted_drivers, ordered=True)

    fig = go.Figure()

    for driver in sorted_drivers:
        driver_df = df[df["Driver"] == driver]
        if driver_df.empty:
            continue

        min_lap = driver_df["Lap Time (s)"].min()
        threshold = min_lap * 1.10
        filtered_laps = driver_df[driver_df["Lap Time (s)"] <= threshold]

        if filtered_laps.empty:
            continue

        fig.add_trace(go.Box(
            x=filtered_laps["Lap Time (s)"],
            y=[driver] * len(filtered_laps),
            name=driver,
            boxpoints="outliers",
            jitter=0.3,
            pointpos=0,
            marker=dict(size=4, color="blue", opacity=0.6),
            line=dict(color="darkblue"),
            orientation="h",
            showlegend=False
        ))

    fig.update_layout(
        height=25 * len(sorted_drivers) + 150,
        margin=dict(l=120, r=20, t=20, b=30),
        xaxis=dict(
            title="Lap Time (s)",
            side="top",
            range=[x_min, x_max] if x_min is not None and x_max is not None else None
        ),
        yaxis=dict(
            title="Driver",
            categoryorder="array",
            categoryarray=sorted_drivers,
            tickfont=dict(size=10),
            autorange="reversed"
        ),
        font=dict(family="Aptos", size=12)
    )

    stats_df = dr_best[dr_best["Driver"].isin(sorted_drivers)].copy()
    stats_df = stats_df[["Driver", "Laptime", "Theo", "Avg Pace", "Dev Std"]]
    stats_df["Driver"] = pd.Categorical(stats_df["Driver"], categories=sorted_drivers, ordered=True)
    stats_df = stats_df.sort_values("Driver")

    style_data_conditional = []

    if "CarNumber" in globals():
        drivers_to_highlight = dr_best[dr_best["Car No."] == CarNumber]["Driver"].unique()
        for driver in drivers_to_highlight:
            style_data_conditional.append({
                "if": {"filter_query": f'{{Driver}} = "{driver}"'},
                "backgroundColor": "#ffff66",
                "color": "black"
            })

    # Color scale
    import matplotlib
    import matplotlib.cm as cm

    def value_to_color(value, vmin, vmax):
        norm = matplotlib.colors.Normalize(vmin=vmin, vmax=vmax)
        cmap = cm.get_cmap('RdYlGn_r')
        rgba = cmap(norm(value))
        r, g, b, _ = [int(255 * c) for c in rgba]
        return f'rgb({r},{g},{b})'

    for col in ["Laptime", "Theo", "Avg Pace", "Dev Std"]:
        vmin, vmax = stats_df[col].min(), stats_df[col].max()
        for i, val in enumerate(stats_df[col]):
            style_data_conditional.append({
                "if": {"row_index": i, "column_id": col},
                "backgroundColor": value_to_color(val, vmin, vmax),
                "color": "black"
            })

    table = dash_table.DataTable(
        columns=[{"name": col, "id": col} for col in stats_df.columns],
        data=stats_df.to_dict("records"),
        style_table={"overflowX": "auto"},
        style_cell={
            "textAlign": "center",
            "fontFamily": "Aptos",
            "fontSize": "12px",
            "padding": "4px",
            "minWidth": "80px",
            "maxWidth": "120px",
        },
        style_header={
            "backgroundColor": "lightgrey",
            "fontWeight": "bold"
        },
        style_data_conditional=style_data_conditional,
        sort_action="native"
    )

    return html.Div([
        dcc.Graph(figure=fig, config={"displayModeBar": False}),
        html.Hr(),
        html.H5("Driver Statistics", style={"textAlign": "center", "fontFamily": "Aptos"}),
        table
    ])


import platform

DEBUG = False
# PORT = 8051

def kill_process_using_port(port):
    if platform.system() == "Windows":
        try:
            result = subprocess.check_output(f'netstat -ano | findstr :{port}', shell=True).decode()
            lines = result.strip().split('\n')
            pids = set()
            for line in lines:
                parts = line.strip().split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    pids.add(pid)

            for pid in pids:
                print(f"Terminando processo PID {pid} sulla porta {port}...")
                os.system(f'taskkill /PID {pid} /F')
        except subprocess.CalledProcessError:
            print(f"Nessun processo in ascolto sulla porta {port}.")
    else:
        print("Supportato solo su Windows")

def open_browser():
    webbrowser.open_new(f"http://127.0.0.1:{PORT}")

# if __name__ == '__main__':
#     kill_process_using_port(PORT)

#     if not DEBUG:
#         threading.Timer(1, open_browser).start()

#     app.run(debug=DEBUG, port=PORT)

def get_port():
    # Se su Render, usa la porta da env, altrimenti usa la porta di default 8051
    return int(os.environ.get("PORT", 8051))

if __name__ == '__main__':
    PORT = get_port()
    app.server.config["SERVER_NAME"] = f"127.0.0.1:{PORT}"
    # Solo in locale (quando DEBUG=False, quindi in locale) uccidi il processo che occupa la porta
    if not DEBUG:
        kill_process_using_port(PORT)
        threading.Timer(1, open_browser).start()
    host = '0.0.0.0' if os.environ.get('RENDER') else '127.0.0.1'
    app.run(debug=DEBUG, host=host, port=PORT)

 
#https://www.dash-bootstrap-components.com/examples/simple-sidebar/page-2
