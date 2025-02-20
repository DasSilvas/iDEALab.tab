# -*- coding: utf-8 -*-
""" Ficheiro de formulas de calculo de RPAE
"""
#Variáveis base (rugosidade, diametros mínimos, etc)
import math

dmin_ramal = 50
dmin_tq = 110
dmin_col = 125
k= 120
i = 0.02

def q_cal(caudal_acumulado):
    qe = round(7.3497*caudal_acumulado**0.5352,2)
    return min(caudal_acumulado, qe)

#Calculo do diametro de cálculo do tubo de queda

def d_tq(caudal_calculo, taxa_ocupacao = 0.17):
    dia = round(4.4205*(caudal_calculo**(0.375))*(taxa_ocupacao**(-0.625)),2)
    return dia

#Calculo do diametro de cálculo através da formula de Mannig-Stricker, utilizado em RAMIS NÃO INDIVIDUAIS e COLECTORES

#Calculo para escoamentos a secção cheia ou meia secção, com conversão do caudal de l/min para m3/s
def d_rni(caudal_calculo, inclinacao, rugosidade, tipo="meia"):

    q = caudal_calculo/(60*1000)
    v = 0.4980 if tipo =="meia" else 0.6459
    dia = round((q**(3/8))/(v*(rugosidade**(3/8))*(inclinacao**(3/16)))*1000,2)
    
    return dia

#Escolha do diametro comercial consoante os diametros de cálculos

def d_pvc(diametro, item="tq"):
    thresholds = [
        (26, 32), (34, 40), (44, 50), (57, 63), 
        (69, 75), (84, 90), (103, 110), (118, 125), 
        (133, 140), (152, 160)
    ]
    
    # Determine the base return value based on thresholds
    return_value = 200  # Default return value
    for threshold, value in thresholds:
        if diametro <= threshold:
            return_value = value
            break

    # Apply conditions based on item
    if item == "tq":
        return max(return_value, 110)
    elif item == "rni":
        return max(return_value, 125)

    return return_value


def tensao_arrastamento(diameter, slope):
    t = round(9800*((diameter/1000)/4)*(slope/100), 2)

    return t


#testing purposes
if __name__ == "__main__":
    #Caudal de cálculo
    qs = 540
    taxa_ocupacao = 0.17


    caudal_cal = q_cal(qs)

    dia_tq = d_tq(caudal_cal)

    dia_rni = d_rni(caudal_cal,i,k, tipo="meia")

    diametro_tq = d_pvc(dia_tq)
    diametro_rni = d_pvc(dia_rni)

    teste = tensao_arrastamento(105.69,1)
    print(teste)
