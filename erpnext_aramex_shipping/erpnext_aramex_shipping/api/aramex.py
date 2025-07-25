import frappe
import requests
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

#
class AramexAPI:
    """
    Aramex API integration class for handling all shipping operations
    """
    
    def __init__(self):
        self.settings = self.get_aramex_settings()
        self.base_url = self.get_base_url()
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def get_aramex_settings(self) -> Dict[str, Any]:
        """Get Aramex API settings from ERPNext configuration"""
        try:
            # In a real implementation, this would fetch from a Settings doctype
            # For now, we'll use site config or environment variables
            settings = frappe.get_site_config().get('aramex_settings', {})
            
            if not settings:
                # Fallback to default test settings
                settings = {
                    'username': frappe.conf.get('aramex_username', 'testuser'),
                    'password': frappe.conf.get('aramex_password', 'testpass'),
                    'account_number': frappe.conf.get('aramex_account_number', '12345'),
                    'account_pin': frappe.conf.get('aramex_account_pin', '123456'),
                    'account_entity': frappe.conf.get('aramex_account_entity', 'AMM'),
                    'account_country_code': frappe.conf.get('aramex_account_country_code', 'JO'),
                    'test_mode': frappe.conf.get('aramex_test_mode', True)
                }
            
            return settings
        except Exception as e:
            frappe.log_error(f"Error getting Aramex settings: {str(e)}", "Aramex API Settings Error")
            return {}
    
    def get_base_url(self) -> str:
        """Get the appropriate Aramex API base URL"""
        if self.settings.get('test_mode', True):
            return 'https://ws.dev.aramex.net'
        else:
            return 'https://ws.aramex.net'
    
    def get_client_info(self) -> Dict[str, Any]:
        """Get client information for API requests"""
        return {
            'UserName': self.settings.get('username'),
            'Password': self.settings.get('password'),
            'Version': 'v1.0',
            'AccountNumber': self.settings.get('account_number'),
            'AccountPin': self.settings.get('account_pin'),
            'AccountEntity': self.settings.get('account_entity'),
            'AccountCountryCode': self.settings.get('account_country_code'),
            'Source': 24  # ERPNext integration source code
        }
    
    def make_api_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make a request to Aramex API with error handling"""
        try:
            url = f"{self.base_url}/{endpoint}"
            
            frappe.logger().info(f"Making Aramex API request to: {url}")
            
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Check for API-level errors
            if result.get('HasErrors', False):
                error_messages = []
                for notification in result.get('Notifications', []):
                    if notification.get('Code') != '000':  # Success code
                        error_messages.append(notification.get('Message', 'Unknown error'))
                
                if error_messages:
                    raise Exception(f"Aramex API Error: {'; '.join(error_messages)}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error connecting to Aramex API: {str(e)}"
            frappe.log_error(error_msg, "Aramex API Network Error")
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Aramex API request failed: {str(e)}"
            frappe.log_error(error_msg, "Aramex API Error")
            raise Exception(error_msg)


@frappe.whitelist()
def get_shipping_rates(shipment_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get shipping rates from Aramex API
    
    Args:
        shipment_data: Dictionary containing shipment information
        
    Returns:
        Dictionary containing shipping rates and services
    """
    try:
        api = AramexAPI()
        
        # Prepare the rate calculation request
        payload = {
            'ClientInfo': api.get_client_info(),
            'Transaction': {
                'Reference1': shipment_data.get('reference', ''),
                'Reference2': '',
                'Reference3': '',
                'Reference4': '',
                'Reference5': ''
            },
            'OriginAddress': {
                'Line1': shipment_data.get('origin_address_line1', ''),
                'Line2': shipment_data.get('origin_address_line2', ''),
                'Line3': shipment_data.get('origin_address_line3', ''),
                'City': shipment_data.get('origin_city', ''),
                'StateOrProvinceCode': shipment_data.get('origin_state', ''),
                'PostCode': shipment_data.get('origin_postal_code', ''),
                'CountryCode': shipment_data.get('origin_country_code', 'AE')
            },
            'DestinationAddress': {
                'Line1': shipment_data.get('destination_address_line1', ''),
                'Line2': shipment_data.get('destination_address_line2', ''),
                'Line3': shipment_data.get('destination_address_line3', ''),
                'City': shipment_data.get('destination_city', ''),
                'StateOrProvinceCode': shipment_data.get('destination_state', ''),
                'PostCode': shipment_data.get('destination_postal_code', ''),
                'CountryCode': shipment_data.get('destination_country_code', 'AE')
            },
            'ShipmentDetails': {
                'Dimensions': {
                    'Length': float(shipment_data.get('length', 10)),
                    'Width': float(shipment_data.get('width', 10)),
                    'Height': float(shipment_data.get('height', 10)),
                    'Unit': shipment_data.get('dimension_unit', 'CM')
                },
                'ActualWeight': {
                    'Value': float(shipment_data.get('weight', 1)),
                    'Unit': shipment_data.get('weight_unit', 'KG')
                },
                'ProductGroup': shipment_data.get('product_group', 'EXP'),
                'ProductType': shipment_data.get('product_type', 'PPX'),
                'PaymentType': shipment_data.get('payment_type', 'P'),
                'PaymentOptions': shipment_data.get('payment_options', ''),
                'Services': shipment_data.get('services', ''),
                'NumberOfPieces': int(shipment_data.get('number_of_pieces', 1)),
                'DescriptionOfGoods': shipment_data.get('description', 'General Goods'),
                'GoodsOriginCountry': shipment_data.get('goods_origin_country', 'AE')
            },
            'PreferredCurrencyCode': shipment_data.get('currency_code', 'AED')
        }
        
        # Make API request
        result = api.make_api_request('ShippingAPI.V2/RateCalculator/CalculateRate', payload)
        
        # Process the response
        rates = []
        if result.get('TotalAmount'):
            rates.append({
                'service_type': 'Standard',
                'service_name': 'Aramex Standard Service',
                'total_amount': result.get('TotalAmount', {}).get('Value', 0),
                'currency': result.get('TotalAmount', {}).get('CurrencyCode', 'AED'),
                'transit_time': 'N/A',
                'description': 'Standard Aramex shipping service'
            })
        
        return {
            'success': True,
            'rates': rates,
            'message': 'Shipping rates retrieved successfully'
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting shipping rates: {str(e)}", "Aramex Rate Calculation Error")
        return {
            'success': False,
            'rates': [],
            'message': f'Error retrieving shipping rates: {str(e)}'
        }


@frappe.whitelist()
def create_shipment(shipment_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a shipment using Aramex API
    
    Args:
        shipment_data: Dictionary containing complete shipment information
        
    Returns:
        Dictionary containing shipment creation result
    """
    try:
        api = AramexAPI()
        
        # Prepare the shipment creation request
        payload = {
            'ClientInfo': api.get_client_info(),
            'Transaction': {
                'Reference1': shipment_data.get('reference', ''),
                'Reference2': '',
                'Reference3': '',
                'Reference4': '',
                'Reference5': ''
            },
            'Shipments': [{
                'Reference1': shipment_data.get('reference', ''),
                'Reference2': '',
                'Reference3': '',
                'Shipper': {
                    'Reference1': '',
                    'Reference2': '',
                    'AccountNumber': api.settings.get('account_number'),
                    'PartyAddress': {
                        'Line1': shipment_data.get('shipper_address_line1', ''),
                        'Line2': shipment_data.get('shipper_address_line2', ''),
                        'Line3': shipment_data.get('shipper_address_line3', ''),
                        'City': shipment_data.get('shipper_city', ''),
                        'StateOrProvinceCode': shipment_data.get('shipper_state', ''),
                        'PostCode': shipment_data.get('shipper_postal_code', ''),
                        'CountryCode': shipment_data.get('shipper_country_code', 'AE')
                    },
                    'Contact': {
                        'Department': '',
                        'PersonName': shipment_data.get('shipper_name', ''),
                        'Title': '',
                        'CompanyName': shipment_data.get('shipper_company', ''),
                        'PhoneNumber1': shipment_data.get('shipper_phone', ''),
                        'PhoneNumber1Ext': '',
                        'PhoneNumber2': '',
                        'PhoneNumber2Ext': '',
                        'FaxNumber': '',
                        'CellPhone': shipment_data.get('shipper_mobile', ''),
                        'EmailAddress': shipment_data.get('shipper_email', ''),
                        'Type': ''
                    }
                },
                'Consignee': {
                    'Reference1': '',
                    'Reference2': '',
                    'AccountNumber': '',
                    'PartyAddress': {
                        'Line1': shipment_data.get('consignee_address_line1', ''),
                        'Line2': shipment_data.get('consignee_address_line2', ''),
                        'Line3': shipment_data.get('consignee_address_line3', ''),
                        'City': shipment_data.get('consignee_city', ''),
                        'StateOrProvinceCode': shipment_data.get('consignee_state', ''),
                        'PostCode': shipment_data.get('consignee_postal_code', ''),
                        'CountryCode': shipment_data.get('consignee_country_code', 'AE')
                    },
                    'Contact': {
                        'Department': '',
                        'PersonName': shipment_data.get('consignee_name', ''),
                        'Title': '',
                        'CompanyName': shipment_data.get('consignee_company', ''),
                        'PhoneNumber1': shipment_data.get('consignee_phone', ''),
                        'PhoneNumber1Ext': '',
                        'PhoneNumber2': '',
                        'PhoneNumber2Ext': '',
                        'FaxNumber': '',
                        'CellPhone': shipment_data.get('consignee_mobile', ''),
                        'EmailAddress': shipment_data.get('consignee_email', ''),
                        'Type': ''
                    }
                },
                'ShipmentDetails': {
                    'Dimensions': {
                        'Length': float(shipment_data.get('length', 10)),
                        'Width': float(shipment_data.get('width', 10)),
                        'Height': float(shipment_data.get('height', 10)),
                        'Unit': shipment_data.get('dimension_unit', 'CM')
                    },
                    'ActualWeight': {
                        'Value': float(shipment_data.get('weight', 1)),
                        'Unit': shipment_data.get('weight_unit', 'KG')
                    },
                    'ProductGroup': shipment_data.get('product_group', 'EXP'),
                    'ProductType': shipment_data.get('product_type', 'PPX'),
                    'PaymentType': shipment_data.get('payment_type', 'P'),
                    'PaymentOptions': shipment_data.get('payment_options', ''),
                    'Services': shipment_data.get('services', ''),
                    'NumberOfPieces': int(shipment_data.get('number_of_pieces', 1)),
                    'DescriptionOfGoods': shipment_data.get('description', 'General Goods'),
                    'GoodsOriginCountry': shipment_data.get('goods_origin_country', 'AE'),
                    'CashOnDeliveryAmount': {
                        'Value': float(shipment_data.get('cod_amount', 0)),
                        'CurrencyCode': shipment_data.get('currency_code', 'AED')
                    },
                    'InsuranceAmount': {
                        'Value': float(shipment_data.get('insurance_amount', 0)),
                        'CurrencyCode': shipment_data.get('currency_code', 'AED')
                    },
                    'CollectAmount': {
                        'Value': float(shipment_data.get('collect_amount', 0)),
                        'CurrencyCode': shipment_data.get('currency_code', 'AED')
                    }
                }
            }],
            'LabelInfo': {
                'ReportID': 9201,
                'ReportType': 'URL'
            }
        }
        
        # Make API request
        result = api.make_api_request('ShippingAPI.V2/Shipping/CreateShipments', payload)
        
        # Process the response
        if result.get('Shipments') and len(result['Shipments']) > 0:
            shipment = result['Shipments'][0]
            return {
                'success': True,
                'shipment_id': shipment.get('ID', ''),
                'reference': shipment.get('Reference1', ''),
                'foreign_hawb': shipment.get('ForeignHAWB', ''),
                'label_url': shipment.get('ShipmentLabel', {}).get('LabelURL', ''),
                'message': 'Shipment created successfully'
            }
        else:
            return {
                'success': False,
                'message': 'Failed to create shipment - no shipment data returned'
            }
        
    except Exception as e:
        frappe.log_error(f"Error creating shipment: {str(e)}", "Aramex Shipment Creation Error")
        return {
            'success': False,
            'message': f'Error creating shipment: {str(e)}'
        }


@frappe.whitelist()
def generate_shipping_label(shipment_id: str) -> Dict[str, Any]:
    """
    Generate shipping label for an existing shipment
    
    Args:
        shipment_id: Aramex shipment ID
        
    Returns:
        Dictionary containing label information
    """
    try:
        api = AramexAPI()
        
        # Prepare the label printing request
        payload = {
            'ClientInfo': api.get_client_info(),
            'Transaction': {
                'Reference1': '',
                'Reference2': '',
                'Reference3': '',
                'Reference4': '',
                'Reference5': ''
            },
            'ShipmentNumber': shipment_id,
            'LabelInfo': {
                'ReportID': 9201,
                'ReportType': 'URL'
            }
        }
        
        # Make API request
        result = api.make_api_request('ShippingAPI.V2/Shipping/PrintLabel', payload)
        
        # Process the response
        if result.get('ShipmentLabel'):
            return {
                'success': True,
                'label_url': result['ShipmentLabel'].get('LabelURL', ''),
                'message': 'Shipping label generated successfully'
            }
        else:
            return {
                'success': False,
                'message': 'Failed to generate shipping label'
            }
        
    except Exception as e:
        frappe.log_error(f"Error generating shipping label: {str(e)}", "Aramex Label Generation Error")
        return {
            'success': False,
            'message': f'Error generating shipping label: {str(e)}'
        }


@frappe.whitelist()
def track_shipment(shipment_id: str) -> Dict[str, Any]:
    """
    Track a shipment using Aramex API
    
    Args:
        shipment_id: Aramex shipment ID or tracking number
        
    Returns:
        Dictionary containing tracking information
    """
    try:
        api = AramexAPI()
        
        # Prepare the tracking request
        payload = {
            'ClientInfo': api.get_client_info(),
            'Transaction': {
                'Reference1': '',
                'Reference2': '',
                'Reference3': '',
                'Reference4': '',
                'Reference5': ''
            },
            'Shipments': [shipment_id],
            'GetLastTrackingUpdateOnly': False
        }
        
        # Make API request
        result = api.make_api_request('ShippingAPI.V2/Tracking/TrackShipments', payload)
        
        # Process the response
        tracking_results = []
        if result.get('TrackingResults'):
            for tracking_result in result['TrackingResults']:
                tracking_events = []
                if tracking_result.get('TrackingUpdateEvents'):
                    for event in tracking_result['TrackingUpdateEvents']:
                        tracking_events.append({
                            'date': event.get('UpdateDateTime', ''),
                            'location': event.get('UpdateLocation', ''),
                            'status': event.get('UpdateDescription', ''),
                            'comments': event.get('Comments', '')
                        })
                
                tracking_results.append({
                    'waybill_number': tracking_result.get('WaybillNumber', ''),
                    'reference': tracking_result.get('Reference', ''),
                    'status': tracking_result.get('UpdateCode', ''),
                    'problem_code': tracking_result.get('ProblemCode', ''),
                    'gross_weight': tracking_result.get('GrossWeight', 0),
                    'charged_weight': tracking_result.get('ChargedWeight', 0),
                    'events': tracking_events
                })
        
        return {
            'success': True,
            'tracking_results': tracking_results,
            'message': 'Tracking information retrieved successfully'
        }
        
    except Exception as e:
        frappe.log_error(f"Error tracking shipment: {str(e)}", "Aramex Tracking Error")
        return {
            'success': False,
            'tracking_results': [],
            'message': f'Error tracking shipment: {str(e)}'
        }


@frappe.whitelist()
def get_shipments(filters: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Get shipments for dashboard display
    
    Args:
        filters: Optional filters for shipments
        
    Returns:
        Dictionary containing shipments list
    """
    try:
        # In a real implementation, this would query the database
        # For now, we'll return mock data for demonstration
        
        mock_shipments = [
            {
                'tracking_id': '1234567890',
                'customer_name': 'John Doe',
                'destination': 'Dubai, UAE',
                'status': 'delivered',
                'weight': 2.5,
                'created_at': '2024-01-15',
                'service_type': 'standard'
            },
            {
                'tracking_id': '1234567891',
                'customer_name': 'Jane Smith',
                'destination': 'Abu Dhabi, UAE',
                'status': 'in_transit',
                'weight': 1.8,
                'created_at': '2024-01-16',
                'service_type': 'express'
            },
            {
                'tracking_id': '1234567892',
                'customer_name': 'Bob Johnson',
                'destination': 'Sharjah, UAE',
                'status': 'pending',
                'weight': 3.2,
                'created_at': '2024-01-17',
                'service_type': 'standard'
            },
            {
                'tracking_id': '1234567893',
                'customer_name': 'Alice Brown',
                'destination': 'Ajman, UAE',
                'status': 'failed',
                'weight': 0.5,
                'created_at': '2024-01-14',
                'service_type': 'priority'
            }
        ]
        
        # Apply filters if provided
        if filters:
            if filters.get('status'):
                mock_shipments = [s for s in mock_shipments if s['status'] == filters['status']]
            if filters.get('search'):
                search_term = filters['search'].lower()
                mock_shipments = [s for s in mock_shipments 
                                if search_term in s['customer_name'].lower() or 
                                   search_term in s['tracking_id'].lower() or
                                   search_term in s['destination'].lower()]
        
        return {
            'success': True,
            'shipments': mock_shipments,
            'message': 'Shipments retrieved successfully'
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting shipments: {str(e)}", "Aramex Get Shipments Error")
        return {
            'success': False,
            'shipments': [],
            'message': f'Error retrieving shipments: {str(e)}'
        }


@frappe.whitelist()
def get_shipment_details(tracking_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific shipment
    
    Args:
        tracking_id: The tracking ID of the shipment
        
    Returns:
        Dictionary containing shipment details
    """
    try:
        # Mock shipment details
        shipment_details = {
            'tracking_id': tracking_id,
            'customer_name': 'John Doe',
            'destination': 'Dubai, UAE',
            'status': 'delivered',
            'weight': 2.5,
            'dimensions': {
                'length': 30,
                'width': 20,
                'height': 15,
                'unit': 'CM'
            },
            'service_type': 'standard',
            'created_at': '2024-01-15',
            'estimated_delivery': '2024-01-18',
            'actual_delivery': '2024-01-17',
            'shipper_address': '123 Main St, Dubai, UAE',
            'consignee_address': '456 Business Ave, Dubai, UAE',
            'total_cost': 45.50,
            'currency': 'AED'
        }
        
        return {
            'success': True,
            'shipment': shipment_details,
            'message': 'Shipment details retrieved successfully'
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting shipment details: {str(e)}", "Aramex Shipment Details Error")
        return {
            'success': False,
            'shipment': {},
            'message': f'Error retrieving shipment details: {str(e)}'
        }


@frappe.whitelist()
def get_dashboard_stats() -> Dict[str, Any]:
    """
    Get dashboard statistics
    
    Returns:
        Dictionary containing dashboard statistics
    """
    try:
        # Mock dashboard stats
        stats = {
            'total_shipments': 156,
            'delivered_shipments': 98,
            'in_transit_shipments': 45,
            'failed_shipments': 13,
            'today_shipments': 12,
            'this_week_shipments': 34,
            'this_month_shipments': 89,
            'average_delivery_time': 2.5,
            'top_destinations': [
                {'destination': 'Dubai, UAE', 'count': 45},
                {'destination': 'Abu Dhabi, UAE', 'count': 32},
                {'destination': 'Sharjah, UAE', 'count': 28}
            ]
        }
        
        return {
            'success': True,
            'stats': stats,
            'message': 'Dashboard statistics retrieved successfully'
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting dashboard stats: {str(e)}", "Aramex Dashboard Stats Error")
        return {
            'success': False,
            'stats': {},
            'message': f'Error retrieving dashboard statistics: {str(e)}'
        }
