import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from io import BytesIO
import requests

tz = ZoneInfo("America/Sao_Paulo")

# Configuração da página
st.set_page_config(layout="wide", page_title="Monitoramento de Ônibus")

# 1. Função para carregar os dados
@st.cache_data(ttl=30)
def load_data(tempo=5):
    data_hoje = datetime.now(tz)
    primeira_data = data_hoje - timedelta(minutes=tempo)
    
    primeira_data_str = primeira_data.strftime("%Y-%m-%d+%H:%M:%S")
    segunda_data_str = data_hoje.strftime("%Y-%m-%d+%H:%M:%S")
    
    url = f"https://dados.mobilidade.rio/gps/sppo?dataInicial={primeira_data_str}&dataFinal={segunda_data_str}"
    resp = requests.get(url)
    
    if resp.status_code == 200:
        df = pd.read_json(BytesIO(resp.content))
        if df.empty:
            return pd.DataFrame()

        df['datahora_legivel'] = pd.to_datetime(df['datahoraenvio'], unit='ms')
        df['datahora_legivel'] = df['datahora_legivel'].dt.tz_localize('UTC').dt.tz_convert(tz).dt.strftime('%d/%m/%Y %H:%M:%S')
    
        df = df.sort_values(by='datahora')
        df['latitude'] = df['latitude'].astype(str).str.replace(',', '.').astype(float)
        df['longitude'] = df['longitude'].astype(str).str.replace(',', '.').astype(float)
        return df
    return pd.DataFrame()

st.title("🚌 Mapa de Monitoramento de Ônibus")

# Carrega os dados base
df_base = load_data()

if df_base.empty:
    st.warning("Nenhum dado retornado pela API no momento.")
    st.stop()

# =====================================================================
# BARRA LATERAL 
# =====================================================================
st.sidebar.header("Navegação")
modo = st.sidebar.radio(
    "O que você deseja visualizar?",
    ("Visão Geral (Última posição)", "Histórico de um Ônibus (Trajeto)")
)

if modo == "Visão Geral (Última posição)":
    df_ultima_base = df_base.drop_duplicates(subset=['ordem'], keep='last')
    linhas_disponiveis = ["Todas"] + list(df_ultima_base['linha'].dropna().unique())
    linha_selecionada = st.sidebar.selectbox("Filtre por Linha:", linhas_disponiveis)
    ordem_selecionada = None
else:
    ordens_disponiveis = df_base['ordem'].dropna().unique()
    ordem_selecionada = st.sidebar.selectbox("Selecione a Ordem do Ônibus (ID):", ordens_disponiveis)
    linha_selecionada = None

# =====================================================================
# ÁREA DO MAPA (Atualiza a cada 30 segundos)
# =====================================================================
@st.fragment(run_every="30s")
def mostrar_mapa_atualizado():        
    # --- MODO 1: VISÃO GERAL ---
    if modo == "Visão Geral (Última posição)":
        df_agora = load_data()
        if df_agora.empty:
            st.warning("Aguardando novos dados da prefeitura...")
            return
        df_ultima_posicao = df_agora.drop_duplicates(subset=['ordem'], keep='last')
        
        # MÁGICA DA PERFORMANCE: Se for "Todas", não colorimos por linha para não travar
        if linha_selecionada != "Todas":
            df_plot = df_ultima_posicao[df_ultima_posicao['linha'] == linha_selecionada]
            cor_pontos = "linha" # Aqui tudo bem criar legenda, é uma linha só
        else:
            df_plot = df_ultima_posicao
            cor_pontos = None # Desliga a separação de cores para ficar muito mais rápido!

        if not df_plot.empty:
            fig = px.scatter_mapbox(
                df_plot, 
                lat="latitude", 
                lon="longitude", 
                color=cor_pontos, # Aplica a variável definida acima
                hover_name="ordem", 
                hover_data=["linha", "velocidade", "datahora_legivel"],
                zoom=10, 
                height=600,
                title=f"Mostrando {len(df_plot)} ônibus (Atualizado a cada 30 segundos)"
            )
            
            fig.update_traces(marker=dict(color='blue'))

            fig.update_traces(
                hovertemplate="<b>Ônibus: %{hovertext}</b><br>Linha: %{customdata[0]}<br>Velocidade: %{customdata[1]} km/h<br>Horário: %{customdata[2]}<extra></extra>"
            )
            
            # MÁGICA DO MAPA COLORIDO: Usar "open-street-map" ao invés de "carto-positron"
            fig.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":40,"l":0,"b":0})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Nenhum dado encontrado para a linha selecionada neste exato momento.")

    # --- MODO 2: HISTÓRICO ---
    elif modo == "Histórico de um Ônibus (Trajeto)":
        # ATENÇÃO: Puxar 60 minutos de TODA a frota do Rio pode deixar o app lento. 
        # Se travar muito no modo histórico, reduza esse 60 para 15 ou 30.
        df_agora = load_data(30)
        if df_agora.empty:
            st.warning("Aguardando novos dados da prefeitura...")
            return
        df_onibus = df_agora[df_agora['ordem'] == ordem_selecionada]
        
        if not df_onibus.empty:
            st.write(f"**Linha(s) operada(s) por este veículo:** {', '.join(df_onibus['linha'].dropna().unique())}")
            
            fig = px.line_mapbox(
                df_onibus, 
                lat="latitude", 
                lon="longitude", 
                hover_name="datahora_legivel",
                hover_data=["velocidade", "linha"],
                zoom=13, 
                height=600
            )
            fig.update_traces(
                mode='lines+markers',
                line=dict(width=3, color='blue'), 
                marker=dict(size=6, color='blue'),
                hovertemplate="<b>Horário: %{hovertext}</b><br>Velocidade: %{customdata[0]} km/h<br>Linha: %{customdata[1]}<extra></extra>"
            )

            ultima_posicao = df_onibus.iloc[[-1]] 
            fig_ultima = px.scatter_mapbox(
                ultima_posicao, 
                lat="latitude", 
                lon="longitude", 
                hover_name="datahora_legivel",
                hover_data=["velocidade", "linha"]
            )
            fig_ultima.update_traces(
                marker=dict(size=14, color='red'),
                hovertemplate="<b>🚨 POSIÇÃO ATUAL</b><br>Horário: %{hovertext}<br>Velocidade: %{customdata[0]} km/h<extra></extra>"
            )
            
            fig.add_trace(fig_ultima.data[0])
            
            # Aplicando o mapa colorido no modo histórico também
            fig.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":0,"l":0,"b":0})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Sem posições recentes para este veículo no período selecionado.")

mostrar_mapa_atualizado()