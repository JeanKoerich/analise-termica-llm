import re
from io import BytesIO

import pandas as pd

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)

DIMENSOES = [
    "ds_origem",
    "ds_estado_processo",
    "ds_status_operacional",
    "ds_valvula_entrada",
    "ds_valvula_saida",
    "ds_condicao_termica",
    "ds_condicao_transferencia",
    "ds_faixa_desempenho_termico",
    "ds_status_valvulas",
    "ds_criticidade",
    "ds_status_validacao",
]


MEDIDAS = [
    "nr_ciclo",
    "nr_temperatura_entrada",
    "nr_temperatura_saida",
    "nr_delta_t",
    "nr_vazao_l_min",
    "nr_volume_instante_l",
    "nr_volume_total_l",
    "nr_nivel_tubulacao_percentual",
    "nr_tempo_maturacao_min",
    "nr_energia_kj",
    "nr_energia_kwh",
    "nr_energia_total_kwh",
    "nr_desempenho_termico_percentual",
    "nr_economia_reais",
    "nr_fator_solar",
]


def preparar_base(df):

    df = df.copy()

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
    )

    # DATA DE CADASTRO
    if "dt_cadastro" in df.columns:

        df["dt_cadastro"] = pd.to_datetime(
            df["dt_cadastro"],
            errors="coerce",
            utc=True
        )

        df["dt_cadastro"] = (
            df["dt_cadastro"]
            .dt.tz_convert("America/Sao_Paulo")
            .dt.tz_localize(None)
        )

    # DATA DA LEITURA
    if "dt_registro" in df.columns:

        df["dt_registro"] = pd.to_datetime(
            df["dt_registro"],
            errors="coerce",
            utc=True
        )

        df["dt_registro"] = (
            df["dt_registro"]
            .dt.tz_convert("America/Sao_Paulo")
            .dt.tz_localize(None)
        )

        df = df.sort_values("dt_registro")

        df["data"] = df["dt_registro"].dt.date
        df["hora"] = df["dt_registro"].dt.hour
        df["mes"] = df["dt_registro"].dt.month
        df["ano"] = df["dt_registro"].dt.year

    # CAMPOS NUMÉRICOS
    for coluna in MEDIDAS:

        if coluna in df.columns:

            df[coluna] = pd.to_numeric(
                df[coluna],
                errors="coerce"
            )

    # FLAG VALIDADO
    if "fg_validado" in df.columns:

        df["fg_validado"] = (
            df["fg_validado"]
            .astype(str)
            .str.lower()
            .str.strip()
        )

    return df


def obter_dimensoes(df):

    return [
        coluna
        for coluna in DIMENSOES
        if coluna in df.columns
    ]


def obter_medidas(df):

    return [
        coluna
        for coluna in MEDIDAS
        if coluna in df.columns
    ]

