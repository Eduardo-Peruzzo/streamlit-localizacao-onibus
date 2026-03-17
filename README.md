<img width="1042" height="1410" alt="image" src="https://github.com/user-attachments/assets/8ed17425-8997-40ff-8525-9b8814f218b0" /># Monitoramento de Ônibus em Tempo Real

---

## 1. Introdução

- Contextualização: mobilidade urbana e transparência de dados públicos
- Apresentação do objeto de estudo: aplicação de monitoramento dos ônibus do Rio de Janeiro
- Objetivo geral do ensaio: apresentar o método utilizado e as tecnologias escolhidas na extração e preparação de dados públicos da localização em tempo real da frota de ônibus do Rio de Janeiro. 

---

## 2. Base de Dados e Fonte

- API pública da Prefeitura do Rio (`dados.mobilidade.rio/gps/sppo`)
- Dados coletados: coordenadas GPS, linha, velocidade, identificador do veículo (`ordem`), timestamp
- Janela temporal de coleta: últimos 5 minutos (visão geral) ou 30 minutos (histórico)
> Nota: Uma visão geral com o dataframe muito extenso (maior período de requisição) teria uma demora de resposta considerável; tal medida foi adotada por fins de otimização.

---

## 3. Arquitetura da Aplicação

- Framework utilizado: **Streamlit**
- Estratégia de cache (`@st.cache_data`, TTL de 30 segundos) para equilibrar atualidade e desempenho
- Atualização automática via `@st.fragment(run_every="30s")`

---

## 4. Fluxo
1. Inicialização — o app sobe e aciona o cache
2. Cache/API — decide se reutiliza dados ou dispara nova requisição HTTP
3. Ingestão — GET na API da prefeitura com janela temporal parametrizada
4. Transformação — parse de timestamps, normalização de lat/lon, ordenação
5. Navegação — usuário escolhe modo na sidebar, gerando dois caminhos distintos
6. Renderização — Plotly constrói o mapa (scatter_mapbox ou line_mapbox)
7. Loop — o @st.fragment reexecuta tudo a cada 30 segundos automaticamente

![Uploading fluxo_monitoramento_onibus.svg…]()

---

## 5. Funcionalidades Implementadas

### 5.1 Visão Geral da Frota
- Exibição da última posição registrada de cada veículo
- Filtro por linha operante

### 5.2 Histórico de Trajeto Individual
- Traçado da rota percorrida por um veículo específico nos últimos 30 minutos
- Marcador destacado (vermelho) para a posição mais recente
- Exibição de velocidade e horário por ponto

---

## 6. Conclusão e Escalonamento

Aplicativos como Moovit fazem um processo semelhante, o que traz um valor poderoso de escalonamento para o produto em si.
Há endpoints para BRT e alguns outros transportes públicos.
Foi complicado de ínicio trabalhar com largura fixa e principalmente com Unix time.
Mas com estes insights valiosos, sistemas tão, senão mais,, eficientes e/ou completo como Moovit podem ser construídos.
---
