"""
Configuracao fixa do Dashboard IQA.

Todo texto mostrado ao usuario, todo numero fixo (limites, faixas, cores)
e todo rotulo vem deste arquivo. O app.py, o processamento.py e o
metricas.py nao escrevem textos nem numeros magicos por conta propria.
"""

# ---------------------------------------------------------------------------
# Pipeline do Douglas (NAO ALTERAR)
# O scaler.pk e o knn_imputer.pk guardam feature_names_in_ com estas siglas
# em ingles, nesta ordem. Dentro do pipeline os nomes continuam em ingles; a
# traducao para portugues acontece so na entrada (upload) e na saida (tela,
# Excel, planilha modelo, avisos), via SIGLAS_EXIBIDAS.
# ---------------------------------------------------------------------------
ORDEM_VARIAVEIS = ['BOD', 'THC', 'TOP', 'DOS', 'PH', 'TOS', 'TUR']
COLUNAS_WINSORIZE = ['BOD', 'THC', 'TOP', 'DOS', 'PH', 'TOS', 'TUR']
LIMITES_WINSORIZE = [0.1, 0.1]
COLUNAS_REMOVIDAS_ANTES_DO_MODELO = ['TON', 'WQI']
COLUNAS_INDICE_LIXO = ['Unnamed: 0', 'index']

# filtro de valores fora da faixa usada no treino dos modelos (mesmo do
# treino): (minimo, maximo).
# None = sem limite daquele lado. Linha reprovada se valor < minimo ou > maximo.
LIMITES_FILTRO = {
    'PH': (2, 12),
    'BOD': (None, 30),
    'DOS': (None, 140),
    'TOS': (None, 500),
    'TUR': (None, 100),
    'TON': (None, 100),
    'TOP': (None, 10),
}

ARQUIVOS_MODELO = {
    'lr': 'modelo_regressao_linear.pk',
    'dta': 'modelo_arvore_decisao.pk',
    'scaler': 'scaler.pk',
    'imputer': 'knn_imputer.pk',
}

# ---------------------------------------------------------------------------
# Colunas da planilha
# ---------------------------------------------------------------------------
COLUNA_WQI = 'WQI'
COLUNA_TON = 'TON'
COLUNA_PONTO = 'Ponto de Coleta'
COLUNA_DATA = 'Data'
NOMES_ACEITOS_DATA = ['data', 'date', 'datas', 'data da coleta', 'data_coleta',
                      'data coleta', 'data_da_coleta']
# nomes aceitos para o Ponto de Coleta (sem diferenciar maiusculas), em
# ordem de prioridade: se houver mais de um, vale o primeiro desta lista
NOMES_ACEITOS_PONTO = ['ponto de coleta', 'ponto_de_coleta', 'ponto', 'ugrhi']
FORMATOS_ACEITOS = ['xlsx', 'xls', 'csv']

# Dicionario unico sigla interna -> sigla exibida (tela, Excel, planilha
# modelo, avisos). No upload, as duas formas sao aceitas.
SIGLAS_EXIBIDAS = {
    'BOD': 'DBO',
    'THC': 'CT',
    'TOP': 'FT',
    'DOS': 'SOD',
    'PH': 'pH',
    'TOS': 'ST',
    'TUR': 'TUR',
    'TON': 'NT',
    'WQI': 'IQA',
    COLUNA_PONTO: 'Ponto de Coleta',
    COLUNA_DATA: 'Data',
}

