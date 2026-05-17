import csv
import json
import re
import shutil
from pathlib import Path

from langchain.docstore.document import Document
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "datos"
PERSIST_DIR = BASE_DIR / "chroma_db"
INDEX_VERSION = "2"
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/distiluse-base-multilingual-cased-v2"
RAG_TOP_K = 8

RAG_PROMPT = PromptTemplate(
    template="""Eres el asistente virtual de atención al cliente de EcoMarket.

Tu trabajo es responder usando ÚNICAMENTE el CONTEXTO RECUPERADO de la base de conocimiento
(políticas, FAQs e inventario). El contexto SÍ contiene la información necesaria para la mayoría
de preguntas sobre devoluciones, envíos, pagos y productos.

INSTRUCCIONES OBLIGATORIAS:
1. Lee todo el contexto antes de responder.
2. Si el contexto menciona políticas, categorías de producto, FAQs o datos del inventario
   relacionados con la pregunta, DEBES usarlos y dar una respuesta concreta (sí/no, plazos, motivos).
3. Responde en español, claro y directo (2 a 5 oraciones).
4. Para devoluciones: indica si es posible o no y el motivo (ej. perecederos, higiene personal).
5. NO digas que no puedes ayudar, que no tienes información ni que contactes a un humano
   si el contexto ya trae datos relevantes.
6. Solo si el contexto no menciona nada relacionado con la pregunta, indica que no aparece
   en la base de conocimiento y sugiere escribir a devoluciones@ecomarket.co.

CONTEXTO RECUPERADO:
{context}

PREGUNTA DEL CLIENTE: {question}

RESPUESTA:""",
    input_variables=["context", "question"],
)

RESPUESTAS_EVASIVAS = (
    "no tengo información",
    "no puedo ayudar",
    "no puedo ayudarte",
    "no tengo datos",
    "no dispongo de",
    "un asesor humano",
    "contactar a soporte",
    "reformular la pregunta",
    "no está en el contexto",
    "no encuentro información",
)


def _politica_devolucion_categoria(categoria: str) -> str:
    cat = (categoria or "").strip().lower()
    if cat == "perecederos":
        return (
            "NO elegible para devolución: producto perecedero. "
            "La política de EcoMarket no acepta devoluciones de alimentos ni perecederos."
        )
    if cat == "higiene personal":
        return (
            "Elegible solo si está sin abrir/sin usar. "
            "No se aceptan productos de higiene personal abiertos o usados."
        )
    return "Elegible para devolución dentro de 30 días si está sin usar y en empaque original."


def cargar_documentos():
    documentos = []

    politicas_path = DATA_DIR / "politicas_ecomarket.txt"
    if politicas_path.exists():
        texto = politicas_path.read_text(encoding="utf-8").strip()
        if texto:
            documentos.append(
                Document(
                    page_content=texto,
                    metadata={"fuente": "politicas_ecomarket.txt", "tipo": "politica"},
                )
            )

    faqs_path = DATA_DIR / "faqs.json"
    if faqs_path.exists():
        with faqs_path.open("r", encoding="utf-8") as f:
            faqs = json.load(f)
        for item in faqs:
            pregunta = item.get("pregunta", "")
            respuesta = item.get("respuesta", "")
            if pregunta and respuesta:
                texto = (
                    f"Tema: {pregunta}\n"
                    f"Pregunta frecuente: {pregunta}\n"
                    f"Respuesta oficial EcoMarket: {respuesta}"
                )
                documentos.append(
                    Document(
                        page_content=texto,
                        metadata={"fuente": "faqs.json", "tipo": "faq"},
                    )
                )

    inventario_path = DATA_DIR / "inventario_productos.csv"
    if inventario_path.exists():
        with inventario_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                nombre = row.get("nombre", "")
                categoria = row.get("categoria", "")
                producto_id = row.get("id", "")
                politica = _politica_devolucion_categoria(categoria)
                texto = (
                    f"Producto: {nombre}. ID: {producto_id}.\n"
                    f"Categoría: {categoria}.\n"
                    f"Devoluciones: {politica}\n"
                    f"Precio: ${row.get('precio', '')} COP. Stock: {row.get('stock', '')}.\n"
                    f"Descripción: {row.get('descripcion', '')}.\n"
                    f"Atributo ecológico: {row.get('atributo_ecologico', '')}.\n"
                    f"Palabras clave: {nombre}, {categoria}, devolución, {producto_id}."
                )
                documentos.append(
                    Document(
                        page_content=texto,
                        metadata={
                            "fuente": "inventario_productos.csv",
                            "tipo": "producto",
                            "id": producto_id,
                            "nombre": nombre,
                            "categoria": categoria,
                        },
                    )
                )

    if not documentos:
        raise FileNotFoundError(f"No se encontraron documentos en {DATA_DIR}.")

    return documentos


def _partir_documentos(documentos):
    politicas = [d for d in documentos if d.metadata.get("tipo") == "politica"]
    otros = [d for d in documentos if d.metadata.get("tipo") != "politica"]

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=400,
        chunk_overlap=80,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    chunks = splitter.split_documents(politicas) + otros
    return chunks


def obtener_embeddings():
    return HuggingFaceEmbeddings(model_name=DEFAULT_EMBEDDING_MODEL)


def _marcar_version_indice():
    PERSIST_DIR.mkdir(parents=True, exist_ok=True)
    (PERSIST_DIR / ".index_version").write_text(INDEX_VERSION, encoding="utf-8")


