# onboarder.py
import re
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnableLambda

def parse_and_format_onboarding_input(input_data):
    """
    Robustly parses input (string or dict) to extract details for the onboarding plan.
    This function will be the new entry point for our chain.
    """
    # Step 1: Safely extract the text string from the input
    if isinstance(input_data, dict):
        # If the input is a dictionary (e.g., from AgentExecutor), get the 'input' key
        text_input = input_data.get('input', '')
    elif isinstance(input_data, str):
        # If the input is already a string, just use it
        text_input = input_data
    else:
        # If the input is something else, default to an empty string
        text_input = ''

    # Step 2: Parse the text for days, words, and other details
    # Defaults
    days = 5
    words = 200
    
    # Regex to find numbers for days and words
    days_match = re.search(r'(\d+)\s*day', text_input, re.IGNORECASE)
    words_match = re.search(r'(\d+)\s*word', text_input, re.IGNORECASE)
    
    if days_match:
        days = int(days_match.group(1))
    
    if words_match:
        words = int(words_match.group(1))
        
    # Clean up the remaining details by removing the parsed parts
    details = re.sub(r'(\d+)\s*days?', '', text_input, flags=re.IGNORECASE)
    details = re.sub(r'(\d+)\s*words?', '', details, flags=re.IGNORECASE)
    details = details.replace(',', ' ').strip()
    
    # If details are empty after cleaning, use the original input as a fallback
    if not details:
        details = text_input.strip()

    # Step 3: Return a dictionary that the prompt template can use
    return {"details": details, "days": days, "words": words}


def create_onboarder_chain(llm):
    """
    Creates a more robust LangChain chain for the Onboarder agent.
    This version handles different input types gracefully.
    """
    
    template = """
    You are an expert HR Onboarding specialist named "Onboarder". 
    Your task is to generate a comprehensive, structured, and welcoming onboarding plan for a new employee.

    The plan should be for the specified number of days.
    The total length of the plan should be approximately the specified word count.
    Include a mix of activities: company culture, technical setup, team integration, and first tasks.

    PLAN DETAILS:
    - New Hire: {details}
    - Plan Duration: {days} days
    - Approximate Total Word Count: {words} words

    Generate the plan clearly with headings for each day.
    
    ONBOARDING PLAN:
    """
    prompt = PromptTemplate.from_template(template)

    # This new chain is simpler and more direct.
    # 1. The RunnableLambda now handles all parsing and formatting.
    # 2. The output of the lambda is passed directly to the prompt.
    chain = (
        RunnableLambda(parse_and_format_onboarding_input)
        | prompt
        | llm
        | StrOutputParser()
    )
    
    print("Onboarder chain created successfully (Robust Dynamic Version).")
    return chain