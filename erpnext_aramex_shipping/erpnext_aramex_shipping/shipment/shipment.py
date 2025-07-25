import frappe
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from erpnext_aramex_shipping.api.aramex import get_shipping_rates, create_shipment, generate_shipping_label, track_shipment


def validate_address_data(address_data: Dict[str, Any], address_type: str) -> List[str]:
    """
    Validate address data for completeness
    
    Args:
        address_data: Dictionary containing address information
        address_type: Type of address (shipper/consignee)
        
    Returns:
        List of validation errors
    """
    errors = []
    required_fields = {
        'name': f'{address_type}_name',
        'address_line1': f'{address_type}_address_line1',
        'city': f'{address_type}_city',
        'country_code': f'{address_type}_country_code',
        'phone': f'{address_type}_phone',
        'email': f'{address_type}_email'
    }
    
    for field_name, field_key in required_fields.items():
        if not address_data.get(field_key):
            errors.append(f"{address_type.title()} {field_name.replace('_', ' ')} is required")
    
    # Validate email format
    email = address_data.get(f'{address_type}_email')
    if email and '@' not in email:
        errors.append(f"{address_type.title()} email format is invalid")
    
    # Validate country code format
    country_code = address_data.get(f'{address_type}_country_code')
    if country_code and len(country_code) != 2:
        errors.append(f"{address_type.title()} country code must be 2 characters")
    
    return errors


def validate_shipment_data(shipment_data: Dict[str, Any]) -> List[str]:
    """
    Validate complete shipment data
    
    Args:
        shipment_data: Dictionary containing shipment information
        
    Returns:
        List of validation errors
    """
    errors = []
    
    # Validate shipper address
    errors.extend(validate_address_data(shipment_data, 'shipper'))
    
    # Validate consignee address
    errors.extend(validate_address_data(shipment_data, 'consignee'))
    
    # Validate package dimensions
    try:
        length = float(shipment_data.get('length', 0))
        width = float(shipment_data.get('width', 0))
        height = float(shipment_data.get('height', 0))
        weight = float(shipment_data.get('weight', 0))
        
        if length <= 0 or width <= 0 or height <= 0:
            errors.append("Package dimensions must be greater than 0")
        
        if weight <= 0:
            errors.append("Package weight must be greater than 0")
            
    except (ValueError, TypeError):
        errors.append("Package dimensions and weight must be valid numbers")
    
    # Validate number of pieces
    try:
        pieces = int(shipment_data.get('number_of_pieces', 0))
        if pieces <= 0:
            errors.append("Number of pieces must be greater than 0")
    except (ValueError, TypeError):
        errors.append("Number of pieces must be a valid number")
    
    # Validate description
    if not shipment_data.get('description'):
        errors.append("Package description is required")
    
    return errors


@frappe.whitelist()
def fetch_shipping_rates(shipment_data: str) -> Dict[str, Any]:
    """
    Fetch shipping rates from Aramex API with validation
    
    Args:
        shipment_data: JSON string containing shipment information
        
    Returns:
        Dictionary containing rates or error information
    """
    try:
        # Parse JSON data
        if isinstance(shipment_data, str):
            data = json.loads(shipment_data)
        else:
            data = shipment_data
        
        # Validate required data for rate calculation
        validation_errors = []
        
        # Basic validation for rate calculation
        required_fields = [
            'origin_city', 'origin_country_code',
            'destination_city', 'destination_country_code',
            'weight', 'length', 'width', 'height'
        ]
        
        for field in required_fields:
            if not data.get(field):
                validation_errors.append(f"{field.replace('_', ' ').title()} is required")
        
        if validation_errors:
            return {
                'success': False,
                'rates': [],
                'message': f"Validation errors: {'; '.join(validation_errors)}"
            }
        
        # Add reference number if not provided
        if not data.get('reference'):
            data['reference'] = f"RATE_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Call Aramex API
        result = get_shipping_rates(data)
        
        # Log the rate request
        frappe.logger().info(f"Rate request for reference {data.get('reference')}: {result.get('message')}")
        
        return result
        
    except json.JSONDecodeError:
        return {
            'success': False,
            'rates': [],
            'message': 'Invalid JSON data provided'
        }
    except Exception as e:
        frappe.log_error(f"Error in fetch_shipping_rates: {str(e)}", "Shipment Rate Fetch Error")
        return {
            'success': False,
            'rates': [],
            'message': f'Error fetching shipping rates: {str(e)}'
        }


