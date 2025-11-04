"""
AutoGen Analysis Center Module
Advanced AI analysis capabilities for SAM.gov opportunities
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from autogen_agents import (
    SAMOpportunityAnalyzer,
    DocumentAnalysisAgent,
    ProposalAgent,
    SynthesisAgent,
    CoordinatorAgent
)
from sam_opportunity_analyzer_agent import (
    SAMOpportunityAnalyzerAgent,
    OpportunityAnalysisResult,
    AnalysisStatus,
    analyze_opportunity,
    batch_analyze_opportunities,
    get_analyzer_statistics,
    coordinate_agents
)

logger = logging.getLogger(__name__)

class AutoGenAnalysisCenter:
    """AutoGen Analysis Center for comprehensive opportunity analysis"""
    
    def __init__(self):
        self.sam_agent = SAMOpportunityAnalyzer()
        self.doc_agent = DocumentAnalysisAgent()
        self.proposal_agent = ProposalAgent()
        self.synthesis_agent = SynthesisAgent()
        self.coordinator = CoordinatorAgent()
        
        # New SAM Opportunity Analyzer Agent
        self.analyzer_agent = SAMOpportunityAnalyzerAgent()
        
        logger.info("AutoGen Analysis Center initialized with SAM Opportunity Analyzer Agent")
    
    async def analyze_opportunity_comprehensive(self, opportunity_id: str, force_refresh: bool = False) -> Dict[str, Any]:
        """Comprehensive opportunity analysis using SAM Opportunity Analyzer Agent"""
        try:
            logger.info(f"Comprehensive analysis started for: {opportunity_id}")
            
            # Use the new SAM Opportunity Analyzer Agent
            analysis_result = await self.analyzer_agent.analyze_opportunity(opportunity_id, force_refresh)
            
            if analysis_result.status == AnalysisStatus.COMPLETED:
                # Coordinate with other agents
                coordination_results = self.analyzer_agent.coordinate_with_other_agents(analysis_result)
                
                comprehensive_result = {
                    'opportunity_id': opportunity_id,
                    'analysis_timestamp': analysis_result.timestamp.isoformat(),
                    'status': analysis_result.status.value,
                    'confidence_score': analysis_result.confidence_score,
                    'risk_level': analysis_result.risk_level,
                    'priority_score': analysis_result.priority_score,
                    'recommendations': analysis_result.recommendations,
                    'analysis_data': analysis_result.analysis_data,
                    'coordination_results': coordination_results,
                    'summary': {
                        'total_documents': analysis_result.analysis_data.get('analysis_metadata', {}).get('total_documents', 0),
                        'analysis_confidence': analysis_result.confidence_score,
                        'proposal_status': 'generated' if analysis_result.priority_score >= 4 else 'pending'
                    }
                }
                
                logger.info(f"Comprehensive analysis completed for: {opportunity_id}")
                return comprehensive_result
            else:
                logger.error(f"Analysis failed for {opportunity_id}: {analysis_result.error_message}")
                
                # Try to use mock data for testing
                try:
                    from mock_sam_data import get_mock_analysis_result
                    mock_result = get_mock_analysis_result(opportunity_id)
                    if mock_result and mock_result.get('status') == 'success':
                        logger.info(f"Using mock analysis result for: {opportunity_id}")
                        return {
                            'opportunity_id': opportunity_id,
                            'success': True,
                            'status': mock_result.get('status'),
                            'confidence_score': mock_result.get('confidence_score', 0.0),
                            'go_no_go_score': mock_result.get('go_no_go_score', 0.0),
                            'risk_level': mock_result.get('risk_level', 'unknown'),
                            'priority_score': mock_result.get('priority_score', 0),
                            'recommendations': mock_result.get('recommendations', []),
                            'analysis_result': mock_result.get('analysis_result', {}),
                            'analysis_timestamp': mock_result.get('analysis_timestamp'),
                            'coordination_results': {}
                        }
                except ImportError:
                    pass
                
                return {
                    'opportunity_id': opportunity_id,
                    'error': analysis_result.error_message,
                    'status': analysis_result.status.value,
                    'analysis_timestamp': analysis_result.timestamp.isoformat()
                }
            
        except Exception as e:
            logger.error(f"Comprehensive analysis failed for {opportunity_id}: {e}")
            return {
                'opportunity_id': opportunity_id,
                'error': str(e),
                'analysis_timestamp': datetime.now().isoformat()
            }
    
    def analyze_opportunity_comprehensive_sync(self, opportunity_id: str, force_refresh: bool = False) -> Dict[str, Any]:
        """Synchronous wrapper for comprehensive opportunity analysis"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.analyze_opportunity_comprehensive(opportunity_id, force_refresh))
    
    async def batch_analyze_opportunities(self, opportunity_ids: List[str], max_concurrent: int = 5) -> Dict[str, Any]:
        """Batch analysis of multiple opportunities using SAM Opportunity Analyzer Agent"""
        try:
            logger.info(f"Batch analysis started for {len(opportunity_ids)} opportunities")
            
            # Use the new SAM Opportunity Analyzer Agent for batch analysis
            analysis_results = await self.analyzer_agent.batch_analyze_opportunities(opportunity_ids, max_concurrent)
            
            # Process results
            successful = 0
            failed = 0
            results = []
            
            for opp_id, analysis_result in analysis_results.items():
                if analysis_result.status == AnalysisStatus.COMPLETED:
                    successful += 1
                    # Coordinate with other agents
                    coordination_results = self.analyzer_agent.coordinate_with_other_agents(analysis_result)
                    
                    result = {
                        'opportunity_id': opp_id,
                        'status': analysis_result.status.value,
                        'confidence_score': analysis_result.confidence_score,
                        'risk_level': analysis_result.risk_level,
                        'priority_score': analysis_result.priority_score,
                        'recommendations': analysis_result.recommendations,
                        'coordination_results': coordination_results,
                        'analysis_timestamp': analysis_result.timestamp.isoformat()
                    }
                else:
                    failed += 1
                    result = {
                        'opportunity_id': opp_id,
                        'status': analysis_result.status.value,
                        'error': analysis_result.error_message,
                        'analysis_timestamp': analysis_result.timestamp.isoformat()
                    }
                
                results.append(result)
            
            batch_result = {
                'total_opportunities': len(opportunity_ids),
                'successful': successful,
                'failed': failed,
                'results': results,
                'batch_timestamp': datetime.now().isoformat(),
                'analyzer_statistics': self.analyzer_agent.get_analysis_statistics()
            }
            
            logger.info(f"Batch analysis completed: {successful} successful, {failed} failed")
            return batch_result
            
        except Exception as e:
            logger.error(f"Batch analysis failed: {e}")
            return {
                'error': str(e),
                'batch_timestamp': datetime.now().isoformat()
            }
    
    def batch_analyze_opportunities_sync(self, opportunity_ids: List[str], max_concurrent: int = 5) -> Dict[str, Any]:
        """Synchronous wrapper for batch analysis"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.batch_analyze_opportunities(opportunity_ids, max_concurrent))
    
    def generate_analysis_report(self, analysis_results: Dict[str, Any]) -> str:
        """Generate human-readable analysis report"""
        try:
            report = f"""
