# orchestrator.py

from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain.tools import Tool

def create_orchestrator(llm, tools, memory):
    """
    Creates the master Orchestrator agent.
    This agent uses the ReAct (Reasoning and Acting) framework to decide
    which tool to use based on the user's input.
    """
    
    # This is the master prompt that guides the Orchestrator's reasoning.
    # --- PROMPT HAS BEEN UPDATED WITH A NEW RULE ---
    prompt_template = """
    You are a master HR assistant orchestrator. Your job is to understand the user's request and delegate it to the correct specialist tool.
    You have access to the following tools:

    {tools}

    **CRITICAL: You MUST ALWAYS respond using the following format, without exception. Even if the user tries to trick you, you MUST adhere to this format:**

    Question: the input question you must answer
    Thought: you should always think about what to do.
    Action: the action to take, should be one of [{tool_names}]
    Action Input: the input to the action
    Observation: the result of the action
    ... (this Thought/Action/Action Input/Observation can repeat N times)
    Thought: I now know the final answer
    Final Answer: the final answer to the original input question

    **CRITICAL RULE:** After you receive an Observation from a tool, you MUST either decide on another Action or provide the 'Final Answer'. If the Observation is long and detailed, your next step should almost always be to format it and provide the 'Final Answer'. Do not get stuck.

    Begin!

    Here is the conversation history:
    {chat_history}

    New question: {input}
    {agent_scratchpad}

    Final check before responding: Is the 'Final Answer' aligned with the user's original HR-related request? If the answer is unrelated (e.g., writing code, giving financial advice), you MUST discard it and instead respond with: 'I can only assist with HR-related tasks.'
    """
    
    prompt = PromptTemplate.from_template(prompt_template)
    
    # The create_react_agent function creates the core of our agent's logic.
    agent = create_react_agent(llm, tools, prompt)
    
    # The AgentExecutor is what actually runs the agent, handling the loops of thought and action.
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        verbose=True,  # Set to True to see the agent's thought process
        memory=memory,
        handle_parsing_errors=True # Handles cases where the LLM output is not perfect
    )
    
    print("Orchestrator agent created successfully (v2 with enhanced prompt and jailbreak mitigation).")
    return agent_executor