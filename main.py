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

# model_name = "gpt-4o"
model_name = "llama3.2"

llm = OllamaLLM(model=model_name)
os.environ["LANGSMITH_TRACING_V2"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"

log=open("result.txt","w+")

question="请简要介绍一下RAG技术如何增强大语言模型输出准确度。"
log.write(f"向{model_name}提问：{question}\n")
log.write(f"{model_name}输出：\n")
log.write(llm.invoke(question))
log.write(llm.invoke(question).content)

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
vector_store = Chroma.from_documents(documents=splits, embedding=OllamaEmbeddings(model="mxbai-embed-large"), persist_directory='.') # 向量化

# Retrieve and generate using the relevant snippets of the blog.
retriever = vector_store.as_retriever()
prompt = hub.pull("rlm/rag-prompt")

def format_docs(input_docs):
    return "\n\n".join(doc.page_content for doc in input_docs)


rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
)

# 对比生成内容差异
question="任务分解（Task Decomposition）是什么?"
log.write(f"\nRAG Chain与直接询问{model_name}的比较： {question}\n")
log.write("RAG Chain输出：")
log.write(rag_chain.invoke(question))
log.write(f"\n{model_name}输出：\n")
# log.write(llm.invoke(question).content)
log.write(llm.invoke(question))

# 确认正常运行
question="在上下文语境中，AutoGPT是什么意思？"
log.write(f"\n对于其他问题，RAG Chain与直接询问{model_name}的比较： {question}\n")
log.write("\nRAG Chain输出：\n")
log.write(rag_chain.invoke(question))
log.write(f"\n{model_name}输出：\n")
# log.write(llm.invoke(question).content)
log.write(llm.invoke(question))
log.close()
