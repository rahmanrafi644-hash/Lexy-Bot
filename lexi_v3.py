import streamlit as st
import os
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from prompts import LEXI_SYSTEM_PROMPT

load_dotenv()

# 1. Page Configuration (Mobile Responsive Architecture)
st.set_page_config(
    page_title="Lexi AI - Corporate Legal Assistant",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Professional UI Styling
st.markdown("""
    <style>
    .main-header { font-size:2.4rem !important; font-weight: 700; color: #1E3A8A; margin-bottom: 5px; }
    .sub-header { font-size:1.1rem !important; color: #4B5563; margin-bottom: 25px; }
    .stButton>button { width: 100%; border-radius: 8px; text-align: left; padding: 10px; background-color: #F3F4F6; border: 1px solid #E5E7EB; }
    .stButton>button:hover { background-color: #EBF5FF; border-color: #3B82F6; }
    </style>
""", unsafe_allow_html=True)

# 2. Professional Sidebar Organization
with st.sidebar:
    st.markdown("<h2 style='color: #1E3A8A;'>⚖️ Knowledge Base</h2>", unsafe_allow_html=True)
    st.markdown("This AI assistant is fully trained on the following regulatory legal frameworks:")
    
    st.markdown("""
    * **Companies Act, 1994**
    * **The Contract Act, 1872**
    * **The Partnership Act, 1932**
    * **The Sale of Goods Act, 1930**
    * **Negotiable Instruments Act, 1881**
    """)
    st.divider()
    st.markdown("<small style='color:gray;'>Lexi Engine v3.1 (High-Performance RAG Build)</small>", unsafe_allow_html=True)

# Main App Title Layout
st.markdown("<div class='main-header'>⚖️ Lexi Corporate AI</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>Elite interactive legal intelligence for business & corporate law frameworks.</div>", unsafe_allow_html=True)

# 3. Bulletproof Database Initialization
def build_clean_database():
    if not os.path.exists("laws"):
        os.makedirs("laws")
        st.warning("📁 'laws' folder created. Drop your PDFs inside and refresh!")
        st.stop()

    loader = PyPDFDirectoryLoader("laws")
    docs = loader.load()
    
    if not docs:
        st.error("❌ No PDFs found inside your 'laws' folder! Please check your files.")
        st.stop()
        
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=100)
    final_chunks = text_splitter.split_documents(docs)
    
    embedding_engine = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_store = FAISS.from_documents(final_chunks, embedding_engine)
    return vector_store

if "vector_db" not in st.session_state:
    with st.spinner("⏳ Constructing secure local law engine..."):
        st.session_state.vector_db = build_clean_database()
        st.success("✅ Clean database built and loaded perfectly!")

# 4. Setup RAG Pipeline
def initialize_rag_pipeline(vector_store):
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", LEXI_SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
    ])
    
    prompt.input_variables = ["context", "chat_history", "input"]
    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 4})
    document_chain = create_stuff_documents_chain(llm, prompt)
    return create_retrieval_chain(retriever, document_chain)

rag_chain = initialize_rag_pipeline(st.session_state.vector_db)

# 5. Chat Interface Logic & Session Management
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display current chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- CRITICAL FIX: GUARANTEE VARIABLES ALWAYS EXIST TO PREVENT NAMEERROR ---
user_query = None
suggested_query = None

# Show Starter Questions ONLY if the chat history is completely empty
if len(st.session_state.messages) == 0:
    st.markdown("### 💡 Quick Start Suggestions")
    st.markdown("Click any case scenario below to instantly query Lexi:")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📋 What are the essential elements of a valid contract?"):
            suggested_query = "What are the essential elements of a valid contract under the Contract Act?"
        if st.button("🏢 How is a company legally incorporated under the 1994 Act?"):
            suggested_query = "What is the complete process of incorporation for a limited company under the Companies Act 1994?"
            
    with col2:
        if st.button("🤝 What are the primary liabilities of a partner in a firm?"):
            suggested_query = "What are the legal liabilities and duties of a partner under the Partnership Act 1932?"
        if st.button("💳 What happens if a cheque bounces?"):
            suggested_query = "What are the legal consequences and penalties of a dishonored cheque under the Negotiable Instruments Act?"

# Capture direct input from the text box at the bottom
chat_input_val = st.chat_input("Ask Lexi a legal question...")

# Determine what the active query is
if suggested_query:
    user_query = suggested_query
elif chat_input_val:
    user_query = chat_input_val

# Execute pipeline if a query exists
if user_query:
    # Display user question
    with st.chat_message("user"):
        st.markdown(user_query)
    st.session_state.messages.append({"role": "user", "content": user_query})
    
    # Process and display AI response
    with st.chat_message("assistant"):
        with st.spinner("Lexi is analyzing legal frameworks..."):
            try:
                history_input = []
                for m in st.session_state.messages[:-1]:
                    history_input.append((m["role"], m["content"]))

                res = rag_chain.invoke({
                    "input": user_query,
                    "chat_history": history_input
                })
                
                bot_answer = res["answer"]
                st.markdown(bot_answer)
                st.session_state.messages.append({"role": "assistant", "content": bot_answer})
                
                # Smoothly refresh screen to update state
                st.rerun()
                
            except Exception as e:
                st.error(f"Execution Error: {str(e)}")