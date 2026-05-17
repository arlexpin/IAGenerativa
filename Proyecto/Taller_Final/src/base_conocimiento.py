import os
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, CSVLoader, JSONLoader
from langchain.schema import Document
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "datos")

def cargar_documentos():
    documentos = []
    # Políticas
    with open(os.path.join(DATA_DIR, "politicas_ecomarket.txt"), "r", encoding="utf-8") as f:
        texto = f.read()
        documentos.append(Document(page_content=texto, metadata={"fuente": "politicas.txt"}))
    # FAQs
    with open(os.path.join(DATA_DIR, "faqs.json"), "r", encoding="utf-8") as f:
        faqs = json.load(f)
        for item in faqs:
            texto = f"Pregunta: {item['pregunta']} Respuesta: {item['respuesta']}"
            documentos.append(Document(page_content=texto, metadata={"fuente": "faqs.json"}))
    # Inventario (como texto plano para RAG)
    import csv
    with open(os.path.join(DATA_DIR, "inventario_productos.csv"), "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            texto = f"Producto {row['id']}: {row['nombre']}, categoría {row['categoria']}, stock {row['stock']}, precio ${row['precio']}, {row['descripcion']}"
            documentos.append(Document(page_content=texto, metadata={"fuente": "inventario.csv", "id": row['id']}))
    return documentos

def crear_vectorstore():
    docs = cargar_documentos()
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    chunks = splitter.split_documents(docs)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/distiluse-base-multilingual-cased-v2")
    vectorstore = Chroma.from_documents(chunks, embeddings, persist_directory="./chroma_db")
    vectorstore.persist()
    return vectorstore

def obtener_retriever():
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/distiluse-base-multilingual-cased-v2")
    vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
    return vectorstore.as_retriever(search_kwargs={"k": 3})