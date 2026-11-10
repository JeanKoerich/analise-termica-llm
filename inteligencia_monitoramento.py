import os
import json
import pandas as pd
import streamlit as st

from dotenv import load_dotenv
from openai import OpenAI

from function_monitoramento import (
    gerar_pdf_relatorio,
    normalizar_moeda_relatorio
)
# ============================================================
# CONFIGURAÇÕES
# ============================================================

load_dotenv()

MODELO_OPENAI = "gpt-6-luna"

TARIFA_KWH = 0.52
DELTA_T_REFERENCIA_C = 15.0
FLUXO_MINIMO_L_MIN = 0.5


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def numero_seguro(valor, casas=2):
    if valor is None or pd.isna(valor):
        return None

    return round(float(valor), casas)


def formatar_valor(valor, unidade=""):
    if valor is None or pd.isna(valor):
        return "N/D"

    return f"{float(valor):.2f}{unidade}"


def distribuicao(base, coluna):
    """
    Retorna quantidade e percentual de cada categoria.
    """
    if coluna not in base.columns or base.empty:
        return {}

    contagem = (
        base[coluna]
        .fillna("Não informado")
        .value_counts()
    )

    total = len(base)
    resultado = {}

    for categoria, quantidade in contagem.items():
        resultado[str(categoria)] = {
            "quantidade": int(quantidade),
            "percentual": round(
                quantidade / total * 100,
                2
            )
        }

    return resultado

def aplicar_conformidade_operacional(base):
    """
    Valida cada registro cruzando:
    - estado operacional;
    - válvula de entrada;
    - válvula de saída;
    - vazão.

    Além da conformidade geral, identifica qual regra lógica
    foi violada no registro.
    """

    base = base.copy()

    # Resultado geral
    base["ds_conformidade_operacional"] = "INDETERMINADA"

    # Motivo lógico da inconformidade
    base["ds_motivo_inconformidade"] = "NÃO AVALIADO"

    # Resultado individual de cada regra
    base["fg_valvula_entrada_conforme"] = pd.Series(
        pd.NA,
        index=base.index,
        dtype="boolean"
    )

    base["fg_valvula_saida_conforme"] = pd.Series(
        pd.NA,
        index=base.index,
        dtype="boolean"
    )

    base["fg_vazao_conforme"] = pd.Series(
        pd.NA,
        index=base.index,
        dtype="boolean"
    )


    colunas_necessarias = [
        "ds_estado_processo",
        "ds_valvula_entrada",
        "ds_valvula_saida",
        "nr_vazao_l_min"
    ]


    if not all(
        coluna in base.columns
        for coluna in colunas_necessarias
    ):
        return base


    # ========================================================
    # NORMALIZAÇÃO
    # ========================================================

    estado = (
        base["ds_estado_processo"]
        .astype("string")
        .str.strip()
        .str.upper()
    )


    entrada = (
        base["ds_valvula_entrada"]
        .astype("string")
        .str.strip()
        .str.upper()
    )


    saida = (
        base["ds_valvula_saida"]
        .astype("string")
        .str.strip()
        .str.upper()
    )


    vazao = pd.to_numeric(
        base["nr_vazao_l_min"],
        errors="coerce"
    )


    # ========================================================
    # REGISTROS AVALIÁVEIS
    # ========================================================

    estados_validos = estado.isin([
        "RECARREGANDO",
        "AQUECENDO",
        "MATURANDO",
        "TRANSFERINDO"
    ])


    valvulas_validas = (
        entrada.isin([
            "ABERTA",
            "FECHADA"
        ])
        &
        saida.isin([
            "ABERTA",
            "FECHADA"
        ])
    )


    registros_avaliaveis = (
        estados_validos
        &
        valvulas_validas
        &
        vazao.notna()
    )


    # ========================================================
    # RECARREGANDO
    # ========================================================

    mascara = (
        estado.eq("RECARREGANDO")
        &
        registros_avaliaveis
    )


    base.loc[
        mascara,
        "fg_valvula_entrada_conforme"
    ] = entrada.loc[
        mascara
    ].eq("ABERTA")


    base.loc[
        mascara,
        "fg_valvula_saida_conforme"
    ] = saida.loc[
        mascara
    ].eq("FECHADA")


    base.loc[
        mascara,
        "fg_vazao_conforme"
    ] = vazao.loc[
        mascara
    ].gt(
        FLUXO_MINIMO_L_MIN
    )


    # ========================================================
    # AQUECENDO
    # ========================================================

    mascara = (
        estado.eq("AQUECENDO")
        &
        registros_avaliaveis
    )


    base.loc[
        mascara,
        "fg_valvula_entrada_conforme"
    ] = entrada.loc[
        mascara
    ].eq("FECHADA")


    base.loc[
        mascara,
        "fg_valvula_saida_conforme"
    ] = saida.loc[
        mascara
    ].eq("FECHADA")


    base.loc[
        mascara,
        "fg_vazao_conforme"
    ] = vazao.loc[
        mascara
    ].le(
        FLUXO_MINIMO_L_MIN
    )


    # ========================================================
    # MATURANDO
    # ========================================================

    mascara = (
        estado.eq("MATURANDO")
        &
        registros_avaliaveis
    )


    base.loc[
        mascara,
        "fg_valvula_entrada_conforme"
    ] = entrada.loc[
        mascara
    ].eq("FECHADA")


    base.loc[
        mascara,
        "fg_valvula_saida_conforme"
    ] = saida.loc[
        mascara
    ].eq("FECHADA")


    base.loc[
        mascara,
        "fg_vazao_conforme"
    ] = vazao.loc[
        mascara
    ].le(
        FLUXO_MINIMO_L_MIN
    )


    # ========================================================
    # TRANSFERINDO
    # ========================================================

    mascara = (
        estado.eq("TRANSFERINDO")
        &
        registros_avaliaveis
    )


    base.loc[
        mascara,
        "fg_valvula_entrada_conforme"
    ] = entrada.loc[
        mascara
    ].eq("ABERTA")


    base.loc[
        mascara,
        "fg_valvula_saida_conforme"
    ] = saida.loc[
        mascara
    ].eq("ABERTA")


    base.loc[
        mascara,
        "fg_vazao_conforme"
    ] = vazao.loc[
        mascara
    ].gt(
        FLUXO_MINIMO_L_MIN
    )


    # ========================================================
    # CONFORMIDADE GERAL
    # ========================================================

    regras_conformes = (
        base["fg_valvula_entrada_conforme"].eq(True)
        &
        base["fg_valvula_saida_conforme"].eq(True)
        &
        base["fg_vazao_conforme"].eq(True)
    )


    base.loc[
        registros_avaliaveis
        &
        regras_conformes,
        "ds_conformidade_operacional"
    ] = "CONFORME"


    base.loc[
        registros_avaliaveis
        &
        ~regras_conformes,
        "ds_conformidade_operacional"
    ] = "INCONFORME"

    # ========================================================
    # MOTIVOS DA INCONFORMIDADE
    # ========================================================

    conformes = (
        base[
            "ds_conformidade_operacional"
        ]
        == "CONFORME"
    )


    inconformes = (
        base[
            "ds_conformidade_operacional"
        ]
        == "INCONFORME"
    )


    base.loc[
        conformes,
        "ds_motivo_inconformidade"
    ] = "SEM INCONFORMIDADE"


    motivos = pd.Series(
        "",
        index=base.index,
        dtype="string"
    )


    erro_entrada = (
        inconformes
        &
        base[
            "fg_valvula_entrada_conforme"
        ]
        .eq(False)
        .fillna(False)
    )


    erro_saida = (
        inconformes
        &
        base[
            "fg_valvula_saida_conforme"
        ]
        .eq(False)
        .fillna(False)
    )


    erro_vazao = (
        inconformes
        &
        base[
            "fg_vazao_conforme"
        ]
        .eq(False)
        .fillna(False)
    )


    motivos.loc[
        erro_entrada
    ] += "Válvula de entrada; "


    motivos.loc[
        erro_saida
    ] += "Válvula de saída; "


    motivos.loc[
        erro_vazao
    ] += "Vazão; "


    base.loc[
        inconformes,
        "ds_motivo_inconformidade"
    ] = (
        motivos.loc[
            inconformes
        ]
        .str.rstrip("; ")
    )

    return base