def gerar_pdf_relatorio(
    texto_markdown,
    tipo_relatorio
):
    """
    Converte o relatório Markdown gerado pela IA em PDF.
    Retorna o PDF em memória como bytes.
    """

    buffer = BytesIO()

    # ========================================================
    # FONTES
    # ========================================================

    fonte_normal = "Helvetica"
    fonte_bold = "Helvetica-Bold"

    # No Windows, utilizar Arial para suportar
    # corretamente caracteres como Δ, ° e acentuação.
    try:

        caminho_arial = (
            r"C:\Windows\Fonts\arial.ttf"
        )

        caminho_arial_bold = (
            r"C:\Windows\Fonts\arialbd.ttf"
        )

        pdfmetrics.registerFont(
            TTFont(
                "Arial",
                caminho_arial
            )
        )

        pdfmetrics.registerFont(
            TTFont(
                "Arial-Bold",
                caminho_arial_bold
            )
        )

        fonte_normal = "Arial"
        fonte_bold = "Arial-Bold"

    except Exception:

        pass


    # ========================================================
    # DOCUMENTO
    # ========================================================

    documento = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=(
            f"Relatório {tipo_relatorio} "
            f"- Monitoramento Térmico"
        )
    )


    estilos_base = (
        getSampleStyleSheet()
    )


    estilo_titulo = ParagraphStyle(
        "TituloRelatorio",
        parent=estilos_base["Title"],
        fontName=fonte_bold,
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        spaceAfter=18
    )


    estilo_h1 = ParagraphStyle(
        "H1Relatorio",
        parent=estilos_base["Heading1"],
        fontName=fonte_bold,
        fontSize=14,
        leading=18,
        spaceBefore=12,
        spaceAfter=8
    )


    estilo_h2 = ParagraphStyle(
        "H2Relatorio",
        parent=estilos_base["Heading2"],
        fontName=fonte_bold,
        fontSize=12,
        leading=16,
        spaceBefore=10,
        spaceAfter=6
    )


    estilo_texto = ParagraphStyle(
        "TextoRelatorio",
        parent=estilos_base["BodyText"],
        fontName=fonte_normal,
        fontSize=10,
        leading=15,
        spaceAfter=7
    )


    estilo_lista = ParagraphStyle(
        "ListaRelatorio",
        parent=estilo_texto,
        leftIndent=14,
        firstLineIndent=-8,
        spaceAfter=4
    )


    elementos = []


    # ========================================================
    # TÍTULO
    # ========================================================

    elementos.append(
        Paragraph(
            f"Relatório {tipo_relatorio}",
            estilo_titulo
        )
    )

    elementos.append(
        Paragraph(
            "Sistema de Monitoramento Térmico",
            estilo_h2
        )
    )

    elementos.append(
        Spacer(
            1,
            10
        )
    )


    # ========================================================
    # FUNÇÃO PARA FORMATAR MARKDOWN SIMPLES
    # ========================================================

    def formatar_markdown(texto):

        texto = texto.strip()

        texto = re.sub(
            r"\*\*(.+?)\*\*",
            r"<b>\1</b>",
            texto
        )

        texto = re.sub(
            r"`(.+?)`",
            r"<font name='Courier'>\1</font>",
            texto
        )

        return texto


    # ========================================================
    # PROCESSAR LINHAS
    # ========================================================

    linhas = texto_markdown.splitlines()

    i = 0

    while i < len(linhas):

        linha = linhas[i].strip()


        # Ignorar título Markdown original
        if linha.startswith("### Relatório"):
            i += 1
            continue


        # Linha vazia
        if not linha:
            elementos.append(
                Spacer(
                    1,
                    4
                )
            )

            i += 1
            continue


        # ====================================================
        # TABELA MARKDOWN
        # ====================================================

        if (
            linha.startswith("|")
            and
            linha.endswith("|")
        ):

            tabela_dados = []


            while (
                i < len(linhas)
                and
                linhas[i].strip().startswith("|")
                and
                linhas[i].strip().endswith("|")
            ):

                linha_tabela = (
                    linhas[i]
                    .strip()
                )


                celulas = [
                    celula.strip()
                    for celula
                    in linha_tabela.strip("|").split("|")
                ]


                # Ignorar linha separadora Markdown:
                # | --- | ---: |
                separador = all(
                    re.match(
                        r"^:?-+:?$",
                        celula.replace(
                            " ",
                            ""
                        )
                    )
                    for celula
                    in celulas
                )


                if not separador:

                    tabela_dados.append([
                        Paragraph(
                            formatar_markdown(
                                celula
                            ),
                            estilo_texto
                        )
                        for celula
                        in celulas
                    ])


                i += 1


            if tabela_dados:

                tabela = Table(
                    tabela_dados,
                    repeatRows=1,
                    hAlign="LEFT"
                )


                tabela.setStyle(
                    TableStyle([
                        (
                            "FONTNAME",
                            (0, 0),
                            (-1, -1),
                            fonte_normal
                        ),

                        (
                            "FONTNAME",
                            (0, 0),
                            (-1, 0),
                            fonte_bold
                        ),

                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, 0),
                            colors.HexColor(
                                "#EDEDED"
                            )
                        ),

                        (
                            "GRID",
                            (0, 0),
                            (-1, -1),
                            0.4,
                            colors.grey
                        ),

                        (
                            "VALIGN",
                            (0, 0),
                            (-1, -1),
                            "TOP"
                        ),

                        (
                            "LEFTPADDING",
                            (0, 0),
                            (-1, -1),
                            5
                        ),

                        (
                            "RIGHTPADDING",
                            (0, 0),
                            (-1, -1),
                            5
                        ),

                        (
                            "TOPPADDING",
                            (0, 0),
                            (-1, -1),
                            5
                        ),

                        (
                            "BOTTOMPADDING",
                            (0, 0),
                            (-1, -1),
                            5
                        )
                    ])
                )


                elementos.append(
                    tabela
                )

                elementos.append(
                    Spacer(
                        1,
                        10
                    )
                )


            continue


        # ====================================================
        # TÍTULOS
        # ====================================================

        if linha.startswith("## "):

            elementos.append(
                Paragraph(
                    formatar_markdown(
                        linha[3:]
                    ),
                    estilo_h1
                )
            )

            i += 1
            continue


        if linha.startswith("### "):

            elementos.append(
                Paragraph(
                    formatar_markdown(
                        linha[4:]
                    ),
                    estilo_h2
                )
            )

            i += 1
            continue


        # ====================================================
        # LISTA
        # ====================================================

        if linha.startswith("- "):

            elementos.append(
                Paragraph(
                    "• "
                    + formatar_markdown(
                        linha[2:]
                    ),
                    estilo_lista
                )
            )

            i += 1
            continue


        # Lista numerada
        if re.match(
            r"^\d+\.\s",
            linha
        ):

            elementos.append(
                Paragraph(
                    formatar_markdown(
                        linha
                    ),
                    estilo_lista
                )
            )

            i += 1
            continue


        # ====================================================
        # PARÁGRAFO NORMAL
        # ====================================================

        elementos.append(
            Paragraph(
                formatar_markdown(
                    linha
                ),
                estilo_texto
            )
        )

        i += 1


    # ========================================================
    # GERAR PDF
    # ========================================================

    documento.build(
        elementos
    )

    pdf = buffer.getvalue()

    buffer.close()

    return pdf

def normalizar_moeda_relatorio(texto):
    if not texto:
        return texto

    texto = texto.replace("R`", "R$")
    texto = texto.replace("R´", "R$")
    texto = texto.replace("R’", "R$")
    texto = texto.replace("R'", "R$")
    texto = texto.replace("R $", "R$")
    texto = texto.replace("R $", "R$")

    return texto