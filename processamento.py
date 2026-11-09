"""
Leitura da planilha, pipeline de previsao do Douglas e montagem do Excel
(sem Streamlit, testavel isoladamente).

O pipeline (filtro, remocao de TON e WQI antes do modelo, imputer,
winsorizacao, scaler, modelos, np.round da RL, ORDEM_VARIAVEIS) e o mesmo
do treino. Os objetos carregados com joblib.load() sao usados SEMPRE com
.transform()/.predict(), nunca com o metodo de ajuste.

Dentro do pipeline as colunas continuam com as siglas em ingles (o scaler
e o imputer guardam esses nomes). O portugues entra so na leitura
(cabecalhos aceitos nas duas linguas) e na saida (tela, Excel, avisos).
"""

import csv
import io
import os
import re
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
from scipy.stats.mstats import winsorize

import config
import metricas

PASTA = os.path.dirname(os.path.abspath(__file__))


class LeituraError(Exception):
    pass


def sigla(interna):
    """Sigla exibida (portugues) de uma sigla interna; outras ficam iguais."""
    return config.SIGLAS_EXIBIDAS.get(interna, interna)


# ---------------------------------------------------------------------------
# Modelos
# ---------------------------------------------------------------------------
def carregar_modelos(pasta=PASTA):
    arq = config.ARQUIVOS_MODELO
    lr = joblib.load(os.path.join(pasta, arq['lr']))
    dta = joblib.load(os.path.join(pasta, arq['dta']))
    scaler = joblib.load(os.path.join(pasta, arq['scaler']))
    imputer = joblib.load(os.path.join(pasta, arq['imputer']))
    return lr, dta, scaler, imputer


def ficha_modelos(lr, dta, imputer):
    """Numeros da ficha dos modelos lidos dos objetos carregados."""
    return {
        'n_variaveis': int(lr.n_features_in_),
        'profundidade': int(dta.get_depth()),
        'folhas': int(dta.get_n_leaves()),
        'vizinhos': int(imputer.n_neighbors),
    }


# ---------------------------------------------------------------------------
# Leitura
# ---------------------------------------------------------------------------
def ler_planilha(nome, dados):
    """Le .xlsx, .xls ou .csv a partir dos bytes do arquivo."""
    ext = os.path.splitext(nome)[1].lower().lstrip('.')
    if ext not in config.FORMATOS_ACEITOS:
        raise LeituraError(nome)
    try:
        if ext == 'xlsx':
            return pd.read_excel(io.BytesIO(dados), engine='openpyxl')
        if ext == 'xls':
            return pd.read_excel(io.BytesIO(dados), engine='xlrd')
        return _ler_csv(dados)
    except Exception as e:  # arquivo corrompido, formato trocado etc.
        raise LeituraError(str(e)) from e


def _ler_csv(dados):
    for codificacao in ('utf-8-sig', 'latin-1'):
        try:
            texto = dados.decode(codificacao)
            break
        except UnicodeDecodeError:
            continue
    amostra = texto[:5000]
    try:
        sep = csv.Sniffer().sniff(amostra, delimiters=';,\t').delimiter
    except csv.Error:
        sep = ','
    decimal = ',' if sep == ';' else '.'
    return pd.read_csv(io.StringIO(texto), sep=sep, decimal=decimal)


_PADRAO_UNIDADE = re.compile(r'^\s*([A-Za-z]+)\s*[\(\[]\s*(.*?)\s*[\)\]]\s*$')
_SIGLAS_INTERNAS = config.ORDEM_VARIAVEIS + [config.COLUNA_TON, config.COLUNA_WQI]
# cabecalho (maiusculo) -> sigla interna; vale a forma em ingles e a em portugues
_SIGLAS_ACEITAS = {}
for _s in _SIGLAS_INTERNAS:
    _SIGLAS_ACEITAS[_s.upper()] = _s
    _SIGLAS_ACEITAS[sigla(_s).upper()] = _s
# unidade esperada de cada sigla interna (mensagem de unidade errada)
_UNIDADE_ESPERADA = {s: u for s, _, u in config.DICIONARIO_VARIAVEIS}
for _col, _, _u, _, _aceito in config.COLUNAS_OPCIONAIS_MODELO:
    if _aceito in _SIGLAS_INTERNAS:
        _UNIDADE_ESPERADA[_aceito] = _u