# Variaveis obrigatorias (as 7 do modelo): sigla interna, nome, unidade
# exibida. Gera as linhas obrigatorias da planilha modelo.
DICIONARIO_VARIAVEIS = [
    ('BOD', 'Demanda Bioquímica de Oxigênio', 'mg/L'),
    ('THC', 'Coliformes termotolerantes (E. coli)', 'UFC/100 mL'),
    ('TOP', 'Fósforo total', 'mg/L'),
    ('DOS', 'Saturação de oxigênio dissolvido', '% de saturação'),
    ('PH', 'pH', 'sem unidade'),
    ('TOS', 'Sólidos totais', 'mg/L'),
    ('TUR', 'Turbidez', 'UNT'),
]
# Colunas opcionais da planilha modelo: coluna, nome, unidade,
# obrigatoria, tambem aceito como
COLUNAS_OPCIONAIS_MODELO = [
    (COLUNA_PONTO, 'Ponto de coleta (código ou nome da estação ou da bacia)', 'sem unidade',
     'Não', 'Ponto, UGRHI'),
    (COLUNA_DATA, 'Data da coleta', 'dd/mm/aaaa', 'Não', ''),
    ('NT', 'Nitrogênio total (só entra no filtro de qualidade)', 'mg/L', 'Não', 'TON'),
    ('IQA', 'IQA real medido (para comparar com as previsões)', 'sem unidade', 'Não', 'WQI'),
]

# Checagem de unidade no cabecalho (ex.: "DBO (mg/L)" ou "BOD (mg/L)").
# Formas aceitas, comparadas sem espacos e sem diferenca de maiusculas.
UNIDADES_ACEITAS = {
    'BOD': ['mg/l', 'mgl'],
    'THC': ['ufc/100ml', 'nmp/100ml', 'ufc/100', 'nmp/100'],
    'TOP': ['mg/l', 'mgl'],
    'DOS': ['%', '%sat', '%desaturação', '%desaturacao', '%saturação', '%saturacao'],
    'PH': ['', 'semunidade', '-'],
    'TOS': ['mg/l', 'mgl'],
    'TUR': ['unt', 'ntu', 'ut'],
    'TON': ['mg/l', 'mgl'],
    'WQI': ['', 'semunidade', '-'],
}
ITEM_COLUNA_FALTANDO = "{exibida} (ou {interna})"   # mensagem de coluna faltando

# ---------------------------------------------------------------------------
# Faixas do IQA (CETESB, Qualidade das Aguas Interiores no Estado de SP 2023)
# (nome, limite inferior exclusivo, limite superior inclusivo, cor, faixa)
# ---------------------------------------------------------------------------
FAIXAS_IQA = [
    ('Péssima', 0, 19, '#f28b82', 'até 19'),
    ('Ruim', 19, 36, '#f9b16e', 'acima de 19 até 36'),
    ('Regular', 36, 51, '#f6dc5c', 'acima de 36 até 51'),
    ('Boa', 51, 79, '#8fd18a', 'acima de 51 até 79'),
    ('Ótima', 79, 100, '#6cc4c0', 'acima de 79 até 100'),
]
FRONTEIRAS_IQA = [19, 36, 51, 79]
IQA_MIN = 0
IQA_MAX = 100
FONTE_FAIXAS_IQA = "Fonte: CETESB, 2023."

# ---------------------------------------------------------------------------
# Faixas de erro absoluto |IQA real - previsao|. O limite de cima pertence
# a faixa (mesma regra das faixas da CETESB).
# (rotulo do grafico, rotulo no Excel, limite inferior exclusivo, limite
# superior inclusivo). None = sem limite daquele lado (a primeira faixa
# comeca em 0, inclusive).
# ---------------------------------------------------------------------------
FAIXAS_ERRO = [
    ("até 5", "% amostras com erro até 5", None, 5),
    ("mais de 5 até 10", "% amostras com erro de mais de 5 até 10", 5, 10),
    ("mais de 10 até 15", "% amostras com erro de mais de 10 até 15", 10, 15),
    ("mais de 15", "% amostras com erro de mais de 15", 15, None),
]

# ---------------------------------------------------------------------------
# Pontos de Coleta
# ---------------------------------------------------------------------------
MINIMO_LINHAS_PONTO = 2

# ---------------------------------------------------------------------------
# Graficos de monitoramento da qualidade da agua: limites fixos e arbitrarios
# (LI e LS), baseados nas faixas da CETESB. A LC e a media do IQA dos pontos
# plotados do ponto de coleta selecionado. Mesma regra das faixas: o limite
# de cima pertence a faixa (ruim ou pessimo = IQA ate o LI; otimo = IQA
# acima do LS).
# ---------------------------------------------------------------------------
LI_MONITORAMENTO = 36
LS_MONITORAMENTO = 79

