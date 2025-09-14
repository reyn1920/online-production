#!/usr / bin / env python3
"""
Creative Studio Integration
Integrates local creative studio components based on Apple Silicon architecture:
- Ollama LLM Engine for local language models
- ComfyUI Visual Engine for image / video generation
- Linly Talker for AI avatar generation
- Cloud software integration (Lingo Blaster, Captionizer)

Based on research findings and paste_content.txt architecture.
"""

import asyncio
import json
import logging
import os
import subprocess
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import requests
import websocket

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StudioComponent(Enum):
    """Available creative studio components"""

    OLLAMA_LLM = "ollama_llm"
    COMFYUI_VISUAL = "comfyui_visual"
    LINLY_TALKER = "linly_talker"
    LINGO_BLASTER = "lingo_blaster"
    CAPTIONIZER = "captionizer"


@dataclass
class OllamaConfig:
    """Configuration for Ollama LLM Engine"""

    base_url: str = "http://localhost:11434"
    model: str = "llama3.2"  # Optimized for Apple Silicon
    temperature: float = 0.7
    max_tokens: int = 2048
    stream: bool = False


@dataclass
class ComfyUIConfig:
    """Configuration for ComfyUI Visual Engine"""

    base_url: str = "http://localhost:8188"
    workflow_path: str = "/workflows"
    output_path: str = "/output"
    use_mps: bool = True  # Apple Silicon Metal Performance Shaders


@dataclass
class LinlyTalkerConfig:
    """Configuration for Linly Talker AI Avatar"""

    base_url: str = "http://localhost:7860"
    model_path: str = "/models / linly_talker"
    voice_clone: bool = True
    multi_modal: bool = True


@dataclass
class CloudSoftwareConfig:
    """Configuration for cloud - based software integration"""

    lingo_blaster_api: Optional[str] = None
    captionizer_api: Optional[str] = None
    youtube_api_key: Optional[str] = None
    translation_languages: List[str] = field(default_factory=lambda: ["en", "es", "fr", "de", "zh"])


