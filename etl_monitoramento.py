import streamlit as st
import pandas as pd

from function_monitoramento import preparar_base


st.title("ETL - Monitoramento Térmico")

st.caption(
    "Extração, transformação e preparação "
    "dos dados do sistema de monitoramento."
)

st.divider()


arquivo = st.file_uploader(
    "Selecione a base de dados",
    type=["csv", "xlsx"]
)


if arquivo is not None:

    if arquivo.name.lower().endswith(".csv"):

        df = pd.read_csv(arquivo)

    else:

        df = pd.read_excel(arquivo)


    st.subheader("Dados originais")

    st.dataframe(
        df.head(100),
        use_container_width=True
    )

    if st.button("Processar dados"):

        base = preparar_base(df)

        st.session_state["monitoramento_df"] = base

        st.success(
            f"{len(base):,} registros processados."
        )

        st.subheader("Dados tratados")

        st.dataframe(
            base.head(100),
            use_container_width=True
        )