# ---------------------------------------------------------------------------
# Cores e formatos
# ---------------------------------------------------------------------------
# cores dos modelos validadas para daltonismo e contraste
COR_RL = '#0057e7'                  # azul
COR_DTA = '#c84a00'                 # laranja escuro
COR_TEXTO = '#0f172a'
COR_TEXTO_SECUNDARIO = '#475569'
COR_TEXTO_EIXO = COR_TEXTO_SECUNDARIO
COR_FUNDO = '#ffffff'
COR_FUNDO_SECUNDARIO = '#eef2f8'
COR_BORDA = '#d6deea'
COR_GRADE = '#e5e9f0'
COR_FRONTEIRA_FAIXA = '#d1d5db'
COR_LINHA_CENTRAL = '#334155'       # LC dos graficos de monitoramento
COR_LIMITES_MONITORAMENTO = '#94a3b8'    # LS e LI
COR_FORA_MONITORAMENTO = '#9d174d'  # marcador X "IQA ruim ou péssimo"
COR_ACIMA_LS = '#15803d'            # marcador losango "IQA ótimo"
# cor de cada serie no eixo do IQA (linhas e quadrados da legenda)
COR_EIXO_SERIES = {'real': COR_TEXTO, 'rl': COR_RL, 'dta': COR_DTA}
COR_DISPERSAO = '#475569'           # pontos da Dispersao RL x Arvore
COR_LINHA_IDEAL = '#0f172a'         # linhas y = x tracejadas
COR_DESTAQUE_TABELA = '#e3ecfd'     # coluna MAE nas tabelas de pontos de coleta
TAMANHO_TITULO_GRAFICO = 17
RAIO_CANTO_BARRA = 4
FOLGA_EIXO_FAIXAS_ERRO = 1.15     # espaço acima da barra mais alta para o rótulo

# casas decimais na tela (arredondamento como o ARRED do Excel: empate vai
# para longe do zero). Calculos internos e Excel usam o valor completo.
CASAS_WQI = 1    # IQA, MAE, RMSE, medianas, medias, LC dos graficos de monitoramento
CASAS_PCT = 1    # porcentagens em geral (inclusive rotulos das faixas de erro)
CASAS_R2 = 2
CASAS_MAPE = 2
FORMATO_DATA_EIXO = '%m/%Y'
FORMATO_DATA_DICA = '%d/%m/%Y'
SEPARADORES_PLOTLY = ',.'
CONFIG_PLOTLY = {
    'toImageButtonOptions': {'format': 'png', 'scale': 3},
    'displaylogo': False,
}
CONFIG_PLOTLY_EIXO = {
    'toImageButtonOptions': {'format': 'png', 'scale': 3},
    'displaylogo': False,
    'modeBarButtonsToRemove': ['zoom2d', 'pan2d', 'select2d', 'lasso2d',
                               'zoomIn2d', 'zoomOut2d', 'autoScale2d',
                               'resetScale2d'],
}
OPACIDADE_PREVISTO_REAL = 0.5
ALERTA_REMOCAO_PCT = 80

# ---------------------------------------------------------------------------
# Textos: topo e abas
# ---------------------------------------------------------------------------
TITULO_PAGINA = "Dashboard de Qualidade da Água (IQA)"
TITULO = "Dashboard de Qualidade da Água (IQA)"

ABA_ANALISE = "Análise da sua base"
ABA_SOBRE = "Sobre o Dashboard"
SUBABA_VISAO_GERAL = "Visão Geral"
SUBABA_CONCORDANCIA = "Previsões dos Modelos"
SUBABA_PONTOS = "Comparação entre Pontos de Coleta"

# ---------------------------------------------------------------------------
# Textos: abertura
# ---------------------------------------------------------------------------
ABERTURA_TITULO = "Compare as previsões dos modelos com o IQA real da sua base"
ABERTURA_PARAGRAFO = (
    "Este painel usa dois modelos de aprendizado de máquina, Regressão Linear e "
    "Árvore de Decisão, para prever o IQA (Índice de Qualidade das Águas) a partir "
    "de 7 variáveis medidas na água. Envie sua planilha e o painel mostra o quanto "
    "cada modelo erra, como os dois se comparam entre si e, se a planilha tiver a "
    "coluna Ponto de Coleta, como o resultado varia entre os pontos de coleta."
)
ABERTURA_LINHA = ("Baixe a planilha modelo para ver o formato esperado e use "
                  "exatamente os nomes das colunas dela.")
