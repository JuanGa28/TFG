import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from .Calcular import *
#import Calcular as cl

 #programa que haga todo el proceso de los pandas


    #leer todos los archivos 
def calcular_precios():
    p_historicos_df = pd.read_csv('C:/Ficheros/FicheroPreciosHistoricos.csv',delimiter=';', encoding='latin-1')
    p_bases_df = pd.read_csv('C:/Ficheros/FicheroPreciosBase.csv',delimiter=';', encoding='latin-1')
    p_basesFut_df = pd.read_csv('C:/Ficheros/FicheroFuturos.csv',header=0,delimiter=';', encoding='latin-1')
    consumo_cli_df = pd.read_csv('C:/Ficheros/ConsumoCliente.csv',delimiter=';', encoding='latin-1')
    f_proveedores_df = pd.read_csv('C:/Ficheros/FicheroProveedores.csv',delimiter=';', encoding='latin-1')

    a = Calcular()
    df_h = a.calculcarHistorico(p_historicos_df)
    df_f = a.calcularBases(p_bases_df,p_basesFut_df)
    df_c = a.calcularCliente(consumo_cli_df)
    df_pvpc = a.calcularPVPC_f(df_h,df_f)
    df_precios = a.calcularTablaPrecio(df_pvpc,df_f,df_c)
    df_prov = a.calcularPreciosProveedores(df_c,f_proveedores_df)

    df_totalPrecio = pd.merge(df_precios, df_prov,on='Mes')
    seriesPrecios = a.sacarPrecios(df_totalPrecio)
    precioMasBarato = a.devuelemenor(seriesPrecios)
    return precioMasBarato, seriesPrecios
 