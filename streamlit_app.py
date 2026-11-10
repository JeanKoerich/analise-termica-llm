from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Monitoramento Térmico Inteligente",
    page_icon=":material/monitoring:",
    layout="wide",
    initial_sidebar_state="expanded",
)

CSS = """
<style>
    .block-container { padding-top: 2rem; padding-bottom: 3rem; }

    .portfolio-hero {
        position: relative;
        padding: 2rem 2.25rem;
        border-radius: 16px;
        background: linear-gradient(115deg, #0c233c 0%, #143a55 58%, #0c525e 100%);
        border: 1px solid rgba(127, 217, 226, .22);
        color: #f4f8fc;
        margin-bottom: 1.3rem;
    }
    .portfolio-eyebrow {
        text-transform: uppercase;
        letter-spacing: .13em;
        color: #89d5df;
        font-weight: 700;
        font-size: .73rem;
        margin-bottom: .65rem;
    }
    .portfolio-hero h1 {
        font-size: clamp(1.9rem, 3vw, 2.8rem);
        line-height: 1.18;
        margin: 0 0 .65rem;
        color: #ffffff;
        font-weight: 750;
    }
    .portfolio-hero p {
        color: #c5d7e2;
        font-size: 1.04rem;
        line-height: 1.55;
        max-width: 760px;
        margin: 0;
    }
    .portfolio-tag {
        display: inline-flex;
        align-items: center;
        gap: .45rem;
        margin-top: 1.25rem;
        border-radius: 999px;
        border: 1px solid rgba(137, 213, 223, .4);
        padding: .35rem .75rem;
        color: #aeeaf0;
        background: rgba(255, 255, 255, .07);
        font-size: .8rem;
        font-weight: 600;
    }
    .flow-pipeline {
        display: flex;
        flex-wrap: wrap;
        gap: .5rem;
        align-items: center;
        margin: .4rem 0 1.1rem;
    }
    .flow-step {
        border: 1px solid rgba(115, 141, 162, .35);
        background: rgba(100, 140, 165, .08);
        border-radius: 10px;
        padding: .65rem .9rem;
        font-weight: 600;
        font-size: .9rem;
    }
    .flow-arrow { color: #7895a7; font-weight: 700; }
    @media (max-width: 680px) {
        .portfolio-hero { padding: 1.5rem 1.2rem; }
        .flow-arrow { display: none; }
    }
</style>
"""

def carregar_base_visao_geral():
    """Prioriza a base ETL da sessão; sem ela, usa amostra *declaradamente sintética*."""
    base_sessao = st.session_state.get("monitoramento_df")
    if isinstance(base_sessao, pd.DataFrame) and not base_sessao.empty:
        return base_sessao.copy(), "Base processada na sessão", False

    caminho = Path(__file__).resolve().parent / "data" / "amostra_leituras.csv"
    if caminho.is_file():
        try:
            amostra = pd.read_csv(caminho)
            if not amostra.empty:
                return amostra, "Amostra sintética de demonstração", True
        except (OSError, ValueError, pd.errors.ParserError):
            pass

    return pd.DataFrame(), "Nenhuma base disponível", False

def coluna_numerica(df, *alternativas):
    for coluna in alternativas:
        if coluna in df.columns:
            return pd.to_numeric(df[coluna], errors="coerce")
    return pd.Series(float("nan"), index=df.index)

def formatar(valor, casas=1, unidade=""):
    if pd.isna(valor):
        return "—"
    texto = f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{texto}{unidade}"

def preparar_preview(df):
    dados = df.copy()
    dados["_entrada"] = coluna_numerica(dados, "nr_temperatura_entrada", "temperatura_entrada")
    dados["_saida"] = coluna_numerica(dados, "nr_temperatura_saida", "temperatura_saida")
    dados["_vazao"] = coluna_numerica(dados, "nr_vazao_l_min", "vazao_l_min")
    dados["_delta"] = coluna_numerica(dados, "nr_delta_t", "delta_t")
    if dados["_delta"].isna().all():
        dados["_delta"] = dados["_saida"] - dados["_entrada"]

    data_col = next((c for c in ("dt_registro", "timestamp") if c in dados.columns), None)
    dados["_instante"] = pd.to_datetime(dados[data_col], errors="coerce") if data_col else pd.NaT
    return dados.sort_values("_instante", na_position="last")