ABERTURA_SUBTITULO = "Antes de enviar, confira:"
ABERTURA_ITENS = [
    "Formatos: .xlsx, .xls ou .csv",
    "Células vazias nas variáveis: são permitidas e preenchidas pelo método dos modelos.",
    ("Valores fora da faixa usada no treino dos modelos: a linha inteira é removida "
     "por um filtro de qualidade."),
    "Valores extremos: são ajustados pelo método dos modelos.",
]
EXPANDER_PREPARAR = "Como preparar sua planilha"

BOTAO_BAIXAR_MODELO = "Baixar modelo"
BOTAO_BASE_EXEMPLO = "Usar base de exemplo"
BOTAO_EXPORTAR = "Exportar resultados (.xlsx)"
ROTULO_UPLOAD = "Envie sua planilha"
FAIXA_BASE_EXEMPLO = "Você está vendo a base de exemplo (CETESB, 2023)"

ARQUIVO_BASE_EXEMPLO = 'UGRHI23_exemplo.xlsx'
NOME_ARQUIVO_MODELO_UPLOAD = 'modelo_planilha_iqa.xlsx'
PREFIXO_ARQUIVO_EXPORTACAO = 'resultados_iqa_'
MIME_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

# ---------------------------------------------------------------------------
# Textos: bloqueios
# ---------------------------------------------------------------------------
BLOQUEIO_LEITURA = ("Não foi possível ler o arquivo. Envie uma planilha .xlsx, .xls "
                    "ou .csv no formato da planilha modelo.")
BLOQUEIO_VAZIO = "O arquivo não tem nenhuma linha de dados."
BLOQUEIO_COLUNAS = ("Faltam colunas obrigatórias na planilha: {colunas}. Use "
                    "exatamente os nomes das colunas da planilha modelo.")
BLOQUEIO_UNIDADE = ("A coluna {coluna} está com a unidade \"{unidade}\", mas o modelo "
                    "espera {esperada}. Converta os valores ou use a planilha modelo.")
BLOQUEIO_TUDO_REMOVIDO = ("Todas as linhas foram removidas pelo filtro de qualidade "
                          "de dados por terem valores fora da faixa usada no treino dos "
                          "modelos. Não há nada para prever. O motivo de cada caso está "
                          "no Excel do botão Exportar resultados.")
BLOQUEIO_ERRO_INESPERADO = "Erro ao processar a base: {erro}"

# ---------------------------------------------------------------------------
# Textos: Visao Geral
# ---------------------------------------------------------------------------
LEGENDA_SIGLAS = "RL = Modelo Regressão Linear | Árvore = Modelo Árvore de Decisão"
NAO_SE_APLICA = "não se aplica"
SEM_DADOS_SUFICIENTES = "sem dados suficientes"
FORMATO_PAR = "RL = {rl} | Árvore = {dta}"
SEPARADOR_PAR = " | "     # separa o trecho da RL e o da Árvore dentro de FORMATO_PAR
FORMATO_GRIFO = ":green-background[{texto}]"     # grifo do modelo melhor nos cartões

# eixo do IQA: uma linha vertical por serie (mediana), cada uma no seu terco
# de altura do retangulo das faixas: (chave, rotulo curto, terco, legenda)
# terco 2 = de cima, 1 = do meio, 0 = de baixo
EIXO_LINHAS = [
    ('real', "Real", 2, "Real = IQA real (mediana) da sua base: {v}"),
    ('rl', "RL", 1, "RL = IQA previsto pela Regressão Linear (mediana): {v}"),
    ('dta', "Árvore", 0, "Árvore = IQA previsto pela Árvore de Decisão (mediana): {v}"),
]
EIXO_NOTA_MEDIANA = "As linhas mostram o valor típico (mediana) de cada série, não o erro dos modelos."
EIXO_NOTA_ERRO = "O erro aparece nos indicadores abaixo."
EIXO_FOLGA_ROTULO = 6     # perto de 0 ou 100, o rotulo curto vai para dentro do eixo
# altura da figura (px) e faixa do eixo Y (a faixa das categorias vai de 0 a 1;
# os numeros ficam acima de 1 e os nomes das categorias abaixo de 0)
ALTURA_EIXO_IQA = 150
EIXO_IQA_RANGE_Y = [-0.38, 1.22]
# quadrado na cor da serie antes de cada linha da legenda do eixo
FORMATO_QUADRADO_COR = ':color[■]{{foreground="{cor}"}} {texto}'

