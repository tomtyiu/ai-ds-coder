import os
import json
import pandas as pd
import argparse
from langchain_core.tools import Tool
from langchain_experimental.utilities import PythonREPL
from langchain_community.chat_models.huggingface import ChatHuggingFace
from transformers import BitsAndBytesConfig
from langchain_huggingface import HuggingFacePipeline
from langchain_core.messages import HumanMessage, SystemMessage
from pathlib import Path

from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="hf.co/legolasyiu/Fireball-Meta-Llama-3.1-8B-Instruct-Agent-0.003-128K-code-ds-Q8_0-GGUF:latest",
    temperature=0.6,
    max_new_tokens=128000,
    # other params...
)



#chat_model = ChatHuggingFace(llm=llm)
os.environ["OPENAI_API_KEY"] = os.getenv('OPENAI_API_KEY')

# Argument parsing
def parse_args():
    parser = argparse.ArgumentParser(description="LLM-based Data Science CLI Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Interactive mode
    subparsers.add_parser("interactive", help="Start an interactive LLM session")

    # Load data command
    load_parser = subparsers.add_parser("load", help="Load a dataset")
    load_parser.add_argument("--file", type=str, required=True, help="Path to the data file")

    # Suggest task (preprocessing, hyperparameter tuning)
    suggest_parser = subparsers.add_parser("suggest", help="LLM suggestions for preprocessing or hyperparameter tuning")
    suggest_parser.add_argument("--task", type=str, required=True, choices=["preprocessing", "hyperparameter_tuning"],
                                help="Task type for LLM suggestion")

    # Train model command
    train_parser = subparsers.add_parser("train", help="Train a machine learning model")
    train_parser.add_argument("--model", type=str, required=True, help="Model name (e.g., random_forest, xgboost)")
    train_parser.add_argument("--file", type=str, required=True, help="Path to the data file")
    train_parser.add_argument("--target", type=str, required=True, help="Target variable for model training")

    # Generate EDA report
    eda_parser = subparsers.add_parser("eda", help="Generate an EDA report")
    eda_parser.add_argument("--file", type=str, required=True, help="Path to the data file")
    eda_parser.add_argument("--plot", type=str, help="Specify plot types (e.g., 'all', 'scatter', 'heatmap')")

    return parser.parse_args()

# Interactive mode
def interactive_mode():
    print("=======================================================================")
    print("Starting Interactive Session with LLM")
    print("=======================================================================")
    query = ""
    while query.lower() != "exit":
        query = input("USER>> ")
        if query.lower() == "exit":
            break
        chat_with_llm(query)

# Load and process data
def load_data(file_path):
    print(f"Loading data from {file_path}...")
    ext = os.path.splitext(file_path)[1].lower()

    if ext == '.csv':
        data = pd.read_csv(file_path)
        print(f"Loaded {data.shape[0]} rows and {data.shape[1]} columns.")
        return data
    else:
        print(f"Unsupported file type: {ext}")
        return None

# Pass task to LLM for suggestions (preprocessing or hyperparameter tuning)
def suggest_task(task):
    if task == "preprocessing":
        query = "Suggest the best preprocessing steps for a CSV dataset."
    elif task == "hyperparameter_tuning":
        query = "Suggest hyperparameter tuning steps for a llama 3.2 model."
    
    chat_with_llm(query)

# Pass model training to the LLM
def train_model_with_llm(model_name, file_path, target):
    try:
        data = load_data(file_path)
        if data is None:
            raise ValueError("Data loading failed")
        if target not in data.columns:
            raise ValueError(f"Target column '{target}' not found in the dataset")

        # Prepare the task for LLM
        query = f"Create python code to train a {model_name} model using the {data} from dataset with the target variable '{target}'. Provide the code only."
        response = chat_with_llm(query)

        # Execute the code generated by LLM (ensure PythonREPL runs it)
        get_python_repl(response)
    except Exception as e:
        print(f"Error during model training: {str(e)}")

# Generate EDA report using the LLM
def generate_eda_with_llm(file_path, plot_type):
    data = load_data(file_path)
    if data is not None:
        # Ask the LLM to generate an EDA report
        query = f"Generate an EDA report for the {data} of dataset. Include {plot_type} plots if applicable."
        response = chat_with_llm(query)

        # Execute the EDA code generated by LLM
        get_python_repl(response)
    else:
        print("Failed to load data for EDA")

# Function to communicate with the LLM
def chat_with_llm(query):
    messages = [
        SystemMessage(content=
                      "You are an assistant for question-answering tasks. "
                      "Use the following pieces of retrieved context to answer the question.\n"
                      "If you don't know the answer, say that you don't know. \n"
                      "Use three sentences maximum and keep the answer concise. "
                      "You are also a coding assistant with retrieved context \n"
                      "\n\n"
                      "{query}"
                      ),
        HumanMessage(content=query),
    ]
    response = llm.invoke(messages)
    print(f"LLM Response:\n{response.content}")
    return response.content

# Execute Python code using a Python REPL
def get_python_repl(ai_msg):
    python_repl = PythonREPL()
    result = python_repl.run(ai_msg)
    print(result)

# Main function
def main():
    args = parse_args()

    if args.command == "interactive":
        interactive_mode()
    elif args.command == "load":
        load_data(args.file)
    elif args.command == "suggest":
        suggest_task(args.task)
    elif args.command == "train":
        train_model_with_llm(args.model, args.file, args.target)
    elif args.command == "eda":
        generate_eda_with_llm(args.file, args.plot)
    else:
        print("Invalid command. Use --help for available commands.")

if __name__ == "__main__":
    main()