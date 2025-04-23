import africastalking
import logging
import os
import re
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings
from django.apps import AppConfig
from decimal import Decimal
from .models import Asset, Site, Human_resource

# Configure logging
logger = logging.getLogger(__name__)

class SMSService:
    @staticmethod
    def initialize_sdk():
        username = settings.AFRICASTALKING_USERNAME
        api_key =  'atsk_ce82959658d9978a5c41d83de565ee5f9deeb3e0af0a96a0e8e6e613c656f79037ff8927'
        
        if not username or not api_key:
            logger.error("AfricasTalking credentials missing: username or API key not configured")
            return None
            
        try:
            africastalking.initialize(username, api_key)
            return africastalking.SMS
        except Exception as e:
            logger.error(f"Failed to initialize AfricasTalking SDK: {str(e)}")
            return None
    

    @staticmethod
    def format_phone_number(phone):
        if not phone:
            return None
        clean_number = re.sub(r'\D', '', phone)
        if not phone.startswith('+'):
           if clean_number.startswith('0'):
               clean_number = '254' + clean_number[1:]
           else:
               clean_number = '254' + clean_number
        return '+' + clean_number
     
    @staticmethod
    def send_sms(message, recipients):
        if not recipients:
            logger.warning("No recipients provided for SMS alert")
            return None
        
        # Format phone numbers properly
        formatted_recipients = []
        for recipient in recipients:
            formatted = SMSService.format_phone_number(recipient)
            if formatted:
                formatted_recipients.append(formatted)
        
        if not formatted_recipients:
            logger.warning("No valid phone numbers after formatting")
            return None
            
        logger.info(f"Attempting to send SMS to {formatted_recipients}")
        
        try:
            sms = SMSService.initialize_sdk()
            if not sms:
                logger.error("Failed to initialize SMS service")
                return None
                
            response = sms.send(message, formatted_recipients)
            logger.info(f"SMS sent successfully: {response}")
            return response
        except Exception as e:
            logger.error(f"Failed to send SMS: {str(e)}")
            return None

class RecipientService:
    @staticmethod
    def get_site_manager_numbers(site):
        managers = Human_resource.objects.filter(
            site=site, 
            role__icontains='manager'
        )
        
        phone_numbers = []
        for manager in managers:
            if hasattr(manager, 'phone_number') and manager.phone_number:
                phone_numbers.append(manager.phone_number)
                
        if not phone_numbers:
            logger.debug(f"No manager phone numbers found for site {site.name}")
            
        return phone_numbers
    
    @staticmethod
    def get_site_owner_number(site):
        if site.owner and hasattr(site.owner, 'phone_number') and site.owner.phone_number:
            return [site.owner.phone_number]
        logger.debug(f"No owner phone number found for site {site.name}")
        return []
    
    @staticmethod
    def get_default_recipients():
        default_recipients = getattr(settings, 'INVENTORY_ALERT_RECIPIENTS', [])
        if not default_recipients:
            logger.debug("No default recipients configured in settings")
        return default_recipients
    
    @staticmethod
    def get_recipients_for_site(site):
        recipients = []
        recipients.extend(RecipientService.get_site_manager_numbers(site))
        recipients.extend(RecipientService.get_site_owner_number(site))
        recipients.extend(RecipientService.get_default_recipients())
        
        # Remove duplicates while preserving order
        unique_recipients = []
        for recipient in recipients:
            if recipient and recipient not in unique_recipients:
                unique_recipients.append(recipient)
        
        logger.info(f"Found {len(unique_recipients)} recipients for site {site.name}: {unique_recipients}")
        return unique_recipients

class InventoryAlertService:
    @staticmethod
    def format_asset_created_message(asset):
        return (
            f"INVENTORY ALERT: New {asset.type} '{asset.name}' added to inventory at "
            f"{asset.site.name}. Quantity: {asset.quantity_in_stock} {asset.units}. "
            f"S/N: {asset.serial_number or 'N/A'}"
        )
    
    @staticmethod
    def format_asset_updated_message(asset, old_quantity):
        quantity_diff = asset.quantity_in_stock - old_quantity
        
        if quantity_diff > 0:
            action = f"ADDED {quantity_diff} {asset.units}"
        else:
            action = f"REMOVED {abs(quantity_diff)} {asset.units}"
            
        return (
            f"INVENTORY ALERT: {asset.type.capitalize()} '{asset.name}' at {asset.site.name} - "
            f"{action}. New quantity: {asset.quantity_in_stock} {asset.units}"
        )
    
    @staticmethod
    def format_asset_deleted_message(asset):
        return (
            f"INVENTORY ALERT: {asset.type.capitalize()} '{asset.name}' COMPLETELY REMOVED "
            f"from inventory at {asset.site.name}. Previous quantity: {asset.quantity_in_stock} {asset.units}"
        )
    
    @staticmethod
    def send_asset_alert(asset, message_type, old_quantity=None):
        # Format appropriate message
        if message_type == "created":
            message = InventoryAlertService.format_asset_created_message(asset)
        elif message_type == "updated":
            message = InventoryAlertService.format_asset_updated_message(asset, old_quantity)
        elif message_type == "deleted":
            message = InventoryAlertService.format_asset_deleted_message(asset)
        else:
            logger.error(f"Invalid message type: {message_type}")
            return
        
        # Get recipients for this site
        recipients = RecipientService.get_recipients_for_site(asset.site)
        
        if not recipients:
            logger.warning(f"No recipients found for alert on asset {asset.id} ({asset.name})")
            return None
            
        # Log recipients for debugging
        logger.info(f"Sending SMS alert for {message_type} event - asset: {asset.name}, message: {message}")
        
        # Send the SMS
        return SMSService.send_sms(message, recipients)