@frappe.whitelist()
def create_aramex_shipment(shipment_data: str) -> Dict[str, Any]:
    """
    Create a shipment with Aramex API after validation
    
    Args:
        shipment_data: JSON string containing complete shipment information
        
    Returns:
        Dictionary containing shipment creation result
    """
    try:
        # Parse JSON data
        if isinstance(shipment_data, str):
            data = json.loads(shipment_data)
        else:
            data = shipment_data
        
        # Validate shipment data
        validation_errors = validate_shipment_data(data)
        
        if validation_errors:
            return {
                'success': False,
                'message': f"Validation errors: {'; '.join(validation_errors)}"
            }
        
        # Add reference number if not provided
        if not data.get('reference'):
            data['reference'] = f"SHIP_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Set default values for optional fields
        defaults = {
            'product_group': 'EXP',
            'product_type': 'PPX',
            'payment_type': 'P',
            'dimension_unit': 'CM',
            'weight_unit': 'KG',
            'currency_code': 'AED',
            'goods_origin_country': data.get('shipper_country_code', 'AE'),
            'cod_amount': 0,
            'insurance_amount': 0,
            'collect_amount': 0
        }
        
        for key, value in defaults.items():
            if not data.get(key):
                data[key] = value
        
        # Call Aramex API
        result = create_shipment(data)
        
        if result.get('success'):
            # Save shipment record in ERPNext
            try:
                shipment_doc = frappe.get_doc({
                    'doctype': 'Aramex Shipment',
                    'reference': data.get('reference'),
                    'aramex_shipment_id': result.get('shipment_id'),
                    'foreign_hawb': result.get('foreign_hawb'),
                    'shipper_name': data.get('shipper_name'),
                    'shipper_company': data.get('shipper_company'),
                    'consignee_name': data.get('consignee_name'),
                    'consignee_company': data.get('consignee_company'),
                    'weight': data.get('weight'),
                    'dimensions': f"{data.get('length')}x{data.get('width')}x{data.get('height')} {data.get('dimension_unit')}",
                    'description': data.get('description'),
                    'status': 'Created',
                    'label_url': result.get('label_url'),
                    'creation_date': datetime.now(),
                    'shipment_data': json.dumps(data)
                })
                shipment_doc.insert()
                frappe.db.commit()
                
                result['erpnext_shipment_id'] = shipment_doc.name
                
            except Exception as e:
                frappe.log_error(f"Error saving shipment record: {str(e)}", "Shipment Save Error")
                # Don't fail the entire operation if saving fails
                result['warning'] = 'Shipment created but failed to save in ERPNext'
        
        # Log the shipment creation
        frappe.logger().info(f"Shipment creation for reference {data.get('reference')}: {result.get('message')}")
        
        return result
        
    except json.JSONDecodeError:
        return {
            'success': False,
            'message': 'Invalid JSON data provided'
        }
    except Exception as e:
        frappe.log_error(f"Error in create_aramex_shipment: {str(e)}", "Shipment Creation Error")
        return {
            'success': False,
            'message': f'Error creating shipment: {str(e)}'
        }


@frappe.whitelist()
def print_shipping_label(shipment_id: str) -> Dict[str, Any]:
    """
    Generate and retrieve shipping label
    
    Args:
        shipment_id: Aramex shipment ID
        
    Returns:
        Dictionary containing label information
    """
    try:
        if not shipment_id:
            return {
                'success': False,
                'message': 'Shipment ID is required'
            }
        
        # Call Aramex API
        result = generate_shipping_label(shipment_id)
        
        if result.get('success'):
            # Update shipment record with label URL if exists
            try:
                shipment_records = frappe.get_all(
                    'Aramex Shipment',
                    filters={'aramex_shipment_id': shipment_id},
                    fields=['name']
                )
                
                if shipment_records:
                    shipment_doc = frappe.get_doc('Aramex Shipment', shipment_records[0].name)
                    shipment_doc.label_url = result.get('label_url')
                    shipment_doc.save()
                    frappe.db.commit()
                    
            except Exception as e:
                frappe.log_error(f"Error updating shipment label URL: {str(e)}", "Label Update Error")
        
        # Log the label generation
        frappe.logger().info(f"Label generation for shipment {shipment_id}: {result.get('message')}")
        
        return result
        
    except Exception as e:
        frappe.log_error(f"Error in print_shipping_label: {str(e)}", "Label Print Error")
        return {
            'success': False,
            'message': f'Error generating shipping label: {str(e)}'
        }


@frappe.whitelist()
def track_aramex_shipment(shipment_id: str) -> Dict[str, Any]:
    """
    Track a shipment and update status
    
    Args:
        shipment_id: Aramex shipment ID or tracking number
        
    Returns:
        Dictionary containing tracking information
    """
    try:
        if not shipment_id:
            return {
                'success': False,
                'message': 'Shipment ID is required'
            }
        
        # Call Aramex API
        result = track_shipment(shipment_id)
        
        if result.get('success') and result.get('tracking_results'):
            # Update shipment record with latest tracking info
            try:
                shipment_records = frappe.get_all(
                    'Aramex Shipment',
                    filters={'aramex_shipment_id': shipment_id},
                    fields=['name']
                )
                
                if shipment_records:
                    tracking_result = result['tracking_results'][0]
                    shipment_doc = frappe.get_doc('Aramex Shipment', shipment_records[0].name)
                    shipment_doc.status = tracking_result.get('status', 'Unknown')
                    shipment_doc.tracking_data = json.dumps(result['tracking_results'])
                    shipment_doc.last_tracking_update = datetime.now()
                    shipment_doc.save()
                    frappe.db.commit()
                    
            except Exception as e:
                frappe.log_error(f"Error updating shipment tracking: {str(e)}", "Tracking Update Error")
        
        # Log the tracking request
        frappe.logger().info(f"Tracking request for shipment {shipment_id}: {result.get('message')}")
        
        return result
        
    except Exception as e:
        frappe.log_error(f"Error in track_aramex_shipment: {str(e)}", "Shipment Tracking Error")
        return {
            'success': False,
            'message': f'Error tracking shipment: {str(e)}'
        }


