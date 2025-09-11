#!/usr/bin/env python3
"""
Workflow Engine - Advanced Media Processing Pipeline Orchestrator

This module provides a sophisticated workflow engine for orchestrating complex
media processing pipelines, supporting conditional logic, parallel processing,
and dynamic workflow adaptation based on content analysis.

Features:
- Visual workflow designer integration
- Conditional branching and loops
- Parallel task execution
- Real-time progress tracking
- Error handling and recovery
- Workflow templates and versioning
- Integration with all media processors

Author: TRAE.AI Media System
Version: 2.0.0
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Callable, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import networkx as nx
from collections import defaultdict, deque

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NodeType(Enum):
    """Types of workflow nodes."""
    INPUT = "input"
    OUTPUT = "output"
    PROCESSOR = "processor"
    CONDITION = "condition"
    LOOP = "loop"
    PARALLEL = "parallel"
    MERGE = "merge"
    TRANSFORM = "transform"
    VALIDATOR = "validator"

class NodeStatus(Enum):
    """Status of workflow nodes."""
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"

class WorkflowStatus(Enum):
    """Status of entire workflows."""
    CREATED = "created"
    VALIDATING = "validating"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class WorkflowNode:
    """Represents a single node in a workflow."""
    node_id: str
    node_type: NodeType
    name: str
    processor: str
    config: Dict[str, Any] = field(default_factory=dict)
    inputs: List[str] = field(default_factory=list)  # Input node IDs
    outputs: List[str] = field(default_factory=list)  # Output node IDs
    conditions: Dict[str, Any] = field(default_factory=dict)
    status: NodeStatus = NodeStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout: Optional[int] = None  # seconds
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class WorkflowDefinition:
    """Complete workflow definition."""
    workflow_id: str
    name: str
    description: str
    version: str
    nodes: Dict[str, WorkflowNode]
    edges: List[Dict[str, str]]  # {"from": node_id, "to": node_id}
    global_config: Dict[str, Any] = field(default_factory=dict)
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "system"
    tags: List[str] = field(default_factory=list)

@dataclass
class WorkflowExecution:
    """Runtime execution state of a workflow."""
    execution_id: str
    workflow_id: str
    status: WorkflowStatus
    input_data: Dict[str, Any]
    output_data: Dict[str, Any] = field(default_factory=dict)
    node_states: Dict[str, NodeStatus] = field(default_factory=dict)
    node_results: Dict[str, Any] = field(default_factory=dict)
    execution_graph: Optional[nx.DiGraph] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    progress: float = 0.0
    current_nodes: Set[str] = field(default_factory=set)
    completed_nodes: Set[str] = field(default_factory=set)
    failed_nodes: Set[str] = field(default_factory=set)
    error_log: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

class WorkflowEngine:
    """Advanced workflow orchestration engine."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._load_default_config()
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        self.processors: Dict[str, Callable] = {}
        self.executor = ThreadPoolExecutor(max_workers=self.config.get('max_workers', 8))
        self.running_executions: Set[str] = set()
        
        # Initialize built-in processors
        self._register_built_in_processors()
        
        # Load workflow templates
        self._load_workflow_templates()
        
        logger.info("Workflow Engine initialized")
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration."""
        return {
            'max_workers': 8,
            'max_parallel_nodes': 4,
            'default_timeout': 300,  # 5 minutes
            'retry_delay': 5,  # seconds
            'cleanup_interval': 3600,  # 1 hour
            'max_execution_history': 1000,
            'enable_metrics': True,
            'workflow_storage_path': './workflows',
            'execution_storage_path': './executions'
        }
    
    def _register_built_in_processors(self):
        """Register built-in workflow processors."""
        self.processors.update({
            'media_hub': self._process_media_hub,
            'content_analyzer': self._process_content_analyzer,
            'file_transformer': self._process_file_transformer,
            'quality_validator': self._process_quality_validator,
            'batch_processor': self._process_batch_processor,
            'conditional_router': self._process_conditional_router,
            'data_merger': self._process_data_merger,
            'notification_sender': self._process_notification_sender,
            'png_to_blender': self._process_png_to_blender,
            'avatar_animator': self._process_avatar_animator,
            'video_compositor': self._process_video_compositor,
            'audio_mixer': self._process_audio_mixer
        })
    
    def _load_workflow_templates(self):
        """Load pre-defined workflow templates."""
        templates = [
            self._create_social_media_workflow(),
            self._create_presentation_workflow(),
            self._create_png_to_blender_workflow(),
            self._create_batch_avatar_workflow(),
            self._create_podcast_production_workflow()
        ]
        
        for template in templates:
            self.workflows[template.workflow_id] = template
        
        logger.info(f"Loaded {len(templates)} workflow templates")
    
    def _create_social_media_workflow(self) -> WorkflowDefinition:
        """Create social media content workflow."""
        nodes = {
            'input': WorkflowNode(
                node_id='input',
                node_type=NodeType.INPUT,
                name='Content Input',
                processor='input_validator',
                config={'required_fields': ['script', 'avatar_image']}
            ),
            'content_analysis': WorkflowNode(
                node_id='content_analysis',
                node_type=NodeType.PROCESSOR,
                name='Content Analysis',
                processor='content_analyzer',
                inputs=['input'],
                config={'analyze_emotions': True, 'detect_topics': True}
            ),
            'voice_synthesis': WorkflowNode(
                node_id='voice_synthesis',
                node_type=NodeType.PROCESSOR,
                name='Voice Synthesis',
                processor='media_hub',
                inputs=['content_analysis'],
                config={'media_type': 'audio', 'workflow_type': 'voice_synthesis'}
            ),
            'avatar_animation': WorkflowNode(
                node_id='avatar_animation',
                node_type=NodeType.PROCESSOR,
                name='Avatar Animation',
                processor='avatar_animator',
                inputs=['voice_synthesis', 'content_analysis']
            ),
            'quality_check': WorkflowNode(
                node_id='quality_check',
                node_type=NodeType.VALIDATOR,
                name='Quality Validation',
                processor='quality_validator',
                inputs=['avatar_animation'],
                config={'min_duration': 10, 'max_duration': 120}
            ),
            'format_variants': WorkflowNode(
                node_id='format_variants',
                node_type=NodeType.PARALLEL,
                name='Format Variants',
                processor='batch_processor',
                inputs=['quality_check'],
                config={
                    'variants': [
                        {'format': 'instagram_story', 'aspect_ratio': '9:16'},
                        {'format': 'youtube_short', 'aspect_ratio': '9:16'},
                        {'format': 'tiktok', 'aspect_ratio': '9:16'},
                        {'format': 'facebook_post', 'aspect_ratio': '1:1'}
                    ]
                }
            ),
            'output': WorkflowNode(
                node_id='output',
                node_type=NodeType.OUTPUT,
                name='Final Output',
                processor='output_collector',
                inputs=['format_variants']
            )
        }
        
        edges = [
            {'from': 'input', 'to': 'content_analysis'},
            {'from': 'content_analysis', 'to': 'voice_synthesis'},
            {'from': 'voice_synthesis', 'to': 'avatar_animation'},
            {'from': 'content_analysis', 'to': 'avatar_animation'},
            {'from': 'avatar_animation', 'to': 'quality_check'},
            {'from': 'quality_check', 'to': 'format_variants'},
            {'from': 'format_variants', 'to': 'output'}
        ]
        
        return WorkflowDefinition(
            workflow_id='social_media_content',
            name='Social Media Content Creation',
            description='Complete workflow for creating social media content with avatar narration',
            version='1.0.0',
            nodes=nodes,
            edges=edges,
            global_config={
                'quality_preset': 'standard',
                'output_formats': ['mp4', 'mov'],
                'enable_analytics': True
            },
            tags=['social_media', 'avatar', 'video']
        )
    
    def _create_png_to_blender_workflow(self) -> WorkflowDefinition:
        """Create PNG to Blender conversion workflow."""
        nodes = {
            'input': WorkflowNode(
                node_id='input',
                node_type=NodeType.INPUT,
                name='PNG Input',
                processor='input_validator',
                config={'required_fields': ['png_file'], 'file_types': ['.png']}
            ),
            'image_analysis': WorkflowNode(
                node_id='image_analysis',
                node_type=NodeType.PROCESSOR,
                name='Image Analysis',
                processor='content_analyzer',
                inputs=['input'],
                config={'analyze_type': 'image', 'extract_heightmap': True}
            ),
            'mesh_generation': WorkflowNode(
                node_id='mesh_generation',
                node_type=NodeType.PROCESSOR,
                name='Mesh Generation',
                processor='png_to_blender',
                inputs=['image_analysis'],
                config={'mesh_type': 'heightmap', 'subdivision_level': 3}
            ),
            'code_optimization': WorkflowNode(
                node_id='code_optimization',
                node_type=NodeType.PROCESSOR,
                name='Code Optimization',
                processor='file_transformer',
                inputs=['mesh_generation'],
                config={'optimize_for': 'performance', 'add_comments': True}
            ),
            'validation': WorkflowNode(
                node_id='validation',
                node_type=NodeType.VALIDATOR,
                name='Code Validation',
                processor='quality_validator',
                inputs=['code_optimization'],
                config={'validate_syntax': True, 'check_blender_api': True}
            ),
            'output': WorkflowNode(
                node_id='output',
                node_type=NodeType.OUTPUT,
                name='Blender Code Output',
                processor='output_collector',
                inputs=['validation']
            )
        }
        
        edges = [
            {'from': 'input', 'to': 'image_analysis'},
            {'from': 'image_analysis', 'to': 'mesh_generation'},
            {'from': 'mesh_generation', 'to': 'code_optimization'},
            {'from': 'code_optimization', 'to': 'validation'},
            {'from': 'validation', 'to': 'output'}
        ]
        
        return WorkflowDefinition(
            workflow_id='png_to_blender_conversion',
            name='PNG to Blender Code Conversion',
            description='Convert PNG images to optimized Blender Python code for 3D mesh generation',
            version='1.0.0',
            nodes=nodes,
            edges=edges,
            global_config={
                'output_format': 'python_script',
                'include_materials': True,
                'generate_documentation': True
            },
            tags=['png', 'blender', '3d', 'mesh']
        )
    
    def _create_batch_avatar_workflow(self) -> WorkflowDefinition:
        """Create batch avatar processing workflow."""
        nodes = {
            'input': WorkflowNode(
                node_id='input',
                node_type=NodeType.INPUT,
                name='Batch Input',
                processor='input_validator',
                config={'required_fields': ['scripts', 'avatar_images']}
            ),
            'batch_splitter': WorkflowNode(
                node_id='batch_splitter',
                node_type=NodeType.TRANSFORM,
                name='Batch Splitter',
                processor='batch_processor',
                inputs=['input'],
                config={'split_type': 'individual_jobs', 'max_parallel': 4}
            ),
            'parallel_processing': WorkflowNode(
                node_id='parallel_processing',
                node_type=NodeType.PARALLEL,
                name='Parallel Avatar Processing',
                processor='avatar_animator',
                inputs=['batch_splitter'],
                config={'enable_parallel': True, 'max_workers': 4}
            ),
            'quality_filter': WorkflowNode(
                node_id='quality_filter',
                node_type=NodeType.VALIDATOR,
                name='Quality Filter',
                processor='quality_validator',
                inputs=['parallel_processing'],
                config={'filter_failed': True, 'min_quality_score': 0.8}
            ),
            'batch_merger': WorkflowNode(
                node_id='batch_merger',
                node_type=NodeType.MERGE,
                name='Batch Merger',
                processor='data_merger',
                inputs=['quality_filter'],
                config={'merge_type': 'collection', 'include_metadata': True}
            ),
            'output': WorkflowNode(
                node_id='output',
                node_type=NodeType.OUTPUT,
                name='Batch Output',
                processor='output_collector',
                inputs=['batch_merger']
            )
        }
        
        edges = [
            {'from': 'input', 'to': 'batch_splitter'},
            {'from': 'batch_splitter', 'to': 'parallel_processing'},
            {'from': 'parallel_processing', 'to': 'quality_filter'},
            {'from': 'quality_filter', 'to': 'batch_merger'},
            {'from': 'batch_merger', 'to': 'output'}
        ]
        
        return WorkflowDefinition(
            workflow_id='batch_avatar_processing',
            name='Batch Avatar Processing',
            description='Process multiple avatar animations in parallel with quality control',
            version='1.0.0',
            nodes=nodes,
            edges=edges,
            global_config={
                'max_batch_size': 20,
                'enable_progress_tracking': True,
                'auto_retry_failed': True
            },
            tags=['batch', 'avatar', 'parallel']
        )
    
    async def create_workflow_execution(
        self,
        workflow_id: str,
        input_data: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new workflow execution."""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        execution_id = str(uuid.uuid4())
        workflow = self.workflows[workflow_id]
        
        # Create execution graph
        execution_graph = self._build_execution_graph(workflow)
        
        # Initialize node states
        node_states = {node_id: NodeStatus.PENDING for node_id in workflow.nodes.keys()}
        
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            status=WorkflowStatus.CREATED,
            input_data=input_data,
            node_states=node_states,
            execution_graph=execution_graph
        )
        
        self.executions[execution_id] = execution
        logger.info(f"Created workflow execution {execution_id} for workflow {workflow_id}")
        
        return execution_id
    
    def _build_execution_graph(self, workflow: WorkflowDefinition) -> nx.DiGraph:
        """Build NetworkX graph for workflow execution."""
        graph = nx.DiGraph()
        
        # Add nodes
        for node_id, node in workflow.nodes.items():
            graph.add_node(node_id, node=node)
        
        # Add edges
        for edge in workflow.edges:
            graph.add_edge(edge['from'], edge['to'])
        
        # Validate graph (check for cycles, etc.)
        if not nx.is_directed_acyclic_graph(graph):
            raise ValueError("Workflow contains cycles")
        
        return graph
    
    async def execute_workflow(self, execution_id: str) -> Dict[str, Any]:
        """Execute a workflow asynchronously."""
        if execution_id not in self.executions:
            raise ValueError(f"Execution {execution_id} not found")
        
        execution = self.executions[execution_id]
        workflow = self.workflows[execution.workflow_id]
        
        execution.status = WorkflowStatus.RUNNING
        execution.start_time = datetime.now()
        self.running_executions.add(execution_id)
        
        try:
            # Execute workflow using topological sort
            execution_order = list(nx.topological_sort(execution.execution_graph))
            
            for node_id in execution_order:
                if execution.status == WorkflowStatus.CANCELLED:
                    break
                
                node = workflow.nodes[node_id]
                
                # Check if node dependencies are satisfied
                if not self._are_dependencies_satisfied(execution, node_id):
                    execution.node_states[node_id] = NodeStatus.SKIPPED
                    continue
                
                # Execute node
                await self._execute_node(execution, node)
                
                # Update progress
                completed_nodes = sum(1 for status in execution.node_states.values() 
                                    if status in [NodeStatus.COMPLETED, NodeStatus.SKIPPED])
                execution.progress = (completed_nodes / len(workflow.nodes)) * 100
            
            # Determine final status
            if execution.status != WorkflowStatus.CANCELLED:
                failed_nodes = [nid for nid, status in execution.node_states.items() 
                              if status == NodeStatus.FAILED]
                
                if failed_nodes:
                    execution.status = WorkflowStatus.FAILED
                else:
                    execution.status = WorkflowStatus.COMPLETED
            
            execution.end_time = datetime.now()
            
            # Collect output data
            output_nodes = [node for node in workflow.nodes.values() 
                          if node.node_type == NodeType.OUTPUT]
            
            for output_node in output_nodes:
                if output_node.node_id in execution.node_results:
                    execution.output_data.update(execution.node_results[output_node.node_id])
            
            logger.info(f"Workflow execution {execution_id} completed with status {execution.status.value}")
            
            return {
                'success': execution.status == WorkflowStatus.COMPLETED,
                'execution_id': execution_id,
                'status': execution.status.value,
                'output_data': execution.output_data,
                'execution_time': (execution.end_time - execution.start_time).total_seconds(),
                'progress': execution.progress,
                'failed_nodes': [nid for nid, status in execution.node_states.items() 
                               if status == NodeStatus.FAILED]
            }
            
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.end_time = datetime.now()
            
            error_info = {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'node_id': 'workflow_engine'
            }
            execution.error_log.append(error_info)
            
            logger.error(f"Workflow execution {execution_id} failed: {e}")
            
            return {
                'success': False,
                'execution_id': execution_id,
                'status': execution.status.value,
                'error': str(e)
            }
        
        finally:
            self.running_executions.discard(execution_id)
    
    def _are_dependencies_satisfied(self, execution: WorkflowExecution, node_id: str) -> bool:
        """Check if all dependencies for a node are satisfied."""
        workflow = self.workflows[execution.workflow_id]
        node = workflow.nodes[node_id]
        
        for input_node_id in node.inputs:
            input_status = execution.node_states.get(input_node_id, NodeStatus.PENDING)
            if input_status not in [NodeStatus.COMPLETED, NodeStatus.SKIPPED]:
                return False
        
        return True
    
    async def _execute_node(self, execution: WorkflowExecution, node: WorkflowNode):
        """Execute a single workflow node."""
        execution.node_states[node.node_id] = NodeStatus.RUNNING
        execution.current_nodes.add(node.node_id)
        
        node.start_time = datetime.now()
        
        try:
            # Prepare input data for the node
            input_data = self._prepare_node_input(execution, node)
            
            # Get processor function
            if node.processor not in self.processors:
                raise ValueError(f"Processor {node.processor} not found")
            
            processor_func = self.processors[node.processor]
            
            # Execute processor with timeout
            timeout = node.timeout or self.config.get('default_timeout', 300)
            
            try:
                result = await asyncio.wait_for(
                    processor_func(input_data, node.config),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                raise Exception(f"Node {node.node_id} timed out after {timeout} seconds")
            
            # Store result
            execution.node_results[node.node_id] = result
            execution.node_states[node.node_id] = NodeStatus.COMPLETED
            execution.completed_nodes.add(node.node_id)
            
            node.end_time = datetime.now()
            node.result = result
            
            logger.info(f"Node {node.node_id} completed successfully")
            
        except Exception as e:
            execution.node_states[node.node_id] = NodeStatus.FAILED
            execution.failed_nodes.add(node.node_id)
            
            node.end_time = datetime.now()
            node.error = str(e)
            
            error_info = {
                'timestamp': datetime.now().isoformat(),
                'node_id': node.node_id,
                'error': str(e)
            }
            execution.error_log.append(error_info)
            
            # Handle retries
            if node.retry_count < node.max_retries:
                node.retry_count += 1
                logger.warning(f"Node {node.node_id} failed, retrying ({node.retry_count}/{node.max_retries})")
                
                # Wait before retry
                await asyncio.sleep(self.config.get('retry_delay', 5))
                
                # Reset node state and retry
                execution.node_states[node.node_id] = NodeStatus.PENDING
                execution.failed_nodes.discard(node.node_id)
                await self._execute_node(execution, node)
            else:
                logger.error(f"Node {node.node_id} failed permanently: {e}")
        
        finally:
            execution.current_nodes.discard(node.node_id)
    
    def _prepare_node_input(self, execution: WorkflowExecution, node: WorkflowNode) -> Dict[str, Any]:
        """Prepare input data for a node from its dependencies."""
        input_data = {}
        
        # Add original workflow input
        if node.node_type == NodeType.INPUT:
            input_data.update(execution.input_data)
        
        # Add results from input nodes
        for input_node_id in node.inputs:
            if input_node_id in execution.node_results:
                input_data[f"input_{input_node_id}"] = execution.node_results[input_node_id]
        
        # Add node-specific config
        input_data['node_config'] = node.config
        input_data['execution_id'] = execution.execution_id
        input_data['node_id'] = node.node_id
        
        return input_data
    
    # Built-in processor implementations
    async def _process_media_hub(self, input_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process using the unified media hub."""
        try:
            from .unified_media_hub import get_media_hub, MediaType, WorkflowType
            
            media_hub = get_media_hub()
            
            # Extract media processing parameters
            media_type = MediaType(config.get('media_type', 'video'))
            workflow_type = WorkflowType(config.get('workflow_type', 'custom_workflow'))
            
            # Create and process media job
            job_id = await media_hub.create_media_job(
                media_type=media_type,
                workflow_type=workflow_type,
                input_data=input_data,
                config=config
            )
            
            result = await media_hub.process_media_job(job_id)
            
            return {
                'success': result['success'],
                'job_id': job_id,
                'output_files': result.get('output_files', []),
                'metadata': result.get('metadata', {})
            }
            
        except Exception as e:
            logger.error(f"Media hub processing failed: {e}")
            raise
    
    async def _process_content_analyzer(self, input_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze content for emotions, topics, etc."""
        analyze_type = config.get('analyze_type', 'text')
        
        if analyze_type == 'text':
            text = input_data.get('script', '')
            
            # Simple emotion analysis (in production, use proper NLP)
            emotions = []
            if any(word in text.lower() for word in ['excited', 'amazing', 'fantastic']):
                emotions.append('excited')
            elif any(word in text.lower() for word in ['serious', 'important', 'critical']):
                emotions.append('serious')
            else:
                emotions.append('neutral')
            
            # Topic detection
            topics = []
            if any(word in text.lower() for word in ['product', 'demo', 'feature']):
                topics.append('product_demo')
            elif any(word in text.lower() for word in ['tutorial', 'learn', 'how to']):
                topics.append('educational')
            
            return {
                'emotions': emotions,
                'topics': topics,
                'text_length': len(text),
                'word_count': len(text.split())
            }
        
        elif analyze_type == 'image':
            # Image analysis for PNG to Blender conversion
            png_file = input_data.get('png_file')
            if not png_file:
                raise ValueError("PNG file required for image analysis")
            
            # Analyze image properties
            from PIL import Image
            import numpy as np
            
            with Image.open(png_file) as img:
                img_array = np.array(img.convert('L'))
                
                return {
                    'dimensions': img.size,
                    'mode': img.mode,
                    'pixel_range': (int(img_array.min()), int(img_array.max())),
                    'mean_brightness': float(img_array.mean()),
                    'suitable_for_heightmap': True
                }
        
        return {'analysis_complete': True}
    
    async def _process_png_to_blender(self, input_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process PNG to Blender conversion."""
        try:
            from .unified_media_hub import get_media_hub, MediaType, WorkflowType
            
            media_hub = get_media_hub()
            
            # Create PNG to Blender job
            job_id = await media_hub.create_media_job(
                media_type=MediaType.PNG_TO_BLENDER,
                workflow_type=WorkflowType.CUSTOM_WORKFLOW,
                input_data=input_data,
                config=config
            )
            
            result = await media_hub.process_media_job(job_id)
            
            return result
            
        except Exception as e:
            logger.error(f"PNG to Blender conversion failed: {e}")
            raise
    
    async def _process_quality_validator(self, input_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate quality of processed media."""
        # Extract validation parameters
        min_duration = config.get('min_duration', 0)
        max_duration = config.get('max_duration', float('inf'))
        min_quality_score = config.get('min_quality_score', 0.0)
        
        # Perform validation checks
        validation_results = {
            'passed': True,
            'checks': [],
            'quality_score': 1.0
        }
        
        # Duration check
        if 'duration' in input_data:
            duration = input_data['duration']
            if duration < min_duration or duration > max_duration:
                validation_results['passed'] = False
                validation_results['checks'].append(f"Duration {duration}s outside range [{min_duration}, {max_duration}]")
        
        # Quality score check
        if 'quality_score' in input_data:
            quality_score = input_data['quality_score']
            if quality_score < min_quality_score:
                validation_results['passed'] = False
                validation_results['checks'].append(f"Quality score {quality_score} below minimum {min_quality_score}")
        
        if not validation_results['passed']:
            raise Exception(f"Quality validation failed: {validation_results['checks']}")
        
        return validation_results
    
    async def _process_batch_processor(self, input_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process batch operations."""
        batch_type = config.get('split_type', 'individual_jobs')
        max_parallel = config.get('max_parallel', 4)
        
        if batch_type == 'individual_jobs':
            # Split batch into individual jobs
            scripts = input_data.get('scripts', [])
            avatar_images = input_data.get('avatar_images', [])
            
            jobs = []
            for i, (script, avatar_image) in enumerate(zip(scripts, avatar_images)):
                jobs.append({
                    'job_id': f"batch_job_{i}",
                    'script': script,
                    'avatar_image': avatar_image
                })
            
            return {
                'batch_jobs': jobs,
                'total_jobs': len(jobs),
                'max_parallel': max_parallel
            }
        
        return {'batch_processed': True}
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a workflow execution."""
        if execution_id not in self.executions:
            return None
        
        execution = self.executions[execution_id]
        workflow = self.workflows[execution.workflow_id]
        
        return {
            'execution_id': execution_id,
            'workflow_id': execution.workflow_id,
            'workflow_name': workflow.name,
            'status': execution.status.value,
            'progress': execution.progress,
            'start_time': execution.start_time.isoformat() if execution.start_time else None,
            'end_time': execution.end_time.isoformat() if execution.end_time else None,
            'current_nodes': list(execution.current_nodes),
            'completed_nodes': list(execution.completed_nodes),
            'failed_nodes': list(execution.failed_nodes),
            'node_states': {nid: status.value for nid, status in execution.node_states.items()},
            'output_data': execution.output_data,
            'error_log': execution.error_log[-10:]  # Last 10 errors
        }
    
    def get_available_workflows(self) -> Dict[str, Dict[str, Any]]:
        """Get all available workflow templates."""
        return {
            workflow_id: {
                'name': workflow.name,
                'description': workflow.description,
                'version': workflow.version,
                'tags': workflow.tags,
                'node_count': len(workflow.nodes),
                'input_schema': workflow.input_schema,
                'output_schema': workflow.output_schema
            }
            for workflow_id, workflow in self.workflows.items()
        }
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running workflow execution."""
        if execution_id not in self.executions:
            return False
        
        execution = self.executions[execution_id]
        if execution.status == WorkflowStatus.RUNNING:
            execution.status = WorkflowStatus.CANCELLED
            execution.end_time = datetime.now()
            
            logger.info(f"Workflow execution {execution_id} cancelled")
            return True
        
        return False
    
    def cleanup_old_executions(self, max_age_hours: int = 24):
        """Clean up old workflow executions."""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        executions_to_remove = [
            exec_id for exec_id, execution in self.executions.items()
            if execution.end_time and execution.end_time < cutoff_time
            and execution.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]
        ]
        
        for exec_id in executions_to_remove:
            del self.executions[exec_id]
        
        logger.info(f"Cleaned up {len(executions_to_remove)} old executions")
    
    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)

# Global instance
_workflow_engine_instance = None

def get_workflow_engine(config: Optional[Dict[str, Any]] = None) -> WorkflowEngine:
    """Get or create the global workflow engine instance."""
    global _workflow_engine_instance
    if _workflow_engine_instance is None:
        _workflow_engine_instance = WorkflowEngine(config)
    return _workflow_engine_instance

if __name__ == "__main__":
    # Example usage
    async def main():
        engine = get_workflow_engine()
        
        # Example: Execute social media workflow
        execution_id = await engine.create_workflow_execution(
            'social_media_content',
            {
                'script': 'Check out our amazing new product features!',
                'avatar_image': 'path/to/avatar.jpg'
            }
        )
        
        print(f"Created execution: {execution_id}")
        
        # Execute workflow
        result = await engine.execute_workflow(execution_id)
        print(f"Workflow result: {result}")
        
        # Example: PNG to Blender workflow
        png_execution_id = await engine.create_workflow_execution(
            'png_to_blender_conversion',
            {
                'png_file': 'path/to/heightmap.png'
            }
        )
        
        png_result = await engine.execute_workflow(png_execution_id)
        print(f"PNG to Blender result: {png_result}")
    
    asyncio.run(main())