def calcular_motivos_inconformidade(base):
    """
    Conta quais regras foram responsáveis pelas
    inconformidades operacionais.

    Um mesmo registro pode violar mais de uma regra.
    """

    if (
        base.empty
        or
        "ds_conformidade_operacional"
        not in base.columns
    ):
        return {}


    inconformes = base[
        base[
            "ds_conformidade_operacional"
        ]
        == "INCONFORME"
    ].copy()


    if inconformes.empty:

        return {
            "total_inconformes": 0,
            "valvula_entrada_incorreta": 0,
            "valvula_saida_incorreta": 0,
            "vazao_incorreta": 0,
            "multiplas_regras_incorretas": 0
        }


    erro_entrada = (
        inconformes[
            "fg_valvula_entrada_conforme"
        ]
        .eq(False)
        .fillna(False)
    )


    erro_saida = (
        inconformes[
            "fg_valvula_saida_conforme"
        ]
        .eq(False)
        .fillna(False)
    )


    erro_vazao = (
        inconformes[
            "fg_vazao_conforme"
        ]
        .eq(False)
        .fillna(False)
    )


    quantidade_erros = (
        erro_entrada.astype(int)
        +
        erro_saida.astype(int)
        +
        erro_vazao.astype(int)
    )


    return {

        "total_inconformes":
            int(
                len(inconformes)
            ),

        "valvula_entrada_incorreta":
            int(
                erro_entrada.sum()
            ),

        "valvula_saida_incorreta":
            int(
                erro_saida.sum()
            ),

        "vazao_incorreta":
            int(
                erro_vazao.sum()
            ),

        "multiplas_regras_incorretas":
            int(
                (
                    quantidade_erros > 1
                ).sum()
            ),

        "observacao": (
            "Um mesmo registro pode aparecer em "
            "mais de um motivo quando viola "
            "múltiplas regras simultaneamente."
        )
    }

