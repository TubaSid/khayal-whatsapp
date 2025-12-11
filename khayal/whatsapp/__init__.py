"""WhatsApp API wrapper for sending and receiving messages"""

import requests
from typing import Dict, Optional
from ..config import Config
from ..utils.logger import get_logger

logger = get_logger(__name__)


class WhatsAppClient:
    """WhatsApp messaging client"""
    
    def __init__(self, phone_number_id: str, access_token: str):
        """
        Initialize WhatsApp client
        
        Args:
            phone_number_id: WhatsApp business phone number ID
            access_token: WhatsApp API access token
        """
        self.phone_number_id = phone_number_id
        self.access_token = access_token
        self.api_version = "v18.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
    
    def send_message(self, to_number: str, message_text: str) -> Dict:
        """
        Send a text message to a WhatsApp user
        
        Args:
            to_number: Recipient phone number
            message_text: Message text to send
        
        Returns:
            Response dict with message ID or error
        """
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
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
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending message to {to_number}: {e}")
            return {"error": str(e)}
    
    def mark_as_read(self, message_id: str) -> bool:
        """
        Mark a message as read
        
        Args:
            message_id: WhatsApp message ID
        
        Returns:
            True if successful, False otherwise
        """
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
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
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.debug(f"Could not mark message {message_id} as read: {e}")
            return False
