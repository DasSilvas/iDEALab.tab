import math

def calc_h_over_D(Q_l_min, D_mm, i_percent, K=120, gamma=9800, section="parcial"):
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
    Q = Q_l_min / 1000 / 60       # L/min -> m³/s
    D = D_mm / 1000               # mm -> m
    i = i_percent / 100           # % -> fração
    n = 1 / K                     # Manning
    
    # --- Tubo cheio ---
    A_full = math.pi * D**2 / 4
    P_full = math.pi * D
    R_full = A_full / P_full
    Q_full = (1/n) * A_full * (R_full**(2/3)) * math.sqrt(i)
    
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
    
    # --- Verificações de autolimpeza ---
    autolimpeza_vel = v >= 0.5
    autolimpeza_tau = tau >= 2.45
    
    return {
        "Q (m3/s)": Q,
        "D (m)": D,
        "Declive i": i,
        "K": K,
        "n": n,
        "Q_full (m3/s)": Q_full,
        "theta (rad)": theta,
        "h/D": h_over_D,
        "h (m)": h,
        "A (m2)": A,
        "P (m)": P,
        "R (m)": R,
        "Velocidade (m/s)": v,
        "Tau (N/m2)": tau,
        "Cumpre autolimpeza (velocidade)": autolimpeza_vel,
        "Cumpre autolimpeza (tensão)": autolimpeza_tau
    }

# --- Exemplo ---
res_parcial = calc_h_over_D(Q_l_min=1710, D_mm=140, i_percent=1, K=100, section="parcial")
print("=== Secção Parcial ===")
for k, v in res_parcial.items():
    print(f"{k}: {v}")