class OllamaLLMEngine:
    """Local LLM Engine using Ollama for Apple Silicon optimization"""

    def __init__(self, config: OllamaConfig):
        self.config = config
        self.session = requests.Session()

    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text using local Ollama model"""
        try:
            # Prepare the request payload
            payload = {
                "model": self.config.model,
                "prompt": prompt,
                "stream": self.config.stream,
                "options": {
                    "temperature": self.config.temperature,
                    "num_predict": self.config.max_tokens,
                },
            }

            if system_prompt:
                payload["system"] = system_prompt

            # Make API request to Ollama
            response = self.session.post(
                f"{self.config.base_url}/api / generate", json=payload, timeout=60
            )

            if response.status_code == 200:
                if self.config.stream:
                    # Handle streaming response
                    full_response = ""
                    for line in response.text.splitlines():
                        if line.strip():
                            data = json.loads(line)
                            full_response += data.get("response", "")
                    return full_response
                else:
                    # Handle single response
                    data = response.json()
                    return data.get("response", "")
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return ""

        except Exception as e:
            logger.error(f"Error generating text with Ollama: {e}")
            return ""

    async def chat_completion(self, messages: List[Dict[str, str]]) -> str:
        """Chat completion using Ollama chat API"""
        try:
            payload = {
                "model": self.config.model,
                "messages": messages,
                "stream": False,
            }

            response = self.session.post(
                f"{self.config.base_url}/api / chat", json=payload, timeout=60
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("message", {}).get("content", "")
            else:
                logger.error(f"Ollama chat API error: {response.status_code}")
                return ""

        except Exception as e:
            logger.error(f"Error in chat completion: {e}")
            return ""

    def list_models(self) -> List[str]:
        """List available Ollama models"""
        try:
            response = self.session.get(f"{self.config.base_url}/api / tags")
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
            return []
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []


class ComfyUIVisualEngine:
    """Visual Engine using ComfyUI for Apple Silicon MPS optimization"""

    def __init__(self, config: ComfyUIConfig):
        self.config = config
        self.client_id = str(uuid.uuid4())

    async def execute_workflow(
        self,
        workflow_json: Dict[str, Any],
        custom_inputs: Optional[Dict[str, Any]] = None,
    ) -> List[bytes]:
        """Execute ComfyUI workflow and return generated images"""
        try:
            # Apply custom inputs to workflow
            if custom_inputs:
                workflow_json = self._apply_custom_inputs(workflow_json, custom_inputs)

            # Queue the workflow
            prompt_id = await self._queue_prompt(workflow_json)
            if not prompt_id:
                return []

            # Monitor execution via WebSocket
            await self._monitor_execution(prompt_id)

            # Retrieve generated images
            return await self._get_images(prompt_id)

        except Exception as e:
            logger.error(f"Error executing ComfyUI workflow: {e}")
            return []

    async def _queue_prompt(self, workflow: Dict[str, Any]) -> Optional[str]:
        """Queue workflow for execution"""
        try:
            payload = {"prompt": workflow, "client_id": self.client_id}

            response = requests.post(f"{self.config.base_url}/prompt", json=payload, timeout=30)

            if response.status_code == 200:
                data = response.json()
                return data.get("prompt_id")
            return None

        except Exception as e:
            logger.error(f"Error queuing prompt: {e}")
            return None

    async def _monitor_execution(self, prompt_id: str) -> bool:
        """Monitor workflow execution via WebSocket"""
        try:
            ws_url = (
                f"ws://{self.config.base_url.replace('http://', '')}/ws?clientId={self.client_id}"
            )
            ws = websocket.WebSocket()
            ws.connect(ws_url)

            while True:
                message = ws.recv()
                if isinstance(message, str):
                    data = json.loads(message)
                    if data.get("type") == "executing":
                        exec_data = data.get("data", {})
                        if (
                            exec_data.get("node") is None
                            and exec_data.get("prompt_id") == prompt_id
                        ):
                            ws.close()
                            return True

        except Exception as e:
            logger.error(f"Error monitoring execution: {e}")
            return False

    async def _get_images(self, prompt_id: str) -> List[bytes]:
        """Retrieve generated images from ComfyUI"""
        try:
            # Get execution history
            response = requests.get(f"{self.config.base_url}/history/{prompt_id}")
            if response.status_code != 200:
                return []

            history = response.json().get(prompt_id, {})
            outputs = history.get("outputs", {})

            images = []
            for node_id, node_output in outputs.items():
                if "images" in node_output:
                    for image_info in node_output["images"]:
                        image_data = self._download_image(
                            image_info["filename"],
                            image_info.get("subfolder", ""),
                            image_info.get("type", "output"),
                        )
                        if image_data:
                            images.append(image_data)

            return images

        except Exception as e:
            logger.error(f"Error retrieving images: {e}")
            return []

    def _download_image(self, filename: str, subfolder: str, folder_type: str) -> Optional[bytes]:
        """Download image from ComfyUI"""
        try:
            params = {"filename": filename, "subfolder": subfolder, "type": folder_type}

            url = f"{self.config.base_url}/view?{urlencode(params)}"
            response = requests.get(url)

            if response.status_code == 200:
                return response.content
            return None

        except Exception as e:
            logger.error(f"Error downloading image: {e}")
            return None

    def _apply_custom_inputs(
        self, workflow: Dict[str, Any], custom_inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply custom inputs to workflow JSON"""
        # Deep copy workflow to avoid modifying original

        import copy

        modified_workflow = copy.deepcopy(workflow)

        # Apply custom inputs based on node IDs and input names
        for input_key, input_value in custom_inputs.items():
            # Parse input key format: "node_id - input_name"
            if "-" in input_key:
                node_id, input_name = input_key.split("-", 1)
                if node_id in modified_workflow:
                    if "inputs" not in modified_workflow[node_id]:
                        modified_workflow[node_id]["inputs"] = {}
                    modified_workflow[node_id]["inputs"][input_name] = input_value

        return modified_workflow


