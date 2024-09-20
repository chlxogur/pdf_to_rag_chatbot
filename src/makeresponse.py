from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.config import OUTPUT_PATH
from dotenv import load_dotenv

load_dotenv()

def format_docs(docs):
    return "\n\n".join("\n".join([str(doc.metadata), doc.page_content]) for doc in docs)


### DB없으면 임베딩하는 함수 여기 넣기###


def load_db():
    text_embedding_model = OpenAIEmbeddings()
    db = Chroma(
        collection_name="saup_markdown",
        persist_directory= "data/output/" + "chromadb",
        #persist_directory= OUTPUT_PATH + "chromadb",
        embedding_function=text_embedding_model
    )
    return db

def make_response(db, query):
    retriever = db.as_retriever(
        search_type = "similarity_score_threshold",
        search_kwargs={"k": 20,
                       "score_threshold":0.8}      # 아 이거 힘드네...
    )
    docs = retriever.invoke(query)
        
    template ="""
    주어진 context 안에서만 대답하고, 절대 임의로 답변을 생성하지 마세요.
    {context}
    Header는 1이 가장 최상위, 숫자가 커질수록 하위 분류입니다. 최하위 분류가 Title입니다.
    Title과 Company가 같고 Header가 다른 데이터가 있으면 별개의 데이터처럼 취급해 주세요. 답변할 때는 Header의 차이점을 명시해 주세요.
    metadata의 Company가 회사명과 일치하지 않으면 임의로 답변을 생성하지 마세요.
    
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