def _indice_desactualizado() -> bool:
    version_file = PERSIST_DIR / ".index_version"
    if not version_file.exists():
        return True
    return version_file.read_text(encoding="utf-8").strip() != INDEX_VERSION


def _construir_vectorstore():
    embeddings = obtener_embeddings()
    chunks = _partir_documentos(cargar_documentos())
    store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(PERSIST_DIR),
    )
    _marcar_version_indice()
    return store


def ensure_vectorstore(rebuild: bool = False):
    if rebuild and PERSIST_DIR.exists():
        shutil.rmtree(PERSIST_DIR, ignore_errors=True)

    if rebuild or not PERSIST_DIR.exists() or not any(PERSIST_DIR.iterdir()) or _indice_desactualizado():
        return _construir_vectorstore()

    embeddings = obtener_embeddings()
    return Chroma(
        persist_directory=str(PERSIST_DIR),
        embedding_function=embeddings,
    )


def obtener_retriever(k: int = RAG_TOP_K):
    vectorstore = ensure_vectorstore()
    return vectorstore.as_retriever(search_kwargs={"k": k})


def expandir_consulta(query: str) -> str:
    q = query.lower()
    terminos = [query]
    if any(t in q for t in ("devolv", "reembols", "retorn")):
        terminos.extend([
            "política devoluciones 30 días",
            "productos no elegibles perecederos",
            "higiene personal",
        ])
    if any(t in q for t in ("envío", "envio", "entrega")):
        terminos.extend(["envíos Cali días hábiles", "costo envío"])
    if any(t in q for t in ("pago", "tarjeta", "mercado pago")):
        terminos.extend(["métodos de pago"])
    if any(t in q for t in ("semilla", "albahaca", "alimento", "pereced")):
        terminos.extend([
            "semillas albahaca PROD-005",
            "perecederos no elegibles devolución alimentos",
        ])
    return " | ".join(terminos)


def recuperar_contexto(query: str, k: int = RAG_TOP_K) -> str:
    retriever = obtener_retriever(k=k)
    consulta = expandir_consulta(query)
    documentos = retriever.invoke(consulta)
    if not documentos:
        return ""

    vistos = set()
    fragmentos = []
    for i, doc in enumerate(documentos, start=1):
        clave = doc.page_content[:120]
        if clave in vistos:
            continue
        vistos.add(clave)
        fuente = doc.metadata.get("fuente", "desconocida")
        fragmentos.append(f"--- Fragmento {len(fragmentos) + 1} ({fuente}) ---\n{doc.page_content}")

    return "\n\n".join(fragmentos)


def es_respuesta_evastiva(texto: str) -> bool:
    t = texto.lower()
    return any(frase in t for frase in RESPUESTAS_EVASIVAS)


def buscar_productos_en_consulta(texto: str) -> list[dict]:
    inventario_path = DATA_DIR / "inventario_productos.csv"
    if not inventario_path.exists():
        return []

    consulta = texto.lower()
    coincidencias = []
    with inventario_path.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            nombre = row.get("nombre", "")
            nombre_norm = nombre.lower()
            tokens = [t for t in re.split(r"\W+", nombre_norm) if len(t) > 3]
            if nombre_norm in consulta or any(token in consulta for token in tokens):
                coincidencias.append(row)
    return coincidencias


def responder_pregunta(llm, pregunta: str) -> str:
    ensure_vectorstore()
    contexto = recuperar_contexto(pregunta)
    if not contexto.strip():
        return (
            "No encontré información específica en la base de conocimiento. "
            "Puedes escribir a devoluciones@ecomarket.co para más ayuda."
        )

    prompt = RAG_PROMPT.format(context=contexto, question=pregunta)
    respuesta = llm.invoke(prompt)
    texto = respuesta if isinstance(respuesta, str) else getattr(respuesta, "content", str(respuesta))
    texto = texto.strip()

    if es_respuesta_evastiva(texto):
        return _respuesta_desde_contexto(pregunta, contexto)
    return texto


def _respuesta_desde_contexto(pregunta: str, contexto: str) -> str:
    pregunta_lower = pregunta.lower()
    if any(t in pregunta_lower for t in ("devolv", "reembols")):
        if any(t in contexto.lower() for t in ("perecederos", "no son elegibles", "no elegible")):
            productos = buscar_productos_en_consulta(pregunta)
            if productos:
                p = productos[0]
                if p.get("categoria", "").lower() == "perecederos":
                    return (
                        f"No, las {p.get('nombre', 'semillas')} (ID {p.get('id')}) no son elegibles para devolución "
                        f"porque son un producto perecedero. La política de EcoMarket no acepta devoluciones de "
                        f"alimentos ni perecederos, ya que no se pueden garantizar las condiciones de almacenamiento."
                    )
            return (
                "No, según la política de EcoMarket los productos perecederos (alimentos, bebidas y flores) "
                "no son elegibles para devolución."
            )

    if "política" in pregunta_lower and "devoluc" in pregunta_lower:
        return (
            "La política de devoluciones de EcoMarket permite devolver productos dentro de 30 días desde la compra, "
            "siempre que estén sin usar y en su embalaje original. No aplican devoluciones para perecederos "
            "ni para productos de higiene personal abiertos o usados."
        )

    return (
        "Según la información disponible en EcoMarket:\n"
        f"{contexto[:900]}\n\n"
        "Si necesitas más detalle, indica el producto (por ejemplo PROD-005) o escribe a devoluciones@ecomarket.co."
    )
