import asyncio
import logging
import httpx
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

class TryOnService:
    API_KEY = "ff3f99e643452b00c3ded0e5d8d60e5a"
    CREATE_TASK_URL = "https://api.kie.ai/api/v1/jobs/createTask"
    QUERY_TASK_URL = "https://api.kie.ai/api/v1/jobs/recordInfo"
    MODEL = "nano-banana-2"

    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {self.API_KEY}",
            "Content-Type": "application/json"
        }

    async def create_generation_task(
        self, 
        prompt: str, 
        image_urls: List[str], 
        aspect_ratio: str = "auto",
        resolution: str = "1K",
        output_format: str = "jpg"
    ) -> Optional[str]:
        """
        Create a generation task using Nano Banana 2 API.
        Returns taskId if successful, None otherwise.
        """
        payload = {
            "model": self.MODEL,
            "input": {
                "prompt": prompt,
                "image_input": image_urls,
                "aspect_ratio": aspect_ratio,
                "resolution": resolution,
                "output_format": output_format
            }
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    self.CREATE_TASK_URL, 
                    headers=self.headers, 
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                if data.get("code") == 200:
                    return data.get("data", {}).get("taskId")
                else:
                    logger.error(f"API Error: {data.get('msg')}")
                    return None
            except Exception as e:
                logger.error(f"Failed to create task: {e}")
                return None

    async def query_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Query the status of a task.
        Returns the data object from the API response.
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    self.QUERY_TASK_URL, 
                    headers=self.headers, 
                    params={"taskId": task_id}
                )
                response.raise_for_status()
                data = response.json()
                if data.get("code") == 200:
                    return data.get("data", {})
                else:
                    logger.error(f"API Error: {data.get('msg')}")
                    return {"state": "fail", "failMsg": data.get("msg")}
            except Exception as e:
                logger.error(f"Failed to query task status: {e}")
                return {"state": "fail", "failMsg": str(e)}

    async def wait_for_result(self, task_id: str, poll_interval: int = 5, max_attempts: int = 60) -> Optional[List[str]]:
        """
        Wait for task completion and return result URLs.
        """
        import json
        for _ in range(max_attempts):
            status_data = await self.query_task_status(task_id)
            state = status_data.get("state")

            if state == "success":
                result_json_str = status_data.get("resultJson")
                if result_json_str:
                    try:
                        result_data = json.loads(result_json_str)
                        return result_data.get("resultUrls", [])
                    except json.JSONDecodeError:
                        logger.error("Failed to decode resultJson")
                        return None
                return []
            elif state == "fail":
                logger.error(f"Task failed: {status_data.get('failMsg')}")
                return None
            
            await asyncio.sleep(poll_interval)
        
        logger.error("Task timed out")
        return None

try_on_service = TryOnService()