def calcular_resumo_conformidade(base):
    """
    Resume a conformidade operacional global.
    O percentual de conformidade considera somente
    os registros efetivamente avaliáveis.
    """

    if (
        base.empty
        or "ds_conformidade_operacional" not in base.columns
    ):
        return {}

    contagem = (
        base["ds_conformidade_operacional"]
        .value_counts()
    )

    conformes = int(
        contagem.get("CONFORME", 0)
    )

    inconformes = int(
        contagem.get("INCONFORME", 0)
    )

    indeterminados = int(
        contagem.get("INDETERMINADA", 0)
    )

    avaliaveis = conformes + inconformes

    percentual_conforme = (
        round(
            conformes / avaliaveis * 100,
            2
        )
        if avaliaveis > 0
        else None
    )

    percentual_inconforme = (
        round(
            inconformes / avaliaveis * 100,
            2
        )
        if avaliaveis > 0
        else None
    )

    return {
        "registros_totais": int(len(base)),
        "registros_avaliaveis": avaliaveis,
        "conformes": conformes,
        "inconformes": inconformes,
        "indeterminados": indeterminados,
        "percentual_conforme_entre_avaliaveis":
            percentual_conforme,
        "percentual_inconforme_entre_avaliaveis":
            percentual_inconforme,
        "criterio": (
            "A conformidade cruza estado, válvula de entrada, "
            "válvula de saída e vazão em cada registro."
        )
    }


def calcular_estatisticas_por_estado(base):
    """
    Consolida indicadores e conformidade por estado operacional.
    """

    resultado = {}

    if (
        base.empty
        or "ds_estado_processo" not in base.columns
    ):
        return resultado

    for nome_estado, grupo in base.groupby(
        "ds_estado_processo",
        dropna=False
    ):

        estado = (
            "Não informado"
            if pd.isna(nome_estado)
            else str(nome_estado)
        )

        total = len(grupo)

        vazao_sem_fluxo_logico = 0
        vazao_com_fluxo_logico = 0

        if "nr_vazao_l_min" in grupo.columns:

            vazao_valida = (
                pd.to_numeric(
                    grupo["nr_vazao_l_min"],
                    errors="coerce"
                )
                .dropna()
            )

            vazao_sem_fluxo_logico = int(
                (
                    vazao_valida
                    <= FLUXO_MINIMO_L_MIN
                ).sum()
            )

            vazao_com_fluxo_logico = int(
                (
                    vazao_valida
                    > FLUXO_MINIMO_L_MIN
                ).sum()
            )

        conformidade = {}

        if (
            "ds_conformidade_operacional"
            in grupo.columns
        ):
            contagem_conformidade = (
                grupo[
                    "ds_conformidade_operacional"
                ]
                .value_counts()
            )

            conformes = int(
                contagem_conformidade.get(
                    "CONFORME",
                    0
                )
            )

            inconformes = int(
                contagem_conformidade.get(
                    "INCONFORME",
                    0
                )
            )

            indeterminados = int(
                contagem_conformidade.get(
                    "INDETERMINADA",
                    0
                )
            )

            avaliaveis = (
                conformes
                + inconformes
            )

            conformidade = {
                "avaliaveis": avaliaveis,
                "conformes": conformes,
                "inconformes": inconformes,
                "indeterminados": indeterminados,
                "percentual_conforme_entre_avaliaveis": (
                    round(
                        conformes
                        / avaliaveis
                        * 100,
                        2
                    )
                    if avaliaveis > 0
                    else None
                )
            }

        motivos_inconformidade = (
            calcular_motivos_inconformidade(
                grupo
            )
        )

        resultado[estado] = {
            "registros": int(total),

            "participacao_percentual": round(
                total / len(base) * 100,
                2
            ),

            "temperatura_entrada_media_c":
                numero_seguro(
                    grupo[
                        "nr_temperatura_entrada"
                    ].mean()
                )
                if "nr_temperatura_entrada"
                in grupo.columns
                else None,

            "temperatura_saida_media_c":
                numero_seguro(
                    grupo[
                        "nr_temperatura_saida"
                    ].mean()
                )
                if "nr_temperatura_saida"
                in grupo.columns
                else None,

            "delta_t_medio_c":
                numero_seguro(
                    grupo[
                        "nr_delta_t"
                    ].mean()
                )
                if "nr_delta_t"
                in grupo.columns
                else None,

            "vazao_media_l_min":
                numero_seguro(
                    grupo[
                        "nr_vazao_l_min"
                    ].mean()
                )
                if "nr_vazao_l_min"
                in grupo.columns
                else None,

            "vazao_minima_l_min":
                numero_seguro(
                    grupo[
                        "nr_vazao_l_min"
                    ].min()
                )
                if "nr_vazao_l_min"
                in grupo.columns
                else None,

            "vazao_maxima_l_min":
                numero_seguro(
                    grupo[
                        "nr_vazao_l_min"
                    ].max()
                )
                if "nr_vazao_l_min"
                in grupo.columns
                else None,

            "registros_sem_fluxo_logico":
                vazao_sem_fluxo_logico,

            "registros_com_fluxo_logico":
                vazao_com_fluxo_logico,

            "desempenho_termico_medio_percentual":
                numero_seguro(
                    grupo[
                        "nr_desempenho_termico_percentual"
                    ].mean()
                )
                if "nr_desempenho_termico_percentual"
                in grupo.columns
                else None,

            "conformidade_operacional":
    conformidade,

            "motivos_inconformidade":
    motivos_inconformidade
        }

    return resultado

# ============================================================
# TÍTULO
# ============================================================

st.title("Relatório com Inteligência Artificial")

st.caption(
    "Geração de relatórios a partir dos indicadores "
    "calculados sobre os dados de monitoramento térmico."
)

st.divider()


# ============================================================
# VERIFICAR BASE
# ============================================================

if "monitoramento_df" not in st.session_state:

    st.warning(
        "Carregue e processe uma base primeiro na etapa ETL."
    )

    st.stop()


