# onboarder.py

from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough

def create_onboarder_chain(llm):
    """
    Creates the main LangChain chain for the Onboarder agent.
    This version is updated to accept a single string input.
    """
    
    template = """
    You are an expert HR Onboarding specialist named "Onboarder". Your task is to generate a comprehensive, structured, and welcoming 5-day onboarding plan for a new employee.

    The plan should be detailed, actionable, and spread across the first week (Monday to Friday).
    Include a mix of activities covering company culture, technical setup, team integration, and first tasks.

    Generate the plan for the following new hire:
    {input}

    Format the output clearly with headings for each day.
    
    ONBOARDING PLAN:
    """
    # Note: We now use `PromptTemplate.from_template` as it's simpler for a single input
    prompt = PromptTemplate.from_template(template)

    # The chain now simply passes the direct input to the prompt.
    chain = {"input": RunnablePassthrough()} | prompt | llm | StrOutputParser()
    
    print("Onboarder chain created successfully (Single Input Version).")
    return chain