class HumanResourceAlertService:
    @staticmethod
    def format_hr_created_message(human_resource):
        return (
            f"PERSONNEL ALERT: New {human_resource.role} '{human_resource.name}' added to staff at "
            f"{human_resource.site.name}. Contact: {human_resource.phone_number or 'N/A'}"
        )
    
    @staticmethod
    def format_hr_deleted_message(human_resource):
        return (
            f"PERSONNEL ALERT: {human_resource.role.capitalize()} '{human_resource.name}' REMOVED "
            f"from staff at {human_resource.site.name}."
        )
    
    @staticmethod
    def send_hr_alert(human_resource, message_type):
        # Format appropriate message
        if message_type == "created":
            message = HumanResourceAlertService.format_hr_created_message(human_resource)
        elif message_type == "deleted":
            message = HumanResourceAlertService.format_hr_deleted_message(human_resource)
        else:
            logger.error(f"Invalid message type: {message_type}")
            return
        
        # Get recipients for this site
        recipients = RecipientService.get_recipients_for_site(human_resource.site)
        
        if not recipients:
            logger.warning(f"No recipients found for alert on human resource {human_resource.id} ({human_resource.name})")
            return None
            
        # Log recipients for debugging
        logger.info(f"Sending SMS alert for {message_type} event - human resource: {human_resource.name}, message: {message}")
        
        # Send the SMS
        return SMSService.send_sms(message, recipients)

# Dictionary to track asset quantities for comparison
_asset_quantities = {}

@receiver(post_save, sender=Asset)
def asset_created_or_updated(sender, instance, created, **kwargs):
    logger.debug(f"Asset signal triggered: created={created}, asset_id={instance.id}")
    
    if created:
        logger.info(f"New asset created: {instance.name} (ID: {instance.id})")
        InventoryAlertService.send_asset_alert(instance, "created")
        _asset_quantities[instance.id] = instance.quantity_in_stock
        return
    
    old_quantity = _asset_quantities.get(instance.id)
    if old_quantity is not None and old_quantity != instance.quantity_in_stock:
        logger.info(f"Asset quantity updated: {instance.name} (ID: {instance.id}), "
                  f"old: {old_quantity}, new: {instance.quantity_in_stock}")
        InventoryAlertService.send_asset_alert(instance, "updated", old_quantity)
    
    _asset_quantities[instance.id] = instance.quantity_in_stock

@receiver(post_delete, sender=Asset)
def asset_deleted(sender, instance, **kwargs):
    logger.info(f"Asset deleted: {instance.name} (ID: {instance.id})")
    InventoryAlertService.send_asset_alert(instance, "deleted")
    
    # Clean up the tracking dictionary
    if instance.id in _asset_quantities:
        del _asset_quantities[instance.id]

# Signal handlers for Human_resource model
@receiver(post_save, sender=Human_resource)
def human_resource_created_or_updated(sender, instance, created, **kwargs):
    logger.debug(f"Human resource signal triggered: created={created}, hr_id={instance.id}")
    
    # Handle new human resource creation
    if created:
        logger.info(f"New human resource created: {instance.name} (ID: {instance.id})")
        HumanResourceAlertService.send_hr_alert(instance, "created")

@receiver(post_delete, sender=Human_resource)
def human_resource_deleted(sender, instance, **kwargs):
    logger.info(f"Human resource deleted: {instance.name} (ID: {instance.id})")
    HumanResourceAlertService.send_hr_alert(instance, "deleted")

class InventoryAlertConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'foreman'
    
    def ready(self):
        # This ensures signals are connected when Django starts
        logger.info("Initializing inventory alert system")
        load_initial_asset_quantities()

# Load initial asset quantities on application startup
def load_initial_asset_quantities():
    logger.info("Loading initial asset quantities")
    try:
        assets = Asset.objects.all()
        count = 0
        for asset in assets:
            _asset_quantities[asset.id] = asset.quantity_in_stock
            count += 1
        logger.info(f"Loaded {count} asset quantities successfully")
    except Exception as e:
        logger.error(f"Failed to load initial asset quantities: {str(e)}")