# (chave, titulo, texto, etiquetas, sufixo do valor, casas decimais,
#  sentido do melhor: 'maior' ou 'menor')
CAIXINHAS_METRICAS = [
    ('R2', "R² (Coeficiente de Determinação)",
     "O quão bem o modelo prevê os dados reais. 0 ou negativo = Modelo não prevê em "
     "nada / 1 = Previsão Perfeita. Logo, quanto mais próximo de 1, melhor.",
     ["Varia de: 1 até negativo", "Unidade: sem unidade"], '', CASAS_R2, 'maior'),
    ('MAPE', "MAPE (Erro Percentual Absoluto Médio)",
     "Erro médio em porcentagem. Quanto menor, melhor.",
     ["Unidade: %"], '%', CASAS_MAPE, 'menor'),
    ('MAE', "MAE (Erro Absoluto Médio)",
     "Em média, quantos pontos de IQA o modelo erra. Quanto menor, melhor.",
     ["Unidade: Pontos de IQA"], '', CASAS_WQI, 'menor'),
    ('RMSE', "RMSE (Raiz do Erro Quadrático Médio)",
     "É parecido com o MAE e nunca é menor que ele, porém, penaliza muito mais os erros "
     "grandes. Por exemplo: uma amostra errada por 20 pontos do IQA piora muito o RMSE, "
     "mesmo que todas as outras estejam quase certas. Quanto menor, melhor.",
     ["Unidade: Pontos de IQA"], '', CASAS_WQI, 'menor'),
]

TITULO_PREVISTO_REAL_RL = "Previsto x Real: Regressão Linear"
TITULO_PREVISTO_REAL_DTA = "Previsto x Real: Árvore de Decisão"
EIXO_X_PREVISTO_REAL = "IQA real"
EIXO_Y_PREVISTO_REAL = "IQA previsto"
LEGENDA_LINHA_IDEAL = "Linha ideal"
DICA_PREVISTO_REAL = "IQA real: %{customdata[0]}<br>IQA previsto: %{customdata[1]}"
DICA_LINHA_IDEAL = "%{customdata}"

TITULO_FAIXAS_ERRO = "Faixas de Erro Absoluto = |IQA Real − IQA Previsto|"
TEXTO_FAIXAS_ERRO = (
    "Objetivo: quando o modelo erra, entender o impacto do erro. Exemplo: o modelo pode "
    "errar 1 ponto ou 20 pontos, e se a porcentagem das amostras em RL é bem superior em "
    "relação à Árvore nas últimas faixas (10 a 15 e >15), significa que quando o RL erra, "
    "gera previsões muito distantes das reais em comparação com a Árvore e cria mais e "
    "piores pontos outliers. Esse gráfico tem total conexão com o RMSE. Quanto menor a "
    "porcentagem das amostras nas últimas faixas, melhor."
)
G_EIXO_X_FAIXAS_ERRO = "Erro absoluto (pontos de IQA)"
G_EIXO_Y_FAIXAS_ERRO = "% das amostras"
SUFIXO_PCT = "%"
DICA_FAIXAS_ERRO = ("<b>%{customdata[0]}</b><br>Faixa de erro: %{customdata[1]}<br>"
                    "%{customdata[2]} das amostras<extra></extra>")

# ---------------------------------------------------------------------------
# Textos: Previsoes dos Modelos
# ---------------------------------------------------------------------------
NOME_RL = 'Regressão Linear'
NOME_DTA = 'Árvore de Decisão'