df = st.session_state[
    "monitoramento_df"
].copy()


# ============================================================
# TRATAMENTO DA DATA
# ============================================================

df["dt_registro"] = pd.to_datetime(
    df["dt_registro"],
    errors="coerce"
)

if df["dt_registro"].dt.tz is not None:

    df["dt_registro"] = (
        df["dt_registro"]
        .dt.tz_localize(None)
    )


df = (
    df
    .dropna(
        subset=["dt_registro"]
    )
    .sort_values(
        "dt_registro"
    )
)


if df.empty:

    st.error(
        "Não existem registros válidos para análise."
    )

    st.stop()


# ============================================================
# FILTRO DE PERÍODO
# ============================================================

st.subheader(
    "Período da análise"
)


periodo = st.segmented_control(
    "Selecione o período",
    options=[
        "1 dia",
        "7 dias",
        "30 dias",
        "90 dias",
        "Todo período",
        "Personalizado"
    ],
    default="30 dias"
)


data_max = df[
    "dt_registro"
].max()

data_min = df[
    "dt_registro"
].min()


if periodo == "1 dia":

    inicio = (
        data_max
        - pd.Timedelta(
            days=1
        )
    )

    fim = data_max


elif periodo == "7 dias":

    inicio = (
        data_max
        - pd.Timedelta(
            days=7
        )
    )

    fim = data_max


elif periodo == "30 dias":

    inicio = (
        data_max
        - pd.Timedelta(
            days=30
        )
    )

    fim = data_max


elif periodo == "90 dias":

    inicio = (
        data_max
        - pd.Timedelta(
            days=90
        )
    )

    fim = data_max


elif periodo == "Todo período":

    inicio = data_min
    fim = data_max


else:

    col_data1, col_data2 = st.columns(
        2
    )

    data_inicial = (
        col_data1.date_input(
            "Data inicial",
            value=data_min.date(),
            min_value=data_min.date(),
            max_value=data_max.date()
        )
    )

    data_final = (
        col_data2.date_input(
            "Data final",
            value=data_max.date(),
            min_value=data_min.date(),
            max_value=data_max.date()
        )
    )

    inicio = pd.Timestamp(
        data_inicial
    )

    fim = (
        pd.Timestamp(
            data_final
        )
        + pd.Timedelta(
            days=1
        )
        - pd.Timedelta(
            microseconds=1
        )
    )


# ============================================================
# VALIDAR PERÍODO
# ============================================================

if inicio > fim:

    st.error(
        "A data inicial não pode ser maior que a data final."
    )

    st.stop()


# ============================================================
# FILTRAR PERÍODO
# ============================================================

base_periodo = df[
    (
        df["dt_registro"]
        >= inicio
    )
    &
    (
        df["dt_registro"]
        <= fim
    )
].copy()


if base_periodo.empty:

    st.warning(
        "Não existem registros no período selecionado."
    )

    st.stop()


st.caption(
    f"Período selecionado: "
    f"{inicio.strftime('%d/%m/%Y %H:%M')} até "
    f"{fim.strftime('%d/%m/%Y %H:%M')} "
    f"• {len(base_periodo):,} registros"
)


# ============================================================
# FILTRO DE ESTADO
# ============================================================

estados = sorted(
    base_periodo[
        "ds_estado_processo"
    ]
    .dropna()
    .unique()
    .tolist()
)


estado = st.selectbox(
    "Estado do processo",
    ["Todos"] + estados
)


if estado == "Todos":

    base = (
        base_periodo.copy()
    )

else:

    base = base_periodo[
        base_periodo[
            "ds_estado_processo"
        ]
        == estado
    ].copy()


if base.empty:

    st.warning(
        "Não existem registros para o estado selecionado."
    )

    st.stop()


# ============================================================
# TIPO DE RELATÓRIO
# ============================================================

tipo_relatorio = st.selectbox(
    "Tipo de relatório",
    [
        "Técnico",
        "Executivo",
        "Acadêmico"
    ]
)


# ============================================================
# CONFORMIDADE OPERACIONAL POR REGISTRO
# ============================================================

base = aplicar_conformidade_operacional(
    base
)


# ============================================================
# INDICADORES DO PERÍODO
# ============================================================

energia_periodo = (
    numero_seguro(
        base[
            "nr_energia_kwh"
        ].sum(),
        4
    )
    if "nr_energia_kwh"
    in base.columns
    else None
)


volume_periodo = (
    numero_seguro(
        base[
            "nr_volume_instante_l"
        ].sum(),
        2
    )
    if "nr_volume_instante_l"
    in base.columns
    else None
)


economia_estimada = (
    round(
        energia_periodo
        * TARIFA_KWH,
        2
    )
    if energia_periodo
    is not None
    else None
)


resumo_conformidade = (
    calcular_resumo_conformidade(
        base
    )
)

motivos_inconformidade_global = (
    calcular_motivos_inconformidade(
        base
    )
)

estatisticas_por_estado = (
    calcular_estatisticas_por_estado(
        base
    )
)


# ============================================================
# REGRAS E PARÂMETROS DO PROJETO
# ============================================================

