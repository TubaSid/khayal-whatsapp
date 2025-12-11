"""
WhatsApp API Client
Wrapper around WhatsApp Graph API for message handling
"""

import requests
import os
from typing import Dict, Optional


class WhatsAppClient:
    """WhatsApp Graph API client for sending and receiving messages"""
    
    def __init__(self, phone_number_id: str, access_token: str):
        """
        Initialize WhatsApp client
        
        Args:
            phone_number_id: WhatsApp Business Phone Number ID
            access_token: WhatsApp API access token
        """
        self.phone_number_id = phone_number_id
        self.access_token = access_token
        self.base_url = f"https://graph.facebook.com/v18.0/{phone_number_id}"
    
    def send_message(self, to_number: str, message_text: str) -> Dict:
        """
        Send a WhatsApp text message
        
        Args:
            to_number: Recipient phone number
            message_text: Message content
            
        Returns:
            API response dictionary
        """
        url = f"{self.base_url}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number,
            "type": "text",
            "text": {"body": message_text}
        }
        
        try:
            response = requests.post(url, json=data, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to send WhatsApp message: {e}")
            return {"error": str(e)}
    
    def mark_message_read(self, message_id: str) -> Dict:
        """
        Mark a received message as read
        
        Args:
            message_id: WhatsApp message ID
            
        Returns:
            API response dictionary
        """
        url = f"{self.base_url}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        
        try:
            response = requests.post(url, json=data, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to mark message as read: {e}")
            return {"error": str(e)}


__all__ = ["WhatsAppClient"]
