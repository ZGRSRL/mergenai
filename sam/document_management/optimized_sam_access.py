#!/usr/bin/env python3
"""
Optimized SAM Document Access with Caching
Enhanced version with database caching and updated_at checking
"""

import os
import json
import logging
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from database_manager import db_manager, DatabaseUtils
from streamlit_cache import cache_api_call, cached_opportunity_data

logger = logging.getLogger(__name__)

class OptimizedSAMDocumentAccess:
    """Optimized SAM document access with caching and rate limiting"""
    
    def __init__(self):
        self.api_key = os.getenv('SAM_API_KEY')
        self.base_url = "https://api.sam.gov/prod/opportunities/v2/search"
        self.last_api_call = 0
        self.rate_limit_delay = 3  # 3 seconds between calls
        
        # Session for connection reuse
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SAM-Document-Manager/1.0',
            'Accept': 'application/json'
        })
        
        logger.info("OptimizedSAMDocumentAccess initialized")
    
    def _wait_for_rate_limit(self):
        """Rate limit management"""
        current_time = time.time()
        time_since_last_call = current_time - self.last_api_call
        
        if time_since_last_call < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_call
            logger.info(f"Rate limiting: waiting {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_api_call = time.time()
    
    @cache_api_call
    def fetch_opportunities_cached(self, keywords: str = "", naics_codes: str = "", 
                                  days_back: int = 30, limit: int = 100) -> Dict[str, Any]:
        """Fetch opportunities with caching"""
        logger.info(f"Fetching opportunities: keywords='{keywords}', days_back={days_back}, limit={limit}")
        
        # Check if we have recent data in database
        if self._has_recent_data(days_back):
            logger.info("Using cached database data instead of API call")
            return self._get_cached_opportunities(keywords, naics_codes, limit)
        
        # Make API call
        return self._fetch_from_api(keywords, naics_codes, days_back, limit)
    
    def _has_recent_data(self, days_back: int) -> bool:
        """Check if we have recent data in database"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            query = """
                SELECT COUNT(*) as count 
                FROM opportunities 
                WHERE posted_date >= %s
            """
            result = db_manager.execute_query(query, (cutoff_date,), fetch='one')
            return result['count'] > 0 if result else False
        except Exception as e:
            logger.error(f"Error checking recent data: {e}")
            return False
    
    def _get_cached_opportunities(self, keywords: str, naics_codes: str, limit: int) -> Dict[str, Any]:
        """Get opportunities from cached database data"""
        try:
            if keywords:
                opportunities = DatabaseUtils.search_opportunities(keywords, limit)
            else:
                opportunities = DatabaseUtils.get_recent_opportunities(limit)
            
            return {
                'opportunities': opportunities,
                'totalRecords': len(opportunities),
                'cached': True,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting cached opportunities: {e}")
            return {'opportunities': [], 'totalRecords': 0, 'cached': False}
    
    def _fetch_from_api(self, keywords: str, naics_codes: str, days_back: int, limit: int) -> Dict[str, Any]:
        """Fetch opportunities from SAM API"""
        if not self.api_key:
            logger.warning("No SAM API key provided, using cached data only")
            return self._get_cached_opportunities(keywords, naics_codes, limit)
        
        self._wait_for_rate_limit()
        
        params = {
            'api_key': self.api_key,
            'limit': min(limit, 1000),  # API limit
            'postedFrom': (datetime.now() - timedelta(days=days_back)).strftime('%m/%d/%Y'),
            'postedTo': datetime.now().strftime('%m/%d/%Y')
        }
        
        if keywords:
            params['q'] = keywords
        if naics_codes:
            params['naics'] = naics_codes
        
        try:
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Cache the results in database
            self._cache_opportunities(data.get('opportunities', []))
            
            return {
                'opportunities': data.get('opportunities', []),
                'totalRecords': data.get('totalRecords', 0),
                'cached': False,
                'timestamp': datetime.now().isoformat()
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return self._get_cached_opportunities(keywords, naics_codes, limit)
    
    def _cache_opportunities(self, opportunities: List[Dict[str, Any]]):
        """Cache opportunities in database"""
        if not opportunities:
            return
        
        try:
            for opp in opportunities:
                self._cache_single_opportunity(opp)
            logger.info(f"Cached {len(opportunities)} opportunities")
        except Exception as e:
            logger.error(f"Error caching opportunities: {e}")
    
    def _cache_single_opportunity(self, opportunity: Dict[str, Any]):
        """Cache single opportunity"""
        try:
            query = """
                INSERT INTO opportunities (
                    opportunity_id, title, description, posted_date, 
                    naics_code, solicitation_number, agency, 
                    cached_data, cache_updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                )
                ON CONFLICT (opportunity_id) 
                DO UPDATE SET
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    posted_date = EXCLUDED.posted_date,
                    naics_code = EXCLUDED.naics_code,
                    solicitation_number = EXCLUDED.solicitation_number,
                    agency = EXCLUDED.agency,
                    cached_data = EXCLUDED.cached_data,
                    cache_updated_at = NOW()
            """
            
            params = (
                opportunity.get('opportunityId'),
                opportunity.get('title'),
                opportunity.get('description'),
                opportunity.get('postedDate'),
                opportunity.get('naicsCode'),
                opportunity.get('solicitationNumber'),
                opportunity.get('agency'),
                json.dumps(opportunity)
            )
            
            db_manager.execute_update(query, params)
            
        except Exception as e:
            logger.error(f"Error caching single opportunity: {e}")
    
    @cached_opportunity_data
    def get_opportunity_details_cached(self, notice_id: str) -> Optional[Dict[str, Any]]:
        """Get opportunity details with caching"""
        logger.info(f"Getting opportunity details for: {notice_id}")
        
        # Check cache first
        cached_data = DatabaseUtils.get_cached_opportunity_data(notice_id)
        if cached_data and DatabaseUtils.is_cache_valid(notice_id, max_age_hours=24):
            logger.info(f"Using cached data for opportunity: {notice_id}")
            return cached_data
        
        # Fetch from API if not cached or expired
        fresh_data = self._fetch_opportunity_from_api(notice_id)
        if fresh_data:
            # Update cache
            DatabaseUtils.update_opportunity_cache(notice_id, fresh_data)
            return fresh_data
        
        # Fallback to cached data even if expired
        if cached_data:
            logger.warning(f"Using expired cached data for opportunity: {notice_id}")
            return cached_data
        
        return None
    
    def _fetch_opportunity_from_api(self, notice_id: str) -> Optional[Dict[str, Any]]:
        """Fetch opportunity details from API"""
        if not self.api_key:
            logger.warning("No SAM API key provided")
            return None
        
        self._wait_for_rate_limit()
        
        url = f"https://api.sam.gov/prod/opportunities/v2/search"
        params = {
            'api_key': self.api_key,
            'noticeId': notice_id
        }
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            opportunities = data.get('opportunities', [])
            
            if opportunities:
                return opportunities[0]
            
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for opportunity {notice_id}: {e}")
            return None
    
    def get_opportunity_description(self, notice_id: str) -> Optional[str]:
        """Get opportunity description with improved error handling"""
        logger.info(f"Getting description for: {notice_id}")
        
        try:
            with db_manager.get_dict_cursor() as cursor:
                cursor.execute(
                    "SELECT point_of_contact FROM opportunities WHERE opportunity_id = %s",
                    (notice_id,)
                )
                result = cursor.fetchone()
                
                if result and result['point_of_contact']:
                    point_of_contact = result['point_of_contact']
                    
                    # Handle different data types
                    if isinstance(point_of_contact, str):
                        try:
                            point_of_contact = json.loads(point_of_contact)
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid JSON in point_of_contact: {point_of_contact}")
                            return None
                    
                    if isinstance(point_of_contact, dict):
                        return point_of_contact.get('description')
                
                return None
                
        except Exception as e:
            logger.error(f"Description URL database error: {e}")
            return None
    
    def get_opportunity_resource_links(self, notice_id: str) -> List[str]:
        """Get opportunity resource links with improved error handling"""
        logger.info(f"Getting resource links for: {notice_id}")
        
        try:
            with db_manager.get_dict_cursor() as cursor:
                cursor.execute(
                    "SELECT point_of_contact FROM opportunities WHERE opportunity_id = %s",
                    (notice_id,)
                )
                result = cursor.fetchone()
                
                if result and result['point_of_contact']:
                    point_of_contact = result['point_of_contact']
                    
                    # Handle different data types
                    if isinstance(point_of_contact, str):
                        try:
                            point_of_contact = json.loads(point_of_contact)
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid JSON in point_of_contact: {point_of_contact}")
                            return []
                    
                    if isinstance(point_of_contact, dict):
                        return point_of_contact.get('resourceLinks', [])
                
                return []
                
        except Exception as e:
            logger.error(f"ResourceLinks database error: {e}")
            return []
    
    def download_all_attachments_optimized(self, notice_id: str) -> List[Dict[str, Any]]:
        """Optimized attachment download with batch processing"""
        logger.info(f"Downloading attachments for: {notice_id}")
        
        resource_links = self.get_opportunity_resource_links(notice_id)
        if not resource_links:
            logger.info(f"No resource links found for: {notice_id}")
            return []
        
        downloaded_files = []
        
        # Process in batches to avoid overwhelming the server
        batch_size = 5
        for i in range(0, len(resource_links), batch_size):
            batch = resource_links[i:i + batch_size]
            batch_results = self._download_batch(batch, notice_id)
            downloaded_files.extend(batch_results)
            
            # Rate limiting between batches
            if i + batch_size < len(resource_links):
                time.sleep(1)
        
        logger.info(f"Downloaded {len(downloaded_files)} attachments for: {notice_id}")
        return downloaded_files
    
    def _download_batch(self, resource_links: List[str], notice_id: str) -> List[Dict[str, Any]]:
        """Download a batch of attachments"""
        downloaded_files = []
        
        for link in resource_links:
            try:
                self._wait_for_rate_limit()
                
                response = self.session.get(link, timeout=30)
                response.raise_for_status()
                
                # Extract filename from URL or Content-Disposition header
                filename = self._extract_filename(link, response.headers)
                
                file_info = {
                    'filename': filename,
                    'url': link,
                    'size': len(response.content),
                    'content_type': response.headers.get('content-type', ''),
                    'downloaded_at': datetime.now().isoformat(),
                    'notice_id': notice_id
                }
                
                downloaded_files.append(file_info)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to download {link}: {e}")
                continue
        
        return downloaded_files
    
    def _extract_filename(self, url: str, headers: Dict[str, str]) -> str:
        """Extract filename from URL or headers"""
        # Try Content-Disposition header first
        content_disposition = headers.get('content-disposition', '')
        if 'filename=' in content_disposition:
            filename = content_disposition.split('filename=')[1].strip('"')
            return filename
        
        # Fallback to URL
        return url.split('/')[-1] or f"attachment_{int(time.time())}"
    
    def get_api_stats(self) -> Dict[str, Any]:
        """Get API usage statistics"""
        return {
            'last_api_call': self.last_api_call,
            'rate_limit_delay': self.rate_limit_delay,
            'session_active': self.session is not None,
            'api_key_configured': bool(self.api_key)
        }

# Global instance
optimized_sam_access = OptimizedSAMDocumentAccess()

# Convenience functions for backward compatibility
def fetch_opportunities(keywords: str = "", naics_codes: str = "", 
                       days_back: int = 30, limit: int = 100) -> Dict[str, Any]:
    """Fetch opportunities with caching"""
    return optimized_sam_access.fetch_opportunities_cached(keywords, naics_codes, days_back, limit)

def get_opportunity_details(notice_id: str) -> Optional[Dict[str, Any]]:
    """Get opportunity details with caching"""
    return optimized_sam_access.get_opportunity_details_cached(notice_id)

def download_all_attachments(notice_id: str) -> List[Dict[str, Any]]:
    """Download all attachments with optimization"""
    return optimized_sam_access.download_all_attachments_optimized(notice_id)
