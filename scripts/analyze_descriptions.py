import os
from pathlib import Path
from typing import List
import argparse
from dotenv import load_dotenv
from loguru import logger
from llama_index.llms.openai import OpenAI
from llama_index.core.llms import ChatMessage, MessageRole

# Load environment variables
load_dotenv()

def read_descriptions(file_path: str) -> List[str]:
    """
    Read descriptions from a file.
    
    Args:
        file_path: Path to the descriptions file
        
    Returns:
        List of descriptions
    """
    descriptions = []
    current_description = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line == "---":
                if current_description:
                    descriptions.append("\n".join(current_description))
                    current_description = []
            elif line:
                current_description.append(line)
                
    # Add last description if exists
    if current_description:
        descriptions.append("\n".join(current_description))
        
    return descriptions

def create_analysis_prompt(descriptions: List[str]) -> str:
    """
    Create a prompt for GPT-4 to analyze descriptions.
    
    Args:
        descriptions: List of descriptions to analyze
        
    Returns:
        Formatted prompt string
    """
    prompt = """You are a retail product description analyst. Your task is to analyze a set of T-shirt descriptions and identify patterns, inconsistencies, and areas for improvement.

For each description, analyze:
1. Structure:
   - What information is included?
   - In what order is information presented?
   - What key product attributes are mentioned?

2. Language:
   - What tone and style is used?
   - What adjectives and descriptive phrases are common?
   - Are there any brand-specific language patterns?

3. Completeness:
   - What essential information might be missing?
   - Are there inconsistencies in detail level between descriptions?
   - Which descriptions are most/least informative?

4. Best Practices:
   - Identify the most effective descriptions and explain why
   - Note any problematic patterns or missed opportunities
   - Suggest improvements for consistency

Based on your analysis, create:
1. A template structure for ideal product descriptions
2. A list of essential information that should always be included
3. Recommendations for standardizing language and tone
4. Examples of how to improve weaker descriptions

Here are the descriptions to analyze:

"""
    
    # Add descriptions with numbering
    for i, desc in enumerate(descriptions, 1):
        prompt += f"\n{i}. {desc}\n"
        
    prompt += "\nProvide your analysis and recommendations for creating more consistent, effective product descriptions."
    
    return prompt

def analyze_descriptions_with_gpt(prompt: str) -> str:
    """
    Send descriptions to GPT-4 for analysis using LlamaIndex.
    
    Args:
        prompt: Formatted prompt with descriptions
        
    Returns:
        GPT-4's analysis
    """
    try:
        # Initialize LLM
        llm = OpenAI(
            model=os.getenv("OPENAI_LLM_MODEL", "gpt-4o"),
            temperature=0.7
        )
        
        # Create messages
        messages = [
            ChatMessage(
                role=MessageRole.SYSTEM,
                content="You are a professional retail product description analyst with expertise in e-commerce and marketing."
            ),
            ChatMessage(
                role=MessageRole.USER,
                content=prompt
            )
        ]
        
        # Get response
        response = llm.chat(messages)
        return response.message.content
        
    except Exception as e:
        logger.error(f"Error calling LLM: {str(e)}")
        return None

def save_analysis(analysis: str, output_file: str):
    """
    Save the analysis to a file.
    
    Args:
        analysis: Analysis text from GPT-4
        output_file: Path to save the analysis
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(analysis)
    logger.info(f"Analysis saved to {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Analyze product descriptions using GPT-4')
    parser.add_argument('input_file', help='Path to the descriptions file')
    parser.add_argument('--output', help='Path to save the analysis (default: analysis_result.md)',
                      default='analysis_result.md')
    
    args = parser.parse_args()
    
    # Read descriptions
    logger.info(f"Reading descriptions from {args.input_file}")
    descriptions = read_descriptions(args.input_file)
    logger.info(f"Found {len(descriptions)} descriptions")
    
    # Create prompt
    prompt = create_analysis_prompt(descriptions)
    
    # Get analysis
    logger.info("Sending descriptions to LLM for analysis...")
    analysis = analyze_descriptions_with_gpt(prompt)
    
    if analysis:
        # Save analysis
        save_analysis(analysis, args.output)
    else:
        logger.error("Failed to get analysis from LLM")

if __name__ == "__main__":
    main() 