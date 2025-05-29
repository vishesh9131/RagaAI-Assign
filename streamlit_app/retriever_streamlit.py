import streamlit as st
from retriever_agent import RetrieverAgent # Assuming it's in the same directory
import json

DEFAULT_INDEX_PATH_ST = "streamlit_faiss_store"

@st.cache_resource # Cache the agent for better performance
def load_agent(index_path):
    print(f"Attempting to load/initialize RetrieverAgent at {index_path}")
    return RetrieverAgent(index_path=index_path)

def run_retriever_app():
    st.set_page_config(page_title="Retriever Agent UI", page_icon="🧠", layout="wide")
    st.title("🧠 Retriever Agent Interface")

    st.sidebar.header("Configuration")
    index_path = st.sidebar.text_input("FAISS Index Path", value=DEFAULT_INDEX_PATH_ST)
    
    # Load the agent (cached)
    try:
        agent = load_agent(index_path)
        st.sidebar.success(f"Agent initialized. Index: {index_path}")
        st.sidebar.caption(f"Model: {agent.embeddings.model_name}")
        st.sidebar.caption(f"Chunk size: {agent.text_splitter._chunk_size}, Overlap: {agent.text_splitter._chunk_overlap}")
    except Exception as e:
        st.error(f"Error initializing RetrieverAgent: {e}")
        st.stop()

    tab1, tab2, tab3 = st.tabs(["Add Documents", "Search Documents", "Store Info"]) 

    with tab1:
        st.header("Add New Documents to Vector Store")
        with st.form("add_document_form"):
            num_texts = st.number_input("Number of texts to add", min_value=1, max_value=10, value=1)
            texts_inputs = []
            metadatas_inputs_str = []
            for i in range(num_texts):
                st.subheader(f"Text {i+1}")
                text_content = st.text_area(f"Text Content {i+1}", height=100, key=f"text_{i}")
                texts_inputs.append(text_content)
                metadata_str = st.text_input(f"Metadata (JSON string) for Text {i+1}", placeholder='{"source": "my_doc.txt"}', key=f"meta_{i}")
                metadatas_inputs_str.append(metadata_str)
            
            submitted_add = st.form_submit_button("Add Texts to Store")

        if submitted_add:
            valid_texts_to_add = []
            parsed_metadatas_list = []
            all_valid = True
            for i in range(len(texts_inputs)):
                if not texts_inputs[i].strip():
                    st.warning(f"Text {i+1} is empty and will be skipped.")
                    continue
                
                valid_texts_to_add.append(texts_inputs[i])
                meta_dict = None
                if metadatas_inputs_str[i].strip():
                    try:
                        meta_dict = json.loads(metadatas_inputs_str[i])
                        if not isinstance(meta_dict, dict):
                            st.error(f"Metadata for text {i+1} is not a valid JSON object. Skipping this text.")
                            all_valid = False; break # Stop processing this batch
                    except json.JSONDecodeError:
                        st.error(f"Invalid JSON in metadata for text {i+1}. Skipping this text.")
                        all_valid = False; break # Stop processing this batch
                parsed_metadatas_list.append(meta_dict if meta_dict else {"source": f"streamlit_input_{i+1}"})
            
            if all_valid and valid_texts_to_add:
                with st.spinner("Processing and adding documents..."):
                    try:
                        doc_ids = agent.add_texts(valid_texts_to_add, metadatas=parsed_metadatas_list)
                        st.success(f"Successfully added {len(valid_texts_to_add)} texts (split into chunks).")
                        st.info(f"FAISS Chunk IDs: {doc_ids}")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Error adding documents: {e}")
            elif not valid_texts_to_add:
                st.warning("No valid texts were provided to add.")

    with tab2:
        st.header("Search Documents")
        query = st.text_input("Enter your search query:")
        top_k = st.slider("Number of results (k):", min_value=1, max_value=20, value=5)

        if st.button("Search") and query:
            with st.spinner("Searching..."):
                results = agent.search(query, k=top_k)
                if results:
                    st.subheader(f"Search Results for '{query}' (Top {len(results)}):")
                    for i, res in enumerate(results):
                        with st.expander(f"Result {i+1} (Score: {res['score']:.4f} - Source: {res['metadata'].get('source', 'N/A')})"):
                            st.markdown(f"**Content:**\n```\n{res['content']}\n```")
                            st.json(res['metadata'], expanded=False)
                else:
                    st.info("No results found.")
        elif st.button("Search") and not query:
            st.warning("Please enter a search query.")

    with tab3:
        st.header("Vector Store Information")
        if st.button("Refresh Store Info"):
            st.experimental_rerun() # Rerun to re-fetch info from cached agent
            
        count = agent.get_document_count()
        sources = agent.list_all_chunk_sources()
        st.metric("Total Document Chunks", count)
        st.subheader("Known Sources in Metadata:")
        if sources:
            for src in sources:
                st.markdown(f"- `{src}`")
        else:
            st.markdown("_No sources found in metadata or store is empty._")

if __name__ == "__main__":
    run_retriever_app() 