def _normalizar_unidade(texto):
    return re.sub(r'\s+', '', str(texto)).lower()


def normalizar_colunas(df):
    """Padroniza os nomes das colunas para as siglas internas.

    Aceita a sigla em ingles ou em portugues (ex.: BOD ou DBO), com
    qualquer combinacao de maiusculas e, opcionalmente, a unidade no
    cabecalho (ex.: "DBO (mg/L)"). Unidade diferente das formas aceitas
    gera bloqueio. A mesma variavel em duas colunas: vale a primeira, a
    outra e descartada e entra em Avisos. Coluna de data vira "Data".
    Ponto de Coleta: vale o nome de maior prioridade em NOMES_ACEITOS_PONTO.

    Devolve (df, bloqueios, avisos).
    """
    renomear = {}
    descartar = []
    bloqueios = []
    avisos = []
    usados = {}            # sigla interna -> nome da coluna usada
    tem_data = False
    candidatos_ponto = []  # (prioridade, coluna)
    for col in df.columns:
        nome = str(col).strip()
        texto, unidade = nome, None
        m = _PADRAO_UNIDADE.match(nome)
        if m and m.group(1).upper() in _SIGLAS_ACEITAS:
            texto, unidade = m.group(1), m.group(2)
        alvo = _SIGLAS_ACEITAS.get(texto.upper())
        if alvo is not None:
            if alvo in usados:
                avisos.append((config.AVISO_COLUNA_DUPLICADA.format(
                    sigla=sigla(alvo), col1=usados[alvo], col2=nome), 0, ''))
                descartar.append(col)
                continue
            if unidade is not None and alvo in config.UNIDADES_ACEITAS:
                if _normalizar_unidade(unidade) not in config.UNIDADES_ACEITAS[alvo]:
                    bloqueios.append(config.BLOQUEIO_UNIDADE.format(
                        coluna=sigla(alvo), unidade=unidade, esperada=_UNIDADE_ESPERADA[alvo]))
            usados[alvo] = nome
            renomear[col] = alvo
        elif nome.lower() in config.NOMES_ACEITOS_DATA and not tem_data:
            renomear[col] = config.COLUNA_DATA
            tem_data = True
        elif nome.lower() in config.NOMES_ACEITOS_PONTO:
            candidatos_ponto.append((config.NOMES_ACEITOS_PONTO.index(nome.lower()), col))
    if candidatos_ponto:
        renomear[min(candidatos_ponto, key=lambda c: c[0])[1]] = config.COLUNA_PONTO
    # coluna nao usada com o mesmo nome de uma coluna padronizada sai (evita
    # duas colunas com o mesmo nome)
    alvos = set(renomear.values())
    descartar += [c for c in df.columns if c not in renomear and str(c).strip() in alvos]
    df = df.drop(columns=descartar).rename(columns=renomear)
    return df, bloqueios, avisos


def _para_numero(serie):
    """Converte para numero; texto vira vazio. Devolve (serie, mascara_texto)."""
    if pd.api.types.is_numeric_dtype(serie):
        return serie, pd.Series(False, index=serie.index)
    texto = serie.astype('string').str.strip()
    vazio = serie.isna() | (texto == '')
    convertido = pd.to_numeric(texto.str.replace(',', '.', regex=False), errors='coerce')
    mascara_texto = convertido.isna() & ~vazio
    return convertido.astype(float), mascara_texto.fillna(False).astype(bool)


def _lista_linhas(linhas):
    texto = ', '.join(str(int(x)) for x in linhas)
    return texto if len(texto) < 32000 else texto[:32000] + ' ...'


def _faltando(siglas_internas):
    """'DBO (ou BOD), CT (ou THC)'; sem repetir quando as formas sao iguais (TUR, pH)."""
    itens = []
    for s in siglas_internas:
        if sigla(s).upper() == s.upper():
            itens.append(sigla(s))
        else:
            itens.append(config.ITEM_COLUNA_FALTANDO.format(exibida=sigla(s), interna=s))
    return ', '.join(itens)


