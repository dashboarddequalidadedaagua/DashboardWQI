"""
Metricas de erro das previsoes contra o IQA real (funcoes puras, sem
Streamlit, testaveis isoladamente).

y = IQA real; p = previsao exatamente como exportada (RL ja arredondada
com np.round; Arvore como sai do modelo). Valor que nao pode ser
calculado volta como None e e exibido como "nao se aplica".
"""

import math
import re
from decimal import ROUND_HALF_UP, Decimal

import numpy as np
import pandas as pd

import config


def calcular_metricas(y, p):
    """R2, MAE, RMSE e MAPE (%) de um modelo.

    R2 segue a definicao do sklearn (r2_score): 1 - SS_res / SS_tot, pode
    ser negativo. MAPE exclui as linhas com y = 0; as posicoes excluidas
    voltam em 'indices_zero' para o registro em Avisos.
    """
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    erro = y - p

    ss_res = float(np.sum(erro ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else None

    mae = float(np.mean(np.abs(erro)))
    rmse = float(np.sqrt(np.mean(erro ** 2)))

    nao_zero = y != 0
    if nao_zero.any():
        mape = float(100 * np.mean(np.abs(erro[nao_zero]) / np.abs(y[nao_zero])))
    else:
        mape = None

    return {
        'R2': r2,
        'MAE': mae,
        'RMSE': rmse,
        'MAPE': mape,
        'indices_zero': np.flatnonzero(~nao_zero).tolist(),
    }


def percentuais_faixas_erro(y, p):
    """% das amostras em cada faixa de erro absoluto |y - p| (config.FAIXAS_ERRO).

    O limite de cima pertence a faixa. As faixas somam 100%. Sem amostras,
    devolve None.
    """
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    if len(y) == 0:
        return None
    erro = np.abs(y - p)
    percentuais = []
    for _, _, lo, hi in config.FAIXAS_ERRO:
        dentro = erro >= 0 if lo is None else erro > lo
        if hi is not None:
            dentro = dentro & (erro <= hi)
        percentuais.append(float(100 * np.mean(dentro)))
    return percentuais


def categoria_iqa(valor):
    """Categoria CETESB de um valor de IQA (config.FAIXAS_IQA). O limite de
    cima pertence a faixa; abaixo de 0 e Pessima, acima de 100 e Otima."""
    for nome, _, hi, _, _ in config.FAIXAS_IQA:
        if valor <= hi:
            return nome
    return config.FAIXAS_IQA[-1][0]


def classificar_monitoramento(y):
    """Amostras do grafico de monitoramento abaixo e acima dos limites.

    Mesma regra das faixas da CETESB (o limite de cima pertence a faixa):
    ruim ou pessimo = IQA ate o LI (inclusive); otimo = IQA acima do LS
    (exatamente o LS e Boa). Compara o valor completo, sem arredondar.
    Devolve (baixo, alto), dois arrays booleanos do tamanho de y.
    """
    y = np.asarray(y, dtype=float)
    return y <= config.LI_MONITORAMENTO, y > config.LS_MONITORAMENTO


# ---------------------------------------------------------------------------
# Pontos de Coleta
# ---------------------------------------------------------------------------
def normalizar_ponto(valor):
    """Valor da coluna Ponto de Coleta como texto. O grupo e o valor como o
    usuario digitou (sem mexer em maiusculas, acentos ou espacos internos).

    Celula vazia ou so com espacos volta None. Numero inteiro vindo do
    Excel como 5.0 volta '5'.
    """
    if valor is None or valor is pd.NA or valor is pd.NaT:
        return None
    if isinstance(valor, bool):
        return str(valor)
    if isinstance(valor, (float, np.floating)):
        if math.isnan(valor):
            return None
        if float(valor).is_integer():
            return str(int(valor))
    elif isinstance(valor, (int, np.integer)):
        return str(int(valor))
    texto = str(valor).strip()
    return texto or None


def _chave_natural(texto):
    """Numeros dentro do texto comparados como numeros ('2 X' antes de '10 X')."""
    partes = re.split(r'(\d+)', texto)
    return tuple(int(p) if i % 2 else p.casefold() for i, p in enumerate(partes))


def ordenar_pontos(pontos):
    """Pontos de coleta distintos (sem os vazios) na ordem da tela:
    1o quantidade de linhas (decrescente), 2o ordem natural, 3o ordem de
    aparicao. Recebe os valores ja normalizados (normalizar_ponto)."""
    contagem = {}
    for p in pontos:
        if p is not None:
            contagem[p] = contagem.get(p, 0) + 1
    # sorted e estavel: no empate total fica a ordem de aparicao
    return sorted(contagem, key=lambda p: (-contagem[p], _chave_natural(p)))


def tabela_pontos(pontos, y, p_rl, p_dta):
    """Metricas por ponto de coleta (R2, MAE, MAPE, RMSE dos dois modelos).

    Recebe so as linhas apos o filtro com IQA real valido, com o ponto ja
    normalizado (None = vazio, fica fora). Devolve uma lista de dicts com
    'ponto', 'n' (linhas do ponto que entraram no calculo), 'suficiente' e
    'rl'/'dta' (dict de metricas ou None), na ordem de ordenar_pontos.
    """
    pontos = list(pontos)
    y = np.asarray(y, dtype=float)
    p_rl = np.asarray(p_rl, dtype=float)
    p_dta = np.asarray(p_dta, dtype=float)

    tabela = []
    for ponto in ordenar_pontos(pontos):
        idx = np.asarray([i for i, p in enumerate(pontos) if p == ponto])
        suficiente = len(idx) >= config.MINIMO_LINHAS_PONTO
        rl = dta = None
        if suficiente:
            rl = calcular_metricas(y[idx], p_rl[idx])
            dta = calcular_metricas(y[idx], p_dta[idx])
        tabela.append({'ponto': ponto, 'n': len(idx), 'suficiente': suficiente,
                       'rl': rl, 'dta': dta})
    return tabela


# ---------------------------------------------------------------------------
# Formatacao para a tela (so exibicao; calculos e Excel usam o valor completo)
# ---------------------------------------------------------------------------
def arredondar(valor, casas):
    """Arredonda para o mais proximo; no empate exato, para longe do zero
    (igual ao ARRED do Excel). Devolve Decimal, sem sinal quando da zero.
    None, NaN e infinito voltam None."""
    if valor is None:
        return None
    valor = float(valor)
    if not math.isfinite(valor):
        return None
    d = Decimal(str(valor)).quantize(Decimal(1).scaleb(-casas), rounding=ROUND_HALF_UP)
    return d.copy_abs() if d == 0 else d


def formatar_numero(valor, casas=config.CASAS_WQI, sufixo=''):
    """1234.56 -> '1.234,6' (casas=1); None -> 'nao se aplica'. Nunca '-0,0'."""
    d = arredondar(valor, casas)
    if d is None:
        return config.NAO_SE_APLICA
    texto = f"{d:,.{casas}f}"
    texto = texto.replace(',', '_').replace('.', ',').replace('_', '.')
    return texto + sufixo


def melhor_modelo(valor_rl, valor_dta, casas, sentido):
    """'rl', 'dta' ou None, comparando os valores ja arredondados como exibidos.

    sentido: 'maior' (R2) ou 'menor' (erros). Empate ou valor None: None.
    """
    a, b = arredondar(valor_rl, casas), arredondar(valor_dta, casas)
    if a is None or b is None or a == b:
        return None
    if sentido == 'maior':
        return 'rl' if a > b else 'dta'
    return 'rl' if a < b else 'dta'


def formatar_par(valor_rl, valor_dta, casas=config.CASAS_WQI, sufixo='', grifo=None):
    """'RL = 0,89 | Arvore = 0,91' (MAPE com sufixo '%').

    grifo: 'rl' ou 'dta' envolve o trecho daquele modelo em config.FORMATO_GRIFO.
    """
    trecho_rl, trecho_dta = config.FORMATO_PAR.split(config.SEPARADOR_PAR)
    trecho_rl = trecho_rl.format(rl=formatar_numero(valor_rl, casas, sufixo))
    trecho_dta = trecho_dta.format(dta=formatar_numero(valor_dta, casas, sufixo))
    if grifo == 'rl':
        trecho_rl = config.FORMATO_GRIFO.format(texto=trecho_rl)
    elif grifo == 'dta':
        trecho_dta = config.FORMATO_GRIFO.format(texto=trecho_dta)
    return config.SEPARADOR_PAR.join([trecho_rl, trecho_dta])