parametros_projeto = {

    "delta_t_referencia_c":
        DELTA_T_REFERENCIA_C,

    "limiar_logico_fluxo_l_min":
        FLUXO_MINIMO_L_MIN,

    "tarifa_referencia_reais_kwh":
        TARIFA_KWH,

    "interpretacao_limiar_fluxo": (
        "O valor de 0,5 L/min é um limiar lógico usado "
        "para distinguir presença e ausência de fluxo. "
        "Não representa a vazão nominal esperada nos "
        "estados AQUECENDO e MATURANDO."
    ),

    "interpretacao_desempenho_termico": (
        "O desempenho térmico representa o percentual "
        "de atendimento ao ganho térmico de referência "
        "de 15 °C. Não representa eficiência termodinâmica."
    ),

    "metodologia_desempenho_termico": (
        "O desempenho térmico é calculado individualmente "
        "para cada leitura com base no ΔT daquela leitura "
        "e depois agregado estatisticamente. "
        "O indicador é limitado ao intervalo de 0% a 100%. "
        "Por isso, o desempenho térmico médio NÃO deve ser "
        "recalculado dividindo o ΔT médio global por 15 °C."
    ),

    "interpretacao_economia": (
        "A economia financeira é estimada a partir da "
        "energia térmica calculada e da tarifa de referência. "
        "Não representa economia financeira comprovada "
        "em ambiente industrial real."
    )
}


regras_operacionais = {

    "RECARREGANDO": {
        "valvula_entrada_esperada":
            "Aberta",

        "valvula_saida_esperada":
            "Fechada",

        "vazao_nominal_esperada":
            "Presença de vazão",

        "criterio_logico_fluxo":
            (
                f"Vazão > "
                f"{FLUXO_MINIMO_L_MIN} L/min"
            ),

        "interpretacao": (
            "Existe entrada de água na tubulação. "
            "A presença de fluxo acima do limiar lógico "
            "é comportamento esperado."
        )
    },


    "AQUECENDO": {
        "valvula_entrada_esperada":
            "Fechada",

        "valvula_saida_esperada":
            "Fechada",

        "vazao_nominal_esperada":
            "0 L/min",

        "criterio_logico_sem_fluxo":
            (
                f"Vazão <= "
                f"{FLUXO_MINIMO_L_MIN} L/min"
            ),

        "interpretacao": (
            "A água permanece na tubulação para aquecimento. "
            "A vazão nominal esperada é 0 L/min. "
            "Para fins de validação lógica, valores até "
            f"{FLUXO_MINIMO_L_MIN} L/min são tratados como "
            "ausência de fluxo."
        )
    },


    "MATURANDO": {
        "valvula_entrada_esperada":
            "Fechada",

        "valvula_saida_esperada":
            "Fechada",

        "vazao_nominal_esperada":
            "0 L/min",

        "criterio_logico_sem_fluxo":
            (
                f"Vazão <= "
                f"{FLUXO_MINIMO_L_MIN} L/min"
            ),

        "interpretacao": (
            "O sistema permanece em estabilização térmica. "
            "A vazão nominal esperada é 0 L/min. "
            "Para fins de validação lógica, valores até "
            f"{FLUXO_MINIMO_L_MIN} L/min são tratados como "
            "ausência de fluxo."
        )
    },


    "TRANSFERINDO": {
        "valvula_entrada_esperada":
            "Aberta",

        "valvula_saida_esperada":
            "Aberta",

        "vazao_nominal_esperada":
            "Presença de vazão",

        "criterio_logico_fluxo":
            (
                f"Vazão > "
                f"{FLUXO_MINIMO_L_MIN} L/min"
            ),

        "interpretacao": (
            "A água aquecida está sendo transferida. "
            "A presença de fluxo acima do limiar lógico "
            "é comportamento esperado."
        )
    }
}


# ============================================================
# RESUMO ESTATÍSTICO
# ============================================================

