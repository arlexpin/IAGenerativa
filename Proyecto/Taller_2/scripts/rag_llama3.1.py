# Sistema RAG para EcoMarket usando Ollama + Llama 3.1 8B
# Carga políticas, inventario y FAQ de EcoMarket, crea un índice Chroma local y responde consultas.

import argparse
import csv
import json
import shutil
from pathlib import Path

from langchain.chains import RetrievalQA
from langchain.docstore.document import Document
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.llms import Ollama

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
PERSIST_DIR = BASE_DIR / "chroma_db"
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/distiluse-base-multilingual-cased-v2"

DEFAULT_PROMPT = """
Eres un asistente de atención al cliente de EcoMarket.
Responde SOLO con información encontrada en el contexto.
Si la respuesta no está en el contexto, responde exactamente:
"No tengo información suficiente. Un asesor humano te contactará."

Contexto:
{context}

Pregunta del cliente: {question}
Respuesta:
"""


def load_documents():
    documents = []

    politicas_path = DATA_DIR / "politicas_ecomarket.txt"
    if politicas_path.exists():
        text = politicas_path.read_text(encoding="utf-8").strip()
        if text:
            documents.append(Document(
                page_content=text,
                metadata={"source": "politicas_ecomarket.txt", "type": "politica"}
            ))

    faqs_path = DATA_DIR / "faqs.json"
    if faqs_path.exists():
        with faqs_path.open("r", encoding="utf-8") as f:
            faqs = json.load(f)
        for item in faqs:
            pregunta = item.get("pregunta", "")
            respuesta = item.get("respuesta", "")
            if pregunta and respuesta:
                text = f"Pregunta: {pregunta}\nRespuesta: {respuesta}"
                documents.append(Document(
                    page_content=text,
                    metadata={"source": "faqs.json", "type": "faq", "pregunta": pregunta}
                ))

    inventario_path = DATA_DIR / "inventario_productos.csv"
    if inventario_path.exists():
        with inventario_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                texto = (
                    f"ID: {row.get('id', '')}\n"
                    f"Nombre: {row.get('nombre', '')}\n"
                    f"Categoría: {row.get('categoria', '')}\n"
                    f"Precio: {row.get('precio', '')}\n"
                    f"Stock: {row.get('stock', '')}\n"
                    f"Atributo ecológico: {row.get('atributo_ecologico', '')}\n"
                    f"Descripción: {row.get('descripcion', '')}"
                )
                documents.append(Document(
                    page_content=texto,
                    metadata={"source": "inventario_productos.csv", "type": "producto", "id": row.get('id', '')}
                ))

    if not documents:
        raise FileNotFoundError(
            f"No se encontraron documentos en {DATA_DIR}."
        )

    return documents


def get_embeddings(model_name: str):
    if model_name is None or model_name.lower().startswith("ollama"):
        return OllamaEmbeddings(model="llama3.1:8b")

    if HuggingFaceEmbeddings is None:
        raise RuntimeError(
            "HuggingFaceEmbeddings no está disponible en este entorno. "
            "Instala sentence-transformers y langchain-community actualizado."
        )

    return HuggingFaceEmbeddings(model_name=model_name)


def build_vectorstore(documents, embedding_model: str):
    embeddings = get_embeddings(embedding_model)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=256,
        chunk_overlap=64,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    chunks = splitter.split_documents(documents)
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(PERSIST_DIR),
    )
    vectorstore.persist()
    return vectorstore


def load_vectorstore(embedding_model: str):
    embeddings = get_embeddings(embedding_model)
    return Chroma(
        persist_directory=str(PERSIST_DIR),
        embedding=embeddings,
    )


def make_qa_chain(vectorstore):
    llm = Ollama(model="llama3.1:8b", temperature=0.1)
    prompt = PromptTemplate(template=DEFAULT_PROMPT, input_variables=["context", "question"])
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": prompt},
        verbose=False,
    )


def ensure_vectorstore(rebuild=False, embedding_model: str = None):
    if rebuild and PERSIST_DIR.exists():
        print(f"Reconstruyendo índice: eliminando {PERSIST_DIR}")
        shutil.rmtree(PERSIST_DIR, ignore_errors=True)

    if not PERSIST_DIR.exists() or not any(PERSIST_DIR.iterdir()):
        print("Creando índice vectorial local con Chroma...")
        docs = load_documents()
        return build_vectorstore(docs, embedding_model)

    print("Cargando índice Chroma existente...")
    return load_vectorstore(embedding_model)


def run_interactive(chain):
    print("\n--- Sistema RAG de EcoMarket con Llama 3.1 8B ---")
    print("Escribe tu pregunta (o 'salir' para terminar).\n")
    while True:
        pregunta = input("Cliente: ")
        if pregunta.strip().lower() in {"salir", "exit", "quit"}:
            break
        print("Consultando base de conocimiento...")
        respuesta = chain.run(pregunta)
        print(f"EcoMarket: {respuesta}\n")


def main():
    parser = argparse.ArgumentParser(description="Sistema RAG local para EcoMarket")
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Reconstruir el índice vectorial desde los archivos de datos",
    )
    parser.add_argument(
        "--embedding-model",
        type=str,
        default=DEFAULT_EMBEDDING_MODEL,
        help="Modelo de embeddings Hugging Face o 'ollama' para OllamaEmbeddings",
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Realizar una sola pregunta y salir",
    )
    args = parser.parse_args()

    try:
        vectorstore = ensure_vectorstore(rebuild=args.rebuild, embedding_model=args.embedding_model)
    except Exception as exc:
        print(f"Error al preparar el vectorstore: {exc}")
        return

    qa_chain = make_qa_chain(vectorstore)

    if args.query:
        respuesta = qa_chain.run(args.query)
        print("Respuesta:")
        print(respuesta)
    else:
        run_interactive(qa_chain)


if __name__ == "__main__":
    main()