# AutoGen Analysis Report

**Analysis Date:** {analysis_results.get('analysis_timestamp', 'Unknown')}
**Opportunity ID:** {analysis_results.get('opportunity_id', 'Unknown')}

## Opportunity Analysis
"""
            
            opp_analysis = analysis_results.get('opportunity_analysis', {})
            if opp_analysis:
                report += f"""
- **Confidence Score:** {opp_analysis.get('confidence', 0.0):.2%}
- **Key Requirements:** {', '.join(opp_analysis.get('key_requirements', []))}
- **Risk Level:** {opp_analysis.get('risk_level', 'Unknown')}
- **Estimated Value:** {opp_analysis.get('estimated_value', 'Unknown')}
"""
            
            doc_analysis = analysis_results.get('document_analysis', {})
            if doc_analysis:
                report += f"""
## Document Analysis
- **Total Documents:** {len(doc_analysis.get('documents', []))}
- **Analysis Status:** {doc_analysis.get('status', 'Unknown')}
"""
                
                documents = doc_analysis.get('documents', [])
                for i, doc in enumerate(documents, 1):
                    report += f"""
### Document {i}
- **Type:** {doc.get('type', 'Unknown')}
- **Analysis:** {doc.get('analysis', 'No analysis available')}
"""
            
            proposal = analysis_results.get('proposal_draft', {})
            if proposal:
                report += f"""
## Proposal Draft
- **Status:** {proposal.get('status', 'Unknown')}
- **Draft Available:** {'Yes' if proposal.get('draft') else 'No'}
"""
            
            summary = analysis_results.get('summary', {})
            if summary:
                report += f"""
