#!/usr/bin/env python3
"""
SAM Opportunity Analyzer Agent
Specialized AutoGen agent for analyzing SAM.gov opportunities, 
storing them in database, and coordinating with other agents
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Database and API imports
from database_manager import DatabaseManager, DatabaseUtils
from sam_document_access_v2 import SAMDocumentAccessManager
from autogen_agents import SynthesisAgent, DocumentAnalysisAgent, ProposalAgent

# AutoGen imports
try:
    from autogen.agentchat.assistant_agent import AssistantAgent
    from autogen.agentchat.user_proxy_agent import UserProxyAgent
    from autogen.agentchat.groupchat import GroupChat, GroupChatManager
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    AssistantAgent = None
    UserProxyAgent = None
    GroupChat = None
    GroupChatManager = None

logger = logging.getLogger(__name__)

class AnalysisStatus(Enum):
    """Analysis status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CACHED = "cached"

@dataclass
class OpportunityAnalysisResult:
    """Structured result for opportunity analysis"""
    opportunity_id: str
    status: AnalysisStatus
    analysis_data: Dict[str, Any]
    timestamp: datetime
    confidence_score: float
    risk_level: str
    priority_score: int
    recommendations: List[str]
    error_message: Optional[str] = None

class SAMOpportunityAnalyzerAgent:
    """
    Specialized AutoGen agent for SAM.gov opportunity analysis
    
    This agent:
    1. Fetches opportunities from SAM.gov API
    2. Analyzes opportunities using AI
    3. Stores results in database
    4. Coordinates with other agents
    5. Provides intelligent caching and rate limiting
    """
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.sam_api = SAMDocumentAccessManager()
        self.synthesis_agent = SynthesisAgent()
        self.doc_agent = DocumentAnalysisAgent()
        self.proposal_agent = ProposalAgent()
        
        # AutoGen configuration
        self.llm_config = self._get_llm_config()
        self.autogen_agent = self._create_autogen_agent()
        
        # Analysis cache
        self.analysis_cache = {}
        self.cache_ttl = int(os.getenv('CACHE_TTL', '3600'))  # 1 hour default
        
        logger.info("SAM Opportunity Analyzer Agent initialized")
    
    def _get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration for AutoGen"""
        use_ollama = os.getenv("USE_OLLAMA", "true").lower() == "true"
        
        if use_ollama:
            ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
            ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")
            config_list = [{
                "model": ollama_model, 
                "base_url": f"{ollama_url}/v1", 
                "api_key": "ollama"
            }]
        else:
            config_list = [{
                "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"), 
                "api_key": os.getenv("OPENAI_API_KEY")
            }]
        
        return {
            "config_list": config_list, 
            "temperature": 0.3, 
            "timeout": 120
        }
    
    def _create_autogen_agent(self) -> Optional[AssistantAgent]:
        """Create AutoGen assistant agent"""
        if not AUTOGEN_AVAILABLE:
            return None
        
        try:
            return AssistantAgent(
                name="SAMOpportunityAnalyzer",
                llm_config=self.llm_config,
                system_message="""Sen bir SAM.gov fırsat analiz uzmanısın. 
                Fırsatları detaylı analiz eder, veritabanına kaydeder ve diğer ajanlara gönderirsin.
                
                Görevlerin:
                1. SAM.gov fırsatlarını analiz et
                2. Analiz sonuçlarını veritabanına kaydet
                3. Diğer ajanlara analiz sonuçlarını gönder
                4. Cache yönetimi yap
                5. Rate limiting uygula
                
                Türkçe yanıt ver ve detaylı analiz yap."""
            )
        except Exception as e:
            logger.error(f"AutoGen agent creation failed: {e}")
            return None
    
    async def analyze_opportunity(self, opportunity_id: str, force_refresh: bool = False) -> OpportunityAnalysisResult:
        """
        Analyze a single opportunity
        
        Args:
            opportunity_id: SAM.gov opportunity ID
            force_refresh: Force refresh even if cached data exists
            
        Returns:
            OpportunityAnalysisResult with analysis data
        """
        try:
            logger.info(f"Starting analysis for opportunity: {opportunity_id}")
            
            # Check cache first
            if not force_refresh:
                cached_result = self._get_cached_analysis(opportunity_id)
                if cached_result:
                    logger.info(f"Using cached analysis for: {opportunity_id}")
                    return cached_result
            
            # Get opportunity data
            opportunity_data = await self._fetch_opportunity_data(opportunity_id)
            if not opportunity_data:
                return OpportunityAnalysisResult(
                    opportunity_id=opportunity_id,
                    status=AnalysisStatus.FAILED,
                    analysis_data={},
                    timestamp=datetime.now(),
                    confidence_score=0.0,
                    risk_level="unknown",
                    priority_score=0,
                    recommendations=[],
                    error_message="Opportunity data not found"
                )
            
            # Perform comprehensive analysis
            analysis_data = await self._perform_comprehensive_analysis(opportunity_data)
            
            # Store in database
            await self._store_analysis_result(opportunity_id, analysis_data)
            
            # Create result object
            result = OpportunityAnalysisResult(
                opportunity_id=opportunity_id,
                status=AnalysisStatus.COMPLETED,
                analysis_data=analysis_data,
                timestamp=datetime.now(),
                confidence_score=analysis_data.get('confidence_score', 0.0),
                risk_level=analysis_data.get('risk_level', 'medium'),
                priority_score=analysis_data.get('priority_score', 3),
                recommendations=analysis_data.get('recommendations', [])
            )
            
            # Cache the result
            self._cache_analysis_result(opportunity_id, result)
            
            logger.info(f"Analysis completed for: {opportunity_id}")
            return result
            
        except Exception as e:
            logger.error(f"Analysis failed for {opportunity_id}: {e}")
            return OpportunityAnalysisResult(
                opportunity_id=opportunity_id,
                status=AnalysisStatus.FAILED,
                analysis_data={},
                timestamp=datetime.now(),
                confidence_score=0.0,
                risk_level="unknown",
                priority_score=0,
                recommendations=[],
                error_message=str(e)
            )
    
    async def batch_analyze_opportunities(self, opportunity_ids: List[str], max_concurrent: int = 5) -> Dict[str, OpportunityAnalysisResult]:
        """
        Analyze multiple opportunities in batch
        
        Args:
            opportunity_ids: List of opportunity IDs to analyze
            max_concurrent: Maximum concurrent analyses
            
        Returns:
            Dictionary mapping opportunity_id to analysis result
        """
        try:
            logger.info(f"Starting batch analysis for {len(opportunity_ids)} opportunities")
            
            # Create semaphore for concurrency control
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def analyze_with_semaphore(opp_id: str) -> Tuple[str, OpportunityAnalysisResult]:
                async with semaphore:
                    result = await self.analyze_opportunity(opp_id)
                    return opp_id, result
            
            # Execute analyses concurrently
            tasks = [analyze_with_semaphore(opp_id) for opp_id in opportunity_ids]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            analysis_results = {}
            successful = 0
            failed = 0
            
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Batch analysis task failed: {result}")
                    failed += 1
                else:
                    opp_id, analysis_result = result
                    analysis_results[opp_id] = analysis_result
                    
                    if analysis_result.status == AnalysisStatus.COMPLETED:
                        successful += 1
                    else:
                        failed += 1
            
            logger.info(f"Batch analysis completed: {successful} successful, {failed} failed")
            return analysis_results
            
        except Exception as e:
            logger.error(f"Batch analysis failed: {e}")
            return {}
    
    async def _fetch_opportunity_data(self, opportunity_id: str) -> Optional[Dict[str, Any]]:
        """Fetch opportunity data from SAM API or database"""
        try:
            # First try database cache
            cached_data = DatabaseUtils.get_cached_opportunity_data(opportunity_id)
            if cached_data and DatabaseUtils.is_cache_valid(opportunity_id):
                logger.info(f"Using cached data for: {opportunity_id}")
                return cached_data
            
            # Fetch from SAM API
            logger.info(f"Fetching fresh data from SAM API for: {opportunity_id}")
            opportunity_data = self.sam_api.get_opportunity_details(opportunity_id)
            
            if opportunity_data:
                # Cache the data
                DatabaseUtils.update_opportunity_cache(opportunity_id, opportunity_data)
                return opportunity_data
            
            # Fallback to database
            logger.info(f"Fallback to database for: {opportunity_id}")
            db_data = DatabaseUtils.get_opportunity_by_id(opportunity_id)
            return db_data
            
        except Exception as e:
            logger.error(f"Error fetching opportunity data for {opportunity_id}: {e}")
            return None
    
    async def _perform_comprehensive_analysis(self, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive analysis using multiple agents"""
        try:
            logger.info("Starting comprehensive analysis")
            
            # 1. AI Analysis
            ai_analysis = self.synthesis_agent.analyze_opportunity(opportunity_data)
            
            # 2. Document Analysis (if documents exist)
            notice_id = opportunity_data.get('noticeId', '')
            doc_analysis = {'success': False, 'documents': []}
            if notice_id:
                try:
                    doc_analysis = self.doc_agent.process_documents(notice_id)
                except Exception as e:
                    logger.warning(f"Document analysis failed: {e}")
            
            # 3. Proposal Generation
            proposal_outline = self.proposal_agent.generate_proposal_outline(opportunity_data, ai_analysis)
            
            # 4. Summary Generation
            summary = self.summary_agent.generate_summary(opportunity_data)
            
            # 5. Combine results
            comprehensive_analysis = {
                'opportunity_data': opportunity_data,
                'ai_analysis': ai_analysis,
                'document_analysis': doc_analysis,
                'proposal_outline': proposal_outline,
                'summary': summary,
                'analysis_metadata': {
                    'analyzed_at': datetime.now().isoformat(),
                    'analyzer_version': '1.0.0',
                    'total_documents': len(doc_analysis.get('documents', [])),
                    'analysis_duration': 0  # Would be calculated in real implementation
                }
            }
            
            # Extract key metrics
            comprehensive_analysis.update({
                'confidence_score': ai_analysis.get('opportunity_score', 5) / 10.0,
                'risk_level': ai_analysis.get('risk_level', 'medium'),
                'priority_score': ai_analysis.get('priority_score', 3),
                'recommendations': ai_analysis.get('recommendations', [])
            })
            
            logger.info("Comprehensive analysis completed")
            return comprehensive_analysis
            
        except Exception as e:
            logger.error(f"Comprehensive analysis failed: {e}")
            return {
                'error': str(e),
                'confidence_score': 0.0,
                'risk_level': 'unknown',
                'priority_score': 0,
                'recommendations': []
            }
    
    async def _store_analysis_result(self, opportunity_id: str, analysis_data: Dict[str, Any]) -> bool:
        """Store analysis result in database"""
        try:
            # Convert datetime objects to strings for JSON serialization
            def json_serializer(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
            
            # Serialize analysis data
            analysis_json = json.dumps(analysis_data, default=json_serializer)
            
            # Store in analysis_results table
            query = """
                INSERT INTO document_analysis_results 
                (opportunity_id, analysis_data, analysis_type, created_at, updated_at)
                VALUES (%s, %s, %s, NOW(), NOW())
                ON CONFLICT (opportunity_id) 
                DO UPDATE SET 
                    analysis_data = EXCLUDED.analysis_data,
                    updated_at = NOW()
            """
            
            self.db_manager.execute_update(
                query, 
                (opportunity_id, analysis_json, 'comprehensive_analysis')
            )
            
            logger.info(f"Analysis result stored for: {opportunity_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store analysis result for {opportunity_id}: {e}")
            return False
    
    def _get_cached_analysis(self, opportunity_id: str) -> Optional[OpportunityAnalysisResult]:
        """Get cached analysis result"""
        if opportunity_id in self.analysis_cache:
            cached_result = self.analysis_cache[opportunity_id]
            cache_age = (datetime.now() - cached_result.timestamp).total_seconds()
            
            if cache_age < self.cache_ttl:
                return cached_result
            else:
                # Remove expired cache
                del self.analysis_cache[opportunity_id]
        
        return None
    
    def _cache_analysis_result(self, opportunity_id: str, result: OpportunityAnalysisResult):
        """Cache analysis result"""
        self.analysis_cache[opportunity_id] = result
        
        # Limit cache size
        if len(self.analysis_cache) > 100:
            # Remove oldest entries
            oldest_key = min(self.analysis_cache.keys(), 
                           key=lambda k: self.analysis_cache[k].timestamp)
            del self.analysis_cache[oldest_key]
    
    def get_analysis_statistics(self) -> Dict[str, Any]:
        """Get analyzer statistics"""
        try:
            # Get database statistics
            total_opportunities = DatabaseUtils.get_opportunity_count()
            recent_opportunities = DatabaseUtils.get_recent_opportunities(limit=10)
            
            # Get cache statistics
            cache_size = len(self.analysis_cache)
            cache_hit_rate = 0.0  # Would be calculated in real implementation
            
            return {
                'total_opportunities': total_opportunities,
                'recent_opportunities_count': len(recent_opportunities),
                'cache_size': cache_size,
                'cache_hit_rate': cache_hit_rate,
                'analyzer_status': 'active',
                'last_analysis': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {'error': str(e)}
    
    def coordinate_with_other_agents(self, analysis_result: OpportunityAnalysisResult) -> Dict[str, Any]:
        """Coordinate with other agents based on analysis result"""
        try:
            coordination_results = {}
            
            # Send to AI Analysis Agent for further processing
            if analysis_result.status == AnalysisStatus.COMPLETED:
                coordination_results['ai_agent'] = {
                    'status': 'notified',
                    'priority': analysis_result.priority_score,
                    'risk_level': analysis_result.risk_level
                }
                
                # Send to Document Analysis Agent if documents exist
                if analysis_result.analysis_data.get('document_analysis', {}).get('documents'):
                    coordination_results['document_agent'] = {
                        'status': 'processing',
                        'document_count': len(analysis_result.analysis_data['document_analysis']['documents'])
                    }
                
                # Send to Proposal Agent for high-priority opportunities
                if analysis_result.priority_score >= 4:
                    coordination_results['proposal_agent'] = {
                        'status': 'generating_proposal',
                        'priority': analysis_result.priority_score
                    }
            
            return coordination_results
            
        except Exception as e:
            logger.error(f"Agent coordination failed: {e}")
            return {'error': str(e)}

# Global instance
analyzer_agent = SAMOpportunityAnalyzerAgent()

# Convenience functions
async def analyze_opportunity(opportunity_id: str, force_refresh: bool = False) -> OpportunityAnalysisResult:
    """Analyze a single opportunity"""
    return await analyzer_agent.analyze_opportunity(opportunity_id, force_refresh)

async def batch_analyze_opportunities(opportunity_ids: List[str], max_concurrent: int = 5) -> Dict[str, OpportunityAnalysisResult]:
    """Analyze multiple opportunities in batch"""
    return await analyzer_agent.batch_analyze_opportunities(opportunity_ids, max_concurrent)

def get_analyzer_statistics() -> Dict[str, Any]:
    """Get analyzer statistics"""
    return analyzer_agent.get_analysis_statistics()

def coordinate_agents(analysis_result: OpportunityAnalysisResult) -> Dict[str, Any]:
    """Coordinate with other agents"""
    return analyzer_agent.coordinate_with_other_agents(analysis_result)

if __name__ == "__main__":
    # Test the analyzer agent
    import asyncio
    
    async def test_analyzer():
        print("Testing SAM Opportunity Analyzer Agent...")
        
        # Test statistics
        stats = get_analyzer_statistics()
        print(f"Analyzer statistics: {stats}")
        
        # Test single analysis (with mock data)
        test_opportunity_id = "test_123"
        result = await analyze_opportunity(test_opportunity_id)
        print(f"Analysis result: {result}")
        
        # Test batch analysis
        test_ids = ["test_1", "test_2", "test_3"]
        batch_results = await batch_analyze_opportunities(test_ids)
        print(f"Batch analysis results: {len(batch_results)} completed")
    
    # Run test
    asyncio.run(test_analyzer())
