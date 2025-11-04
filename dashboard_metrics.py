#!/usr/bin/env python3
"""
Dashboard Metrics
Ana sayfa için gösterge ve istatistikler
"""

import sys
sys.path.append('.')

import psycopg2
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import os

class DashboardMetrics:
    """Dashboard metrikleri ve göstergeleri"""
    
    def __init__(self):
        self.conn = psycopg2.connect(
            host='localhost',
            database='ZGR_AI',
            user='postgres',
            password='postgres',
            port='5432'
        )
    
    def get_today_metrics(self) -> Dict[str, Any]:
        """Bugünkü metrikleri getirir"""
        cursor = self.conn.cursor()
        
        today = datetime.now().date()
        
        # Bugünkü analiz sayısı
        cursor.execute("""
            SELECT COUNT(*) FROM sow_analysis 
            WHERE DATE(created_at) = %s
        """, (today,))
        today_analyses = cursor.fetchone()[0]
        
        # Bugünkü otel aramaları
        cursor.execute("""
            SELECT COUNT(*) FROM hotel_suggestions 
            WHERE DATE(created_at) = %s
        """, (today,))
        today_hotels = cursor.fetchone()[0]
        
        # Bugünkü başarı oranı
        cursor.execute("""
            SELECT COUNT(*) FROM sow_analysis 
            WHERE DATE(created_at) = %s AND template_version IS NOT NULL
        """, (today,))
        successful_analyses = cursor.fetchone()[0]
        
        success_rate = (successful_analyses / today_analyses * 100) if today_analyses > 0 else 0
        
        return {
            "today_analyses": today_analyses,
            "today_hotels": today_hotels,
            "success_rate": round(success_rate, 1),
            "successful_analyses": successful_analyses
        }
    
    def get_week_metrics(self) -> Dict[str, Any]:
        """Haftalık metrikleri getirir"""
        cursor = self.conn.cursor()
        
        week_ago = datetime.now().date() - timedelta(days=7)
        
        # Haftalık analiz sayısı
        cursor.execute("""
            SELECT COUNT(*) FROM sow_analysis 
            WHERE DATE(created_at) >= %s
        """, (week_ago,))
        week_analyses = cursor.fetchone()[0]
        
        # Haftalık otel aramaları
        cursor.execute("""
            SELECT COUNT(*) FROM hotel_suggestions 
            WHERE DATE(created_at) >= %s
        """, (week_ago,))
        week_hotels = cursor.fetchone()[0]
        
        # En popüler notice'lar
        cursor.execute("""
            SELECT notice_id, COUNT(*) as count
            FROM sow_analysis 
            WHERE DATE(created_at) >= %s
            GROUP BY notice_id
            ORDER BY count DESC
            LIMIT 5
        """, (week_ago,))
        top_notices = cursor.fetchall()
        
        return {
            "week_analyses": week_analyses,
            "week_hotels": week_hotels,
            "top_notices": [{"notice_id": row[0], "count": row[1]} for row in top_notices]
        }
    
    def get_agent_performance(self) -> Dict[str, Any]:
        """Agent performans metrikleri"""
        try:
            # Agent log dosyasından oku
            log_file = f"logs/agent_actions_{datetime.now().strftime('%Y%m%d')}.json"
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
                
                # Agent bazında istatistikler
                agent_stats = {}
                durations = []
                
                for log in logs:
                    agent_name = log.get('agent_name', 'Unknown')
                    if agent_name not in agent_stats:
                        agent_stats[agent_name] = {
                            'total_actions': 0,
                            'successful_actions': 0,
                            'total_duration': 0,
                            'avg_duration': 0
                        }
                    
                    agent_stats[agent_name]['total_actions'] += 1
                    if log.get('status') == 'success':
                        agent_stats[agent_name]['successful_actions'] += 1
                    
                    duration = log.get('duration_ms', 0)
                    agent_stats[agent_name]['total_duration'] += duration
                    durations.append(duration)
                
                # Ortalama süre hesapla
                for agent in agent_stats.values():
                    if agent['total_actions'] > 0:
                        agent['avg_duration'] = agent['total_duration'] / agent['total_actions']
                        agent['success_rate'] = (agent['successful_actions'] / agent['total_actions']) * 100
                
                # P95 hesapla
                p95_duration = 0
                if durations:
                    durations.sort()
                    p95_index = int(len(durations) * 0.95)
                    p95_duration = durations[p95_index] if p95_index < len(durations) else durations[-1]
                
                # Son 7 gün başarı oranı
                week_ago = datetime.now() - timedelta(days=7)
                week_logs = [log for log in logs if datetime.fromisoformat(log.get('timestamp', '1970-01-01').replace('Z', '+00:00')) >= week_ago]
                week_success_rate = 0
                if week_logs:
                    week_successful = len([log for log in week_logs if log.get('status') == 'success'])
                    week_success_rate = (week_successful / len(week_logs)) * 100
                
                return {
                    "agent_stats": agent_stats,
                    "total_logs": len(logs),
                    "p95_duration_ms": p95_duration,
                    "week_success_rate": round(week_success_rate, 1)
                }
        except:
            pass
        
        return {"agent_stats": {}, "total_logs": 0, "p95_duration_ms": 0, "week_success_rate": 0}
    
    def get_recent_activities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Son aktiviteleri getirir"""
        cursor = self.conn.cursor()
        
        # Son SOW analizleri
        cursor.execute("""
            SELECT notice_id, template_version, created_at
            FROM sow_analysis 
            ORDER BY created_at DESC 
            LIMIT %s
        """, (limit,))
        
        sow_activities = cursor.fetchall()
        
        activities = []
        for row in sow_activities:
            activities.append({
                "type": "SOW Analysis",
                "notice_id": row[0],
                "status": "Completed" if row[1] else "Failed",
                "timestamp": row[2],
                "description": f"SOW analysis for {row[0]}"
            })
        
        return activities[:limit]
    
    def get_system_health(self) -> Dict[str, Any]:
        """Sistem sağlık durumu"""
        cursor = self.conn.cursor()
        
        # Veritabanı bağlantı testi
        try:
            cursor.execute("SELECT 1")
            db_status = "Connected"
        except:
            db_status = "Disconnected"
        
        # Tablo sayıları
        cursor.execute("SELECT COUNT(*) FROM sow_analysis")
        sow_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM hotel_suggestions")
        hotel_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM opportunities")
        opportunity_count = cursor.fetchone()[0]
        
        return {
            "database_status": db_status,
            "sow_analyses": sow_count,
            "hotel_suggestions": hotel_count,
            "opportunities": opportunity_count,
            "last_check": datetime.now().isoformat()
        }
    
    def close(self):
        """Bağlantıyı kapat"""
        self.conn.close()

# Test function
def test_dashboard_metrics():
    """Test dashboard metrics"""
    metrics = DashboardMetrics()
    
    print("=== Today's Metrics ===")
    today = metrics.get_today_metrics()
    print(f"Today's Analyses: {today['today_analyses']}")
    print(f"Today's Hotels: {today['today_hotels']}")
    print(f"Success Rate: {today['success_rate']}%")
    
    print("\n=== Week's Metrics ===")
    week = metrics.get_week_metrics()
    print(f"Week's Analyses: {week['week_analyses']}")
    print(f"Week's Hotels: {week['week_hotels']}")
    print(f"Top Notices: {week['top_notices']}")
    
    print("\n=== Agent Performance ===")
    agents = metrics.get_agent_performance()
    print(f"Total Logs: {agents['total_logs']}")
    for agent, stats in agents['agent_stats'].items():
        print(f"{agent}: {stats['total_actions']} actions, {stats['success_rate']:.1f}% success")
    
    print("\n=== System Health ===")
    health = metrics.get_system_health()
    print(f"Database: {health['database_status']}")
    print(f"SOW Analyses: {health['sow_analyses']}")
    print(f"Hotel Suggestions: {health['hotel_suggestions']}")
    print(f"Opportunities: {health['opportunities']}")
    
    metrics.close()

if __name__ == "__main__":
    test_dashboard_metrics()
