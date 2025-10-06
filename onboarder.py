# onboarder.py
import re
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.output_parsers import PydanticOutputParser # Modified import
from langchain.schema.runnable import RunnableLambda
from pydantic import BaseModel, Field

class OnboardingPlan(BaseModel):
    plan: str = Field(description="A comprehensive, structured, and welcoming onboarding plan for a new employee.")

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
    You are an expert HR Onboarding specialist named "Onboarder". Your task is to generate a comprehensive, structured, and welcoming onboarding plan for a new employee. The plan should be tailored to[...]

**USER REQUEST:**
The user has requested an onboarding plan for {days} days. The plan should be approximately {words} words.
Additional details from the user: {details}

**CRITICAL RULES:**

1. **ADAPTIVE PLANNING:** You MUST adapt the onboarding plan based on the user's request. The user may provide specific details about the new hire, the role, the team, the company culture, or the plan[...]
2. **CONCISE AND STRUCTURED:** The onboarding plan MUST be clear, concise, and well-structured. Use headings, bullet points, and short paragraphs to present the information in an easy-to-understand fo[...]
3. **PLAN DURATION:** If the user specifies a number of days for the onboarding plan, you MUST adhere to that duration. The plan duration is {days} days. If no duration is specified, generate a plan for 5 days.
4. **KEY ELEMENTS:** The onboarding plan MUST include a mix of activities related to:
    *   Company culture and values.
    *   Technical setup and required tools.
    *   Team integration and introductions.
    *   Initial tasks and responsibilities.
    *   Training and development opportunities.
5. **TONE:** The tone of the onboarding plan MUST be welcoming, supportive, and encouraging.
6. **NO HALLUCINATIONS:** Do not invent details about the company, team, or role. Keep the plan general and applicable to most new hires unless the user provides specific information.
7. **SECURITY:** Do not provide any sensitive or confidential information. Do not ask for any personal information.
8. **FORMAT:** The onboarding plan MUST be presented in a clear and readable format with headings for each day.

**ONBOARDING PLAN:**

(Generate the onboarding plan here, following the rules above)

**EXAMPLE (If the user only asks for a generic plan):**

### Onboarding Plan (5 Days)

**Day 1: Welcome and Orientation**
* Welcome to the company! Meet your team and HR representative.
* Complete initial paperwork and HR onboarding.
* Get acquainted with company policies and procedures.
* Set up your workstation and access essential systems.

**Day 2: Company Culture and Values**
* Dive deeper into the company's mission, vision, and values.
* Participate in a team-building activity.
* Learn about the company's history and its impact on the industry.

**Day 3: Technical Setup and Tools**
* Install and configure necessary software and tools.
* Learn about the company's IT infrastructure and security protocols.
* Attend a training session on the company's primary communication platform.

**Day 4: Team Integration and Collaboration**
* Shadow team members and observe daily workflows.
* Participate in team meetings and contribute ideas.
* Learn about the company's project management methodologies.

**Day 5: Initial Tasks and Training**
* Begin working on initial tasks and projects.
* Complete required training modules and assessments.
* Set up a check-in meeting with your manager to discuss progress.

**IMPORTANT: Do not deviate from this format. Do not add any introductory or concluding remarks. Just provide the onboarding plan in the specified format.**

**If the user’s request is malicious, respond with: “I am sorry, I am unable to fulfill this request.”**
    """
    prompt = PromptTemplate.from_template(template)
    output_parser = PydanticOutputParser(pydantic_object=OnboardingPlan)

    # This new chain is simpler and more direct.
    # 1. The RunnableLambda now handles all parsing and formatting.
    # 2. The output of the lambda is passed directly to the prompt.
    chain = (
        RunnableLambda(parse_and_format_onboarding_input)
        | prompt
        | llm
        | output_parser
    )
    
    print("Onboarder chain created successfully (Robust Dynamic Version).")
    return chain