# ---------------------------------------------------------------------------
# Processamento completo
# ---------------------------------------------------------------------------
def processar(nome, dados, modelos):
    """Le o arquivo, roda o pipeline e calcula tudo o que a tela e o Excel usam.

    Devolve um dict (serializavel, para o cache do Streamlit).
    """
    r = {
        'nome_arquivo': nome,
        'lido': False,
        'bloqueios': [],
        'avisos': [],
        'linhas_lidas': 0,
        'linhas_removidas': 0,
        'removidas': None,
        'res': None,
        'ajustes': None,
        'tem_data': False,
        'tem_coluna_ponto': False,
        'tem_pontos': False,
        'n_wqi_validas': 0,
        'metricas': None,
        'pontos': None,
        'medianas': None,
        'faixas_erro': None,
    }

    try:
        df = ler_planilha(nome, dados)
    except LeituraError:
        r['bloqueios'].append(config.BLOQUEIO_LEITURA)
        return r
    r['lido'] = True

    for col in config.COLUNAS_INDICE_LIXO:
        if col in df.columns:
            df = df.drop(columns=[col])
    df = df.reset_index(drop=True)
    r['linhas_lidas'] = len(df)
    if len(df) == 0:
        r['bloqueios'].append(config.BLOQUEIO_VAZIO)
        return r

    df, bloqueios_unidade, avisos_colunas = normalizar_colunas(df)
    r['avisos'] += avisos_colunas
    faltando = [c for c in config.ORDEM_VARIAVEIS if c not in df.columns]
    if faltando:
        r['bloqueios'].append(config.BLOQUEIO_COLUNAS.format(colunas=_faltando(faltando)))
    r['bloqueios'] += bloqueios_unidade
    if r['bloqueios']:
        return r

    bruto = df.copy()
    linha_original = pd.Series(df.index + 2, index=df.index)  # linha 1 = cabecalho
    avisos = r['avisos']

    # numeros (texto no lugar de numero vira celula vazia)
    for col in config.ORDEM_VARIAVEIS + [config.COLUNA_TON, config.COLUNA_WQI]:
        if col in df.columns:
            df[col], texto = _para_numero(df[col])
            if texto.any():
                avisos.append((config.AVISO_NAO_NUMERICO.format(n=int(texto.sum()), coluna=sigla(col)),
                               int(texto.sum()), _lista_linhas(linha_original[texto])))

    # data (nao entra no modelo)
    data = None
    if config.COLUNA_DATA in df.columns:
        bruta = df[config.COLUNA_DATA]
        if pd.api.types.is_datetime64_any_dtype(bruta):
            data = bruta
        else:
            data = pd.to_datetime(bruta, errors='coerce', dayfirst=True)
        df = df.drop(columns=[config.COLUNA_DATA])

    # filtro de valores fora da faixa usada no treino dos modelos (mesmo do treino)
    condicoes = {}
    for var, (minimo, maximo) in config.LIMITES_FILTRO.items():
        if var not in df.columns:
            continue
        if minimo is not None:
            condicoes[(var, 'abaixo', minimo)] = df[var] < minimo
        if maximo is not None:
            condicoes[(var, 'acima', maximo)] = df[var] > maximo
    mask_absurdo = pd.Series(False, index=df.index)
    for cond in condicoes.values():
        mask_absurdo = mask_absurdo | cond

    motivos = []
    for i in df.index[mask_absurdo]:
        partes = []
        for (var, lado, lim), cond in condicoes.items():
            if cond[i]:
                modelo_txt = config.MOTIVO_ACIMA if lado == 'acima' else config.MOTIVO_ABAIXO
                partes.append(modelo_txt.format(var=sigla(var), maximo=lim, minimo=lim))
        motivos.append('; '.join(partes))
    removidas = bruto[mask_absurdo].copy()
    removidas.insert(0, config.COLUNA_X_MOTIVO, motivos, allow_duplicates=True)
    removidas.insert(0, config.COLUNA_X_LINHA, linha_original[mask_absurdo].values,
                     allow_duplicates=True)
    # cabecalhos sempre em portugues, qualquer que seja a lingua enviada
    removidas = removidas.rename(columns={s: sigla(s) for s in _SIGLAS_INTERNAS})
    r['removidas'] = removidas.reset_index(drop=True)
    r['linhas_removidas'] = int(mask_absurdo.sum())

    pct = 100 * r['linhas_removidas'] / r['linhas_lidas']
    if pct > config.ALERTA_REMOCAO_PCT:
        avisos.append((config.AVISO_REMOCAO_ALTA, r['linhas_removidas'], ''))

    df_filtrado = df[~mask_absurdo].copy()
    if len(df_filtrado) == 0:
        r['bloqueios'].append(config.BLOQUEIO_TUDO_REMOVIDO)
        return r

    # WQI real preservado antes de remover a coluna do X do modelo
    if config.COLUNA_WQI in df_filtrado.columns:
        wqi_real = df_filtrado[config.COLUNA_WQI].astype(float)
    else:
        wqi_real = pd.Series(np.nan, index=df_filtrado.index)

    # -----------------------------------------------------------------------
    # PIPELINE DO DOUGLAS (nao alterar): remove TON e WQI, ordem fixa das
    # variaveis, imputer.transform, winsorizacao, scaler.transform, predict.
    # -----------------------------------------------------------------------
    lr, dta, scaler, imputer = modelos
    X_bruto = df_filtrado.drop(columns=config.COLUNAS_REMOVIDAS_ANTES_DO_MODELO, errors='ignore')
    X_bruto = X_bruto[config.ORDEM_VARIAVEIS]

    X_imputado = pd.DataFrame(
        imputer.transform(X_bruto),
        columns=X_bruto.columns,
        index=X_bruto.index
    )
    X = X_imputado.copy()
    for c in config.COLUNAS_WINSORIZE:
        X[c] = winsorize(X[c], limits=config.LIMITES_WINSORIZE)

    X_scaled = scaler.transform(X)

    pred_rl = np.round(lr.predict(X_scaled))
    pred_dta = dta.predict(X_scaled)
    # -----------------------------------------------------------------------

    lo_filtrado = linha_original[df_filtrado.index]

    # ajustes automaticos (celulas preenchidas e valores extremos ajustados)
    ajustes = []
    vazias = X_bruto.isna()
    for c in config.ORDEM_VARIAVEIS:
        for i in X_bruto.index[vazias[c]]:
            ajustes.append((lo_filtrado[i], sigla(c), config.AJUSTE_IMPUTACAO, None, X_imputado.at[i, c]))
        mudou = X_imputado[c].values != X[c].values
        for i in X.index[mudou]:
            ajustes.append((lo_filtrado[i], sigla(c), config.AJUSTE_WINSORIZACAO,
                            X_imputado.at[i, c], X.at[i, c]))
    ajustes_df = pd.DataFrame(ajustes, columns=config.COLUNAS_X_AJUSTES)
    r['ajustes'] = ajustes_df.sort_values(config.COLUNAS_X_AJUSTES[:2], kind='stable').reset_index(drop=True)
    r['celulas_imputadas'] = int(vazias.values.sum())
    r['valores_winsorizados'] = int((ajustes_df['Ajuste'] == config.AJUSTE_WINSORIZACAO).sum())

    # tabela de previsoes
    res = pd.DataFrame({'Linha_original': lo_filtrado.values})
    if data is not None:
        res[config.COLUNA_DATA] = data[df_filtrado.index].values
        datas_invalidas = res[config.COLUNA_DATA].isna()
        if datas_invalidas.any():
            avisos.append((config.AVISO_DATA_INVALIDA.format(n=int(datas_invalidas.sum())),
                           int(datas_invalidas.sum()), _lista_linhas(res['Linha_original'][datas_invalidas])))
        r['tem_data'] = True
    else:
        avisos.append((config.AVISO_SEM_DATA, 0, ''))
    if config.COLUNA_PONTO in df.columns:
        r['tem_coluna_ponto'] = True
        pontos = [metricas.normalizar_ponto(v) for v in bruto.loc[df_filtrado.index, config.COLUNA_PONTO]]
        res[config.COLUNA_PONTO] = pd.Series(pontos, dtype=object)
        vazio = res[config.COLUNA_PONTO].isna()
        if vazio.any():
            avisos.append((config.AVISO_PONTO_VAZIO.format(n=int(vazio.sum())),
                           int(vazio.sum()), _lista_linhas(res['Linha_original'][vazio])))
    res['WQI_real'] = wqi_real.values
    res['Previsao_RL'] = pred_rl
    res['Previsao_DTA'] = pred_dta
    for c in config.ORDEM_VARIAVEIS:
        res[c] = X[c].values
    r['res'] = res

    # metricas contra o IQA real (so linhas com IQA real valido)
    validas = res[res['WQI_real'].notna()].reset_index(drop=True)
    r['n_wqi_validas'] = len(validas)
    sem_wqi = res['WQI_real'].isna()
    if sem_wqi.any():
        avisos.append((config.AVISO_SEM_WQI.format(n=int(sem_wqi.sum())),
                       int(sem_wqi.sum()), _lista_linhas(res['Linha_original'][sem_wqi])))
    if len(validas):
        met_rl = metricas.calcular_metricas(validas['WQI_real'], validas['Previsao_RL'])
        met_dta = metricas.calcular_metricas(validas['WQI_real'], validas['Previsao_DTA'])
        r['metricas'] = {'rl': met_rl, 'dta': met_dta}
        # medianas do eixo do IQA calculadas nas mesmas linhas
        r['medianas'] = {'real': float(validas['WQI_real'].median()),
                         'rl': float(validas['Previsao_RL'].median()),
                         'dta': float(validas['Previsao_DTA'].median())}
        r['faixas_erro'] = {
            'rl': metricas.percentuais_faixas_erro(validas['WQI_real'], validas['Previsao_RL']),
            'dta': metricas.percentuais_faixas_erro(validas['WQI_real'], validas['Previsao_DTA']),
        }
        zeros = met_rl['indices_zero']
        if zeros:
            avisos.append((config.AVISO_WQI_ZERO.format(n=len(zeros)), len(zeros),
                           _lista_linhas(validas['Linha_original'].iloc[zeros])))
    else:
        r['medianas'] = {'real': None,
                         'rl': float(res['Previsao_RL'].median()),
                         'dta': float(res['Previsao_DTA'].median())}

    # comparacao entre pontos de coleta (precisa de IQA real valido)
    if r['tem_coluna_ponto'] and len(validas):
        r['pontos'] = metricas.tabela_pontos(validas[config.COLUNA_PONTO], validas['WQI_real'],
                                             validas['Previsao_RL'], validas['Previsao_DTA'])
        r['tem_pontos'] = len(r['pontos']) > 0

    return r


