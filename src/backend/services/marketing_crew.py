"""Marketing team crew service using CrewAI."""

import os
from typing import Optional

from crewai import Agent, Crew, Process, Task
from langchain_openai import ChatOpenAI

from src.shared.config import settings


class MarketingCrewService:
    """Service for managing marketing team crew."""

    def __init__(self):
        """Initialize the marketing crew service."""
        # Set OpenAI API key
        os.environ["OPENAI_API_KEY"] = settings.openai_api_key
        
        # Initialize LLM - Using configurable model for cost efficiency
        # Model options:
        # - "gpt-3.5-turbo": Cheapest option (~$0.50 per 1M input tokens, ~$1.50 per 1M output tokens)
        # - "gpt-4o-mini": Balanced option (~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens) - RECOMMENDED
        # - "gpt-4-turbo": Best quality but expensive (~$10 per 1M input tokens, ~$30 per 1M output tokens)
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=0.7,
        )

    def create_marketing_crew(self, topic: str, language: Optional[str] = None) -> Crew:
        """Create a marketing crew with specialized agents."""
        output_language = language or settings.app_language

        # Define Marketing Strategist Agent
        strategist = Agent(
            role="Marketing Strategist",
            goal=f"Develop comprehensive marketing strategies for {topic}",
            backstory="""You are an experienced marketing strategist with over 15 years 
            of experience in developing successful marketing campaigns. You excel at 
            understanding market trends, target audiences, and competitive landscapes. 
            Your strategies are data-driven and innovative.""",
            verbose=True,
            allow_delegation=False,  # Disable delegation to avoid tool errors
            llm=self.llm,
        )

        # Define Content Creator Agent
        content_creator = Agent(
            role="Content Creator",
            goal=f"Create engaging and compelling content for {topic}",
            backstory="""You are a creative content creator specializing in marketing 
            content. You have a talent for crafting messages that resonate with audiences, 
            creating blog posts, social media content, and marketing copy that drives 
            engagement and conversions.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
        )

        # Define Social Media Specialist Agent
        social_media_specialist = Agent(
            role="Social Media Specialist",
            goal=f"Develop social media strategies and posts for {topic}",
            backstory="""You are a social media expert who understands the nuances of 
            different platforms. You know how to create content that performs well on 
            Instagram, Twitter, LinkedIn, Facebook, and TikTok. Your posts are optimized 
            for engagement and reach.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
        )

        # Define Campaign Manager Agent
        campaign_manager = Agent(
            role="Campaign Manager",
            goal=f"Coordinate and manage marketing campaigns for {topic}",
            backstory="""You are a results-driven campaign manager with expertise in 
            planning, executing, and optimizing marketing campaigns. You ensure all 
            marketing efforts are aligned, on schedule, and delivering measurable results. 
            You excel at coordinating between different team members and stakeholders.""",
            verbose=True,
            allow_delegation=False,  # Disable delegation to avoid tool errors
            llm=self.llm,
        )

        # Define Tasks
        strategy_task = Task(
            description=f"""Develop a comprehensive marketing strategy for {topic}. 
            Include target audience analysis, key messaging, competitive positioning, 
            and recommended marketing channels. Output should be in {output_language}.""",
            agent=strategist,
            expected_output="A detailed marketing strategy document with audience analysis, messaging, and channel recommendations",
        )

        content_task = Task(
            description=f"""Based on the marketing strategy, create engaging content 
            including a blog post outline, key messaging points, and content themes. 
            Output should be in {output_language}.""",
            agent=content_creator,
            expected_output="Content plan with blog outline, messaging points, and content themes",
        )

        social_media_task = Task(
            description=f"""Create 5-7 social media posts for different platforms 
            (Instagram, Twitter, LinkedIn) based on the marketing strategy and content 
            plan. Each post should be platform-appropriate and engaging. Output should 
            be in {output_language}.""",
            agent=social_media_specialist,
            expected_output="A list of 5-7 social media posts optimized for different platforms",
        )

        campaign_task = Task(
            description=f"""Based on all previous work, create a comprehensive campaign 
            plan that includes timeline, key milestones, success metrics, and 
            implementation steps. Ensure all elements are coordinated. Output should 
            be in {output_language}.""",
            agent=campaign_manager,
            expected_output="A complete campaign plan with timeline, milestones, metrics, and implementation steps",
        )

        # Create Crew
        crew = Crew(
            agents=[
                strategist,
                content_creator,
                social_media_specialist,
                campaign_manager,
            ],
            tasks=[
                strategy_task,
                content_task,
                social_media_task,
                campaign_task,
            ],
            process=Process.sequential,
            verbose=True,
        )

        return crew

    def execute_marketing_task(self, topic: str, language: Optional[str] = None) -> dict:
        """Execute a marketing task and return results."""
        crew = self.create_marketing_crew(topic, language)
        
        try:
            # Execute the crew
            result = crew.kickoff()
            
            # Convert CrewOutput to string for processing
            result_str = str(result)
            
            # Parse and structure the results
            return {
                "status": "completed",
                "topic": topic,
                "result": result_str,
                "content_strategy": self._extract_content_strategy(result_str),
                "social_media_posts": self._extract_social_posts(result_str),
                "blog_outline": self._extract_blog_outline(result_str),
                "campaign_ideas": self._extract_campaign_ideas(result_str),
            }
        except Exception as e:
            return {
                "status": "failed",
                "topic": topic,
                "error_message": str(e),
            }

    def _extract_content_strategy(self, result: str) -> Optional[str]:
        """Extract content strategy from crew result."""
        # Simple extraction - can be enhanced with better parsing
        if "strategy" in result.lower() or "content" in result.lower():
            return result
        return None

    def _extract_social_posts(self, result: str) -> list[str]:
        """Extract social media posts from crew result."""
        # Simple extraction - can be enhanced with better parsing
        posts = []
        lines = result.split("\n")
        for line in lines:
            if any(platform in line.lower() for platform in ["instagram", "twitter", "linkedin", "facebook"]):
                posts.append(line.strip())
        return posts[:7]  # Return up to 7 posts

    def _extract_blog_outline(self, result: str) -> Optional[str]:
        """Extract blog outline from crew result."""
        if "blog" in result.lower() or "outline" in result.lower():
            return result
        return None

    def _extract_campaign_ideas(self, result: str) -> list[str]:
        """Extract campaign ideas from crew result."""
        ideas = []
        lines = result.split("\n")
        for line in lines:
            if "campaign" in line.lower() or "idea" in line.lower():
                ideas.append(line.strip())
        return ideas[:5]  # Return up to 5 ideas

