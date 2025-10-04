# onboarder.py

from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser

def create_onboarder_chain(llm):
    """
    Creates the main LangChain chain for the Onboarder agent.
    
    This agent's purpose is to generate a structured 5-day onboarding plan
    for a new hire based on their name and job title.
    """
    
    template = """
    You are an expert HR Onboarding specialist named "Onboarder". Your task is to generate a comprehensive, structured, and welcoming 5-day onboarding plan for a new employee.

    The plan should be detailed, actionable, and spread across the first week (Monday to Friday).
    Include a mix of activities covering:
    1.  **Company Culture & Admin:** HR paperwork, company values, office tour.
    2.  **Technical Setup:** Equipment, software access, environment configuration.
    3.  **Team Integration:** Introductions to the team, key stakeholders, and a designated "buddy".
    4.  **Role-Specific Knowledge:** Introduction to the codebase, current projects, and key documentation.
    5.  **First Tasks:** A small, well-defined initial task to help them contribute early.

    Generate the plan for the following new hire:
    **Candidate Name:** {candidate_name}
    **Job Title:** {job_title}

    Format the output clearly with headings for each day.
    
    ONBOARDING PLAN:
    """
    prompt = PromptTemplate.from_template(template)

    # This is a simple chain: it takes the input, formats the prompt, sends it to the LLM, and parses the output.
    chain = prompt | llm | StrOutputParser()
    
    print("Onboarder chain created successfully.")
    return chain