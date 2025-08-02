from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
from typing import TypedDict, Annotated, Literal
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage
import operator
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Define the structured output model
class UserInfo(BaseModel):
    """Information about a user."""
    name: str = Field(description="The name of the person")
    age: int = Field(description="The age of the person")
    city: str = Field(description="The city where the person lives")

@tool
def write_to_file(filename: str, data: UserInfo):
    """Writes the user information to a JSON file."""
    with open(filename, 'w') as f:
        json.dump(data.dict(), f, indent=4)
    return f"Successfully wrote data to {filename}"

# Define the state for the graph
class StructuredOutputState(TypedDict):
    text: str
    output_file: str
    messages: Annotated[list, operator.add]

# Initialize the language model with structured output capabilities
llm = ChatOpenAI(model="gpt-4o", temperature=0)
llm_with_tools = llm.bind_tools([write_to_file])

# Define the prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert extraction algorithm. Extract the user's information from the following text and then use the available tools to write the extracted information to a file."),
    ("user", "{text}\n\nThe output file is: {output_file}")
])

def call_model(state: StructuredOutputState):
    """
    Invokes the LLM to extract information and generate a tool call in a single step.
    """
    response = llm_with_tools.invoke({
        "text": state['text'],
        "output_file": state['output_file']
    })
    return {"messages": [response]}

def should_continue(state: StructuredOutputState) -> Literal["tools", "__end__"]:
    """
    Determines whether to continue with tool execution or end the graph.
    """
    if state["messages"][-1].tool_calls:
        return "tools"
    return "__end__"

tool_node = ToolNode([write_to_file])

# Define the graph
def create_structured_output_graph():
    """
    Creates and compiles the structured output graph with tool calling.
    """
    workflow = StateGraph(StructuredOutputState)
    workflow.add_node("extract_info", call_model)
    workflow.add_node("tools", tool_node)
    
    workflow.set_entry_point("extract_info")
    
    workflow.add_conditional_edges(
        "extract_info",
        should_continue,
    )
    workflow.add_edge("tools", END)
    
    return workflow.compile()

if __name__ == '__main__':
    # Example of how to run the graph
    graph = create_structured_output_graph()
    
    # Input text and output file
    input_text = "My name is John Doe, I am 30 years old and I live in New York."
    output_file = "user_info.json"
    
    # Run the graph
    result = graph.invoke({"text": input_text, "output_file": output_file, "messages": []})
    
    # Print the final state
    print("Graph execution finished. Final state:")
    print(result)

    # Verify the file was created
    if os.path.exists(output_file):
        print(f"\nFile '{output_file}' created successfully.")
        with open(output_file, 'r') as f:
            print("File content:")
            print(f.read())
        # Clean up the created file
        os.remove(output_file)
    else:
        print(f"\nFile '{output_file}' was not created.")
