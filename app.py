import streamlit as st
from datetime import datetime
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- Configurações ---
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = "1PLSVD3VxmgfWKOyr3Z700TbxCIZr1sT8IlOiSIvDvxM"
RANGE = "CAIXAS!A2:K6009"
BACKGROUND_URL = "https://raw.githubusercontent.com/leomarjms26-netizen/app.py/refs/heads/main/Copilot_20251016_121602.png"

st.markdown(
    """
    <link rel="apple-touch-icon" sizes="180x180" href="c64a4e55-0ce2-40c5-9392-fdc6f50f8b1aPNG.png">
    <link rel="icon" type="image/png" sizes="32x32" href="c64a4e55-0ce2-40c5-9392-fdc6f50f8b1aPNG.png">
    <link rel="icon" type="image/png" sizes="16x16" href="c64a4e55-0ce2-40c5-9392-fdc6f50f8b1aPNG.png">
    <link rel="manifest" href="manifest.json">
    """,
    unsafe_allow_html=True
)

# --- CSS para Mobile ---
st.markdown(f"""
<style>
html, body, [class*="stAppViewContainer"], [class*="stApp"], [data-testid="stAppViewContainer"] {{
    background: linear-gradient(rgba(0, 32, 46,0.75), rgba(0, 32, 46,0.75)),
                url('{BACKGROUND_URL}') !important;
    background-size: cover !important;
    background-position: center center !important;
    background-attachment: fixed !important;
}}
h1, h2, h3, h4, h5, h6, p, label, span, div {{
    color: #f8f9fa !important;
    text-align: center;
}}
.div-campo {{
    margin-bottom: 20px;
}}
.label {{
    font-weight: bold;
    font-size: 16px;
}}
.valor {{
    font-size: 18px;
    margin-top: 6px;
}}
.stButton > button {{
    border-radius: 6px;
    padding: 6px 16px;
}}
/* Botões principais e de download */
button[kind="primary"], .stDownloadButton > button, div.stButton > button {{
    background-color: rgb(32, 201, 58) !important;
    color: #ffffff !important;
    border: none !important;
}}
</style>
""", unsafe_allow_html=True)

# --- Funções Google Sheets ---
def autenticar_google():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "integracaogooglesheet.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds

def buscar_portas(creds, identificador):
    try:
        service = build("sheets", "v4", credentials=creds).spreadsheets()
        result = service.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE).execute()
        values = result.get("values", [])
        if not values:
            return []
        cab_val, prim_val, caixa_val = [x.strip().upper() for x in identificador.split("-")]
        portas_disponiveis = []
        for idx, row in enumerate(values):
            row += [""] * (11 - len(row))
            if (row[0].upper() == cab_val and row[1].upper() == prim_val 
                and row[2].upper() == caixa_val and row[8].upper() == "NÃO"):
                portas_disponiveis.append((idx + 2, row))
        return portas_disponiveis
    except HttpError as err:
        st.error(f"Erro ao buscar dados: {err}")
        return []

# --- Funções para atualização de portas ---
def sim_click(creds, linha, porta):
    atualizar_porta(creds, linha, porta)
    # Remove porta da lista local
    if 'portas' in st.session_state:
        st.session_state['portas'] = [p for p in st.session_state['portas'] if p[0] != linha]

def nao_click(linha, row):
    if 'portas' in st.session_state:
        st.session_state['portas'] = [p for p in st.session_state['portas'] if p[0] != linha]

def atualizar_porta(creds, linha, porta):
    try:
        service = build("sheets", "v4", credentials=creds).spreadsheets()
        data_atual = datetime.now().strftime("%d/%m/%Y")
        body = {"values": [["SIM", f"SIM, {data_atual}"]]}  # Colunas I e K
        service.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"CAIXAS!I{linha}:K{linha}",
            valueInputOption="USER_ENTERED",
            body=body
        ).execute()
        st.session_state['ultima_atualizacao'] = f"✅ Porta {porta} atualizada com sucesso!"
    except HttpError as err:
        st.error(f"❌ Erro ao atualizar a porta {porta} (linha {linha}): {err}")

# --- Streamlit ---
st.set_page_config(
    page_title="Verificador de Portas", layout="centered",
    page_icon="c64a4e55-0ce2-40c5-9392-fdc6f50f8b1aPNG.png"
    )
st.title("Verificador de Portas")

# Autenticação
if 'creds' not in st.session_state:
    st.session_state['creds'] = autenticar_google()
creds = st.session_state['creds']

# Entrada e busca
entrada = st.text_input("Digite o identificador (ex: CB07-SP06-CX15)").upper()
buscar = st.button("🔍 Buscar")

if buscar and entrada:
    st.session_state['portas'] = buscar_portas(creds, entrada)

if 'portas' in st.session_state:
    portas = st.session_state['portas']

    if not portas or len(portas) == 0:
        st.error(
            f"❌ Nenhuma Porta disponível encontrada para: \n{entrada}  \n"
            f"📞 Ligue para o TI para Atualizar a Caixa: (11) 94484-7040 ou Clique no Ícone do Whatsapp para ser redirecionado"
        )
        st.markdown(
            "<a href='https://wa.link/xcmibx' target='_blank'>"
            "<img src='https://logodownload.org/wp-content/uploads/2015/04/whatsapp-logo-2-1.png' width='40'></a>",
            unsafe_allow_html=True
        )
    else:
        st.success(f"🟢 Portas Disponíveis para: {entrada}")
        for linha, row in portas:
            # Campos verticais
            for label, valor in [("CABO", row[0]),
                                 ("PRIMARIA", row[1]),
                                 ("CAIXA", row[2]),
                                 ("PORTA", row[4]),
                                 ("CAPACIDADE", row[5]),
                                 ("INTERFACE", row[6])]:
                st.markdown(f"""
                <div class="div-campo">
                    <div class="label">{label}</div>
                    <div class="valor">{valor}</div>
                </div>
                """, unsafe_allow_html=True)

            # Botões centralizados
            st.markdown('<div class="label">ADICIONOU CLIENTE?</div>', unsafe_allow_html=True)
            col1, col2, col3 = st.columns([1,2,1])
            with col2:
                st.button("SIM", key=f"sim_{linha}", on_click=sim_click, args=(creds, linha, row[4]), use_container_width=True)
                st.button("NÃO", key=f"nao_{linha}", on_click=nao_click, args=(linha,row), use_container_width=True)
                st.markdown("<hr>", unsafe_allow_html=True)

# Mensagem de atualização
if 'ultima_atualizacao' in st.session_state:
    st.success(st.session_state['ultima_atualizacao'])
    del st.session_state['ultima_atualizacao']