class LinlyTalkerEngine:
    """AI Avatar Engine using Linly Talker for talking head synthesis"""

    def __init__(self, config: LinlyTalkerConfig):
        self.config = config

    async def generate_avatar_video(
        self, text: str, reference_image: bytes, voice_sample: Optional[bytes] = None
    ) -> Optional[bytes]:
        """Generate talking avatar video from text and reference image"""
        try:
            # Prepare multipart form data
            files = {"reference_image": ("reference.jpg", reference_image, "image / jpeg")}

            data = {
                "text": text,
                "voice_clone": self.config.voice_clone,
                "multi_modal": self.config.multi_modal,
            }

            if voice_sample and self.config.voice_clone:
                files["voice_sample"] = ("voice.wav", voice_sample, "audio / wav")

            # Make request to Linly Talker API
            response = requests.post(
                f"{self.config.base_url}/api / generate",
                files=files,
                data=data,
                timeout=120,
            )

            if response.status_code == 200:
                return response.content
            else:
                logger.error(f"Linly Talker API error: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error generating avatar video: {e}")
            return None

    async def clone_voice(self, voice_sample: bytes, text: str) -> Optional[bytes]:
        """Clone voice from sample and generate speech"""
        try:
            files = {"voice_sample": ("sample.wav", voice_sample, "audio / wav")}

            data = {"text": text, "clone_voice": True}

            response = requests.post(
                f"{self.config.base_url}/api / voice_clone",
                files=files,
                data=data,
                timeout=60,
            )

            if response.status_code == 200:
                return response.content
            return None

        except Exception as e:
            logger.error(f"Error cloning voice: {e}")
            return None


