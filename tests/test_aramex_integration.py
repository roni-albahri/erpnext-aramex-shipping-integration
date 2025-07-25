import unittest
import json
from unittest.mock import Mock, patch, MagicMock
import frappe
from erpnext_aramex_shipping.api.aramex import AramexAPI, get_shipping_rates, create_shipment, generate_shipping_label, track_shipment
from erpnext_aramex_shipping.shipment.shipment import (
    validate_address_data, validate_shipment_data, fetch_shipping_rates,
    create_aramex_shipment, print_shipping_label, track_aramex_shipment
)
#test

class TestAramexAPI(unittest.TestCase):
    """Test cases for Aramex API integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_settings = {
            'username': 'testuser',
            'password': 'testpass',
            'account_number': '12345',
            'account_pin': '123456',
            'account_entity': 'AMM',
            'account_country_code': 'JO',
            'test_mode': True
        }
        
        self.sample_shipment_data = {
            'reference': 'TEST_REF_001',
            'origin_address_line1': '123 Test Street',
            'origin_city': 'Dubai',
            'origin_country_code': 'AE',
            'destination_address_line1': '456 Destination Ave',
            'destination_city': 'Riyadh',
            'destination_country_code': 'SA',
            'weight': 1.5,
            'length': 20,
            'width': 15,
            'height': 10,
            'dimension_unit': 'CM',
            'weight_unit': 'KG',
            'description': 'Test package'
        }
    
    @patch('frappe.get_site_config')
    def test_aramex_api_initialization(self, mock_get_site_config):
        """Test AramexAPI class initialization"""
        mock_get_site_config.return_value.get.return_value = self.mock_settings
        
        api = AramexAPI()
        
        self.assertEqual(api.settings, self.mock_settings)
        self.assertEqual(api.base_url, 'https://ws.dev.aramex.net')
    
    @patch('frappe.get_site_config')
    def test_get_client_info(self, mock_get_site_config):
        """Test client info generation"""
        mock_get_site_config.return_value.get.return_value = self.mock_settings
        
        api = AramexAPI()
        client_info = api.get_client_info()
        
        self.assertEqual(client_info['UserName'], 'testuser')
        self.assertEqual(client_info['Password'], 'testpass')
        self.assertEqual(client_info['AccountNumber'], '12345')
        self.assertEqual(client_info['Source'], 24)
    
    @patch('requests.post')
    @patch('frappe.get_site_config')
    def test_successful_api_request(self, mock_get_site_config, mock_post):
        """Test successful API request"""
        mock_get_site_config.return_value.get.return_value = self.mock_settings
        
        # Mock successful response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'HasErrors': False,
            'TotalAmount': {'Value': 25.50, 'CurrencyCode': 'AED'}
        }
        mock_post.return_value = mock_response
        
        api = AramexAPI()
        result = api.make_api_request('test/endpoint', {'test': 'data'})
        
        self.assertFalse(result.get('HasErrors'))
        self.assertEqual(result['TotalAmount']['Value'], 25.50)
    
    @patch('requests.post')
    @patch('frappe.get_site_config')
    @patch('frappe.log_error')
    def test_api_request_with_errors(self, mock_log_error, mock_get_site_config, mock_post):
        """Test API request with errors"""
        mock_get_site_config.return_value.get.return_value = self.mock_settings
        
        # Mock error response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'HasErrors': True,
            'Notifications': [
                {'Code': '001', 'Message': 'Test error message'}
            ]
        }
        mock_post.return_value = mock_response
        
        api = AramexAPI()
        
        with self.assertRaises(Exception) as context:
            api.make_api_request('test/endpoint', {'test': 'data'})
        
        self.assertIn('Test error message', str(context.exception))
    
    @patch('erpnext_aramex_shipping.api.aramex.AramexAPI')
    def test_get_shipping_rates_success(self, mock_api_class):
        """Test successful shipping rates retrieval"""
        mock_api = Mock()
        mock_api.make_api_request.return_value = {
            'TotalAmount': {'Value': 30.00, 'CurrencyCode': 'AED'}
        }
        mock_api_class.return_value = mock_api
        
        result = get_shipping_rates(self.sample_shipment_data)
        
        self.assertTrue(result['success'])
        self.assertEqual(len(result['rates']), 1)
        self.assertEqual(result['rates'][0]['total_amount'], 30.00)
    
    @patch('erpnext_aramex_shipping.api.aramex.AramexAPI')
    @patch('frappe.log_error')
    def test_get_shipping_rates_failure(self, mock_log_error, mock_api_class):
        """Test shipping rates retrieval failure"""
        mock_api = Mock()
        mock_api.make_api_request.side_effect = Exception('API Error')
        mock_api_class.return_value = mock_api
        
        result = get_shipping_rates(self.sample_shipment_data)
        
        self.assertFalse(result['success'])
        self.assertEqual(len(result['rates']), 0)
        self.assertIn('API Error', result['message'])


class TestShipmentValidation(unittest.TestCase):
    """Test cases for shipment data validation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.valid_address_data = {
            'shipper_name': 'John Doe',
            'shipper_address_line1': '123 Test Street',
            'shipper_city': 'Dubai',
            'shipper_country_code': 'AE',
            'shipper_phone': '+971501234567',
            'shipper_email': 'john@example.com'
        }
        
        self.valid_shipment_data = {
            **self.valid_address_data,
            'consignee_name': 'Jane Smith',
            'consignee_address_line1': '456 Destination Ave',
            'consignee_city': 'Riyadh',
            'consignee_country_code': 'SA',
            'consignee_phone': '+966501234567',
            'consignee_email': 'jane@example.com',
            'weight': 1.5,
            'length': 20,
            'width': 15,
            'height': 10,
            'number_of_pieces': 1,
            'description': 'Test package'
        }
    
    def test_valid_address_data(self):
        """Test validation of valid address data"""
        errors = validate_address_data(self.valid_address_data, 'shipper')
        self.assertEqual(len(errors), 0)
    
    def test_missing_required_address_fields(self):
        """Test validation with missing required address fields"""
        incomplete_data = self.valid_address_data.copy()
        del incomplete_data['shipper_name']
        del incomplete_data['shipper_email']
        
        errors = validate_address_data(incomplete_data, 'shipper')
        self.assertGreater(len(errors), 0)
        self.assertTrue(any('name' in error for error in errors))
        self.assertTrue(any('email' in error for error in errors))
    
    def test_invalid_email_format(self):
        """Test validation with invalid email format"""
        invalid_data = self.valid_address_data.copy()
        invalid_data['shipper_email'] = 'invalid-email'
        
        errors = validate_address_data(invalid_data, 'shipper')
        self.assertTrue(any('email format' in error for error in errors))
    
    def test_invalid_country_code(self):
        """Test validation with invalid country code"""
        invalid_data = self.valid_address_data.copy()
        invalid_data['shipper_country_code'] = 'INVALID'
        
        errors = validate_address_data(invalid_data, 'shipper')
        self.assertTrue(any('country code must be 2 characters' in error for error in errors))
    
    def test_valid_shipment_data(self):
        """Test validation of valid shipment data"""
        errors = validate_shipment_data(self.valid_shipment_data)
        self.assertEqual(len(errors), 0)
    
    def test_invalid_package_dimensions(self):
        """Test validation with invalid package dimensions"""
        invalid_data = self.valid_shipment_data.copy()
        invalid_data['weight'] = 0
        invalid_data['length'] = -5
        
        errors = validate_shipment_data(invalid_data)
        self.assertTrue(any('weight must be greater than 0' in error for error in errors))
        self.assertTrue(any('dimensions must be greater than 0' in error for error in errors))
    
    def test_invalid_number_of_pieces(self):
        """Test validation with invalid number of pieces"""
        invalid_data = self.valid_shipment_data.copy()
        invalid_data['number_of_pieces'] = 0
        
        errors = validate_shipment_data(invalid_data)
        self.assertTrue(any('pieces must be greater than 0' in error for error in errors))
    
    def test_missing_description(self):
        """Test validation with missing description"""
        invalid_data = self.valid_shipment_data.copy()
        del invalid_data['description']
        
        errors = validate_shipment_data(invalid_data)
        self.assertTrue(any('description is required' in error for error in errors))


