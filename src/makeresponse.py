from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.config import OUTPUT_PATH
from dotenv import load_dotenv

load_dotenv()

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


### DB없으면 임베딩하는 함수 여기 넣기###


def load_db():
    text_embedding_model = OpenAIEmbeddings()
    db = Chroma(
        collection_name="saup_text",
        persist_directory= OUTPUT_PATH + "chromadb",
        embedding_function=text_embedding_model
    )
    return db

def make_response(db, query):
    retriever = db.as_retriever(
        search_type = "mmr",
        search_kwargs={"k": 10, "fetch_k": 30}      # 아 이거 힘드네...
    )
    docs = retriever.invoke(query)
        
    template ="""
    주어진 context 안에서만 대답하고, 절대 임의로 답변을 생성하지 마세요.
    {context}
    Ancestors가 다른 문서가 있으면 Ancestors 별로 구분해서 답변해 주세요.
    
    Question : {question}
    """

    prompt = ChatPromptTemplate.from_template(template)

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.1,
        max_tokens=500
    )

    chain = prompt | llm | StrOutputParser()

    response = chain.invoke({"context":(format_docs(docs)), "question":query})
    
    return response