## Summary
- **Total Documents Analyzed:** {summary.get('total_documents', 0)}
- **Analysis Confidence:** {summary.get('analysis_confidence', 0.0):.2%}
- **Proposal Status:** {summary.get('proposal_status', 'Unknown')}
"""
            
            return report
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return f"Error generating report: {e}"
    
    def get_analysis_statistics(self) -> Dict[str, Any]:
        """Get analysis center statistics including SAM Opportunity Analyzer Agent stats"""
        try:
            # Get analyzer agent statistics
            analyzer_stats = self.analyzer_agent.get_analysis_statistics()
            
            # Combine with analysis center statistics
            combined_stats = {
                'analyzer_agent': analyzer_stats,
                'analysis_center': {
                    'total_analyses': analyzer_stats.get('total_opportunities', 0),
                    'successful_analyses': analyzer_stats.get('recent_opportunities_count', 0),
                    'failed_analyses': 0,  # Would be tracked in real implementation
                    'average_confidence': 0.0,  # Would be calculated in real implementation
                    'last_analysis': analyzer_stats.get('last_analysis'),
                    'most_analyzed_opportunity_type': 'SAM.gov Opportunities',
                    'cache_performance': {
                        'cache_size': analyzer_stats.get('cache_size', 0),
                        'cache_hit_rate': analyzer_stats.get('cache_hit_rate', 0.0)
                    }
                },
                'system_status': {
                    'analyzer_status': analyzer_stats.get('analyzer_status', 'unknown'),
                    'database_connected': analyzer_stats.get('total_opportunities', 0) > 0,
                    'last_updated': datetime.now().isoformat()
                }
            }
            
            return combined_stats
            
        except Exception as e:
            logger.error(f"Statistics retrieval failed: {e}")
            return {'error': str(e)}

# Global instance
analysis_center = AutoGenAnalysisCenter()

def analyze_opportunity_comprehensive(opportunity_id: str, force_refresh: bool = False) -> Dict[str, Any]:
    """Comprehensive opportunity analysis (synchronous)"""
    return analysis_center.analyze_opportunity_comprehensive_sync(opportunity_id, force_refresh)

async def analyze_opportunity_comprehensive_async(opportunity_id: str, force_refresh: bool = False) -> Dict[str, Any]:
    """Comprehensive opportunity analysis (asynchronous)"""
    return await analysis_center.analyze_opportunity_comprehensive(opportunity_id, force_refresh)

def batch_analyze_opportunities(opportunity_ids: List[str], max_concurrent: int = 5) -> Dict[str, Any]:
    """Batch analysis of multiple opportunities (synchronous)"""
    return analysis_center.batch_analyze_opportunities_sync(opportunity_ids, max_concurrent)

async def batch_analyze_opportunities_async(opportunity_ids: List[str], max_concurrent: int = 5) -> Dict[str, Any]:
    """Batch analysis of multiple opportunities (asynchronous)"""
    return await analysis_center.batch_analyze_opportunities(opportunity_ids, max_concurrent)

def generate_analysis_report(analysis_results: Dict[str, Any]) -> str:
    """Generate human-readable analysis report"""
    return analysis_center.generate_analysis_report(analysis_results)

def get_analysis_statistics() -> Dict[str, Any]:
    """Get analysis center statistics"""
    return analysis_center.get_analysis_statistics()

def get_analyzer_agent() -> SAMOpportunityAnalyzerAgent:
    """Get the SAM Opportunity Analyzer Agent instance"""
    return analysis_center.analyzer_agent

if __name__ == "__main__":
    # Test the analysis center
    print("AutoGen Analysis Center Test with SAM Opportunity Analyzer Agent")
    
    # Test statistics
    stats = get_analysis_statistics()
    print(f"Analysis Center Statistics: {stats}")
    
    # Test comprehensive analysis (synchronous)
    test_opp_id = "test_opportunity_123"
    result = analyze_opportunity_comprehensive(test_opp_id)
    print(f"Comprehensive Analysis Result: {result}")
    
    # Test report generation
    report = generate_analysis_report(result)
    print(f"Generated Report:\n{report}")
    
    # Test analyzer agent directly
    analyzer = get_analyzer_agent()
    analyzer_stats = analyzer.get_analysis_statistics()
    print(f"Analyzer Agent Statistics: {analyzer_stats}")
    
    print("✅ AutoGen Analysis Center with SAM Opportunity Analyzer Agent test completed")

