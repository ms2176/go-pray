#!/usr/bin/env python3
"""
Prayer Times Notification Script
Checks current time against prayer times and sends notifications via ntfy
"""

import requests
from datetime import datetime
import json
import os
import sys

# Configuration from environment variables
NTFY_TOPIC = os.getenv('NTFY_TOPIC', 'your-unique-topic-name')
LATITUDE = os.getenv('LATITUDE', '25.3463')  # Sharjah
LONGITUDE = os.getenv('LONGITUDE', '55.4209')  # Sharjah
CALCULATION_METHOD = os.getenv('CALCULATION_METHOD', '4')  # 4 = Umm Al-Qura University, Makkah

# Prayer time tolerance in minutes (how early to send notification)
NOTIFICATION_WINDOW = 5

def get_prayer_times():
    """
    Fetch prayer times from aladhan.com API
    Method 4 is Umm Al-Qura (used in Saudi Arabia)
    You can change to method 3 for MWL or method 2 for ISNA
    """
    try:
        # Using the Aladhan API - reliable and free
        url = f"http://api.aladhan.com/v1/timings"
        params = {
            'latitude': LATITUDE,
            'longitude': LONGITUDE,
            'method': CALCULATION_METHOD
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data['code'] == 200:
            timings = data['data']['timings']
            # Extract the 5 daily prayers
            prayers = {
                'Fajr': timings['Fajr'],
                'Dhuhr': timings['Dhuhr'],
                'Asr': timings['Asr'],
                'Maghrib': timings['Maghrib'],
                'Isha': timings['Isha']
            }
            return prayers
        else:
            print(f"API returned error code: {data['code']}")
            return None
            
    except Exception as e:
        print(f"Error fetching prayer times: {e}")
        return None

def send_notification(prayer_name, prayer_time):
    """Send notification via ntfy.sh"""
    try:
        url = f"https://ntfy.sh/{NTFY_TOPIC}"
        
        # You can customize the notification
        data = {
            "topic": NTFY_TOPIC,
            "title": f"🕌 {prayer_name} Time",
            "message": f"It's time for {prayer_name} prayer ({prayer_time})",
            "priority": 5,  # High priority
            "tags": ["mosque", "pray"]
        }
        
        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()
        
        print(f"✅ Notification sent for {prayer_name} at {prayer_time}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending notification: {e}")
        return False

def check_and_notify():
    """Main function to check prayer times and send notifications"""
    
    # Get current time
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    
    print(f"🕐 Current time: {current_time}")
    
    # Fetch prayer times
    prayers = get_prayer_times()
    
    if not prayers:
        print("Failed to fetch prayer times")
        sys.exit(1)
    
    print(f"📅 Today's prayer times: {json.dumps(prayers, indent=2)}")
    
    # Check each prayer time
    for prayer_name, prayer_time in prayers.items():
        # Parse prayer time (format: HH:MM)
        prayer_hour, prayer_minute = map(int, prayer_time.split(':'))
        
        # Check if current time matches prayer time (within tolerance window)
        if now.hour == prayer_hour and abs(now.minute - prayer_minute) <= NOTIFICATION_WINDOW:
            print(f"🔔 Time for {prayer_name}!")
            send_notification(prayer_name, prayer_time)
            
            # Only send one notification per run
            return
    
    print("⏳ No prayer time right now")

if __name__ == "__main__":
    check_and_notify()