def exibir_grafico(df):
    plot = df.dropna(subset=["_instante"]).copy()
    if plot.empty or (plot["_entrada"].isna().all() and plot["_saida"].isna().all()):
        st.info("Não há temperaturas e datas suficientes para montar o gráfico.")
        return

    # Evita renderizar dezenas de milhares de pontos na tela inicial.
    passo = max(1, (len(plot) + 599) // 600)
    plot = plot.iloc[::passo]

    figura = go.Figure()
    figura.add_trace(go.Scatter(
        x=plot["_instante"], y=plot["_entrada"],
        mode="lines", name="Entrada", line=dict(color="#50a8e8", width=2),
    ))
    figura.add_trace(go.Scatter(
        x=plot["_instante"], y=plot["_saida"],
        mode="lines", name="Saída", line=dict(color="#21b99a", width=2.5),
    ))
    figura.update_layout(
        margin=dict(l=5, r=5, t=8, b=5),
        height=315,
        hovermode="x unified",
        legend=dict(orientation="h", y=1.13, x=0),
        xaxis_title=None,
        yaxis_title="Temperatura (°C)",
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#899aab"),
    )
    figura.update_xaxes(showgrid=False)
    figura.update_yaxes(gridcolor="rgba(127, 145, 165, .18)")
    st.plotly_chart(figura, use_container_width=True, config={"displayModeBar": False})

def pagina_inicial():
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(
        """
        <section class="portfolio-hero">
            <div class="portfolio-eyebrow">Portfólio de IA aplicada à indústria</div>
            <h1>Monitoramento Térmico Inteligente</h1>
            <p>Transformando leituras do pré-aquecimento de água industrial
               em indicadores, análise exploratória e relatórios interpretados por LLM.</p>
            <span class="portfolio-tag">● Python &nbsp;·&nbsp; ETL &nbsp;·&nbsp; Dados &nbsp;·&nbsp; IA generativa</span>
        </section>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Explore os módulos")
    col_etl, col_analise, col_ia = st.columns(3, gap="medium")

    with col_etl:
        with st.container(border=True):
            st.markdown("#### :material/database: Engenharia de dados")
            st.caption("01 · Entrada e tratamento")
            st.write("Importe CSV ou XLSX e prepare as medições para análise.")
            st.page_link("etl_monitoramento.py", label="Abrir ETL", icon=":material/arrow_forward:")

    with col_analise:
        with st.container(border=True):
            st.markdown("#### :material/analytics: Análise exploratória")
            st.caption("02 · Indicadores e tendências")
            st.write("Investigue temperaturas, vazão e comportamento térmico.")
            st.page_link("exploratoria_monitoramento.py", label="Abrir análise", icon=":material/arrow_forward:")

    with col_ia:
        with st.container(border=True):
            st.markdown("#### :material/smart_toy: Relatório com IA")
            st.caption("03 · Interpretação com LLM")
            st.write("Transforme indicadores em um relatório técnico interpretativo.")
            st.page_link("inteligencia_monitoramento.py", label="Abrir IA", icon=":material/arrow_forward:")

    st.markdown("### Panorama dos dados")
    base, origem, sintetica = carregar_base_visao_geral()
    if base.empty:
        st.warning("Nenhuma base encontrada. Comece por **ETL** e processe seu CSV ou XLSX.")
    else:
        if sintetica:
            st.info("**Demonstração:** os indicadores abaixo usam dados **sintéticos** de `data/amostra_leituras.csv`, não medições industriais reais. Para usar seus dados, processe um arquivo na página ETL.")
        else:
            st.success("Exibindo os dados processados na sessão atual. Indicadores atualizados a partir da base carregada.")

        preview = preparar_preview(base)
        m1, m2, m3, m4 = st.columns(4, gap="medium")
        m1.metric("Registros", formatar(len(preview), casas=0))
        m2.metric("Temperatura média de saída", formatar(preview["_saida"].mean(), unidade=" °C"))
        m3.metric("Ganho térmico médio (ΔT)", formatar(preview["_delta"].mean(), unidade=" °C"))
        m4.metric("Vazão média", formatar(preview["_vazao"].mean(), casas=2, unidade=" L/min"))
        st.caption("Médias simples calculadas sobre os registros disponíveis; podem incluir diferentes estados operacionais. Não representam uma avaliação de eficiência por si só.")

        grafico, contexto = st.columns([2.2, 1], gap="large")
        with grafico:
            st.markdown("#### Evolução das temperaturas")
            exibir_grafico(preview)
        with contexto:
            st.markdown("#### Contexto dos dados")
            st.write(f"**Fonte:** {origem}")
            validos = preview["_instante"].dropna()
            if not validos.empty:
                st.write(f"**Primeira leitura:** {validos.min():%d/%m/%Y %H:%M}")
                st.write(f"**Última leitura:** {validos.max():%d/%m/%Y %H:%M}")
            estado_col = next((c for c in ("ds_estado_processo", "estado_processo") if c in preview.columns), None)
            if estado_col:
                estados = preview[estado_col].dropna()
                if not estados.empty:
                    st.write(f"**Último estado registrado:** {estados.iloc[-1]}")
            st.caption("Resumo da base; não representa leitura ao vivo de sensores.")

    st.markdown("### Como funciona")
    st.markdown(
        """
        <div class="flow-pipeline" aria-label="Fluxo de processamento">
          <span class="flow-step">01 · CSV / XLSX</span><span class="flow-arrow">→</span>
          <span class="flow-step">02 · ETL</span><span class="flow-arrow">→</span>
          <span class="flow-step">03 · Análise exploratória</span><span class="flow-arrow">→</span>
          <span class="flow-step">04 · Relatório com LLM</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("O LLM interpreta indicadores derivados das medições; cálculos e validações devem permanecer reproduzíveis no código.")

pages = {
    "MONITORAMENTO TÉRMICO": [
        st.Page(pagina_inicial, title="Visão Geral", icon=":material/home:", default=True),
    ],
    "ENGENHARIA DE DADOS": [
        st.Page("etl_monitoramento.py", title="ETL", icon=":material/pivot_table_chart:"),
        st.Page("exploratoria_monitoramento.py", title="Análise Exploratória", icon=":material/analytics:"),
    ],
    "INTELIGÊNCIA ARTIFICIAL": [
        st.Page("inteligencia_monitoramento.py", title="Relatório com IA", icon=":material/smart_toy:"),
    ],
}

pagina = st.navigation(pages)
pagina.run()