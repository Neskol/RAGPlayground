import os
import bs4
from langchain import hub
from langchain_community.document_loaders import WebBaseLoader
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableSerializable
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain_ollama import OllamaLLM, OllamaEmbeddings

# llm = ChatOpenAI(model="gpt-4o")
llm = OllamaLLM(model="llama3.2")
os.environ["LANGSMITH_TRACING_V2"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"

log=open("result.txt","w+")

question="Can you specify how RAG paradigm improves the precision of LLM output?"
log.write(f"向GPT4o提问：{question}\n")
log.write("GPT4o输出：\n")
log.write(llm.invoke(question))
# log.write(llm.invoke(question).content)

# 以下内容为LangChain官网提供的一个简便RAG实例程序 https://python.langchain.com/v0.1/docs/use_cases/question_answering/quickstart/

# Load, chunk and index the contents of the blog.
loader = WebBaseLoader(
    web_paths=("https://lilianweng.github.io/posts/2023-06-23-agent/",),
    bs_kwargs=dict(
        parse_only=bs4.SoupStrainer(
            class_=("post-content", "post-title", "post-header")
        )
    ),
)
docs = loader.load()

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
splits = text_splitter.split_documents(docs)
vectorstore = Chroma.from_documents(documents=splits, embedding=OllamaEmbeddings(model="mxbai-embed-large")) # 向量化

# Retrieve and generate using the relevant snippets of the blog.
retriever = vectorstore.as_retriever()
prompt = hub.pull("rlm/rag-prompt")

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
)

# 对比生成内容差异
question="What is Task Decomposition?"
log.write(f"\nRAG Chain与直接询问GPT4o的比较： {question}\n")
log.write("RAG Chain输出：")
log.write(rag_chain.invoke(question))
log.write("\nGPT4o输出：\n")
# log.write(llm.invoke(question).content)
log.write(llm.invoke(question))

# 确认正常运行
question="What is AutoGPT in the context of your knowledge?"
log.write(f"\n对于其他问题，RAG Chain与直接询问GPT4o的比较： {question}\n")
log.write("\nRAG Chain输出：\n")
log.write(rag_chain.invoke(question))
log.write("\nGPT4o输出：\n")
# log.write(llm.invoke(question).content)
log.write(llm.invoke(question))
log.close()