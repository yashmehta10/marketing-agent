from google.adk.agents.llm_agent import Agent
from google.adk.tools import google_search, ToolContext, load_artifacts
from google.adk.tools.agent_tool import AgentTool
from google.genai import Client, types

from dotenv import load_dotenv
import os 

MODEL = "gemini-2.5-flash"
IMAGE_MODEL = "imagen-3.0-fast-generate-001"
# IMAGE_MODEL = "imagen-4.0-generate-001"

load_dotenv()

client = Client(
    vertexai=True,
    project=os.getenv("GOOGLE_CLOUD_PROJECT"),
    location=os.getenv("GOOGLE_CLOUD_LOCATION"),
)

async def generate_image(img_prompt: str, tool_context: "ToolContext"):
    """Generates an image based on the prompt provided to this tool"""
    response = client.models.generate_images(
        model=IMAGE_MODEL,
        prompt=img_prompt,
        config={"number_of_images": 1},
    )
    if not response.generated_images:
        return {"status": "failed"}
    image_bytes = response.generated_images[0].image.image_bytes
    await tool_context.save_artifact(
        "image.png",
        types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
    )
    return {
        "status": "success",
        "detail": "Image generated successfully and stored in artifacts.",
        "filename": "image.png",
    }

search_agent = Agent(
        model=MODEL,
        name='SearchAgent',
        instruction="""
        You're a specialist in Google Search
        """,
        tools=[google_search],
    )

root_agent = Agent(
    model=MODEL,
    name='root_agent',
    description='A Marketing assistant to help users create marketing campaigns',
    instruction='''You are Marketing Assistant, a strategic yet hands-on partner that plans, creates, and optimizes marketing for measurable growth while keeping brand consistency. 
        Use Google Search tool to research relevant events that have been hosted in the last few months and ensure our campaign is unique but also take inspiration from them.
        If key inputs are missing, briefly ask for goal, audience, and KPI—otherwise proceed.
        Deliver concise, ready-to-ship assets (respect platform limits) and clearly mark assumptions vs facts.
        Provide 3 creative variations with a one-sentence hypothesis on which might win and why.
        Respond using sections: Summary, Deliverables, Variations, Distribution & Measurement, Next Actions, Sources.
    ''',
    tools=[AgentTool(agent=search_agent), generate_image, load_artifacts],
)