resumo = {

    "filtros": {

        "periodo_selecionado":
            periodo,

        "inicio":
            inicio.strftime(
                "%d/%m/%Y %H:%M"
            ),

        "fim":
            fim.strftime(
                "%d/%m/%Y %H:%M"
            ),

        "estado_analisado":
            estado,

        "tipo_relatorio":
            tipo_relatorio
    },


    "amostra": {

        "total_registros":
            int(
                len(base)
            ),

        "primeira_leitura":
            (
                base[
                    "dt_registro"
                ]
                .min()
                .strftime(
                    "%d/%m/%Y %H:%M:%S"
                )
            ),

        "ultima_leitura":
            (
                base[
                    "dt_registro"
                ]
                .max()
                .strftime(
                    "%d/%m/%Y %H:%M:%S"
                )
            )
    },


    "parametros_projeto":
        parametros_projeto,


    "regras_operacionais":
        regras_operacionais,


    "conformidade_operacional":
        resumo_conformidade,

    "motivos_inconformidade_operacional":
        motivos_inconformidade_global,


    "temperatura_entrada_c": {

        "media":
            numero_seguro(
                base[
                    "nr_temperatura_entrada"
                ].mean()
            ),

        "minima":
            numero_seguro(
                base[
                    "nr_temperatura_entrada"
                ].min()
            ),

        "maxima":
            numero_seguro(
                base[
                    "nr_temperatura_entrada"
                ].max()
            ),

        "desvio_padrao":
            numero_seguro(
                base[
                    "nr_temperatura_entrada"
                ].std()
            )
    },


    "temperatura_saida_c": {

        "media":
            numero_seguro(
                base[
                    "nr_temperatura_saida"
                ].mean()
            ),

        "minima":
            numero_seguro(
                base[
                    "nr_temperatura_saida"
                ].min()
            ),

        "maxima":
            numero_seguro(
                base[
                    "nr_temperatura_saida"
                ].max()
            ),

        "desvio_padrao":
            numero_seguro(
                base[
                    "nr_temperatura_saida"
                ].std()
            )
    },


    "delta_t_c": {

        "media":
            numero_seguro(
                base[
                    "nr_delta_t"
                ].mean()
            ),

        "minimo":
            numero_seguro(
                base[
                    "nr_delta_t"
                ].min()
            ),

        "maximo":
            numero_seguro(
                base[
                    "nr_delta_t"
                ].max()
            ),

        "desvio_padrao":
            numero_seguro(
                base[
                    "nr_delta_t"
                ].std()
            ),

        "referencia_projeto_c":
            DELTA_T_REFERENCIA_C
    },


    "vazao_l_min": {

        "media":
            numero_seguro(
                base[
                    "nr_vazao_l_min"
                ].mean()
            ),

        "minima":
            numero_seguro(
                base[
                    "nr_vazao_l_min"
                ].min()
            ),

        "maxima":
            numero_seguro(
                base[
                    "nr_vazao_l_min"
                ].max()
            ),

        "desvio_padrao":
            numero_seguro(
                base[
                    "nr_vazao_l_min"
                ].std()
            ),

        "limiar_logico_fluxo_l_min":
            FLUXO_MINIMO_L_MIN
    },


    "desempenho_termico_percentual": {

        "media":
            numero_seguro(
                base[
                    "nr_desempenho_termico_percentual"
                ].mean()
            ),

        "minimo":
            numero_seguro(
                base[
                    "nr_desempenho_termico_percentual"
                ].min()
            ),

        "maximo":
            numero_seguro(
                base[
                    "nr_desempenho_termico_percentual"
                ].max()
            ),

        "delta_t_referencia_c":
            DELTA_T_REFERENCIA_C,

        "observacao_calculo": (
            "Calculado por leitura e depois agregado. "
            "Não recalcular a média usando apenas "
            "o ΔT médio global."
        )
    },


    "energia_e_volume": {

        "energia_termica_periodo_kwh":
            energia_periodo,

        "volume_periodo_l":
            volume_periodo,

        "tarifa_referencia_reais_kwh":
            TARIFA_KWH,

        "economia_financeira_estimada_reais":
            economia_estimada
    },


    "estatisticas_por_estado":
        estatisticas_por_estado,


    "distribuicao_estados":
        distribuicao(
            base,
            "ds_estado_processo"
        ),


    "distribuicao_conformidade_operacional":
        distribuicao(
            base,
            "ds_conformidade_operacional"
        ),


    "distribuicao_criticidades":
        distribuicao(
            base,
            "ds_criticidade"
        ),


    "distribuicao_condicao_termica":
        distribuicao(
            base,
            "ds_condicao_termica"
        ),


    "distribuicao_status_operacional":
        distribuicao(
            base,
            "ds_status_operacional"
        ),


    "distribuicao_status_validacao":
        distribuicao(
            base,
            "ds_status_validacao"
        ),


    "distribuicao_valvula_entrada":
        distribuicao(
            base,
            "ds_valvula_entrada"
        ),


    "distribuicao_valvula_saida":
        distribuicao(
            base,
            "ds_valvula_saida"
        ),


    "distribuicao_origem":
        distribuicao(
            base,
            "ds_origem"
        )
}


# ============================================================
# MÉTRICAS VISUAIS
# ============================================================

st.subheader(
    "Resumo da análise"
)


col1, col2, col3, col4 = st.columns(
    4
)


col1.metric(
    "Registros",
    f"{len(base):,}"
)


col2.metric(
    "T. entrada média",
    formatar_valor(
        base[
            "nr_temperatura_entrada"
        ].mean(),
        " °C"
    )
)


col3.metric(
    "T. saída média",
    formatar_valor(
        base[
            "nr_temperatura_saida"
        ].mean(),
        " °C"
    )
)


col4.metric(
    "ΔT médio",
    formatar_valor(
        base[
            "nr_delta_t"
        ].mean(),
        " °C"
    )
)


col5, col6, col7, col8 = st.columns(
    4
)


col5.metric(
    "Vazão média",
    formatar_valor(
        base[
            "nr_vazao_l_min"
        ].mean(),
        " L/min"
    )
)


col6.metric(
    "Energia térmica",
    (
        f"{energia_periodo:.4f} kWh"
        if energia_periodo
        is not None
        else "N/D"
    )
)


col7.metric(
    "Desempenho médio",
    formatar_valor(
        base[
            "nr_desempenho_termico_percentual"
        ].mean(),
        " %"
    )
)


col8.metric(
    "Economia estimada",
    (
        f"R$ {economia_estimada:.2f}"
        if economia_estimada
        is not None
        else "N/D"
    )
)


# ============================================================
# CONFORMIDADE OPERACIONAL VISUAL
# ============================================================

st.subheader(
    "Conformidade operacional"
)


conformes = (
    resumo_conformidade.get(
        "conformes",
        0
    )
)

inconformes = (
    resumo_conformidade.get(
        "inconformes",
        0
    )
)

indeterminados = (
    resumo_conformidade.get(
        "indeterminados",
        0
    )
)

percentual_conforme = (
    resumo_conformidade.get(
        "percentual_conforme_entre_avaliaveis"
    )
)


