#!/usr / bin / env python3
"""
TRAE.AI Orchestrator - Master Control System
Coordinates all agents and manages the complete workflow
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import requests
import schedule
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from loguru import logger
from pydantic import BaseModel

# Load environment variables
load_dotenv()


class OrchestratorConfig:
    """Configuration for the orchestrator"""


    def __init__(self):
        self.use_mock = os.getenv("USE_MOCK", "false").lower() == "true"
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        self.content_agent_url = os.getenv(
            "CONTENT_AGENT_URL", "http://content_agent:8001"
        )
        self.marketing_agent_url = os.getenv(
            "MARKETING_AGENT_URL", "http://marketing_agent:8002"
        )
        self.monetization_url = os.getenv(
            "MONETIZATION_URL", "http://monetization_bundle:8003"
        )
        self.revenue_rollup_url = os.getenv(
            "REVENUE_ROLLUP_URL", "http://revenue_rollup:8004"
        )
        self.log_level = os.getenv("LOG_LEVEL", "INFO")


class WorkflowTask(BaseModel):
    """Represents a workflow task"""

    id: str
    name: str
    agent: str
    status: str = "pending"
    created_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[Dict] = None
    error: Optional[str] = None


class TraeAIOrchestrator:
    """Main orchestrator class that manages all agents"""


    def __init__(self, config: OrchestratorConfig):
        self.config = config
        self.app = FastAPI(title="TRAE.AI Orchestrator", version="1.0.0")
        self.tasks: Dict[str, WorkflowTask] = {}
        self.setup_logging()
        self.setup_routes()


    def setup_logging(self):
        """Configure logging"""
        logger.remove()
        logger.add(
            sys.stdout,
                level = self.config.log_level,
                format="<green>{time:YYYY - MM - DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
                )
        logger.add(
            "/app / logs / orchestrator.log",
                rotation="1 day",
                retention="30 days",
                level = self.config.log_level,
                )


    def setup_routes(self):
        """Setup FastAPI routes"""

        @self.app.get("/health")


        async def health_check():
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}

        @self.app.get("/status")


        async def get_status():
            return {
                "orchestrator": "running",
                    "tasks_pending": len(
                    [t for t in self.tasks.values() if t.status == "pending"]
                ),
                    "tasks_running": len(
                    [t for t in self.tasks.values() if t.status == "running"]
                ),
                    "tasks_completed": len(
                    [t for t in self.tasks.values() if t.status == "completed"]
                ),
                    "config": {
                    "use_mock": self.config.use_mock,
                        "agents_configured": bool(self.config.openai_api_key),
                        },
                    }

        @self.app.post("/workflow / start")


        async def start_workflow():
            """Start the complete TRAE.AI workflow"""
            try:
                workflow_id = await self.execute_full_workflow()
                return {"workflow_id": workflow_id, "status": "started"}
            except Exception as e:
                logger.error(f"Failed to start workflow: {e}")
                raise HTTPException(status_code = 500, detail = str(e))

        @self.app.get("/workflow/{workflow_id}")


        async def get_workflow_status(workflow_id: str):
            """Get workflow status"""
            if workflow_id not in self.tasks:
                raise HTTPException(status_code = 404, detail="Workflow not found")
            return self.tasks[workflow_id].dict()


    async def check_agent_health(self, agent_url: str, agent_name: str) -> bool:
        """Check if an agent is healthy and responsive"""
        try:
            response = requests.get(f"{agent_url}/health", timeout = 5)
            if response.status_code == 200:
                logger.info(f"✅ {agent_name} is healthy")
                return True
            else:
                logger.warning(f"⚠️ {agent_name} returned status {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ {agent_name} health check failed: {e}")
            return False


    async def execute_content_creation(self) -> Dict:
        """Execute content creation workflow"""
        logger.info("🎬 Starting content creation workflow")

        try:
            # Check content agent health
            if not await self.check_agent_health(
                self.config.content_agent_url, "Content Agent"
            ):
                raise Exception("Content Agent is not available")

            # Request content creation
            response = requests.post(
                f"{self.config.content_agent_url}/create",
                    json={
                    "type": "video",
                        "topic": "trending_news",
                        "format": "educational",
                        "duration": 300,  # 5 minutes
                },
                    timeout = 300,  # 5 minutes timeout
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(
                    f"✅ Content creation completed: {result.get('content_id')}"
                )
                return result
            else:
                raise Exception(f"Content creation failed: {response.text}")

        except Exception as e:
            logger.error(f"❌ Content creation failed: {e}")
            raise


    async def execute_marketing_campaign(self, content_data: Dict) -> Dict:
        """Execute marketing campaign for created content"""
        logger.info("📢 Starting marketing campaign")

        try:
            # Check marketing agent health
            if not await self.check_agent_health(
                self.config.marketing_agent_url, "Marketing Agent"
            ):
                raise Exception("Marketing Agent is not available")

            # Launch marketing campaign
            response = requests.post(
                f"{self.config.marketing_agent_url}/campaign / launch",
                    json={
                    "content_id": content_data.get("content_id"),
                        "content_type": content_data.get("type"),
                        "title": content_data.get("title"),
                        "description": content_data.get("description"),
                        "channels": ["youtube", "twitter", "newsletter", "seo"],
                        },
                    timeout = 120,
                    )

            if response.status_code == 200:
                result = response.json()
                logger.info(
                    f"✅ Marketing campaign launched: {result.get('campaign_id')}"
                )
                return result
            else:
                raise Exception(f"Marketing campaign failed: {response.text}")

        except Exception as e:
            logger.error(f"❌ Marketing campaign failed: {e}")
            raise


    async def execute_monetization(
        self, content_data: Dict, marketing_data: Dict
    ) -> Dict:
        """Execute monetization workflow"""
        logger.info("💰 Starting monetization workflow")

        try:
            # Check monetization service health
            if not await self.check_agent_health(
                self.config.monetization_url, "Monetization Bundle"
            ):
                raise Exception("Monetization Bundle is not available")

            # Execute monetization
            response = requests.post(
                f"{self.config.monetization_url}/monetize",
                    json={
                    "content_id": content_data.get("content_id"),
                        "transcript": content_data.get("transcript"),
                        "title": content_data.get("title"),
                        "campaign_id": marketing_data.get("campaign_id"),
                        "channels": ["ebook", "merch", "affiliate", "newsletter"],
                        },
                    timeout = 180,
                    )

            if response.status_code == 200:
                result = response.json()
                logger.info(
                    f"✅ Monetization completed: {len(result.get('products', []))} products created"
                )
                return result
            else:
                raise Exception(f"Monetization failed: {response.text}")

        except Exception as e:
            logger.error(f"❌ Monetization failed: {e}")
            raise


    async def update_revenue_tracking(self, monetization_data: Dict) -> Dict:
        """Update revenue tracking with new data"""
        logger.info("📊 Updating revenue tracking")

        try:
            # Check revenue rollup service health
            if not await self.check_agent_health(
                self.config.revenue_rollup_url, "Revenue Rollup"
            ):
                raise Exception("Revenue Rollup service is not available")

            # Update revenue data
            response = requests.post(
                f"{self.config.revenue_rollup_url}/revenue / update",
                    json={
                    "products": monetization_data.get("products", []),
                        "timestamp": datetime.now().isoformat(),
                        "source": "orchestrator",
                        },
                    timeout = 60,
                    )

            if response.status_code == 200:
                result = response.json()
                logger.info(
                    f"✅ Revenue tracking updated: ${result.get('total_revenue', 0):.2f}"
                )
                return result
            else:
                raise Exception(f"Revenue tracking update failed: {response.text}")

        except Exception as e:
            logger.error(f"❌ Revenue tracking update failed: {e}")
            raise


    async def execute_full_workflow(self) -> str:
        """Execute the complete TRAE.AI workflow"""
        workflow_id = f"workflow_{int(time.time())}"

        task = WorkflowTask(
            id = workflow_id,
                name="Full TRAE.AI Workflow",
                agent="orchestrator",
                status="running",
                created_at = datetime.now(),
                )
        self.tasks[workflow_id] = task

        try:
            logger.info(f"🚀 Starting full workflow: {workflow_id}")

            # Step 1: Content Creation
            logger.info("Step 1 / 4: Content Creation")
            content_data = await self.execute_content_creation()

            # Step 2: Marketing Campaign
            logger.info("Step 2 / 4: Marketing Campaign")
            marketing_data = await self.execute_marketing_campaign(content_data)

            # Step 3: Monetization
            logger.info("Step 3 / 4: Monetization")
            monetization_data = await self.execute_monetization(
                content_data, marketing_data
            )

            # Step 4: Revenue Tracking
            logger.info("Step 4 / 4: Revenue Tracking")
            revenue_data = await self.update_revenue_tracking(monetization_data)

            # Complete workflow
            task.status = "completed"
            task.completed_at = datetime.now()
            task.result = {
                "content": content_data,
                    "marketing": marketing_data,
                    "monetization": monetization_data,
                    "revenue": revenue_data,
                    }

            logger.info(f"✅ Full workflow completed: {workflow_id}")
            return workflow_id

        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            logger.error(f"❌ Workflow failed: {workflow_id} - {e}")
            raise


    def schedule_daily_workflows(self):
        """Schedule daily automated workflows"""
        logger.info("📅 Setting up daily workflow schedule")

        # Schedule daily content creation at 9 AM
        schedule.every().day.at("09:00").do(self.run_daily_workflow)

        # Schedule revenue snapshot at 11 PM
        schedule.every().day.at("23:00").do(self.run_revenue_snapshot)


    async def run_daily_workflow(self):
        """Run the daily automated workflow"""
        try:
            logger.info("🌅 Running daily automated workflow")
            await self.execute_full_workflow()
        except Exception as e:
            logger.error(f"❌ Daily workflow failed: {e}")


    async def run_revenue_snapshot(self):
        """Run daily revenue snapshot"""
        try:
            logger.info("📸 Taking daily revenue snapshot")
            response = requests.get(
                f"{self.config.revenue_rollup_url}/revenue / snapshot"
            )
            if response.status_code == 200:
                snapshot = response.json()
                logger.info(f"💰 Daily revenue: ${snapshot.get('total', 0):.2f}")
            else:
                logger.error(f"Failed to get revenue snapshot: {response.text}")
        except Exception as e:
            logger.error(f"❌ Revenue snapshot failed: {e}")


    async def run_scheduler(self):
        """Run the scheduler in the background"""
        while True:
            schedule.run_pending()
            await asyncio.sleep(60)  # Check every minute


    async def start_server(self):
        """Start the orchestrator server"""
        import uvicorn

        logger.info("🎬 Starting TRAE.AI Orchestrator")
        logger.info(f"📊 Mock mode: {self.config.use_mock}")

        # Schedule daily workflows
        self.schedule_daily_workflows()

        # Start scheduler in background
        asyncio.create_task(self.run_scheduler())

        # Start the FastAPI server
        config = uvicorn.Config(
            app = self.app,
                host="0.0.0.0",
                port = 8000,
                log_level = self.config.log_level.lower(),
                )
        server = uvicorn.Server(config)
        await server.serve()


async def main():
    """Main entry point"""
    config = OrchestratorConfig()
    orchestrator = TraeAIOrchestrator(config)
    await orchestrator.start_server()

if __name__ == "__main__":
    asyncio.run(main())
