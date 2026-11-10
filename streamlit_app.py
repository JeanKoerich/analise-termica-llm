import streamlit as st


st.set_page_config(
    page_title="Monitoramento Térmico Inteligente",
    page_icon=":material/monitoring:",
    layout="wide"
)


def pagina_inicial():

    st.title("Monitoramento Térmico Inteligente")

    st.caption(
        "Análise dos dados do sistema de monitoramento "
        "de pré-aquecimento de água industrial."
    )

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Engenharia de Dados")
        st.write(
            "Importação, tratamento e preparação "
            "dos dados provenientes de arquivos CSV ou XLSX."
        )

    with col2:
        st.subheader("Análise de Dados")
        st.write(
            "Análise das temperaturas, vazão, energia "
            "e desempenho térmico."
        )

    with col3:
        st.subheader("Inteligência Artificial")
        st.write(
            "Geração de relatórios e interpretação "
            "dos indicadores utilizando IA."
        )

    st.divider()

    st.subheader("Fluxo do sistema")

    st.markdown(
        """
        **CSV / XLSX**
        → **ETL**
        → **Análise Exploratória**
        → **Relatório com IA**
        """
    )


pages = {

    "MONITORAMENTO TÉRMICO": [

        st.Page(
            pagina_inicial,
            title="Visão Geral",
            icon=":material/home:"
        ),

    ],

    "ENGENHARIA DE DADOS": [

        st.Page(
            page="etl_monitoramento.py",
            title="ETL",
            icon=":material/pivot_table_chart:"
        ),

        st.Page(
            page="exploratoria_monitoramento.py",
            title="Análise Exploratória",
            icon=":material/analytics:"
        ),

    ],

    "INTELIGÊNCIA ARTIFICIAL": [

        st.Page(
            page="inteligencia_monitoramento.py",
            title="Relatório com IA",
            icon=":material/smart_toy:"
        ),

    ],

}


pg = st.navigation(pages)

pg.run()