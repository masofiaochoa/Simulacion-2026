import numpy as np
from scipy.stats import (
    uniform,
    expon,
    gamma,
    norm,
    nbinom,
    binom,
    hypergeom,
    poisson,
)
from config import N_GLOBAL
from inverse_transform_generators import (
    generar_uniforme,
    generar_exponencial,
    generar_gamma,
    generar_normal,
    generar_pascal,
    generar_binomial,
    generar_hipergeometrica,
    generar_poisson,
    generar_empirica_discreta,
)
from rejection_method_generators import (
    generar_uniforme_rechazo,
    generar_exponencial_rechazo,
    generar_normal_rechazo,
)
from plotter import testear_distribucion


if __name__ == "__main__":
    print(f"Iniciando simulación con {N_GLOBAL} muestras por distribución...")

    # --- 1. UNIFORME ---
    a_unif, b_unif = 2, 10
    # Test Uniforme (T. Inversa)
    testear_distribucion(
        "Uniforme",
        generar_uniforme,
        (a_unif, b_unif),
        lambda x, a, b: uniform.pdf(x, loc=a, scale=b - a),
        N_muestras=N_GLOBAL,
        es_discreta=False,
        usa_rechazo=False,
        rango_grafica_teorica=(a_unif - 1, b_unif + 1),
    )
    # Test Uniforme (Rechazo)
    testear_distribucion(
        "Uniforme",
        generar_uniforme_rechazo,
        (a_unif, b_unif),
        lambda x, a, b: uniform.pdf(x, loc=a, scale=b - a),
        N_muestras=N_GLOBAL,
        es_discreta=False,
        usa_rechazo=True,
        rango_grafica_teorica=(a_unif - 1, b_unif + 1),
    )

    # --- 2. EXPONENCIAL ---
    lam_exp = 0.5
    # Test Exponencial (T. Inversa)
    testear_distribucion(
        "Exponencial",
        generar_exponencial,
        (lam_exp,),
        lambda x, l: expon.pdf(x, scale=1 / l),
        N_muestras=N_GLOBAL,
        es_discreta=False,
        usa_rechazo=False,
        rango_grafica_teorica=(0, expon.ppf(0.999, scale=1 / lam_exp)),
    )
    # Test Exponencial (Rechazo)
    testear_distribucion(
        "Exponencial",
        generar_exponencial_rechazo,
        (lam_exp,),
        lambda x, l: expon.pdf(x, scale=1 / l),
        N_muestras=N_GLOBAL,
        es_discreta=False,
        usa_rechazo=True,
        rango_grafica_teorica=(0, expon.ppf(0.999, scale=1 / lam_exp)),
    )

    # --- 3. GAMMA (T. Inversa) ---
    k_g, th_g = 2.0, 1.5  # Modificado k>=1 para verificar estabilidad en transformada inversa
    testear_distribucion(
        "Gamma",
        generar_gamma,
        (k_g, th_g),
        lambda x, k, t: gamma.pdf(x, a=k, scale=t),
        N_muestras=N_GLOBAL,
        es_discreta=False,
        usa_rechazo=False,
        rango_grafica_teorica=(0, gamma.ppf(0.999, a=k_g, scale=th_g)),
    )

    # --- 4. NORMAL ---
    mu_norm, sigma_norm = 5, 2
    # Test Normal (T. Inversa)
    testear_distribucion(
        "Normal",
        generar_normal,
        (mu_norm, sigma_norm),
        lambda x, mu, sig: norm.pdf(x, loc=mu, scale=sig),
        N_muestras=N_GLOBAL,
        es_discreta=False,
        usa_rechazo=False,
        rango_grafica_teorica=(
            norm.ppf(0.001, mu_norm, sigma_norm),
            norm.ppf(0.999, mu_norm, sigma_norm),
        ),
    )
    # Test Normal (Rechazo)
    testear_distribucion(
        "Normal",
        generar_normal_rechazo,
        (mu_norm, sigma_norm),
        lambda x, mu, sig: norm.pdf(x, loc=mu, scale=sig),
        N_muestras=N_GLOBAL,
        es_discreta=False,
        usa_rechazo=True,
        rango_grafica_teorica=(
            norm.ppf(0.001, mu_norm, sigma_norm),
            norm.ppf(0.999, mu_norm, sigma_norm),
        ),
    )

    # --- 5. PASCAL (T. Inversa) ---
    r_pasc, p_pasc = 5, 0.4
    testear_distribucion(
        "Pascal",
        generar_pascal,
        (r_pasc, p_pasc),
        lambda k, r, p: nbinom.pmf(k, r, p),
        N_muestras=N_GLOBAL,
        es_discreta=True,
        usa_rechazo=False,
        rango_grafica_teorica=(0, int(nbinom.ppf(0.999, n=r_pasc, p=p_pasc)) + 5),
    )

    # --- 6. BINOMIAL (T. Inversa) ---
    n_bin, p_bin = 25, 0.25
    testear_distribucion(
        "Binomial",
        generar_binomial,
        (n_bin, p_bin),
        lambda k, n, p: binom.pmf(k, n, p),
        N_muestras=N_GLOBAL,
        es_discreta=True,
        usa_rechazo=False,
        rango_grafica_teorica=(0, n_bin),
    )

    # --- 7. HIPERGEOMÉTRICA (T. Inversa) ---
    N_h, K_h, n_h = 60, 15, 20
    testear_distribucion(
        "Hipergeométrica",
        generar_hipergeometrica,
        (N_h, K_h, n_h),
        lambda k, M, n, N_sample: hypergeom.pmf(k, M, n, N_sample),
        N_muestras=N_GLOBAL,
        es_discreta=True,
        usa_rechazo=False,
        rango_grafica_teorica=(max(0, n_h - (N_h - K_h)), min(n_h, K_h)),
    )

    # --- 8. POISSON (T. Inversa) ---
    lam_pois = 8.0
    testear_distribucion(
        "Poisson",
        generar_poisson,
        (lam_pois,),
        lambda k, l: poisson.pmf(k, l),
        N_muestras=N_GLOBAL,
        es_discreta=True,
        usa_rechazo=False,
        rango_grafica_teorica=(0, int(poisson.ppf(0.9999, lam_pois)) + 5),
    )

    # --- 9. EMPÍRICA DISCRETA (T. Inversa) ---
    val_emp, prob_emp = [1, 2, 3, 4, 5, 6], [0.1, 0.1, 0.3, 0.2, 0.15, 0.15]

    def pmf_emp(k_val, v_list, p_list):
        res = []
        k_val_iter = np.atleast_1d(k_val)
        for kv in k_val_iter:
            try:
                idx = v_list.index(kv)
                res.append(p_list[idx])
            except ValueError:
                res.append(0)
        return np.array(res)

    testear_distribucion(
        "Empírica Discreta",
        generar_empirica_discreta,
        (val_emp, prob_emp),
        lambda k, v, p: pmf_emp(k, v, p),
        N_muestras=N_GLOBAL,
        es_discreta=True,
        usa_rechazo=False,
        rango_grafica_teorica=(min(val_emp), max(val_emp)),
    )

    print("\n--- Todas las simulaciones finalizadas. Revisa la carpeta 'graficas/'. ---")