class TestShipmentBusinessLogic(unittest.TestCase):
    """Test cases for shipment business logic"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.valid_shipment_json = json.dumps({
            'shipper_name': 'John Doe',
            'shipper_address_line1': '123 Test Street',
            'shipper_city': 'Dubai',
            'shipper_country_code': 'AE',
            'shipper_phone': '+971501234567',
            'shipper_email': 'john@example.com',
            'consignee_name': 'Jane Smith',
            'consignee_address_line1': '456 Destination Ave',
            'consignee_city': 'Riyadh',
            'consignee_country_code': 'SA',
            'consignee_phone': '+966501234567',
            'consignee_email': 'jane@example.com',
            'origin_city': 'Dubai',
            'origin_country_code': 'AE',
            'destination_city': 'Riyadh',
            'destination_country_code': 'SA',
            'weight': 1.5,
            'length': 20,
            'width': 15,
            'height': 10,
            'number_of_pieces': 1,
            'description': 'Test package'
        })
    
    @patch('erpnext_aramex_shipping.api.aramex.get_shipping_rates')
    @patch('frappe.logger')
    def test_fetch_shipping_rates_success(self, mock_logger, mock_get_rates):
        """Test successful shipping rates fetch"""
        mock_get_rates.return_value = {
            'success': True,
            'rates': [{'service_name': 'Standard', 'total_amount': 25.50}],
            'message': 'Success'
        }
        
        result = fetch_shipping_rates(self.valid_shipment_json)
        
        self.assertTrue(result['success'])
        self.assertEqual(len(result['rates']), 1)
    
    def test_fetch_shipping_rates_invalid_json(self):
        """Test shipping rates fetch with invalid JSON"""
        result = fetch_shipping_rates('invalid json')
        
        self.assertFalse(result['success'])
        self.assertIn('Invalid JSON', result['message'])
    
    def test_fetch_shipping_rates_missing_fields(self):
        """Test shipping rates fetch with missing required fields"""
        incomplete_data = json.dumps({'weight': 1.5})
        
        result = fetch_shipping_rates(incomplete_data)
        
        self.assertFalse(result['success'])
        self.assertIn('Validation errors', result['message'])
    
    @patch('erpnext_aramex_shipping.api.aramex.create_shipment')
    @patch('frappe.get_doc')
    @patch('frappe.db.commit')
    @patch('frappe.logger')
    def test_create_aramex_shipment_success(self, mock_logger, mock_commit, mock_get_doc, mock_create):
        """Test successful shipment creation"""
        mock_create.return_value = {
            'success': True,
            'shipment_id': 'SHIP123',
            'reference': 'REF123',
            'foreign_hawb': 'HAWB123',
            'label_url': 'http://example.com/label.pdf'
        }
        
        mock_doc = Mock()
        mock_doc.name = 'ERPNEXT_SHIP_001'
        mock_doc.insert.return_value = None
        mock_get_doc.return_value = mock_doc
        
        result = create_aramex_shipment(self.valid_shipment_json)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['shipment_id'], 'SHIP123')
        self.assertEqual(result['erpnext_shipment_id'], 'ERPNEXT_SHIP_001')
    
    def test_create_aramex_shipment_validation_error(self):
        """Test shipment creation with validation errors"""
        invalid_data = json.dumps({'weight': 0})  # Invalid weight
        
        result = create_aramex_shipment(invalid_data)
        
        self.assertFalse(result['success'])
        self.assertIn('Validation errors', result['message'])
    
    @patch('erpnext_aramex_shipping.api.aramex.generate_shipping_label')
    @patch('frappe.get_all')
    @patch('frappe.get_doc')
    @patch('frappe.db.commit')
    @patch('frappe.logger')
    def test_print_shipping_label_success(self, mock_logger, mock_commit, mock_get_doc, mock_get_all, mock_generate):
        """Test successful label printing"""
        mock_generate.return_value = {
            'success': True,
            'label_url': 'http://example.com/label.pdf'
        }
        
        mock_get_all.return_value = [{'name': 'ERPNEXT_SHIP_001'}]
        mock_doc = Mock()
        mock_doc.save.return_value = None
        mock_get_doc.return_value = mock_doc
        
        result = print_shipping_label('SHIP123')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['label_url'], 'http://example.com/label.pdf')
    
    def test_print_shipping_label_missing_id(self):
        """Test label printing with missing shipment ID"""
        result = print_shipping_label('')
        
        self.assertFalse(result['success'])
        self.assertIn('Shipment ID is required', result['message'])
    
    @patch('erpnext_aramex_shipping.api.aramex.track_shipment')
    @patch('frappe.get_all')
    @patch('frappe.get_doc')
    @patch('frappe.db.commit')
    @patch('frappe.logger')
    def test_track_aramex_shipment_success(self, mock_logger, mock_commit, mock_get_doc, mock_get_all, mock_track):
        """Test successful shipment tracking"""
        mock_track.return_value = {
            'success': True,
            'tracking_results': [{
                'waybill_number': 'HAWB123',
                'status': 'In Transit',
                'events': [
                    {'date': '2024-01-01', 'location': 'Dubai', 'status': 'Picked up'}
                ]
            }]
        }
        
        mock_get_all.return_value = [{'name': 'ERPNEXT_SHIP_001'}]
        mock_doc = Mock()
        mock_doc.save.return_value = None
        mock_get_doc.return_value = mock_doc
        
        result = track_aramex_shipment('SHIP123')
        
        self.assertTrue(result['success'])
        self.assertEqual(len(result['tracking_results']), 1)
        self.assertEqual(result['tracking_results'][0]['status'], 'In Transit')
    
    def test_track_aramex_shipment_missing_id(self):
        """Test shipment tracking with missing shipment ID"""
        result = track_aramex_shipment('')
        
        self.assertFalse(result['success'])
        self.assertIn('Shipment ID is required', result['message'])


class TestUtilityFunctions(unittest.TestCase):
    """Test cases for utility functions"""
    
    @patch('frappe.get_all')
    def test_get_shipment_history_success(self, mock_get_all):
        """Test successful shipment history retrieval"""
        from erpnext_aramex_shipping.shipment.shipment import get_shipment_history
        
        mock_get_all.return_value = [
            {
                'name': 'SHIP001',
                'reference': 'REF001',
                'shipper_name': 'John Doe',
                'consignee_name': 'Jane Smith',
                'status': 'Created'
            }
        ]
        
        result = get_shipment_history(10)
        
        self.assertTrue(result['success'])
        self.assertEqual(len(result['shipments']), 1)
        self.assertEqual(result['shipments'][0]['reference'], 'REF001')
    
    def test_get_country_codes(self):
        """Test country codes retrieval"""
        from erpnext_aramex_shipping.shipment.shipment import get_country_codes
        
        country_codes = get_country_codes()
        
        self.assertIsInstance(country_codes, list)
        self.assertGreater(len(country_codes), 0)
        
        # Check if UAE is in the list
        uae_found = any(country['code'] == 'AE' for country in country_codes)
        self.assertTrue(uae_found)
    
    def test_get_shipping_configuration(self):
        """Test shipping configuration retrieval"""
        from erpnext_aramex_shipping.shipment.shipment import get_shipping_configuration
        
        config = get_shipping_configuration()
        
        self.assertTrue(config['success'])
        self.assertIn('country_codes', config)
        self.assertIn('dimension_units', config)
        self.assertIn('weight_units', config)
        self.assertIn('currency_codes', config)


if __name__ == '__main__':
    # Set up Frappe test environment
    try:
        import frappe
        frappe.init(site='test_site')
        frappe.connect()
    except:
        # Mock frappe if not available
        import sys
        from unittest.mock import MagicMock
        sys.modules['frappe'] = MagicMock()
    
    unittest.main()