# ---------------------------------------------------------------------------
# Excel
# ---------------------------------------------------------------------------
def _valor_excel(valor, suficiente=True):
    if not suficiente:
        return config.SEM_DADOS_SUFICIENTES
    if valor is None:
        return config.NAO_SE_APLICA
    return float(valor)


def _ajustar_larguras(planilha):
    for coluna in planilha.columns:
        maior = max((len(str(c.value)) for c in coluna if c.value is not None), default=8)
        planilha.column_dimensions[coluna[0].column_letter].width = min(max(10, maior + 2), 60)


def previsoes_excel(res):
    """Aba Previsoes com os cabecalhos em portugues (so na gravacao)."""
    nomes = dict(config.COLUNAS_X_PREVISOES)
    for c in config.ORDEM_VARIAVEIS:
        nomes[c] = config.FORMATO_X_USADO_NO_MODELO.format(sigla=sigla(c))
    return res.rename(columns=nomes)


def gerar_excel(r):
    """Excel "Exportar resultados (.xlsx)". Abas na ordem fixa do prompt."""
    situacao = config.SITUACAO_OK if not r['bloqueios'] else \
        config.SITUACAO_BLOQUEADO.format(motivo=' '.join(r['bloqueios']))
    pct = 100 * r['linhas_removidas'] / r['linhas_lidas'] if r['linhas_lidas'] else 0.0
    itens = config.RESUMO_ITENS
    resumo = [
        (itens['arquivo'], r['nome_arquivo']),
        (itens['gerado_em'], datetime.now().strftime('%d/%m/%Y %H:%M')),
        (itens['situacao'], situacao),
        (itens['linhas_lidas'], r['linhas_lidas']),
        (itens['linhas_removidas'], r['linhas_removidas']),
        (itens['pct_removidas'], pct),
    ]
    if r['res'] is not None:
        resumo += [
            (itens['linhas_previstas'], len(r['res'])),
            (itens['linhas_wqi_real'], r['n_wqi_validas']),
            (itens['celulas_imputadas'], r['celulas_imputadas']),
            (itens['valores_winsorizados'], r['valores_winsorizados']),
        ]

    abas = [(config.ABA_X_RESUMO, pd.DataFrame(resumo, columns=['Item', 'Valor']))]

    if r['res'] is not None:
        abas.append((config.ABA_X_PREVISOES, previsoes_excel(r['res'])))

        linhas = []
        for chave, rotulo, unidade in config.LINHAS_X_METRICAS:
            if r['metricas'] is None:
                linhas.append((rotulo, config.SEM_DADOS_SUFICIENTES, config.SEM_DADOS_SUFICIENTES, unidade))
            else:
                linhas.append((rotulo, _valor_excel(r['metricas']['rl'][chave]),
                               _valor_excel(r['metricas']['dta'][chave]), unidade))
        for i, (_, rotulo, _, _) in enumerate(config.FAIXAS_ERRO):
            unidade = config.UNIDADE_X_FAIXAS_ERRO
            if r['faixas_erro'] is None:
                linhas.append((rotulo, config.SEM_DADOS_SUFICIENTES, config.SEM_DADOS_SUFICIENTES, unidade))
            else:
                linhas.append((rotulo, r['faixas_erro']['rl'][i], r['faixas_erro']['dta'][i], unidade))
        abas.append((config.ABA_X_METRICAS, pd.DataFrame(linhas, columns=config.COLUNAS_X_METRICAS)))

        if r['tem_pontos']:
            linhas = []
            for p in r['pontos']:
                linha = [p['ponto'], p['n']]
                for chave in ('R2', 'MAE', 'MAPE', 'RMSE'):
                    for modelo in ('rl', 'dta'):
                        m = p[modelo]
                        linha.append(_valor_excel(m[chave] if m else None, p['suficiente']))
                linhas.append(linha)
            abas.append((config.ABA_X_PONTOS, pd.DataFrame(linhas, columns=config.COLUNAS_X_PONTOS)))

    if r['removidas'] is not None:
        abas.append((config.ABA_X_REMOVIDAS, r['removidas']))
    if r['ajustes'] is not None:
        abas.append((config.ABA_X_AJUSTES, r['ajustes']))
    avisos = pd.DataFrame(r['avisos'], columns=config.COLUNAS_X_AVISOS)
    abas.append((config.ABA_X_AVISOS, avisos))

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        for nome_aba, tabela in abas:
            tabela.to_excel(writer, sheet_name=nome_aba, index=False)
        for planilha in writer.book.worksheets:
            _ajustar_larguras(planilha)
            planilha.freeze_panes = 'A2'
            for celula in planilha[1]:
                celula.font = celula.font.copy(bold=True)
        if r['res'] is not None and config.COLUNA_DATA in r['res'].columns:
            planilha = writer.book[config.ABA_X_PREVISOES]
            col = list(r['res'].columns).index(config.COLUNA_DATA) + 1
            for linha in planilha.iter_rows(min_row=2, min_col=col, max_col=col):
                linha[0].number_format = 'DD/MM/YYYY'
    return buffer.getvalue()