conf1, conf2, conf3, conf4 = (
    st.columns(4)
)


conf1.metric(
    "Conformes",
    f"{conformes:,}"
)


conf2.metric(
    "Inconformes",
    f"{inconformes:,}"
)


conf3.metric(
    "Indeterminados",
    f"{indeterminados:,}"
)


conf4.metric(
    "Conformidade",
    (
        f"{percentual_conforme:.2f} %"
        if percentual_conforme
        is not None
        else "N/D"
    ),
    help=(
        "Percentual calculado apenas entre "
        "os registros avaliáveis."
    )
)


st.caption(
    "A conformidade operacional cruza, em cada registro, "
    "o estado do processo, as válvulas de entrada e saída "
    "e a vazão."
)


# ============================================================
# DADOS UTILIZADOS PELA IA
# ============================================================

st.subheader(
    "Dados utilizados pela IA"
)


with st.expander(
    "Visualizar resumo estatístico"
):

    st.json(
        resumo
    )


# ============================================================
# CONTEXTO DO RELATÓRIO
# ============================================================

contexto_atual = (
    f"{inicio.isoformat()}|"
    f"{fim.isoformat()}|"
    f"{estado}|"
    f"{tipo_relatorio}|"
    f"{len(base)}|"
    f"{conformes}|"
    f"{inconformes}|"
    f"{indeterminados}"
)


if (
    st.session_state.get(
        "relatorio_contexto"
    )
    != contexto_atual
):

    st.session_state.pop(
        "relatorio_ia",
        None
    )


# ============================================================
# INSTRUÇÕES POR TIPO DE RELATÓRIO
# ============================================================

if tipo_relatorio == "Técnico":

    instrucoes_tipo = """
Produza um relatório técnico detalhado.

Estruture obrigatoriamente em:

1. Resumo executivo
2. Caracterização dos dados analisados
3. Análise das temperaturas
4. Análise do ganho térmico (ΔT)
5. Análise da vazão
6. Análise dos estados operacionais
7. Análise da conformidade operacional
8. Análise do desempenho térmico
9. Energia térmica e economia estimada
10. Criticidades e validações
11. Pontos de atenção
12. Conclusão técnica

Apresente valores numéricos relevantes ao longo da análise.

Utilize a conformidade operacional calculada pelo Pandas
como principal referência para avaliar a coerência entre
estado, válvulas e vazão.
"""


elif tipo_relatorio == "Executivo":

    instrucoes_tipo = """
Produza um relatório executivo conciso.

Estruture em:

1. Visão geral
2. Principais indicadores
3. Conformidade operacional
4. Desempenho observado
5. Pontos de atenção
6. Conclusão

Evite excesso de detalhes estatísticos.

Priorize informações relevantes para tomada de decisão.

A conformidade operacional já foi calculada pelo sistema.
Não tente recalculá-la a partir de distribuições marginais.
"""


else:

    instrucoes_tipo = """
Produza um relatório acadêmico formal.

Estruture em:

1. Contextualização da análise
2. Caracterização da amostra
3. Análise dos dados
4. Comportamento das temperaturas
5. Ganho térmico e vazão
6. Estados operacionais
7. Conformidade operacional
8. Desempenho térmico
9. Discussão dos resultados
10. Limitações da análise
11. Considerações finais

Utilize linguagem acadêmica, impessoal,
clara e objetiva.

Diferencie os resultados calculados pelo sistema
das interpretações produzidas pelo modelo de linguagem.
"""


# ============================================================
# GERAR RELATÓRIO
# ============================================================

