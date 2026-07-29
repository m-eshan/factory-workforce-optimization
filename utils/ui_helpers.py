from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st


def apply_global_style() -> None:
    st.markdown(
        """
        <style>
        .stApp, [data-testid="stAppViewContainer"] {
            background: #ffffff;
            color: #172033;
        }
        .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
        .stApp p, .stApp span, .stApp label,
        [data-testid="stMarkdownContainer"],
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stWidgetLabel"],
        [data-testid="stWidgetLabel"] p,
        [data-testid="stCaptionContainer"],
        [data-testid="stRadio"] label,
        [data-testid="stFileUploader"] label,
        [data-testid="stDateInput"] label,
        [data-testid="stSlider"] label {
            color: #172033 !important;
        }
        [data-testid="stHeader"] {
            background: rgba(255, 255, 255, 0.96);
        }
        [data-testid="stSidebar"] {
            background: #f7f9fc;
        }
        [data-testid="stSidebar"] * {
            color: #172033 !important;
        }
        .stButton button,
        .stDownloadButton button {
            background: #1d4ed8;
            color: #ffffff !important;
            border: 1px solid #1d4ed8;
            border-radius: 8px;
        }
        .stButton button p,
        .stDownloadButton button p,
        .stButton button span,
        .stDownloadButton button span {
            color: #ffffff !important;
        }
        .stButton button:hover,
        .stDownloadButton button:hover {
            background: #1e40af;
            border-color: #1e40af;
            color: #ffffff !important;
        }
        input, textarea, select {
            color: #101828 !important;
            background: #ffffff !important;
        }
        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e3e8ef;
            border-radius: 8px;
            padding: 12px 14px;
            box-shadow: 0 1px 3px rgba(16, 24, 40, 0.06);
        }
        div[data-testid="stMetricLabel"] p {
            color: #475467 !important;
            font-size: 0.92rem;
        }
        div[data-testid="stMetricValue"] {
            color: #101828 !important;
        }
        div[data-testid="stMetricDelta"] {
            color: #475467 !important;
        }
        .manager-note {
            background: #f8fbff;
            border: 1px solid #d7e6fb;
            border-left: 4px solid #2563eb;
            border-radius: 8px;
            padding: 12px 14px;
            margin: 8px 0;
            color: #172033 !important;
        }
        .manager-note * {
            color: #172033 !important;
        }
        .good-note {
            background: #f6fef9;
            border-color: #abefc6;
            border-left-color: #16a34a;
        }
        .warn-note {
            background: #fffbeb;
            border-color: #fedf89;
            border-left-color: #d97706;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def readable_chart(fig: go.Figure, height: int = 430) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        height=height,
        margin=dict(l=35, r=25, t=60, b=45),
        font=dict(size=14, color="#0b1220"),
        title_font=dict(size=19, color="#0b1220"),
        legend_title_text="",
        hovermode="x unified",
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
    )
    fig.update_xaxes(showgrid=True, gridcolor="#e5e7eb", zeroline=False, title_font=dict(size=15, color="#0b1220"), tickfont=dict(size=13, color="#0b1220"), linecolor="#475467")
    fig.update_yaxes(showgrid=True, gridcolor="#e5e7eb", zeroline=False, title_font=dict(size=15, color="#0b1220"), tickfont=dict(size=13, color="#0b1220"), linecolor="#475467")
    return fig


def manager_note(text: str, tone: str = "info") -> None:
    css_class = {"good": "good-note", "warn": "warn-note"}.get(tone, "")
    st.markdown(f"<div class='manager-note {css_class}'>{text}</div>", unsafe_allow_html=True)