class CloudSoftwareIntegration:
    """Integration with cloud - based software tools"""

    def __init__(self, config: CloudSoftwareConfig):
        self.config = config

    async def translate_video_content(
        self, video_url: str, target_languages: List[str]
    ) -> Dict[str, Any]:
        """Translate video content using Lingo Blaster API"""
        try:
            if not self.config.lingo_blaster_api:
                logger.warning("Lingo Blaster API not configured")
                return {}

            payload = {
                "video_url": video_url,
                "target_languages": target_languages,
                "auto_rank": True,
                "use_youtube_api": True,
            }

            headers = {
                "Authorization": f"Bearer {self.config.lingo_blaster_api}",
                "Content - Type": "application / json",
            }

            response = requests.post(
                "https://api.lingoblaster.com / v1 / translate",
                json=payload,
                headers=headers,
                timeout=300,
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Lingo Blaster API error: {response.status_code}")
                return {}

        except Exception as e:
            logger.error(f"Error translating video content: {e}")
            return {}

    async def generate_captions(self, video_file: bytes) -> Dict[str, Any]:
        """Generate captions using Captionizer API"""
        try:
            if not self.config.captionizer_api:
                logger.warning("Captionizer API not configured")
                return {}

            files = {"video": ("video.mp4", video_file, "video / mp4")}

            data = {
                "auto_translate": True,
                "languages": ",".join(self.config.translation_languages),
                "style": "modern",
            }

            headers = {"Authorization": f"Bearer {self.config.captionizer_api}"}

            response = requests.post(
                "https://api.captionizer.com / v1 / generate",
                files=files,
                data=data,
                headers=headers,
                timeout=300,
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Captionizer API error: {response.status_code}")
                return {}

        except Exception as e:
            logger.error(f"Error generating captions: {e}")
            return {}


class CreativeStudioOrchestrator:
    """Main orchestrator for the creative studio integration"""

    def __init__(self):
        # Initialize configurations
        self.ollama_config = OllamaConfig()
        self.comfyui_config = ComfyUIConfig()
        self.linly_config = LinlyTalkerConfig()
        self.cloud_config = CloudSoftwareConfig()

        # Initialize engines
        self.llm_engine = OllamaLLMEngine(self.ollama_config)
        self.visual_engine = ComfyUIVisualEngine(self.comfyui_config)
        self.avatar_engine = LinlyTalkerEngine(self.linly_config)
        self.cloud_integration = CloudSoftwareIntegration(self.cloud_config)

        logger.info("Creative Studio Orchestrator initialized")

    async def health_check(self) -> Dict[str, bool]:
        """Check health status of all components"""
        status = {}

        # Check Ollama
        try:
            response = requests.get(f"{self.ollama_config.base_url}/api / tags", timeout=5)
            status["ollama"] = response.status_code == 200
        except Exception:
            status["ollama"] = False

        # Check ComfyUI
        try:
            response = requests.get(f"{self.comfyui_config.base_url}/system_stats", timeout=5)
            status["comfyui"] = response.status_code == 200
        except Exception:
            status["comfyui"] = False

        # Check Linly Talker
        try:
            response = requests.get(f"{self.linly_config.base_url}/api / health", timeout=5)
            status["linly_talker"] = response.status_code == 200
        except Exception:
            status["linly_talker"] = False

        return status

    async def create_complete_media_workflow(
        self,
        prompt: str,
        reference_image: Optional[bytes] = None,
        voice_sample: Optional[bytes] = None,
    ) -> Dict[str, Any]:
        """Create a complete media workflow combining all engines"""
        try:
            results = {}

            # Step 1: Generate enhanced prompt using LLM
            enhanced_prompt = await self.llm_engine.generate_text(
                f"Enhance this creative prompt for visual generation: {prompt}",
                "You are a creative director. Enhance prompts for visual AI generation.",
            )
            results["enhanced_prompt"] = enhanced_prompt

            # Step 2: Generate visual content using ComfyUI
            if enhanced_prompt:
                # Load a basic text - to - image workflow
                workflow = self._load_default_workflow()
                custom_inputs = {
                    "6 - text": enhanced_prompt,  # Assuming node 6 is the text prompt
                    "3 - seed": 42,  # Fixed seed for reproducibility
                }

                images = await self.visual_engine.execute_workflow(workflow, custom_inputs)
                results["generated_images"] = len(images)

                # Step 3: Generate avatar video if reference image provided
                if reference_image and images:
                    avatar_video = await self.avatar_engine.generate_avatar_video(
                        prompt, reference_image, voice_sample
                    )
                    results["avatar_video"] = avatar_video is not None

            # Step 4: Generate captions and translations
            if "avatar_video" in results and results["avatar_video"]:
                # This would be the actual video bytes in a real implementation
                captions = await self.cloud_integration.generate_captions(b"dummy_video")
                results["captions_generated"] = bool(captions)

            return results

        except Exception as e:
            logger.error(f"Error in complete media workflow: {e}")
            return {"error": str(e)}

    def _load_default_workflow(self) -> Dict[str, Any]:
        """Load a default ComfyUI workflow for text - to - image generation"""
        # This would typically load from a JSON file
        # For now, return a basic structure
        return {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "cfg": 8,
                    "denoise": 1,
                    "seed": 42,
                    "steps": 20,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                },
            },
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "sd_xl_base_1.0.safetensors"},
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": "placeholder prompt"},
            },
        }

    async def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        info = {
            "platform": "Apple Silicon",
            "components": {
                "ollama": {
                    "models": self.llm_engine.list_models(),
                    "config": self.ollama_config.__dict__,
                },
                "comfyui": {"config": self.comfyui_config.__dict__},
                "linly_talker": {"config": self.linly_config.__dict__},
                "cloud_software": {
                    "configured": bool(
                        self.cloud_config.lingo_blaster_api or self.cloud_config.captionizer_api
                    )
                },
            },
            "health": await self.health_check(),
        }

        return info


# Example usage and testing
if __name__ == "__main__":

    async def main():
        orchestrator = CreativeStudioOrchestrator()

        # Health check
        health = await orchestrator.health_check()
        print(f"System Health: {health}")

        # System info
        info = await orchestrator.get_system_info()
        print(f"System Info: {json.dumps(info, indent = 2)}")

        # Test workflow (if components are running)
        if health.get("ollama", False):
            result = await orchestrator.create_complete_media_workflow(
                "Create a futuristic cityscape with flying cars"
            )
            print(f"Workflow Result: {result}")

    asyncio.run(main())