if st.button(
    "Gerar relatório com IA",
    type="primary",
    use_container_width=False
):

    api_key = os.getenv(
        "OPENAI_API_KEY"
    )


    if not api_key:

        st.error(
            "A chave OPENAI_API_KEY não foi encontrada no arquivo .env."
        )

        st.stop()


    dados_json = json.dumps(
        resumo,
        ensure_ascii=False,
        indent=2,
        default=str
    )


    prompt = f"""
Você é um analista de dados industriais especializado
em sistemas de monitoramento térmico.

Os dados fornecidos abaixo foram previamente tratados
e calculados por uma aplicação Python utilizando Pandas.

Sua função NÃO é recalcular os dados.
Sua função é interpretar os indicadores fornecidos e
produzir um relatório em linguagem natural.

{instrucoes_tipo}


REGRAS OBRIGATÓRIAS:

- Utilize exclusivamente os dados fornecidos.

- Não invente valores.

- Não invente causas para os comportamentos observados.

- Não afirme que existe uma causa física sem evidência
  suficiente nos dados.

- Diferencie claramente fatos observados de interpretações.

- Caso identifique comportamento incomum, classifique-o
  como ponto de atenção, não como diagnóstico definitivo.

- A conformidade operacional já foi calculada pelo Pandas
  cruzando estado, válvula de entrada, válvula de saída
  e vazão em cada registro.

- Use os resultados de "conformidade_operacional" e
  "estatisticas_por_estado" como referência principal
  para analisar coerência operacional.

- Quando existirem registros INCONFORMES, utilize os campos
  "motivos_inconformidade_operacional" e
  "motivos_inconformidade" de cada estado para informar
  quais regras lógicas foram violadas.

- Diferencie claramente:
  válvula de entrada incorreta,
  válvula de saída incorreta
  e vazão incompatível com o estado.

- Um mesmo registro pode violar mais de uma regra.
  Portanto, a soma das quantidades por motivo pode ser
  maior que o total de registros inconformes.

- Esses motivos representam violações das regras lógicas
  do sistema. Não os apresente como causa física comprovada
  de uma falha.

- NÃO tente reconstruir a conformidade usando apenas
  distribuições agregadas de válvulas ou vazão.

- O valor de {FLUXO_MINIMO_L_MIN:.1f} L/min é um
  LIMIAR LÓGICO para distinguir presença e ausência de fluxo.

- Esse limiar NÃO representa a vazão nominal esperada
  em AQUECENDO e MATURANDO.

- Em AQUECENDO, a vazão nominal esperada é 0 L/min.
  Para a validação lógica do sistema, vazão <=
  {FLUXO_MINIMO_L_MIN:.1f} L/min é tratada como ausência
  de fluxo.

- Em MATURANDO, a vazão nominal esperada é 0 L/min.
  Para a validação lógica do sistema, vazão <=
  {FLUXO_MINIMO_L_MIN:.1f} L/min é tratada como ausência
  de fluxo.

- Em RECARREGANDO, espera-se entrada aberta, saída fechada
  e vazão > {FLUXO_MINIMO_L_MIN:.1f} L/min.

- Em TRANSFERINDO, esperam-se ambas as válvulas abertas
  e vazão > {FLUXO_MINIMO_L_MIN:.1f} L/min.

- Não classifique automaticamente ΔT baixo como falha.
  Utilize as classificações de criticidade fornecidas
  pelo próprio sistema.

- O ΔT de referência do projeto é
  {DELTA_T_REFERENCIA_C:.0f} °C.

- O indicador de desempenho térmico NÃO representa
  eficiência termodinâmica.

- O desempenho térmico é calculado individualmente em
  cada leitura e depois agregado estatisticamente.

- NÃO recalcule o desempenho térmico médio usando
  simplesmente:
  ΔT médio / {DELTA_T_REFERENCIA_C:.0f} × 100.

- A média dos desempenhos individuais pode diferir do
  resultado obtido ao aplicar a fórmula sobre o ΔT médio.

- 100% de desempenho térmico significa que o ganho térmico
  de referência foi atingido ou superado naquela leitura.
  Isso NÃO significa 100% de eficiência termodinâmica.

- A economia financeira apresentada é uma ESTIMATIVA,
  calculada a partir da energia térmica e da tarifa de
  referência de R$ {TARIFA_KWH:.2f}/kWh.

- Não apresente a economia como redução financeira
  comprovada em ambiente industrial real.

- Considere a origem dos dados apresentada no resumo.
  Caso a origem seja simulada, deixe explícito que os
  resultados foram obtidos sobre dados simulados.

- Quando comentar a frequência dos estados, utilize os
  termos "percentual de registros" ou "participação dos
  registros". Não converta automaticamente esse percentual
  em tempo de operação.

- Ao escrever valores monetários brasileiros, use
  obrigatoriamente o formato "R$ 0,00".

- Nunca utilize "R`", "R´" ou outra variação.

- Utilize unidades sempre que apresentar valores:
  °C, L/min, L, kWh, % e R$.

- Utilize linguagem clara, profissional e objetiva.


DADOS CALCULADOS PELO SISTEMA:

{dados_json}
"""


    try:

        with st.spinner(
            "Analisando os indicadores e gerando o relatório..."
        ):

            client = OpenAI(
                api_key=api_key
            )


            response = (
                client.responses.create(
                    model=MODELO_OPENAI,
                    input=prompt
                )
            )

        relatorio = normalizar_moeda_relatorio(
            response.output_text
        )

        st.session_state[
            "relatorio_ia"
        ] = relatorio


        st.session_state[
            "relatorio_contexto"
        ] = contexto_atual


    except Exception as erro:

        st.error(
            f"Erro ao gerar relatório: {erro}"
        )

# ============================================================
# EXIBIR RELATÓRIO
# ============================================================

if (
    "relatorio_ia"
    in st.session_state
    and
    st.session_state.get(
        "relatorio_contexto"
    )
    == contexto_atual
):

    st.divider()

    st.subheader(
        f"Relatório {tipo_relatorio}"
    )

    # ========================================================
    # NORMALIZAR TEXTO DO RELATÓRIO
    # ========================================================

    relatorio_corrigido = normalizar_moeda_relatorio(
        st.session_state[
            "relatorio_ia"
        ]
    )

    st.session_state[
        "relatorio_ia"
    ] = relatorio_corrigido


    # ========================================================
    # EXIBIÇÃO NO STREAMLIT
    # ========================================================
    # Escapa o símbolo $ para evitar que o Markdown
    # interprete R$ como expressão matemática.

    relatorio_exibicao = relatorio_corrigido.replace(
        "R$",
        r"R\$"
    )

    st.markdown(
        relatorio_exibicao
    )


    # ========================================================
    # GERAR PDF
    # ========================================================
    # O PDF usa o texto normal, sem o escape \$

    pdf_relatorio = gerar_pdf_relatorio(
        relatorio_corrigido,
        tipo_relatorio
    )


    # ========================================================
    # DOWNLOAD
    # ========================================================

    st.download_button(
        label="Baixar relatório em PDF",
        data=pdf_relatorio,
        file_name=(
            f"relatorio_"
            f"{tipo_relatorio.lower()}_"
            f"monitoramento.pdf"
        ),
        mime="application/pdf"
    )