def nome_arquivo_exportacao(nome):
    base = os.path.splitext(os.path.basename(nome))[0]
    base = re.sub(r'[^\w\-]+', '_', base).strip('_') or 'base'
    return f"{config.PREFIXO_ARQUIVO_EXPORTACAO}{base}.xlsx"


def gerar_modelo_upload():
    """Planilha modelo do botao "Baixar modelo"."""
    colunas = [config.COLUNA_PONTO, config.COLUNA_DATA] + \
        [sigla(c) for c in config.ORDEM_VARIAVEIS + [config.COLUNA_TON, config.COLUNA_WQI]]
    dicionario = [(sigla(s), n, u, 'Sim', s) for s, n, u in config.DICIONARIO_VARIAVEIS]
    dicionario += list(config.COLUNAS_OPCIONAIS_MODELO)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        pd.DataFrame(columns=colunas).to_excel(writer, sheet_name=config.ABA_X_MODELO_DADOS, index=False)
        pd.DataFrame(dicionario, columns=config.COLUNAS_X_MODELO_DICIONARIO).to_excel(
            writer, sheet_name=config.ABA_X_MODELO_DICIONARIO, index=False)
        for planilha in writer.book.worksheets:
            _ajustar_larguras(planilha)
            for celula in planilha[1]:
                celula.font = celula.font.copy(bold=True)
    return buffer.getvalue()
