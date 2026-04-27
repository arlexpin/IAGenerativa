# Sistema RAG para EcoMarket usando Ollama + Llama 3.1 8B
# Basado en el ejemplo de LangChain, adaptado al modelo del taller

import os
from langchain_community.llms import Ollama
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# ------------------------------------------------------------
# Configuración de rutas (asumiendo que se ejecuta desde /scripts)
# ------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOC_PATH = os.path.join(BASE_DIR, "data", "politicas_ecomarket.txt")

# ------------------------------------------------------------
# 1. Cargar base de conocimiento desde archivo .txt
# ------------------------------------------------------------
try:
    with open(DOC_PATH, "r", encoding="utf-8") as f:
        documento_empresa = f.read()
    print(f"Documento cargado desde {DOC_PATH}")
except FileNotFoundError:
    print(f"No se encontró el archivo en {DOC_PATH}. Usando documento por defecto.")
    documento_empresa = """
    Política de Devoluciones de EcoMarket:
    Permite devoluciones hasta 30 días, productos sin usar y en empaque original.
    No se aceptan perecederos ni productos de higiene personal usados.
    """

# ------------------------------------------------------------
# 2. Configurar modelos (Llama 3.1 8B)
# ------------------------------------------------------------
try:
    embeddings = OllamaEmbeddings(model="llama3.1:8b")
    llm = Ollama(model="llama3.1:8b", temperature=0.1)
    print("Modelos Ollama inicializados correctamente.")
except Exception as e:
    print(f"Error al conectar con Ollama: {e}")
    print("Asegúrate de que Ollama esté corriendo y el modelo 'llama3.1:8b' esté descargado.")
    exit()

# ------------------------------------------------------------
# 3. Dividir documento en fragmentos (chunks)
# ------------------------------------------------------------
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100,
    separators=["\n\n", "\n", ".", " ", ""]
)
docs = text_splitter.create_documents([documento_empresa])
print(f"Documento dividido en {len(docs)} fragmentos.")

# ------------------------------------------------------------
# 4. Crear base de datos vectorial (Chroma en memoria)
# ------------------------------------------------------------
vectorstore = Chroma.from_documents(documents=docs, embedding=embeddings)
print("Base vectorial creada (en memoria).")

# ------------------------------------------------------------
# 5. Crear prompt personalizado para reducir alucinaciones
# ------------------------------------------------------------
template = """
Eres un agente de atención al cliente de EcoMarket. Responde ÚNICAMENTE basado en el siguiente contexto. 
Si la respuesta no está en el contexto, di: "No tengo información suficiente. Un asesor humano te contactará."

Contexto:
{context}

Pregunta del cliente: {question}
Respuesta:
"""
prompt = PromptTemplate(template=template, input_variables=["context", "question"])

# ------------------------------------------------------------
# 6. Construir cadena RAG
# ------------------------------------------------------------
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever,
    chain_type_kwargs={"prompt": prompt},
    verbose=False
)

# ------------------------------------------------------------
# 7. Bucle interactivo
# ------------------------------------------------------------
print("\n--- Sistema RAG de EcoMarket con Llama 3.1 8B ---")
print("Escribe tu pregunta (o 'salir' para terminar).\n")

while True:
    pregunta = input("Cliente: ")
    if pregunta.lower() in ["salir", "exit"]:
        break
    print("Consultando base de conocimiento...")
    respuesta = qa_chain.run(pregunta)
    print(f"EcoMarket: {respuesta}\n")