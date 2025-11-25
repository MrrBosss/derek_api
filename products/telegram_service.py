import requests
import logging
from django.conf import settings
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class TelegramService:
    """Service for sending notifications to Telegram"""
    
    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """
        Send a message to the configured Telegram chat
        
        Args:
            message: The message text to send
            parse_mode: Parse mode for the message (HTML, Markdown, etc.)
            
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info(f"Telegram message sent successfully. Response: {response.json()}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Telegram message: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Telegram message: {str(e)}")
            return False
    
    def send_sale_notification(self, order_data: Dict[str, Any]) -> bool:
        """
        Send a formatted sale notification to Telegram
        
        Args:
            order_data: Dictionary containing order information
            
        Returns:
            bool: True if notification was sent successfully
        """
        try:
            # Format the sale notification message
            message = self._format_sale_message(order_data)
            return self.send_message(message)
            
        except Exception as e:
            logger.error(f"Error creating sale notification: {str(e)}")
            return False
    
    def _format_sale_message(self, order_data: Dict[str, Any]) -> str:
        """
        Format the order data into a readable Telegram message
        
        Args:
            order_data: Dictionary containing order information
            
        Returns:
            str: Formatted message for Telegram
        """
        # Extract order information
        order_id = order_data.get('id', 'N/A')
        customer_name = order_data.get('name', 'Неизвестно')
        phone_number = order_data.get('phone_number', 'Не указан')
        order_date = order_data.get('order_date', 'Не указана')
        items = order_data.get('items', [])
        
        # Start building the message
        message_lines = [
            "🎉 <b>НОВАЯ ПРОДАЖА!</b> 🎉",
            "",
            f"📋 <b>Заказ №:</b> {order_id}",
            f"👤 <b>Клиент:</b> {customer_name}",
            f"📞 <b>Телефон:</b> {phone_number}",
            f"📅 <b>Дата заказа:</b> {order_date}",
            "",
            "🛒 <b>Товары:</b>"
        ]
        
        total_amount = 0
        
        # Add items to the message
        for item in items:
            product_name = item.get('product_name', 'Неизвестный товар')
            color = item.get('color', 'Не указан')
            weight = item.get('weight', 'Не указан')
            quantity = item.get('quantity', 0)
            price = item.get('price', 0)
            item_total = price * quantity
            total_amount += item_total
            
            item_lines = [
                f"  • <b>{product_name}</b>",
                f"    🎨 Цвет: {color}",
                f"    ⚖️ Вес: {weight}",
                f"    📦 Количество: {quantity}",
                f"    💰 Цена: {price:,.0f} $",
                f"    💵 Сумма: {item_total:,.0f} $",
                ""
            ]
            message_lines.extend(item_lines)
        
        # Add total amount
        message_lines.extend([
            f"💎 <b>ОБЩАЯ СУММА: {total_amount:,.0f} $</b>",
            "",
            "✅ Обработайте заказ в кратчайшие сроки!"
        ])
        
        return "\n".join(message_lines)


# Create a singleton instance
telegram_service = TelegramService()
