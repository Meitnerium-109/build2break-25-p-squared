# talent_scout.py
import re
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnablePassthrough, RunnableLambda
from langchain.schema.output_parser import StrOutputParser

# This is the new function that will orchestrate the two agents.
def run_scout_and_bias_check(input_data, talent_scout_chain, bias_checker_chain):
    """
    An orchestrator function that:
    1. Runs the base TalentScout chain to get candidate rankings.
    2. Parses the output to find each candidate's summary.
    3. Runs the BiasChecker on each summary.
    4. Appends the bias check result to the final output.
    """
    print("--- Running TalentScout analysis... ---")
    # 1. Get the initial analysis from the TalentScout agent
    talent_scout_output = talent_scout_chain.invoke(input_data)
    
    print("--- TalentScout analysis complete. Now running automatic bias check... ---")
    
    # 2. Parse the output to process each candidate individually.
    # The '---' separator from the prompt makes this reliable.
    candidate_blocks = talent_scout_output.split('---')
    
    final_report_parts = []
    
    # We process each block. The first block is usually the header, so we process it differently.
    if candidate_blocks:
        final_report_parts.append(candidate_blocks[0]) # Keep the header
    
    for block in candidate_blocks[1:]:
        if not block.strip():
            continue
            
        # 3. For each candidate, find the summary to be analyzed.
        # We look for the "Summary:" and "Justification:" fields.
        summary_match = re.search(r"-\s*\*\*Summary:\*\*\s*(.*)", block, re.DOTALL)
        justification_match = re.search(r"-\s*\*\*Justification:\*\*\s*(.*)", block, re.DOTALL)
        
        text_to_check = ""
        if justification_match:
            text_to_check += justification_match.group(1).strip() + " "
        if summary_match:
            text_to_check += summary_match.group(1).strip()

        bias_analysis_result = "Bias check could not be performed."
        if text_to_check:
            # Run the BiasChecker on the extracted text
            bias_analysis_result = bias_checker_chain.invoke(text_to_check)
        
        # 4. Append the bias check result to the candidate's block.
        # We add a new "Bias Analysis" field to the output.
        enhanced_block = block.strip() + f"\n    - **Bias Analysis:** {bias_analysis_result.strip()}"
        final_report_parts.append(enhanced_block)

    print("--- Bias check complete. ---")
    return "\n\n---\n".join(final_report_parts)


# We modify the main creation function to accept the bias_checker_chain
def create_talent_scout_chain(retriever, llm, bias_checker_chain):
    """
    Creates the enhanced TalentScout meta-chain.
    """
    
    # --- PROMPT HAS BEEN UPDATED WITH A NEW RULE FOR SPECIFICITY ---
    template = """
    You are an expert HR analyst, TalentScout. Your only job is to analyze and rank candidates based on the resume context provided.

    **CONTEXT FROM RESUMES:**
    {context}

    **USER'S QUESTION:**
    {question}

    **CRITICAL RULES FOR YOUR RESPONSE:**
    1.  **SPECIFICITY:** If the "USER'S QUESTION" asks about a specific person by name, you MUST ONLY provide the analysis for that one person. If the question is general (e.g., "rank all candidates"), then you should analyze everyone found in the context.
    2.  **INCLUDE EVERYONE (if general):** If the request is general, you MUST analyze every candidate found in the context. Do not omit anyone.
    3.  **EXTRACT NAME:** You MUST find the full name of each candidate. If a name is not in the resume, you MUST state "Name Not Found".
    4.  **RANK AND JUSTIFY:** Provide a numbered priority list (if multiple candidates) or a detailed analysis (if a single candidate). For each candidate, you MUST briefly justify your ranking or analysis.
    5.  **STRICT MARKDOWN FORMAT:** Your final output MUST use the exact Markdown format below. Use headings, bold text, and dashes for bullet points.

    ### Candidate Analysis

    Based on your request, here is the analysis:

    ---
    **1. Candidate Name**
    - **Source:** `[source_filename.pdf]`
    - **Justification:** [Explain why this candidate is ranked first/relevant based on their skills and experience.]
    - **Summary:** [Provide a brief summary of the candidate's profile.]

    (Continue for all other relevant candidates if the request was general)
    """
    prompt = PromptTemplate.from_template(template)

    # This is the original chain that just runs the analysis.
    base_talent_scout_chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    # This is the meta-chain that adds the automatic bias check.
    enhanced_chain = RunnableLambda(
        lambda input_data: run_scout_and_bias_check(
            input_data,
            talent_scout_chain=base_talent_scout_chain,
            bias_checker_chain=bias_checker_chain
        )
    )
    
    print("TalentScout meta-chain with automatic bias check created successfully (v2 with specificity).")
    return enhanced_chain