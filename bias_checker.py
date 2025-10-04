# bias_checker.py
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough

def create_bias_checker_chain(llm):
    """
    Creates a LangChain chain for the BiasChecker agent.
    This agent is designed to detect and flag potential bias in text.
    """
    
    template = """
    You are an AI ethics and bias detection assistant. Your sole purpose is to analyze text for potential bias.
    
    Analyze the following text for potential bias. Look for subjective, non-factual language (e.g., 'seems like a good fit,' 'lacks confidence') or any language that focuses on protected characteristics like age, gender, or origin in a non-neutral way.

    If bias is found, you MUST clearly state what the bias is and why it's problematic.
    If no bias is detected, you MUST respond with only the words: 'No bias detected.'

    TEXT TO ANALYZE:
    {text_input}

    ANALYSIS:
    """
    prompt = PromptTemplate.from_template(template)

    chain = (
        {"text_input": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    print("BiasChecker chain created successfully.")
    return chain