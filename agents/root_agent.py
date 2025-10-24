import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from google.genai import types

from tools.bq import get_scan_cost, get_dry_run_size, get_query_equivalence, get_farm_fingerprint
from .prompts.root_agent import get_instructions


# load_dotenv()

scan_cost_tool = FunctionTool(func=get_scan_cost)
dry_run_size_tool = FunctionTool(func=get_dry_run_size)
query_equivalence_tool = FunctionTool(func=get_query_equivalence)
farm_fingerprint_tool = FunctionTool(func=get_farm_fingerprint)

MODEL = "gemini-2.5-pro"
AGENT_APP_NAME = 'BQ_SQL_AGENT'

root_agent = Agent(
        model=MODEL,
        name=AGENT_APP_NAME,
        description="You are helpful assitant answering all kinds of questions in a very positive way!",
        instruction=get_instructions(),
        generate_content_config=types.GenerateContentConfig(temperature=0.0),
        tools=[scan_cost_tool, dry_run_size_tool, query_equivalence_tool, farm_fingerprint_tool]
)