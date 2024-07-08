#Clase que se encarga de hacer los cálculos de programa
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

class Calcular:
    def __init__(self) -> None:
        pass
    
    #Calculamos el precio historico PVPC ajustado por meses
    def calculcarHistorico(self, p_historicos_df):
        #Usamos el promedio para agrupar de precio diario a precio mensual por tarifa tipo
        grupo = p_historicos_df.groupby(['Codigo','Año','Mes','TarifaTipo']).agg({'Precio':['mean']}).reset_index()

        #renombramos columnas
        grupo.columns = (['Codigo','Año','Mes','TarifaTipo','P_medio'])

        #calculamos la EMA para la combinacion mes y tarifatipo
        grupo['EMA'] = grupo.groupby('TarifaTipo')['P_medio'].transform(lambda x: x.ewm(span=2,adjust=False).mean())

        #Hacemos el agrupamineto Mes y tarifaTipo y calcular la media
        resultado_media_expo = grupo.groupby(['Mes','TarifaTipo']).agg({'EMA':'mean'}).reset_index()

        #Redondeamos los valores a dos decimales
        resultado_media_expo['EMA'] = resultado_media_expo['EMA'].round(2)

        #Renombramos columnas
        resultado_media_expo.columns = ['Mes','TarifaTipo','P_medio']

        #Transformamos el dataFrame
        resultado_pivot_expo = resultado_media_expo.pivot(index='Mes',columns='TarifaTipo',values='P_medio').reset_index()
        resultado_pivot_expo.columns = ['Mes','PrecioPunta','PrecioValle']
        resultado_pivot_expo = resultado_pivot_expo [['Mes','PrecioValle','PrecioPunta']]
        resultado_pivot_expo['P_Medio'] = (resultado_pivot_expo ['PrecioPunta'] + resultado_pivot_expo ['PrecioValle']) / 2

        return resultado_pivot_expo
    
    #transfomar el precio base en un precio base mensual hisorico - haciendo promedio
    #devuelve un dataframe mensual precio futuros mensuales; el precio base historicos y el precio promedio de ambos
    def calcularBases(self,p_bases_df,p_futur_df):

        #Usamos el promedio para agrupar de precio diario a precio mensual por tarifa tipo
        p_ba_pf = p_bases_df.groupby(['Mes']).agg({'PrecioBase':['mean']}).reset_index()
        p_ba_pf.columns = ['Mes','PrecioHistorico']

        #tratamos el fichero de los futuros
        # Convertir la columna de fechas a tipo datetime
        p_futur_df['Fecha'] = pd.to_datetime(p_futur_df['Fecha'],dayfirst=True)
        # Función para obtener los meses relevantes para cada tipo de frecuencia
        def obtener_meses(fila):
            if fila['TipoPrecio'] == 'Diario':
                return [fila['Fecha'].month]
            elif fila['TipoPrecio'] == 'Semana':
                return [fila['Fecha'].month]
            elif fila['TipoPrecio'] == 'Mes':
                return [fila['Fecha'].month]
            elif fila['TipoPrecio'] == 'Quaterly':
                # Última fecha del cuatrimestre, incluye tres meses anteriores
                mes = fila['Fecha'].month
                return [(mes - 1) % 12 + 1, (mes - 2) % 12 + 1, (mes - 3) % 12 + 1]
            elif fila['TipoPrecio'] == 'Año':
                return list(range(1, 13))
            return []

        # Expandir el DataFrame para incluir todos los meses relevantes para cada fila
        expandidos = []
        for _, row in p_futur_df.iterrows():
            meses = obtener_meses(row)
            for mes in meses:
                expandidos.append({
                'Mes': mes,
                'Precio': row['Composite']
                })

        df_expandido = pd.DataFrame(expandidos)

        # Agrupar por mes y calcular el promedio
        futurosBase = df_expandido.groupby('Mes').agg({'Precio': 'mean'}).reset_index()
        futurosBase.columns = ['Mes','PrecioFuturos']
        preciosBase = pd.merge(p_ba_pf,futurosBase,on='Mes')
        preciosBase ['PrecioPromedio'] = (preciosBase ['PrecioHistorico'] + preciosBase ['PrecioFuturos']) / 2
        return preciosBase
    
    def calcularPVPC_f(self,df_hist,df_base):
        df_t = pd.merge(df_hist,df_base,on='Mes')
        #para inferir el precio futuro calculmos los diferenciales entre el preciopromedio de la base y el historico valle/punta PVPC
        df_t['SpreadValle'] = df_t ['PrecioValle'] - df_t['PrecioPromedio']
        df_t['SpreadPunta'] = df_t ['PrecioPunta'] - df_t['PrecioPromedio']
        #Sacamos el factor de corrección, que se corresponde con el spread que hay que aplicar a la base para llegar al futuro PVPC
        df_t['FCorValle'] = df_t ['SpreadValle'] / df_t['P_Medio']
        df_t['FCorPunta'] = df_t ['SpreadPunta'] / df_t['P_Medio']
        #Sacamos el PrecioValle y PrecioPunta esperados como PVPC
        df_t['PVPCValle'] = df_t ['PrecioPromedio'] + (df_t['PrecioPromedio'] * df_t['FCorValle'])
        df_t['PVPCPunta'] = df_t ['PrecioPromedio'] + (df_t['PrecioPromedio'] * df_t['FCorPunta'])
        df_pvpc = df_t[['Mes','PVPCValle','PVPCPunta']]
        return df_pvpc
        

    
    #Calcular, por meses, los datos relevantes de la curva del cliente
    def calcularCliente(self, consumo_cli_df):
        #agrupo todos los datos a formato mensual
        clienteHistorico = consumo_cli_df.groupby(['Mes']).agg({'ConsumoPunta':['mean'],'ConsumoValle':['mean']}).reset_index()
        clienteHistorico.columns = ['Mes','ConsumoPunta','ConsumoValle']
        #añadimos nuevas columnas
        clienteHistorico['TotalConsumo'] = clienteHistorico ['ConsumoPunta'] + clienteHistorico ['ConsumoValle']
        clienteHistorico['PorcentajeValle'] = clienteHistorico ['ConsumoValle'] / clienteHistorico ['TotalConsumo']
        clienteHistorico['PorcentajePunta'] = clienteHistorico ['ConsumoPunta'] / clienteHistorico ['TotalConsumo']
        consumo = clienteHistorico.groupby(['Mes']).agg({'TotalConsumo':'sum'}).reset_index()
        sumaTConsumo = consumo['TotalConsumo'].sum()
        clienteHistorico['PorcentajeConsumo'] = clienteHistorico ['TotalConsumo'] / sumaTConsumo
        return(clienteHistorico)
    
    #calcular las tablas con los precios del PVPC futuros y los de los clientes por meses
    def calcularTablaPrecio(self, df_pvpc,df_base,df_cli):
        #juntamos los diferentes dataframes en uno para poder trabajar mejor
        #df_t = pd.merge(df_pvpc,df_base,on='Mes')
        #df_tabla = pd.merge(df_t,df_cli,on='Mes')
        #print(df_cli)
        df_c = df_cli[['Mes','PorcentajeValle','PorcentajePunta','PorcentajeConsumo','TotalConsumo']]
        df_tabla = pd.merge(df_c,df_pvpc,on='Mes')
        df_tabla['VallePonde'] = df_tabla['PVPCValle'] * df_tabla['PorcentajeValle']
        df_tabla['PuntaPonde'] = df_tabla['PVPCPunta'] * df_tabla['PorcentajePunta']
        df_tabla['PMedio_R'] = df_tabla['VallePonde'] + df_tabla['PuntaPonde'] 
        df_tabla['PrecioRegulado'] = df_tabla['PMedio_R'] * df_tabla['PorcentajeConsumo'] 
        
        #Tabla de salida
        df_reg = df_tabla[['Mes','PrecioRegulado']]
        #df_tabla ['Pr_M_Pon_Valle'] = df_tabla ['PorcentajeValle'] + df_tabla ['']
        #print(df_tabla.columns)
        #print(df_reg)
        #print(df_tabla)
        return(df_reg)

    #Para sacar el precio mensual para la tarifa plan en función del consumo del cliente
    def calcularPrecioTarifaPlana (self, df_consumo, precioMes):
        df_consumo ['PrecioTP'] = precioMes / df_consumo['TotalConsumo'] 
        return df_consumo
    
    def calcularPrecioFijo (self, df_consumo, precioV, precioP):
        #En df_consumo necesito el porcentaValle y el porcentajePunta en la tabla
        df_consumo['PValle'] = precioP * df_consumo['PorcentajeValle']
        df_consumo['PPunta'] = precioP * df_consumo['PorcentajePunta']
        df_consumo['PrPro'] = df_consumo['PValle'] + df_consumo['PPunta']
        return df_consumo
    
    def calcularPreciosProveedores (self,df_cli,df_proveedores):
        #para cada una de las entradas de df_cli hay que comprobar si es tarifa plana o no
        #cuando sea tarifa plana, llamar a su funcion y cuando no lo sea, llamar a la otra
        #agrupar todo en un df para devolverlo. 
        campos = []
        campos.append('Mes')
        df_si = df_proveedores[df_proveedores['TarifaPlana']=='Si']
        df_no = df_proveedores[df_proveedores['TarifaPlana']=='No']
        #ajuste de tarifaPlana
        for row in df_si.itertuples():
            df_cli [row.Tarifa] = (row.PrecioTP / df_cli['TotalConsumo']) * 1000 * df_cli['PorcentajeConsumo']
            campos.append(row.Tarifa)
        ##Ajuste de tarifa Precio fijo
        for row in df_no.itertuples():
            df_cli [row.Tarifa] = ((row.TarifaPunta * df_cli ['PorcentajePunta']) + (df_cli['PorcentajeValle'] * row.TarifaValle)) * df_cli['PorcentajeConsumo']
            campos.append(row.Tarifa)
        df_salida = df_cli [campos]
        return df_salida
    
    def sacarPrecios(self,df_precios):
        df_aux = df_precios.drop(columns = 'Mes')
        salida = df_aux.sum().round(2)
        return salida
    
    def devuelemenor(self, s_salida):
        minimo = s_salida.min()
        nombre = s_salida.idxmin()
        return [nombre,minimo]
    
    







