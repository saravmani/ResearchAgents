import streamlit as st
from graphs.structured_output_graph import create_structured_output_graph
import uuid

def structured_output_page():
    st.header("Structured Output Agent")

    # Get user input
    user_input = st.text_area("Enter text to extract information from:", "My name is Jane Doe, I am 25 years old and I live in London.")

    if st.button("Extract Information"):
        if user_input:
            with st.spinner("Extracting information..."):
                # Create a new graph instance
                graph = create_structured_output_graph()

                # Define the input for the graph
                inputs = {"text": user_input}

                # Run the graph
                result = graph.invoke(inputs)

                st.write("Extracted Information:")
                # The output is a pydantic model, so we convert it to a dict
                st.json(result['structured_info'].dict())

                st.success("Extraction complete!")
        else:
            st.warning("Please enter some text.")