SECAO_DISPERSAO = "Dispersão entre modelos"
TEXTO_DISPERSAO = (
    "**O que mostra:** cada ponto é uma amostra, posicionada pela previsão da "
    "Regressão Linear (eixo horizontal) e da Árvore (eixo vertical). A linha "
    "tracejada representa concordância perfeita entre os dois modelos.\n\n"
    "- **Resultado bom:** os pontos se alinham próximos da linha tracejada, "
    "indicando que os modelos previram valores parecidos.\n"
    "- **Resultado ruim:** pontos espalhados longe da linha indicam "
    "discordância entre os modelos naquelas amostras.\n\n"
    "Os pontos formam colunas verticais porque a previsão da Regressão Linear é "
    "arredondada para número inteiro.")

# rotulos da dispersao
G_AMOSTRAS = 'Amostras'
G_CONCORDANCIA_YX = 'Concordância (y=x)'
G_TITULO_DISPERSAO = 'Dispersão: Regressão Linear vs Árvore'
G_EIXO_PREVISTO_RL = 'IQA previsto (RL)'
G_EIXO_PREVISTO_DTA = 'IQA previsto (Árvore)'
DICA_DISPERSAO = "IQA previsto (RL): %{customdata[0]}<br>IQA previsto (Árvore): %{customdata[1]}"

# ---------------------------------------------------------------------------
# Textos: Graficos de monitoramento da qualidade da agua (Visao Geral e
# Previsoes dos Modelos)
# ---------------------------------------------------------------------------
_TEXTO_MONITORAMENTO_LIMITES = (
    "O objetivo do gráfico é entender em quais datas a qualidade da água esteve muito "
    "baixa (até o LI) ou muito alta (acima do LS). Os limites LS e LI foram definidos "
    "arbitrariamente; a LC é calculada a partir dos dados:\n\n"
    "1. LS (Limite Superior) = {ls}, pois, segundo as faixas de qualidade da água da "
    "CETESB, acima de {ls} a água tem qualidade ótima\n"
    "2. LI (Limite Inferior) = {li}, pois, segundo as faixas de qualidade da água da "
    "CETESB, até {li} a água tem qualidade ruim ou péssima\n"
    "3. LC (Linha Central) = IQA médio do ponto de coleta selecionado\n\n"
    "- **Resultado bom:** existem poucos pontos até o LI = {li} e muitos acima do "
    "LS = {ls}.\n"
    "- **Resultado ruim:** existem muitos pontos até o LI = {li} e poucos acima do "
    "LS = {ls}.").format(ls=LS_MONITORAMENTO, li=LI_MONITORAMENTO)
SECAO_MONITORAMENTO_PREVISTO = "Gráficos de Monitoramento da Qualidade da Água (Previsto)"
TEXTO_MONITORAMENTO_PREVISTO = (
    "**O que mostra:** o IQA previsto por cada modelo ao longo do tempo no ponto de coleta "
    "selecionado. " + _TEXTO_MONITORAMENTO_LIMITES)
SECAO_MONITORAMENTO_REAL = "Gráfico de Monitoramento da Qualidade da Água (Real)"
TEXTO_MONITORAMENTO_REAL = (
    "**O que mostra:** o IQA real ao longo do tempo no ponto de coleta selecionado. "
    + _TEXTO_MONITORAMENTO_LIMITES)
INFO_MONITORAMENTO_SEM_COLUNAS = ("Para ver o gráfico de monitoramento da qualidade da água, "
                                  "inclua as colunas Ponto de Coleta e Data na planilha.")
ROTULO_SELETOR_PONTO = "Ponto de Coleta"

# resumo abaixo de cada grafico: {pct} = qtd / total em %, {palavra} =
# PALAVRA_AMOSTRA_SING quando total == 1, senao PALAVRA_AMOSTRA_PLURAL
FORMATO_MONITORAMENTO_BAIXO = (":red-background[**{pct}** das amostras ({qtd} de {total} "
                               "{palavra}) com IQA ruim ou péssimo (até {li}).]")
FORMATO_MONITORAMENTO_ALTO = (":green-background[**{pct}** das amostras ({qtd} de {total} "
                              "{palavra}) com IQA ótimo (acima de {ls}).]")
