import html
import io
import time
from typing import Iterable, Optional

import pandas as pd
import requests
import streamlit as st


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="Predicción de Arriendos Medellín",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

REQUIRED_COLUMNS = [
    "metros_cuadrados",
    "habitaciones",
    "banos",
    "estrato",
]


# ============================================================
# CONFIGURACIÓN DATAROBOT DESDE STREAMLIT SECRETS
# ============================================================

def get_secret(name: str, default: Optional[str] = None) -> Optional[str]:
    """Obtiene un secreto sin mostrarlo en la interfaz."""
    try:
        value = st.secrets[name]
        return str(value).strip()
    except (KeyError, FileNotFoundError):
        return default


DATAROBOT_API_KEY = get_secret("DATAROBOT_API_KEY")
DATAROBOT_DEPLOYMENT_ID = get_secret("DATAROBOT_DEPLOYMENT_ID")
DATAROBOT_HOST = (
    get_secret("DATAROBOT_HOST", "https://app.datarobot.com")
    or "https://app.datarobot.com"
).rstrip("/")


# ============================================================
# ESTILOS VISUALES
# ============================================================

st.markdown(
    """
    <style>
        :root {
            --primary: #6366f1;
            --secondary: #8b5cf6;
            --accent: #ec4899;
            --success: #14b8a6;
            --text: #f8fafc;
            --muted: #cbd5e1;
        }

        .stApp {
            background:
                radial-gradient(circle at 85% 10%, rgba(99, 102, 241, 0.22), transparent 30%),
                radial-gradient(circle at 15% 90%, rgba(236, 72, 153, 0.12), transparent 28%),
                linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #312e81 100%);
            color: var(--text);
        }

        .block-container {
            max-width: 1450px;
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }

        [data-testid="stSidebar"] {
            background: rgba(15, 23, 42, 0.96);
            border-right: 1px solid rgba(255, 255, 255, 0.10);
        }

        [data-testid="stSidebar"] * {
            color: #f8fafc;
        }

        .title-card {
            background: linear-gradient(120deg, #4f46e5, #7c3aed, #db2777);
            padding: 2.2rem 1.5rem;
            border-radius: 26px;
            color: white;
            text-align: center;
            box-shadow: 0 18px 55px rgba(0, 0, 0, 0.34);
            margin-bottom: 1.7rem;
            border: 1px solid rgba(255, 255, 255, 0.16);
        }

        .title-card h1 {
            font-size: clamp(2rem, 4vw, 3.3rem);
            margin: 0 0 0.4rem 0;
            line-height: 1.1;
        }

        .title-card p {
            font-size: 1.08rem;
            opacity: 0.94;
            margin: 0;
        }

        .section-card {
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.13);
            border-left: 5px solid #38bdf8;
            padding: 1.15rem 1.3rem;
            border-radius: 18px;
            color: white;
            margin: 0.6rem 0 1.2rem 0;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.16);
            backdrop-filter: blur(10px);
        }

        .section-card h3 {
            margin: 0 0 0.25rem 0;
        }

        .section-card p {
            margin: 0;
            color: #dbeafe;
        }

        .metric-card {
            background: linear-gradient(
                145deg,
                rgba(255, 255, 255, 0.10),
                rgba(255, 255, 255, 0.055)
            );
            padding: 1.25rem 0.75rem;
            border-radius: 22px;
            border: 1px solid rgba(255, 255, 255, 0.14);
            color: white;
            text-align: center;
            box-shadow: 0 10px 28px rgba(0, 0, 0, 0.22);
            min-height: 165px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            transition: transform 0.2s ease, border-color 0.2s ease;
        }

        .metric-card:hover {
            transform: translateY(-3px);
            border-color: rgba(129, 140, 248, 0.55);
        }

        .metric-card .icon {
            font-size: 2rem;
            margin-bottom: 0.45rem;
        }

        .metric-card .value {
            font-size: 1.9rem;
            font-weight: 800;
            margin-bottom: 0.35rem;
        }

        .metric-card .label {
            color: #e2e8f0;
            font-size: 1rem;
            font-weight: 600;
        }

        .prediction-card {
            background: linear-gradient(135deg, #16a34a, #0d9488);
            padding: 2.2rem 1.2rem;
            border-radius: 25px;
            color: white;
            text-align: center;
            box-shadow: 0 15px 42px rgba(0, 0, 0, 0.34);
            margin-top: 1.4rem;
            border: 1px solid rgba(255, 255, 255, 0.20);
        }

        .prediction-card h2 {
            margin: 0;
            font-size: 1.45rem;
        }

        .prediction-card h1 {
            margin: 0.55rem 0;
            font-size: clamp(2.2rem, 5vw, 4rem);
        }

        .prediction-card p {
            margin: 0;
            opacity: 0.9;
        }

        .error-card {
            background: linear-gradient(135deg, #dc2626, #ea580c);
            padding: 1.45rem;
            border-radius: 18px;
            color: white;
            margin-top: 1rem;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
        }

        div.stButton > button {
            width: 100%;
            min-height: 3.4rem;
            border-radius: 15px;
            font-size: 1.08rem;
            font-weight: 750;
            background: linear-gradient(135deg, #6366f1, #db2777);
            color: white;
            border: none;
            box-shadow: 0 7px 22px rgba(0, 0, 0, 0.26);
            transition: transform 0.18s ease, filter 0.18s ease;
        }

        div.stButton > button:hover {
            color: white;
            transform: translateY(-2px);
            filter: brightness(1.08);
        }

        div[data-testid="stDataFrame"] {
            border-radius: 16px;
            overflow: hidden;
        }

        .small-note {
            color: #cbd5e1;
            font-size: 0.91rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def formato_cop(valor: object) -> str:
    """Convierte un valor numérico a pesos colombianos."""
    try:
        numero = float(valor)
        return f"${numero:,.0f}".replace(",", ".") + " COP"
    except (TypeError, ValueError):
        return str(valor)


def validar_configuracion() -> list[str]:
    """Retorna la lista de secretos faltantes."""
    faltantes = []

    if not DATAROBOT_API_KEY:
        faltantes.append("DATAROBOT_API_KEY")

    if not DATAROBOT_DEPLOYMENT_ID:
        faltantes.append("DATAROBOT_DEPLOYMENT_ID")

    if not DATAROBOT_HOST:
        faltantes.append("DATAROBOT_HOST")

    return faltantes


def detectar_columna_prediccion(
    resultado: pd.DataFrame,
    columnas_entrada: Iterable[str],
) -> Optional[str]:
    """
    Detecta la columna numérica de predicción generada por DataRobot.
    Prioriza nombres estándar de regresión y descarta columnas auxiliares.
    """
    columnas_entrada = set(columnas_entrada)
    columnas = list(resultado.columns)

    nombres_prioritarios = [
        "precio_arriendo_PREDICTION",
        "precio_arriendo_prediction",
        "prediction",
        "PREDICTION",
    ]

    for nombre in nombres_prioritarios:
        if nombre in columnas:
            return nombre

    candidatas = [
        columna
        for columna in columnas
        if columna not in columnas_entrada
        and "status" not in columna.lower()
        and "threshold" not in columna.lower()
        and "class" not in columna.lower()
        and (
            "prediction" in columna.lower()
            or "predicted" in columna.lower()
        )
    ]

    for columna in candidatas:
        if pd.to_numeric(resultado[columna], errors="coerce").notna().any():
            return columna

    # Último recurso: buscar una columna numérica nueva.
    for columna in columnas:
        if columna in columnas_entrada:
            continue
        if "status" in columna.lower():
            continue

        serie_numerica = pd.to_numeric(resultado[columna], errors="coerce")
        if serie_numerica.notna().any():
            return columna

    return None


def _request(
    method: str,
    url: str,
    *,
    headers: dict,
    timeout: int = 60,
    **kwargs,
) -> requests.Response:
    """Ejecuta una petición HTTP y genera mensajes de error legibles."""
    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            timeout=timeout,
            **kwargs,
        )
    except requests.RequestException as exc:
        raise RuntimeError(
            f"No fue posible comunicarse con DataRobot: {exc}"
        ) from exc

    if response.status_code >= 400:
        detalle = response.text.strip()
        if len(detalle) > 1200:
            detalle = detalle[:1200] + "..."

        raise RuntimeError(
            f"DataRobot respondió con HTTP {response.status_code}: {detalle}"
        )

    return response


def hacer_prediccion_batch(df_input: pd.DataFrame) -> pd.DataFrame:
    """
    Envía un DataFrame a DataRobot mediante Batch Predictions API.

    Flujo:
    1. Crea el job.
    2. Sube el CSV.
    3. Consulta el estado.
    4. Descarga el resultado.
    """
    faltantes = validar_configuracion()
    if faltantes:
        raise RuntimeError(
            "Faltan secretos en Streamlit: " + ", ".join(faltantes)
        )

    batch_url = f"{DATAROBOT_HOST}/api/v2/batchPredictions/"
    auth_headers = {
        "Authorization": f"Token {DATAROBOT_API_KEY}",
        "User-Agent": "Streamlit-Arriendos-Medellin/1.0",
    }

    payload = {
        "deploymentId": DATAROBOT_DEPLOYMENT_ID,
        "passthroughColumnsSet": "all",
        "includePredictionStatus": True,
    }

    create_response = _request(
        "POST",
        batch_url,
        headers={
            **auth_headers,
            "Content-Type": "application/json; encoding=utf-8",
        },
        json=payload,
        timeout=60,
    )

    job = create_response.json()
    links = job.get("links", {})

    upload_url = links.get("csvUpload")
    job_url = links.get("self")

    if not upload_url or not job_url:
        raise RuntimeError(
            "DataRobot creó el job, pero no devolvió los enlaces esperados."
        )

    csv_bytes = df_input.to_csv(index=False).encode("utf-8")

    _request(
        "PUT",
        upload_url,
        headers={
            **auth_headers,
            "Content-Type": "text/csv; encoding=utf-8",
            "Content-Length": str(len(csv_bytes)),
        },
        data=csv_bytes,
        timeout=120,
    )

    progress_bar = st.progress(0)
    status_text = st.empty()

    started_at = time.time()
    max_wait_seconds = 600
    job_data = job

    while True:
        status_response = _request(
            "GET",
            job_url,
            headers=auth_headers,
            timeout=60,
        )

        job_data = status_response.json()
        status = str(job_data.get("status", "")).upper()

        try:
            porcentaje = int(float(job_data.get("percentageCompleted", 0)))
        except (TypeError, ValueError):
            porcentaje = 0

        porcentaje = max(0, min(porcentaje, 100))
        progress_bar.progress(porcentaje)
        status_text.info(
            f"⏳ Estado del modelo: {status or 'INICIALIZANDO'} · {porcentaje}%"
        )

        if status == "COMPLETED":
            break

        if status in {"FAILED", "ABORTED"}:
            detalles = job_data.get("statusDetails") or job_data.get("logs") or ""
            raise RuntimeError(
                f"El job terminó con estado {status}. {detalles}"
            )

        if time.time() - started_at > max_wait_seconds:
            raise TimeoutError(
                "La predicción superó el tiempo máximo de espera de 10 minutos."
            )

        time.sleep(2)

    download_url = job_data.get("links", {}).get("download")
    if not download_url:
        raise RuntimeError(
            "La predicción terminó, pero DataRobot no entregó el enlace de descarga."
        )

    download_response = _request(
        "GET",
        download_url,
        headers=auth_headers,
        timeout=120,
    )

    try:
        result_df = pd.read_csv(io.BytesIO(download_response.content))
    except Exception as exc:
        raise RuntimeError(
            "No fue posible interpretar el resultado CSV enviado por DataRobot."
        ) from exc

    progress_bar.progress(100)
    status_text.success("✅ Predicción completada correctamente")

    return result_df


# ============================================================
# ENCABEZADO
# ============================================================

st.markdown(
    """
    <div class="title-card">
        <h1>🏠 Predicción Inteligente de Arriendos</h1>
        <p>
            Estimación del precio mensual de un inmueble en Medellín mediante
            un modelo desplegado en DataRobot.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.header("⚙️ Panel de control")
    st.write(
        "Configura las características del inmueble y ejecuta la predicción."
    )

    modo_demo = st.toggle(
        "🧪 Activar modo demo",
        value=False,
        help="Permite probar la interfaz sin realizar solicitudes a DataRobot.",
    )

    st.divider()

    st.subheader("📌 Variables de entrada")
    st.write("📐 `metros_cuadrados`")
    st.write("🛏️ `habitaciones`")
    st.write("🚿 `banos`")
    st.write("🏙️ `estrato`")

    st.divider()

    st.subheader("🎯 Variable objetivo")
    st.write("💰 `precio_arriendo`")
    st.caption(
        "La variable objetivo no se envía al modelo porque es el valor que se desea estimar."
    )

    st.divider()

    secretos_faltantes = validar_configuracion()
    if secretos_faltantes and not modo_demo:
        st.warning(
            "Faltan secretos: " + ", ".join(secretos_faltantes)
        )
    elif not modo_demo:
        st.success("Configuración de DataRobot detectada")


# ============================================================
# FORMULARIO DE ENTRADA
# ============================================================

st.markdown(
    """
    <div class="section-card">
        <h3>🏡 Datos del inmueble</h3>
        <p>
            Ingresa las características de la vivienda. El modelo estimará
            el precio mensual de arriendo.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.form("formulario_prediccion", clear_on_submit=False):
    col1, col2 = st.columns(2, gap="large")

    with col1:
        metros_cuadrados = st.slider(
            "📐 Metros cuadrados",
            min_value=20,
            max_value=350,
            value=70,
            step=1,
            help="Área construida aproximada del inmueble.",
        )

        habitaciones = st.number_input(
            "🛏️ Habitaciones",
            min_value=1,
            max_value=7,
            value=2,
            step=1,
            help="Cantidad de habitaciones del inmueble.",
        )

    with col2:
        banos = st.number_input(
            "🚿 Baños",
            min_value=1,
            max_value=5,
            value=1,
            step=1,
            help="Cantidad de baños del inmueble.",
        )

        estrato = st.select_slider(
            "🏙️ Estrato",
            options=[1, 2, 3, 4, 5, 6],
            value=3,
            help="Estrato socioeconómico del inmueble.",
        )

    st.write("")
    calcular = st.form_submit_button(
        "🚀 Predecir precio de arriendo",
        use_container_width=True,
    )


# ============================================================
# RESUMEN VISUAL
# ============================================================

st.subheader("📊 Resumen de entrada")

resumen_col1, resumen_col2, resumen_col3, resumen_col4 = st.columns(4)

metricas = [
    (resumen_col1, "📐", metros_cuadrados, "Metros cuadrados"),
    (resumen_col2, "🛏️", habitaciones, "Habitaciones"),
    (resumen_col3, "🚿", banos, "Baños"),
    (resumen_col4, "🏙️", estrato, "Estrato"),
]

for columna, icono, valor, etiqueta in metricas:
    with columna:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="icon">{icono}</div>
                <div class="value">{valor}</div>
                <div class="label">{etiqueta}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# DATAFRAME ENVIADO AL MODELO
# ============================================================

input_data = pd.DataFrame(
    [
        {
            "metros_cuadrados": float(metros_cuadrados),
            "habitaciones": int(habitaciones),
            "banos": int(banos),
            "estrato": int(estrato),
        }
    ],
    columns=REQUIRED_COLUMNS,
)

with st.expander("🧾 Ver datos enviados al modelo", expanded=False):
    st.dataframe(
        input_data,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# EJECUCIÓN
# ============================================================

if calcular:
    if modo_demo:
        prediccion_demo = (
            280_000
            + metros_cuadrados * 10_500
            + habitaciones * 85_000
            + banos * 145_000
            + estrato * 210_000
            + (estrato**2) * 28_000
        )

        st.markdown(
            f"""
            <div class="prediction-card">
                <h2>🧪 Precio estimado en modo demo</h2>
                <h1>{formato_cop(prediccion_demo)}</h1>
                <p>Valor simulado localmente; no corresponde a una respuesta de DataRobot.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    else:
        try:
            with st.spinner("🤖 Enviando información a DataRobot..."):
                resultado = hacer_prediccion_batch(input_data)

            columna_prediccion = detectar_columna_prediccion(
                resultado,
                REQUIRED_COLUMNS,
            )

            if columna_prediccion is None:
                st.warning(
                    "La respuesta llegó correctamente, pero no se detectó "
                    "automáticamente la columna de predicción."
                )
            else:
                valor_predicho = pd.to_numeric(
                    resultado[columna_prediccion],
                    errors="coerce",
                ).iloc[0]

                if pd.isna(valor_predicho):
                    raise RuntimeError(
                        f"La columna '{columna_prediccion}' no contiene una predicción numérica."
                    )

                st.markdown(
                    f"""
                    <div class="prediction-card">
                        <h2>🎯 Precio de arriendo estimado</h2>
                        <h1>{formato_cop(valor_predicho)}</h1>
                        <p>Resultado generado por el deployment configurado en DataRobot.</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with st.expander("📌 Ver respuesta completa de DataRobot"):
                st.dataframe(
                    resultado,
                    use_container_width=True,
                    hide_index=True,
                )

                csv_resultado = resultado.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    "⬇️ Descargar resultado CSV",
                    data=csv_resultado,
                    file_name="prediccion_arriendo.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

        except Exception as exc:
            mensaje = html.escape(str(exc))
            st.markdown(
                f"""
                <div class="error-card">
                    <h3>❌ Error al realizar la predicción</h3>
                    <p>{mensaje}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ============================================================
# PIE DE PÁGINA
# ============================================================

st.markdown("---")
st.caption(
    "Aplicación desarrollada con Streamlit y DataRobot · "
    "Variable objetivo: precio_arriendo"
)
