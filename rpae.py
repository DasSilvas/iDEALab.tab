# -*- coding: utf-8 -*-
#!python3
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
def d_rni(caudal_calculo, inclinacao = 0.01, rugosidade = 120, tipo="meia"):

    if inclinacao < 0.01:
        inclinacao = 0.01
    
    q = caudal_calculo/(60*1000)
    v = 0.4980 if tipo =="meia" else 0.6459
    dia = round((q**(0.375))/(v*(rugosidade**(0.375))*(inclinacao**(0.1875)))*1000,2)
    
    return dia

#Escolha do diametro comercial consoante os diametros de cálculos

def d_pvc(diametro, item="rni"):
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
    elif item == "colector":
        return max(return_value, 125)
    else:
        return return_value


def tensao_arrastamento(diameter, slope):
    t = round(9800*((diameter/1000)/4)*(slope/100), 2)

    return t

def calc_h_over_D(Q_l_min, D_mm, i_percent, K=100, gamma=9800, section="parcial"):
    """
    Calcula parâmetros hidráulicos de um coletor circular, usando coeficiente K (Strickler).
    
    Parâmetros:
        Q_l_min : caudal em litros por minuto
        D_mm    : diâmetro interno da tubagem em mm
        i_percent : declive da tubagem em %
        K       : coeficiente de Strickler [m^(1/3)/s], default 120
        gamma   : peso específico da água (N/m³), default 9800
        section : "parcial" (default) ou "cheia"
        
    Retorna:
        dicionário com resultados
    """
    
    # --- Conversões ---
    Q = Q_l_min / 1000 / 60       # L/mSin -> m³/s
    D = D_mm              # mm -> m
    i = float(i_percent)          # % -> fração
    #n = 1 / K                     # Manning
    
    if D <= 0:
        raise ValueError("Diâmetro inválido: deve ser > 0 mm")

    if i < 0.01:
        i = 0.01

    # --- Tubo cheio ---
    A_full = (math.pi * (D**2)) *0.25
    P_full = math.pi * D
    if P_full == 0:
        raise ZeroDivisionError("Perímetro hidráulico inválido (P_full == 0).")
    R_full = A_full / P_full
    Q_full = K * A_full * (R_full**(0.67)) * math.sqrt(i)
    
    # Inicializa variáveis
    h_over_D = 1.0
    h = D
    A = A_full
    P = P_full
    R = R_full
    v = Q / A_full if A_full > 0 else 0
    theta = 2 * math.pi
    
    if section == "parcial":
        phi = Q / Q_full   # fração do caudal cheio

        # --- Função adimensional F(θ) ---
        def F(theta):
            if theta <= 0 or theta >= 2*math.pi:
                return -phi
            area_ratio = (theta - math.sin(theta)) / (2*math.pi)
            R_ratio = (theta - math.sin(theta)) / theta
            return area_ratio * (R_ratio**(2/3)) - phi

        # --- Resolver para θ (bisseção simples) ---
        a, b = 1e-6, 2*math.pi - 1e-6
        for _ in range(100):
            mid = (a + b) / 2
            if F(a) * F(mid) <= 0:
                b = mid
            else:
                a = mid
        theta = (a + b) / 2

        # --- Calcular h/D ---
        h_over_D = (1 - math.cos(theta/2)) / 2
        h = h_over_D * D

        # --- Geometria parcial ---
        A = (D**2 / 8) * (theta - math.sin(theta))
        P = (D/2) * theta
        R = A / P
        v = Q / A if A > 0 else 0
    
    # --- Tensão de arrastamento ---
    tau = gamma * R * i  # N/m²

    return tau, v, h_over_D

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