PALAVRA_AMOSTRA_SING = "amostra"
PALAVRA_AMOSTRA_PLURAL = "amostras"

G_TITULO_MONITORAMENTO = 'Monitoramento do IQA: {nome}'
G_NOME_REAL = 'Real'
G_EIXO_DATA = 'Data'
G_EIXO_IQA_REAL = 'IQA real'
G_EIXO_IQA_PREVISTO = 'IQA previsto'
G_LC = 'LC = média ({v})'
G_LI = 'LI = {v}'
G_LS = 'LS = {v}'
G_IQA_RUIM = 'IQA ruim ou péssimo'
G_IQA_OTIMO = 'IQA ótimo'
FOLGA_EIXO_MONITORAMENTO = 2     # folga do eixo Y quando algum valor passa de 0 a 100
DICA_MONITORAMENTO = "Data: %{customdata[0]}<br>IQA: %{customdata[1]}<br>Categoria: %{customdata[2]}"

# ---------------------------------------------------------------------------
# Textos: Comparacao entre Pontos de Coleta
# ---------------------------------------------------------------------------
NOTA_PONTOS = ("O R² de um ponto de coleta costuma ser menor porque o IQA varia menos "
               "dentro dele. Para comparar pontos de coleta, use o MAE.")
COLUNAS_TABELA_PONTOS = ["Ponto de Coleta", "Amostras", "R²", "MAE", "MAPE", "RMSE"]
COLUNA_DESTAQUE_PONTOS = "MAE"    # métrica recomendada pela NOTA_PONTOS

# ---------------------------------------------------------------------------
# Textos: Sobre o Dashboard
# ---------------------------------------------------------------------------
SOBRE_TITULO_VARIAVEIS = "Variáveis de qualidade da água"
SOBRE_COLUNAS_VARIAVEIS = ["Sigla", "Nome", "Unidade"]
# lista propria da tabela da aba Sobre (NT e IQA nao entram nas linhas
# obrigatorias da planilha modelo)
SOBRE_VARIAVEIS = [
    ('DBO', 'Demanda Bioquímica de Oxigênio', 'mg/L'),
    ('CT', 'Coliformes termotolerantes (E. coli)', 'UFC/100 mL'),
    ('FT', 'Fósforo total', 'mg/L'),
    ('SOD', 'Saturação de oxigênio dissolvido', '% de saturação'),
    ('pH', 'pH', 'sem unidade'),
    ('ST', 'Sólidos totais', 'mg/L'),
    ('TUR', 'Turbidez', 'UNT'),
    ('NT', 'Nitrogênio total', 'mg/L'),
    ('IQA', 'Índice de Qualidade das Águas', 'sem unidade'),
]
SOBRE_TITULO_FICHA = "Ficha dos modelos"
SOBRE_FICHA = [
    "Variáveis de entrada: {n_variaveis}",
    "Árvore de Decisão: profundidade {profundidade} e {folhas} folhas",
    "Valores vazios: preenchidos pelo método dos {vizinhos} vizinhos mais próximos "
    "(KNN), com o ajuste feito no treino.",
]
SOBRE_TITULO_FAIXAS = "Faixas do IQA"
SOBRE_COLUNAS_FAIXAS = ["Categoria", "Faixa do IQA"]

# ---------------------------------------------------------------------------
# Excel de exportacao
# ---------------------------------------------------------------------------
ABA_X_RESUMO = 'Resumo'
ABA_X_PREVISOES = 'Previsões'
ABA_X_METRICAS = 'Métricas'
ABA_X_PONTOS = 'Pontos de Coleta'      # o Excel aceita no maximo 31 caracteres
ABA_X_REMOVIDAS = 'Linhas removidas'
ABA_X_AJUSTES = 'Ajustes automáticos'
ABA_X_AVISOS = 'Avisos'
ABA_X_MODELO_DADOS = 'Dados'
ABA_X_MODELO_DICIONARIO = 'Dicionário'

