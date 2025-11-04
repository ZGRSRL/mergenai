#!/usr/bin/env python3
"""
Budget Estimator Agent
Oda/gece × gece sayısı + A/V varsayımları → kaba bütçe
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys
import os
sys.path.append('.')

logger = logging.getLogger(__name__)

class BudgetEstimatorAgent:
    """Bütçe tahmini yapar"""
    
    def __init__(self):
        self.logger = logging.getLogger("BudgetEstimatorAgent")
        
        # Varsayılan fiyatlandırma (USD)
        self.pricing_rates = {
            "hotel_room_per_night": 120.0,  # Ortalama oda fiyatı
            "av_equipment_daily": 500.0,    # Günlük A/V ekipman
            "catering_per_person": 45.0,    # Kişi başı catering
            "meeting_room_daily": 200.0,    # Günlük toplantı salonu
            "setup_fee": 1000.0,            # Kurulum ücreti
            "tax_rate": 0.08                # %8 vergi
        }
    
    def estimate_budget(self, sow_payload: Dict, custom_rates: Optional[Dict] = None) -> Dict[str, Any]:
        """SOW'dan bütçe tahmini yapar"""
        
        if custom_rates:
            self.pricing_rates.update(custom_rates)
        
        # SOW'dan verileri çıkar
        room_block = sow_payload.get('room_block', {})
        function_space = sow_payload.get('function_space', {})
        av = sow_payload.get('av', {})
        period = sow_payload.get('period_of_performance', {})
        
        # Temel parametreler
        rooms_per_night = room_block.get('total_rooms_per_night', 0)
        total_nights = room_block.get('total_nights', 1)
        capacity = function_space.get('general_session', {}).get('capacity', 0)
        breakout_rooms = function_space.get('breakout_rooms', {}).get('count', 0)
        
        # Dönem hesaplama
        if isinstance(period, dict):
            start_date = period.get('start', '')
            end_date = period.get('end', '')
            duration_days = self._calculate_duration_days(start_date, end_date)
        else:
            duration_days = total_nights
        
        # Bütçe hesaplamaları
        budget_breakdown = {
            "accommodation": self._calculate_accommodation_cost(rooms_per_night, total_nights),
            "av_equipment": self._calculate_av_cost(duration_days, av),
            "catering": self._calculate_catering_cost(capacity, duration_days),
            "meeting_rooms": self._calculate_meeting_room_cost(breakout_rooms, duration_days),
            "setup": self.pricing_rates["setup_fee"],
            "subtotal": 0,
            "tax": 0,
            "total": 0
        }
        
        # Subtotal hesapla
        budget_breakdown["subtotal"] = sum([
            budget_breakdown["accommodation"],
            budget_breakdown["av_equipment"],
            budget_breakdown["catering"],
            budget_breakdown["meeting_rooms"],
            budget_breakdown["setup"]
        ])
        
        # Vergi hesapla
        budget_breakdown["tax"] = budget_breakdown["subtotal"] * self.pricing_rates["tax_rate"]
        
        # Toplam
        budget_breakdown["total"] = budget_breakdown["subtotal"] + budget_breakdown["tax"]
        
        # Ek bilgiler
        budget_breakdown["parameters"] = {
            "rooms_per_night": rooms_per_night,
            "total_nights": total_nights,
            "capacity": capacity,
            "breakout_rooms": breakout_rooms,
            "duration_days": duration_days
        }
        
        budget_breakdown["pricing_rates"] = self.pricing_rates.copy()
        budget_breakdown["estimation_date"] = datetime.now().isoformat()
        
        return budget_breakdown
    
    def _calculate_accommodation_cost(self, rooms_per_night: int, total_nights: int) -> float:
        """Konaklama maliyeti hesaplar"""
        return rooms_per_night * total_nights * self.pricing_rates["hotel_room_per_night"]
    
    def _calculate_av_cost(self, duration_days: int, av_config: Dict) -> float:
        """A/V ekipman maliyeti hesaplar"""
        base_cost = duration_days * self.pricing_rates["av_equipment_daily"]
        
        # Projector lumens'e göre ek maliyet
        lumens = av_config.get('projector_lumens', 0)
        if lumens > 5000:
            base_cost *= 1.5  # Yüksek lümenli projektör
        elif lumens > 3000:
            base_cost *= 1.2  # Orta lümenli projektör
        
        return base_cost
    
    def _calculate_catering_cost(self, capacity: int, duration_days: int) -> float:
        """Catering maliyeti hesaplar"""
        # Günde 3 öğün varsayımı
        meals_per_day = 3
        return capacity * duration_days * meals_per_day * self.pricing_rates["catering_per_person"]
    
    def _calculate_meeting_room_cost(self, breakout_rooms: int, duration_days: int) -> float:
        """Toplantı salonu maliyeti hesaplar"""
        return breakout_rooms * duration_days * self.pricing_rates["meeting_room_daily"]
    
    def _calculate_duration_days(self, start_date: str, end_date: str) -> int:
        """Tarih aralığından gün sayısı hesaplar"""
        try:
            from datetime import datetime
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            return (end - start).days
        except:
            return 1  # Varsayılan 1 gün
    
    def generate_budget_csv(self, budget_data: Dict, notice_id: str) -> str:
        """Bütçe verilerini CSV formatında döndürür"""
        import csv
        import io
        
        buf = io.StringIO()
        writer = csv.writer(buf)
        
        # Header
        writer.writerow(['Category', 'Amount (USD)', 'Description'])
        
        # Budget breakdown
        writer.writerow(['Accommodation', f"{budget_data['accommodation']:.2f}", 
                        f"{budget_data['parameters']['rooms_per_night']} rooms × {budget_data['parameters']['total_nights']} nights"])
        
        writer.writerow(['AV Equipment', f"{budget_data['av_equipment']:.2f}", 
                        f"{budget_data['parameters']['duration_days']} days"])
        
        writer.writerow(['Catering', f"{budget_data['catering']:.2f}", 
                        f"{budget_data['parameters']['capacity']} people × {budget_data['parameters']['duration_days']} days"])
        
        writer.writerow(['Meeting Rooms', f"{budget_data['meeting_rooms']:.2f}", 
                        f"{budget_data['parameters']['breakout_rooms']} rooms × {budget_data['parameters']['duration_days']} days"])
        
        writer.writerow(['Setup Fee', f"{budget_data['setup']:.2f}", 'One-time setup'])
        
        writer.writerow(['Subtotal', f"{budget_data['subtotal']:.2f}", ''])
        writer.writerow(['Tax', f"{budget_data['tax']:.2f}", f"{budget_data['pricing_rates']['tax_rate']*100:.1f}%"])
        writer.writerow(['TOTAL', f"{budget_data['total']:.2f}", ''])
        
        return buf.getvalue()

# Test function
def test_budget_estimation():
    """Test budget estimation"""
    agent = BudgetEstimatorAgent()
    
    # Sample SOW payload
    sow_payload = {
        "room_block": {
            "total_rooms_per_night": 80,
            "total_nights": 3
        },
        "function_space": {
            "general_session": {"capacity": 120},
            "breakout_rooms": {"count": 4}
        },
        "av": {
            "projector_lumens": 5000
        },
        "period_of_performance": {
            "start": "2024-11-01T00:00:00Z",
            "end": "2024-11-03T00:00:00Z"
        }
    }
    
    budget = agent.estimate_budget(sow_payload)
    
    print(f"Total Budget: ${budget['total']:,.2f}")
    print(f"Accommodation: ${budget['accommodation']:,.2f}")
    print(f"AV Equipment: ${budget['av_equipment']:,.2f}")
    print(f"Catering: ${budget['catering']:,.2f}")
    
    # Generate CSV
    csv_data = agent.generate_budget_csv(budget, "TEST001")
    print("\nCSV Data:")
    print(csv_data)

if __name__ == "__main__":
    test_budget_estimation()

