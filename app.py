"""
Dashboard de Qualidade da Agua (IQA)
TCC - Matteo | Abordagem com Machine Learning

Compara dois modelos preditivos (Regressao Linear e Arvore de Decisao)
na previsao do Indice de Qualidade das Aguas (IQA) e, se a planilha tiver
IQA real, mede o erro de cada modelo contra ele (geral e por ponto de
coleta).

Como rodar (na pasta wqi):
    C:\\v\\Scripts\\streamlit.exe run app.py

Arquivos esperados na mesma pasta:
    modelo_regressao_linear.pk, modelo_arvore_decisao.pk, scaler.pk,
    knn_imputer.pk, config.py, metricas.py, processamento.py
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import config
import metricas
import processamento
from metricas import formatar_numero, formatar_par

st.set_page_config(page_title=config.TITULO_PAGINA, layout="wide",
                   initial_sidebar_state="collapsed")

COR_RL = config.COR_RL
COR_DTA = config.COR_DTA


# ---------------------------------------------------------------------------
# Cache: modelos carregados uma vez; processamento e Excel uma vez por arquivo
# ---------------------------------------------------------------------------
@st.cache_resource
def carregar_modelos():
    return processamento.carregar_modelos()


@st.cache_data(show_spinner=False)
def processar_arquivo(nome, dados):
    return processamento.processar(nome, dados, carregar_modelos())


@st.cache_data(show_spinner=False)
def excel_resultados(nome, dados):
    return processamento.gerar_excel(processar_arquivo(nome, dados))


@st.cache_data(show_spinner=False)
def excel_modelo_upload():
    return processamento.gerar_modelo_upload()


@st.cache_data(show_spinner=False)
def bytes_base_exemplo():
    caminho = os.path.join(processamento.PASTA, config.ARQUIVO_BASE_EXEMPLO)
    with open(caminho, 'rb') as f:
        return f.read()


# ---------------------------------------------------------------------------
# Graficos
# ---------------------------------------------------------------------------
def _layout(fig, **kwargs):
    """Layout comum: fundo branco, texto na cor de texto, grade clara,
    titulos maiores e barras com cantos arredondados."""
    fig.update_layout(separators=config.SEPARADORES_PLOTLY, **kwargs)
    fig.update_layout(paper_bgcolor=config.COR_FUNDO, plot_bgcolor=config.COR_FUNDO,
                      font=dict(color=config.COR_TEXTO))
    if fig.layout.title.text:   # sem titulo, a fonte do titulo faria aparecer "undefined"
        fig.update_layout(title_font=dict(size=config.TAMANHO_TITULO_GRAFICO,
                                          color=config.COR_TEXTO))
    fig.update_xaxes(gridcolor=config.COR_GRADE)
    fig.update_yaxes(gridcolor=config.COR_GRADE)
    fig.update_traces(marker_cornerradius=config.RAIO_CANTO_BARRA, selector=dict(type='bar'))
    return fig


def mostrar_grafico(fig, key, eixo=False):
    st.plotly_chart(fig, width='stretch', key=key,
                    config=config.CONFIG_PLOTLY_EIXO if eixo else config.CONFIG_PLOTLY)


def _textos_wqi(valores):
    """Valores de IQA ja formatados para o texto ao passar o mouse."""
    return [formatar_numero(v, config.CASAS_WQI) for v in valores]


def _linha_ideal(fig, lo, hi, nome):
    """Linha y = x tracejada (Previsto x Real e Dispersao)."""
    fig.add_scatter(x=[lo, hi], y=[lo, hi], mode='lines', name=nome,
                    line=dict(color=config.COR_LINHA_IDEAL, dash='dash'),
                    customdata=_textos_wqi([lo, hi]), hovertemplate=config.DICA_LINHA_IDEAL)


def grafico_monitoramento(datas, y, cor, nome, eixo_y):
    """Grafico de monitoramento da qualidade da agua de um ponto de coleta:
    LC = media do IQA dos pontos plotados, LI e LS fixos (config), X nas
    amostras com IQA ate o LI (ruim ou pessimo) e losango nas amostras com
    IQA acima do LS (otimo). Devolve (fig, qtd_baixo, qtd_alto, total), com
    total = numero de pontos desenhados."""
    y = pd.Series(y, dtype=float).reset_index(drop=True)
    datas = pd.Series(datas).reset_index(drop=True)
    dados_dica = np.column_stack([datas.dt.strftime(config.FORMATO_DATA_DICA), _textos_wqi(y),
                                  [metricas.categoria_iqa(v) for v in y]])
    media = y.mean()
    li, ls = config.LI_MONITORAMENTO, config.LS_MONITORAMENTO

    fig = go.Figure()
    fig.add_scatter(x=datas, y=y, mode='markers', name=nome, marker=dict(color=cor, size=5),
                    cliponaxis=False, customdata=dados_dica, hovertemplate=config.DICA_MONITORAMENTO)
    fonte = dict(color=config.COR_TEXTO)
    fig.add_hline(y=media, line_dash='dash', line_color=config.COR_LINHA_CENTRAL,
                  annotation_text=config.G_LC.format(v=formatar_numero(media, config.CASAS_WQI)),
                  annotation_position='top left', annotation_font=fonte,
                  annotation_bgcolor=config.COR_FUNDO)
    fig.add_hline(y=ls, line_dash='dot', line_color=config.COR_LIMITES_MONITORAMENTO,
                  annotation_text=config.G_LS.format(v=ls),
                  annotation_position='bottom right', annotation_font=fonte,
                  annotation_bgcolor=config.COR_FUNDO)
    fig.add_hline(y=li, line_dash='dot', line_color=config.COR_LIMITES_MONITORAMENTO,
                  annotation_text=config.G_LI.format(v=li),
                  annotation_position='bottom right', annotation_font=fonte,
                  annotation_bgcolor=config.COR_FUNDO)
    baixo, alto = metricas.classificar_monitoramento(y)
    if baixo.any():
        fig.add_scatter(x=datas[baixo], y=y[baixo], mode='markers', name=config.G_IQA_RUIM,
                        marker=dict(color=config.COR_FORA_MONITORAMENTO, size=11, symbol='x'),
                        cliponaxis=False, customdata=dados_dica[baixo],
                        hovertemplate=config.DICA_MONITORAMENTO)
    if alto.any():
        fig.add_scatter(x=datas[alto], y=y[alto], mode='markers', name=config.G_IQA_OTIMO,
                        marker=dict(color=config.COR_ACIMA_LS, size=10, symbol='diamond'),
                        cliponaxis=False, customdata=dados_dica[alto],
                        hovertemplate=config.DICA_MONITORAMENTO)

    # eixo Y de 0 a 100, estendido se algum valor sair dessa faixa
    folga = config.FOLGA_EIXO_MONITORAMENTO
    lo = config.IQA_MIN if y.min() >= config.IQA_MIN else np.floor(y.min()) - folga
    hi = config.IQA_MAX if y.max() <= config.IQA_MAX else np.ceil(y.max()) + folga
    fig.update_yaxes(range=[lo, hi])
    fig.update_xaxes(tickformat=config.FORMATO_DATA_EIXO, hoverformat=config.FORMATO_DATA_DICA)
    _layout(fig, title=config.G_TITULO_MONITORAMENTO.format(nome=nome),
            xaxis_title=config.G_EIXO_DATA, yaxis_title=eixo_y,
            legend=dict(orientation='h', y=1.12))
    return fig, int(baixo.sum()), int(alto.sum()), len(y)


def grafico_dispersao(res):
    """Dispersao RL vs Arvore com linha de identidade."""
    lo = min(res['Previsao_RL'].min(), res['Previsao_DTA'].min())
    hi = max(res['Previsao_RL'].max(), res['Previsao_DTA'].max())
    fig = go.Figure()
    fig.add_scatter(x=res['Previsao_RL'], y=res['Previsao_DTA'],
                    mode='markers', name=config.G_AMOSTRAS,
                    marker=dict(color=config.COR_DISPERSAO, opacity=0.6),
                    customdata=np.column_stack([_textos_wqi(res['Previsao_RL']),
                                                _textos_wqi(res['Previsao_DTA'])]),
                    hovertemplate=config.DICA_DISPERSAO)
    _linha_ideal(fig, lo, hi, config.G_CONCORDANCIA_YX)
    return _layout(fig, title=config.G_TITULO_DISPERSAO,
                   xaxis_title=config.G_EIXO_PREVISTO_RL,
                   yaxis_title=config.G_EIXO_PREVISTO_DTA,
                   legend=dict(orientation='h', y=1.12))


def _lado_rotulo(x):
    """+1 (rotulo a direita da linha) ou -1 (a esquerda, perto de 100)."""
    return -1 if x > config.IQA_MAX - config.EIXO_FOLGA_ROTULO else 1


def grafico_eixo_iqa(medianas):
    """Eixo do IQA de 0 a 100 com as faixas oficiais (larguras proporcionais),
    os numeros das fronteiras e uma linha vertical por serie (mediana), cada
    uma no seu terco de altura: Real em cima, RL no meio, Arvore embaixo."""
    fig = go.Figure()
    fonte = dict(color=config.COR_TEXTO_EIXO)

    for nome, lo, hi, cor, _ in config.FAIXAS_IQA:
        fig.add_shape(type='rect', x0=lo, x1=hi, y0=0, y1=1, fillcolor=cor,
                      line=dict(color=config.COR_FUNDO, width=2), layer='below')
        # nome da faixa logo abaixo do retangulo: dentro dele ficam as 3 linhas
        fig.add_annotation(x=(lo + hi) / 2, y=-0.04, yanchor='top', text=f"<b>{nome}</b>",
                           showarrow=False, font=dict(size=14, **fonte))
    numeros = [(config.IQA_MIN, 'left'), (config.IQA_MAX, 'right')]
    numeros += [(f, 'center') for f in config.FRONTEIRAS_IQA]
    for x, ancora in numeros:
        fig.add_annotation(x=x, y=1.12, text=str(x), showarrow=False,
                           xanchor=ancora, font=dict(size=12, **fonte))

    altura = 1 / 3
    for chave, rotulo, terco, _ in config.EIXO_LINHAS:
        x = medianas[chave]
        if x is None:
            continue
        y0, y1 = terco * altura, (terco + 1) * altura
        fig.add_shape(type='line', x0=x, x1=x, y0=y0 + 0.03, y1=y1 - 0.03,
                      line=dict(color=config.COR_EIXO_SERIES[chave], width=3))
        lado = _lado_rotulo(x)
        fig.add_annotation(x=x, y=(y0 + y1) / 2, text=rotulo, showarrow=False,
                           xanchor='left' if lado > 0 else 'right', xshift=5 * lado,
                           font=dict(size=12, color=config.COR_TEXTO))

    fig.update_xaxes(range=[config.IQA_MIN - 1, config.IQA_MAX + 1], visible=False, fixedrange=True)
    fig.update_yaxes(range=config.EIXO_IQA_RANGE_Y, visible=False, fixedrange=True)
    return _layout(fig, height=config.ALTURA_EIXO_IQA, margin=dict(l=10, r=10, t=10, b=10),
                   showlegend=False, dragmode=False)


def grafico_previsto_real(validas, coluna, cor, titulo):
    """Previsto x Real de um modelo, com linha ideal y = x e fronteiras de faixa."""
    y_real = validas['WQI_real']
    y_prev = validas[coluna]
    minimo = min(y_real.min(), y_prev.min())
    maximo = max(y_real.max(), y_prev.max())
    lo = config.IQA_MIN if minimo >= config.IQA_MIN else np.floor(minimo) - 2
    hi = config.IQA_MAX if maximo <= config.IQA_MAX else np.ceil(maximo) + 2

    fig = go.Figure()
    for f in config.FRONTEIRAS_IQA:
        linha = dict(color=config.COR_FRONTEIRA_FAIXA, width=1)
        fig.add_shape(type='line', x0=f, x1=f, y0=lo, y1=hi, line=linha, layer='below')
        fig.add_shape(type='line', x0=lo, x1=hi, y0=f, y1=f, line=linha, layer='below')
    fig.add_scatter(x=y_real, y=y_prev, mode='markers', name=config.G_AMOSTRAS,
                    marker=dict(color=cor, opacity=config.OPACIDADE_PREVISTO_REAL),
                    customdata=np.column_stack([_textos_wqi(y_real), _textos_wqi(y_prev)]),
                    hovertemplate=config.DICA_PREVISTO_REAL)
    _linha_ideal(fig, lo, hi, config.LEGENDA_LINHA_IDEAL)
    fig.update_xaxes(range=[lo, hi], title=config.EIXO_X_PREVISTO_REAL)
    fig.update_yaxes(range=[lo, hi], title=config.EIXO_Y_PREVISTO_REAL)
    return _layout(fig, title=titulo, height=480, legend=dict(orientation='h', y=1.1))


def grafico_faixas_erro(faixas):
    """% das amostras de cada modelo em cada faixa de erro absoluto (barras agrupadas)."""
    rotulos = [f[0] for f in config.FAIXAS_ERRO]
    fig = go.Figure()
    for chave, cor, nome in (('rl', COR_RL, config.NOME_RL), ('dta', COR_DTA, config.NOME_DTA)):
        textos = [formatar_numero(v, config.CASAS_PCT, config.SUFIXO_PCT) for v in faixas[chave]]
        fig.add_bar(x=rotulos, y=faixas[chave], name=nome, marker_color=cor,
                    text=textos, textposition='outside', textangle=0, cliponaxis=False,
                    textfont=dict(color=config.COR_TEXTO),
                    customdata=[[nome, r, t] for r, t in zip(rotulos, textos)],
                    hovertemplate=config.DICA_FAIXAS_ERRO)
    maximo = max(faixas['rl'] + faixas['dta'])
    fig.update_yaxes(range=[0, maximo * config.FOLGA_EIXO_FAIXAS_ERRO], ticksuffix=config.SUFIXO_PCT)
    return _layout(fig, barmode='group', xaxis_title=config.G_EIXO_X_FAIXAS_ERRO,
                   yaxis_title=config.G_EIXO_Y_FAIXAS_ERRO,
                   legend=dict(orientation='h', y=1.1))


# ---------------------------------------------------------------------------
# Blocos de tela
# ---------------------------------------------------------------------------
def texto_abertura():
    st.subheader(config.ABERTURA_TITULO, anchor=False)
    st.markdown(config.ABERTURA_PARAGRAFO)
    st.markdown(config.ABERTURA_LINHA)
    st.markdown(f"**{config.ABERTURA_SUBTITULO}**")
    st.markdown("\n".join(f"- {item}" for item in config.ABERTURA_ITENS))


def botao_baixar_modelo(key):
    st.download_button(config.BOTAO_BAIXAR_MODELO, excel_modelo_upload(),
                       file_name=config.NOME_ARQUIVO_MODELO_UPLOAD,
                       mime=config.MIME_XLSX, key=key, on_click='ignore')


def botao_exportar(nome, dados, key):
    st.download_button(config.BOTAO_EXPORTAR, excel_resultados(nome, dados),
                       file_name=processamento.nome_arquivo_exportacao(nome),
                       mime=config.MIME_XLSX, key=key, on_click='ignore')


def usar_base_exemplo():
    st.session_state['fonte'] = 'exemplo'
    # key nova no envio de arquivo: o campo de envio volta vazio
    st.session_state['n_uploader'] = st.session_state.get('n_uploader', 0) + 1


def seletor_ponto(pontos, key):
    """Seletor de Ponto de Coleta. A key leva o numero da base: quando a base
    muda, o seletor volta ao primeiro ponto da lista."""
    return st.selectbox(config.ROTULO_SELETOR_PONTO, pontos, index=0,
                        key=f"{key}_{st.session_state.get('n_base', 0)}")


def eixo_iqa_com_legenda(medianas):
    mostrar_grafico(grafico_eixo_iqa(medianas), key='g_eixo_iqa', eixo=True)
    linhas = [config.FORMATO_QUADRADO_COR.format(
                  cor=config.COR_EIXO_SERIES[chave],
                  texto=legenda.format(v=formatar_numero(medianas[chave], config.CASAS_WQI)))
              for chave, _, _, legenda in config.EIXO_LINHAS if medianas[chave] is not None]
    st.markdown("  \n".join(linhas))
    nota = config.EIXO_NOTA_MEDIANA
    if medianas['real'] is not None:
        nota += " " + config.EIXO_NOTA_ERRO
    st.caption(nota)


def dados_monitoramento(r, coluna):
    """Linhas que entram nos graficos de monitoramento (data, ponto e valor
    validos) ou None se a planilha nao tem Ponto de Coleta e Data."""
    if not (r['tem_data'] and r['tem_coluna_ponto']):
        return None
    res = r['res']
    ok = res[config.COLUNA_DATA].notna() & res[config.COLUNA_PONTO].notna() & res[coluna].notna()
    return res[ok]


def resumo_monitoramento(formato, qtd, total, **limite):
    """Uma linha de resumo abaixo do grafico de monitoramento:
    porcentagem, contagem e total de amostras ('1 de 1 amostra')."""
    pct = 100 * qtd / total if total else None
    palavra = config.PALAVRA_AMOSTRA_SING if total == 1 else config.PALAVRA_AMOSTRA_PLURAL
    return formato.format(pct=formatar_numero(pct, config.CASAS_PCT, config.SUFIXO_PCT),
                          qtd=qtd, total=total, palavra=palavra, **limite)


def monitoramento_de_um_ponto(dados, coluna, cor, nome, eixo_y, key):
    """Seletor + grafico de monitoramento + resumo de um ponto de coleta."""
    pontos = metricas.ordenar_pontos(dados[config.COLUNA_PONTO])
    escolhido = seletor_ponto(pontos, key=f"sel_{key}")
    sel = dados[dados[config.COLUNA_PONTO] == escolhido]
    fig, qtd_baixo, qtd_alto, total = grafico_monitoramento(sel[config.COLUNA_DATA], sel[coluna],
                                                            cor, nome, eixo_y)
    mostrar_grafico(fig, key=f"g_{key}")
    st.markdown(resumo_monitoramento(config.FORMATO_MONITORAMENTO_BAIXO, qtd_baixo, total,
                                     li=config.LI_MONITORAMENTO))
    st.markdown(resumo_monitoramento(config.FORMATO_MONITORAMENTO_ALTO, qtd_alto, total,
                                     ls=config.LS_MONITORAMENTO))


def secao_monitoramento_real(r):
    st.subheader(config.SECAO_MONITORAMENTO_REAL, anchor=False)
    st.markdown(config.TEXTO_MONITORAMENTO_REAL)
    dados = dados_monitoramento(r, 'WQI_real')
    if dados is None or dados.empty:
        st.info(config.INFO_MONITORAMENTO_SEM_COLUNAS)
        return
    monitoramento_de_um_ponto(dados, 'WQI_real', config.COR_TEXTO, config.G_NOME_REAL,
                              config.G_EIXO_IQA_REAL, key='monitoramento_real')


def secao_monitoramento_previsto(r):
    st.subheader(config.SECAO_MONITORAMENTO_PREVISTO, anchor=False)
    st.markdown(config.TEXTO_MONITORAMENTO_PREVISTO)
    dados = dados_monitoramento(r, 'Previsao_RL')
    if dados is None or dados.empty:
        st.info(config.INFO_MONITORAMENTO_SEM_COLUNAS)
        return
    col1, col2 = st.columns(2)
    with col1:
        monitoramento_de_um_ponto(dados, 'Previsao_RL', COR_RL, config.NOME_RL,
                                  config.G_EIXO_IQA_PREVISTO, key='monitoramento_rl')
    with col2:
        monitoramento_de_um_ponto(dados, 'Previsao_DTA', COR_DTA, config.NOME_DTA,
                                  config.G_EIXO_IQA_PREVISTO, key='monitoramento_dta')


def subaba_visao_geral(r, nome, dados):
    with st.container(border=True):
        st.markdown(config.LEGENDA_SIGLAS, text_alignment='center')
    eixo_iqa_com_legenda(r['medianas'])

    if r['metricas'] is not None:
        met_rl, met_dta = r['metricas']['rl'], r['metricas']['dta']
        colunas = st.columns(len(config.CAIXINHAS_METRICAS))
        for col, caixinha in zip(colunas, config.CAIXINHAS_METRICAS):
            chave, titulo, texto, etiquetas, sufixo, casas, sentido = caixinha
            grifo = metricas.melhor_modelo(met_rl[chave], met_dta[chave], casas, sentido)
            with col:
                with st.container(border=True, height='stretch'):
                    st.markdown(f"**{titulo}**")
                    st.markdown(formatar_par(met_rl[chave], met_dta[chave], casas, sufixo, grifo))
                    st.caption(texto)
                    with st.container(horizontal=True, gap='small'):
                        for etiqueta in etiquetas:
                            st.badge(etiqueta, color='gray')

        validas = r['res'][r['res']['WQI_real'].notna()]
        g1, g2 = st.columns(2)
        with g1:
            mostrar_grafico(grafico_previsto_real(validas, 'Previsao_RL', COR_RL,
                                                  config.TITULO_PREVISTO_REAL_RL), key='g_pr_rl')
        with g2:
            mostrar_grafico(grafico_previsto_real(validas, 'Previsao_DTA', COR_DTA,
                                                  config.TITULO_PREVISTO_REAL_DTA), key='g_pr_dta')

        st.subheader(config.TITULO_FAIXAS_ERRO, anchor=False)
        st.markdown(config.TEXTO_FAIXAS_ERRO)
        mostrar_grafico(grafico_faixas_erro(r['faixas_erro']), key='g_faixas_erro')

        secao_monitoramento_real(r)

    botao_exportar(nome, dados, key='exportar_visao_geral')


def subaba_concordancia(r, nome, dados):
    st.subheader(config.SECAO_DISPERSAO, anchor=False)
    st.markdown(config.TEXTO_DISPERSAO)
    mostrar_grafico(grafico_dispersao(r['res']), key='g_dispersao')

    secao_monitoramento_previsto(r)

    botao_exportar(nome, dados, key='exportar_concordancia')


def tabela_pontos_tela(pontos):
    linhas = []
    for p in pontos:
        if not p['suficiente']:
            celulas = [config.SEM_DADOS_SUFICIENTES] * 4
        else:
            celulas = [
                formatar_par(p['rl']['R2'], p['dta']['R2'], config.CASAS_R2),
                formatar_par(p['rl']['MAE'], p['dta']['MAE'], config.CASAS_WQI),
                formatar_par(p['rl']['MAPE'], p['dta']['MAPE'], config.CASAS_MAPE, sufixo='%'),
                formatar_par(p['rl']['RMSE'], p['dta']['RMSE'], config.CASAS_WQI),
            ]
        linhas.append([p['ponto'], p['n']] + celulas)
    return pd.DataFrame(linhas, columns=config.COLUNAS_TABELA_PONTOS)


def mostrar_tabela_pontos(tabela):
    """Tabela de pontos de coleta com a coluna MAE destacada (fundo das
    celulas e cabecalho em negrito)."""
    destaque = config.COLUNA_DESTAQUE_PONTOS
    coluna = list(tabela.columns).index(destaque)
    estilo = (tabela.style
              .set_properties(subset=[destaque], **{'background-color': config.COR_DESTAQUE_TABELA})
              .set_table_styles([{'selector': f'th.col_heading.col{coluna}',
                                  'props': [('font-weight', 'bold'),
                                            ('background-color', config.COR_DESTAQUE_TABELA)]}]))
    st.table(estilo, hide_index=True)


def subaba_pontos(r, nome, dados):
    st.info(config.NOTA_PONTOS)
    tabela = tabela_pontos_tela(r['pontos'])
    escolhido = seletor_ponto(list(tabela[config.COLUNAS_TABELA_PONTOS[0]]), key='sel_tabela_pontos')
    mostrar_tabela_pontos(tabela[tabela[config.COLUNAS_TABELA_PONTOS[0]] == escolhido])
    mostrar_tabela_pontos(tabela)
    botao_exportar(nome, dados, key='exportar_pontos')


def aba_sobre():
    st.subheader(config.SOBRE_TITULO_VARIAVEIS, anchor=False)
    st.dataframe(pd.DataFrame(config.SOBRE_VARIAVEIS, columns=config.SOBRE_COLUNAS_VARIAVEIS),
                 hide_index=True)

    st.subheader(config.SOBRE_TITULO_FICHA, anchor=False)
    lr, dta, _, imputer = carregar_modelos()
    ficha = processamento.ficha_modelos(lr, dta, imputer)
    st.markdown("\n".join(f"- {linha.format(**ficha)}" for linha in config.SOBRE_FICHA))

    st.subheader(config.SOBRE_TITULO_FAIXAS, anchor=False)
    faixas = [(nome, faixa) for nome, _, _, _, faixa in config.FAIXAS_IQA]
    st.dataframe(pd.DataFrame(faixas, columns=config.SOBRE_COLUNAS_FAIXAS), hide_index=True)
    st.caption(config.FONTE_FAIXAS_IQA)


def aba_analise():
    topo = st.container()

    with st.container(horizontal=True, gap='small'):
        botao_baixar_modelo(key='modelo_topo')
        st.button(config.BOTAO_BASE_EXEMPLO, on_click=usar_base_exemplo, key='botao_exemplo')

    if 'n_uploader' not in st.session_state:
        st.session_state['n_uploader'] = 0
    arquivo = st.file_uploader(config.ROTULO_UPLOAD, type=config.FORMATOS_ACEITOS,
                               key=f"arquivo_{st.session_state['n_uploader']}")

    # qual base mostrar: um arquivo novo enviado substitui tudo (inclusive
    # a base de exemplo); o botao de exemplo vale ate o proximo envio
    if arquivo is not None and arquivo.file_id != st.session_state.get('upload_id'):
        st.session_state['upload_id'] = arquivo.file_id
        st.session_state['fonte'] = 'upload'
    if arquivo is None and st.session_state.get('fonte') == 'upload':
        st.session_state['fonte'] = None
    if arquivo is None:
        st.session_state['upload_id'] = None

    fonte = st.session_state.get('fonte')
    if fonte == 'upload':
        nome, dados = arquivo.name, arquivo.getvalue()
        base_id = arquivo.file_id
    elif fonte == 'exemplo':
        nome, dados = config.ARQUIVO_BASE_EXEMPLO, bytes_base_exemplo()
        base_id = 'exemplo'
    else:
        with topo:
            texto_abertura()
        return

    # base nova (upload novo ou base de exemplo): os seletores de ponto de
    # coleta voltam ao ponto pre-selecionado
    if st.session_state.get('base_id') != base_id:
        st.session_state['base_id'] = base_id
        st.session_state['n_base'] = st.session_state.get('n_base', 0) + 1

    try:
        r = processar_arquivo(nome, dados)
    except Exception as e:
        with topo:
            texto_abertura()
        st.error(config.BLOQUEIO_ERRO_INESPERADO.format(erro=e))
        botao_baixar_modelo(key='modelo_bloqueio')
        return

    if r['bloqueios']:
        with topo:
            texto_abertura()
        for mensagem in r['bloqueios']:
            st.error(mensagem)
        botao_baixar_modelo(key='modelo_bloqueio')
        if r['lido']:
            botao_exportar(nome, dados, key='exportar_bloqueio')
        return

    with topo:
        with st.expander(config.EXPANDER_PREPARAR):
            texto_abertura()

    if fonte == 'exemplo':
        st.info(config.FAIXA_BASE_EXEMPLO)

    nomes = [config.SUBABA_VISAO_GERAL, config.SUBABA_CONCORDANCIA]
    if r['tem_pontos']:
        nomes.append(config.SUBABA_PONTOS)
    subabas = st.tabs(nomes)
    with subabas[0]:
        subaba_visao_geral(r, nome, dados)
    with subabas[1]:
        subaba_concordancia(r, nome, dados)
    if r['tem_pontos']:
        with subabas[2]:
            subaba_pontos(r, nome, dados)


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
st.title(config.TITULO, anchor=False)

aba_analise_tab, aba_sobre_tab = st.tabs([config.ABA_ANALISE, config.ABA_SOBRE])
with aba_sobre_tab:
    aba_sobre()
with aba_analise_tab:
    aba_analise()