# cabecalhos em portugues das abas Previsoes e Linhas removidas (as chaves
# internas continuam no codigo; so a gravacao do Excel usa estes nomes)
COLUNA_X_LINHA = 'Linha original'
COLUNA_X_MOTIVO = 'Motivo'
COLUNAS_X_PREVISOES = {
    'Linha_original': COLUNA_X_LINHA,
    COLUNA_DATA: 'Data',
    COLUNA_PONTO: 'Ponto de Coleta',
    'WQI_real': 'IQA real',
    'Previsao_RL': 'Previsão RL',
    'Previsao_DTA': 'Previsão Árvore',
}
FORMATO_X_USADO_NO_MODELO = "{sigla} (usado no modelo)"

COLUNAS_X_METRICAS = ['Indicador', 'Regressão Linear', 'Árvore de Decisão', 'Unidade']
LINHAS_X_METRICAS = [
    ('R2', 'R²', 'sem unidade'),
    ('MAPE', 'MAPE (%)', '%'),
    ('MAE', 'MAE', 'Pontos de IQA'),
    ('RMSE', 'RMSE', 'Pontos de IQA'),
]
UNIDADE_X_FAIXAS_ERRO = '%'    # linhas das faixas de erro (rotulos em FAIXAS_ERRO)
COLUNAS_X_PONTOS = ['Ponto de Coleta', 'Amostras', 'R² RL', 'R² Árvore', 'MAE RL', 'MAE Árvore',
                    'MAPE RL', 'MAPE Árvore', 'RMSE RL', 'RMSE Árvore']
COLUNAS_X_AVISOS = ['Aviso', 'Quantidade de linhas', COLUNA_X_LINHA]
COLUNAS_X_AJUSTES = [COLUNA_X_LINHA, 'Variável', 'Ajuste', 'Valor original',
                     'Valor usado pelo modelo']
COLUNAS_X_MODELO_DICIONARIO = ['Coluna', 'Nome', 'Unidade', 'Obrigatória', 'Também aceito como']

AJUSTE_IMPUTACAO = 'Célula vazia preenchida (KNN, 5 vizinhos)'
AJUSTE_WINSORIZACAO = 'Valor extremo ajustado (winsorização 10%)'
MOTIVO_ACIMA = '{var} acima de {maximo}'
MOTIVO_ABAIXO = '{var} abaixo de {minimo}'

RESUMO_ITENS = {
    'arquivo': 'Arquivo',
    'gerado_em': 'Gerado em',
    'situacao': 'Situação',
    'linhas_lidas': 'Linhas lidas',
    'linhas_removidas': 'Linhas removidas pelo filtro',
    'pct_removidas': 'Linhas removidas pelo filtro (%)',
    'linhas_previstas': 'Linhas previstas',
    'linhas_wqi_real': 'Linhas com IQA real válido',
    'celulas_imputadas': 'Células vazias preenchidas',
    'valores_winsorizados': 'Valores extremos ajustados',
}
SITUACAO_OK = 'Processado'
SITUACAO_BLOQUEADO = 'Bloqueado: {motivo}'

AVISO_WQI_ZERO = "{n} linhas com IQA real igual a 0 ficaram fora apenas do MAPE"
AVISO_SEM_WQI = "{n} linhas sem IQA real válido: têm previsão, mas ficam fora das métricas, dos gráficos Previsto x Real, do gráfico de monitoramento (Real) e da comparação entre pontos de coleta"
AVISO_NAO_NUMERICO = "{n} células com texto no lugar de número em {coluna}: tratadas como vazias"
AVISO_PONTO_VAZIO = "{n} linhas com Ponto de Coleta vazio ficaram fora da comparação entre pontos de coleta e dos gráficos de monitoramento"
AVISO_COLUNA_DUPLICADA = "A variável {sigla} aparece em duas colunas ({col1} e {col2}): foi usada a coluna {col1}"
AVISO_DATA_INVALIDA = "{n} linhas com data que não pôde ser lida ficaram fora dos gráficos de monitoramento"
AVISO_SEM_DATA = "A planilha não tem coluna de data: os gráficos de monitoramento não são gerados"
AVISO_REMOCAO_ALTA = ("Mais de 80% das linhas foram removidas. Confira se as unidades "
                      "das colunas são as mesmas da planilha modelo.")
