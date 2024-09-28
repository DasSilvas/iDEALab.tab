# -*- coding: utf-8 -*-
""" Ficheiro de formulas de calculo de RPAE
"""
#Variáveis base (rugosidade, diametros mínimos, etc)

dmin_ramal = 50
dmin_tq = 50
dmin_col = 125
k= 120
ts = 0.33
i = 0.01

#Caudal de caldulo
qs = 240

@staticmethod
def q_cal(caudal_acumulado):
    qe = 7.3497*caudal_acumulado**0.5352
    return min(caudal_acumulado, qe)

#Calculo do diametro do tubo de queda

@staticmethod
def d_tq(caudal_calculo, taxa_ocupacao):
    dia = 4.4205*(caudal_calculo**(3/8))*(taxa_ocupacao**(-5/8))
    return dia

#Calculo do diametro através da formula de Mannig-Stricker, utilizado em RAMIS NÃO INDIVIDUAIS e COLECTORES

#Calculo para escoamentos a secção cheia ou meia secção, com conversão do caudal de l/min para m3/s
def d_rni(caudal_calculo, inclinacao, rugosidade, tipo="meia"):

    q = caudal_calculo/(60*1000)
    v = 0.4980 if tipo =="meia" else 0.6459
    dia = (q**(3/8))/(v*(rugosidade**(3/8))*(inclinacao**(3/16)))*1000
    
    return dia


#Calculo do diametro dos Colectores

#testing purposes
if __name__ == "__main__":

    caudal_cal = q_cal(qs)

    dia_tq = d_tq(caudal_cal,ts)

    dia_rni = d_rni(caudal_cal,i,k, tipo="cheia")
    print(caudal_cal, dia_rni)
