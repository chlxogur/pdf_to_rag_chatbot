from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

def format_docs(docs):
    return "\n\n".join("\n".join([str(doc.metadata), doc.page_content]) for doc in docs)

def make_response(db, query):
    retriever = db.as_retriever(
        search_type = "similarity_score_threshold",
        search_kwargs={"k": 15,
                       "score_threshold":0.75}      # 아 이거 힘드네...
    )
    docs = retriever.invoke(query)
        
    template ="""
    주어진 context 안에서만 대답하고, 절대 임의로 답변을 생성하지 마세요.
    {context}
    Header는 1이 가장 최상위, 숫자가 커질수록 하위 분류입니다. 최하위 분류가 Title입니다.
    Title과 Company가 같고 Header가 다른 데이터가 있으면 별개의 데이터처럼 취급해 주세요. 답변할 때는 Header의 차이점을 명시해 주세요.
    metadata의 Company가 회사명과 일치하지 않으면 임의로 답변을 생성하지 마세요.
    기본 단위는 "백만원" 이므로 단위를 붙여서 출력해주세요. 그러나 (단위 : 원) 이 붙은 Title에 대해서는 "원" 단위를 붙여서 회계양식으로 출력해주되, 절대 주어진 context 외에서 임의로 답변을 생성하지 마세요.
    
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