@frappe.whitelist()
def get_shipment_history(limit: int = 50) -> Dict[str, Any]:
    """
    Get shipment history from ERPNext
    
    Args:
        limit: Number of records to retrieve
        
    Returns:
        Dictionary containing shipment history
    """
    try:
        shipments = frappe.get_all(
            'Aramex Shipment',
            fields=[
                'name', 'reference', 'aramex_shipment_id', 'foreign_hawb',
                'shipper_name', 'consignee_name', 'weight', 'dimensions',
                'description', 'status', 'creation_date', 'last_tracking_update'
            ],
            order_by='creation_date desc',
            limit=limit
        )
        
        return {
            'success': True,
            'shipments': shipments,
            'message': f'Retrieved {len(shipments)} shipment records'
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting shipment history: {str(e)}", "Shipment History Error")
        return {
            'success': False,
            'shipments': [],
            'message': f'Error retrieving shipment history: {str(e)}'
        }


def get_country_codes() -> List[Dict[str, str]]:
    """
    Get list of supported country codes
    
    Returns:
        List of country code dictionaries
    """
    return [
        {'code': 'AE', 'name': 'United Arab Emirates'},
        {'code': 'SA', 'name': 'Saudi Arabia'},
        {'code': 'KW', 'name': 'Kuwait'},
        {'code': 'QA', 'name': 'Qatar'},
        {'code': 'BH', 'name': 'Bahrain'},
        {'code': 'OM', 'name': 'Oman'},
        {'code': 'JO', 'name': 'Jordan'},
        {'code': 'LB', 'name': 'Lebanon'},
        {'code': 'EG', 'name': 'Egypt'},
        {'code': 'US', 'name': 'United States'},
        {'code': 'GB', 'name': 'United Kingdom'},
        {'code': 'DE', 'name': 'Germany'},
        {'code': 'FR', 'name': 'France'},
        {'code': 'IN', 'name': 'India'},
        {'code': 'PK', 'name': 'Pakistan'},
        {'code': 'BD', 'name': 'Bangladesh'},
        {'code': 'LK', 'name': 'Sri Lanka'},
        {'code': 'PH', 'name': 'Philippines'},
        {'code': 'MY', 'name': 'Malaysia'},
        {'code': 'SG', 'name': 'Singapore'},
        {'code': 'TH', 'name': 'Thailand'},
        {'code': 'CN', 'name': 'China'},
        {'code': 'JP', 'name': 'Japan'},
        {'code': 'KR', 'name': 'South Korea'},
        {'code': 'AU', 'name': 'Australia'},
        {'code': 'CA', 'name': 'Canada'}
    ]


@frappe.whitelist()
def get_shipping_configuration() -> Dict[str, Any]:
    """
    Get shipping configuration data for the frontend
    
    Returns:
        Dictionary containing configuration data
    """
    try:
        return {
            'success': True,
            'country_codes': get_country_codes(),
            'dimension_units': [
                {'code': 'CM', 'name': 'Centimeters'},
                {'code': 'IN', 'name': 'Inches'}
            ],
            'weight_units': [
                {'code': 'KG', 'name': 'Kilograms'},
                {'code': 'LB', 'name': 'Pounds'}
            ],
            'currency_codes': [
                {'code': 'AED', 'name': 'UAE Dirham'},
                {'code': 'USD', 'name': 'US Dollar'},
                {'code': 'EUR', 'name': 'Euro'},
                {'code': 'GBP', 'name': 'British Pound'},
                {'code': 'SAR', 'name': 'Saudi Riyal'}
            ],
            'product_groups': [
                {'code': 'EXP', 'name': 'Express'},
                {'code': 'DOM', 'name': 'Domestic'}
            ],
            'product_types': [
                {'code': 'PPX', 'name': 'Prepaid Express'},
                {'code': 'PDX', 'name': 'Prepaid Deferred'},
                {'code': 'CDS', 'name': 'Cash on Delivery'}
            ]
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting shipping configuration: {str(e)}", "Configuration Error")
        return {
            'success': False,
            'message': f'Error getting configuration: {str(e)}'
        }

#test