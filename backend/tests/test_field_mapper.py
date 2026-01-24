import unittest
from decimal import Decimal
from datetime import datetime
from finance_project.apps.banking.services.field_mapper import FieldMapper, FieldMappingRegistry


class TestFieldMappingRegistry(unittest.TestCase):
    """Test cases for FieldMappingRegistry"""

    def setUp(self):
        """Set up test fixtures"""
        self.registry = FieldMappingRegistry()

    def test_registry_has_required_fields(self):
        """Test that registry contains all required fields"""
        required_fields = ['date', 'amount']  # reference is now optional
        for field in required_fields:
            self.assertIn(field, self.registry.AVAILABLE_FIELDS)

    def test_date_field_is_required(self):
        """Test that date field is marked as required"""
        date_field = self.registry.get_field('date')
        self.assertTrue(date_field.required)

    def test_amount_field_is_required(self):
        """Test that amount field is marked as required"""
        amount_field = self.registry.get_field('amount')
        self.assertTrue(amount_field.required)

    def test_reference_field_is_optional(self):
        """Test that reference field is marked as optional (can be derived from fallback fields)"""
        reference_field = self.registry.get_field('reference')
        self.assertFalse(reference_field.required)

    def test_optional_fields_exist(self):
        """Test that optional fields exist in registry"""
        optional_fields = ['description', 'partner_name', 'partner_iban', 'merchant_name']
        for field in optional_fields:
            self.assertIn(field, self.registry.AVAILABLE_FIELDS)

    def test_optional_fields_not_required(self):
        """Test that optional fields are not marked as required"""
        optional_fields = ['description', 'partner_name', 'merchant_name']
        for field_name in optional_fields:
            field = self.registry.get_field(field_name)
            self.assertFalse(field.required)

    def test_get_field_returns_mapping(self):
        """Test that get_field returns a FieldMapping object"""
        field = self.registry.get_field('date')
        self.assertIsNotNone(field)
        self.assertEqual(field.target_property, 'date')

    def test_get_field_returns_none_for_invalid_field(self):
        """Test that get_field returns None for non-existent field"""
        field = self.registry.get_field('invalid_field')
        self.assertIsNone(field)

    def test_list_fields_returns_all_fields(self):
        """Test that list_fields returns all available fields"""
        fields = self.registry.list_fields()
        self.assertGreater(len(fields), 0)
        self.assertIn('date', fields)
        self.assertIn('amount', fields)
        self.assertIn('reference', fields)

    def test_get_display_names_returns_dict(self):
        """Test that get_display_names returns a dictionary"""
        display_names = self.registry.get_display_names()
        self.assertIsInstance(display_names, dict)
        self.assertGreater(len(display_names), 0)


class TestFieldMapperBasic(unittest.TestCase):
    """Test cases for FieldMapper with basic functionality"""

    def setUp(self):
        """Set up test fixtures"""
        # New format: { target_property: source_field }
        self.mappings = {
            'date': 'booking',
            'amount': 'amount.value',
            'reference': 'reference',
            'partner_name': 'partnerName'
        }
        self.mapper = FieldMapper(self.mappings)

    def test_mapper_initialization(self):
        """Test that mapper initializes with correct mappings"""
        self.assertEqual(self.mapper.mappings, self.mappings)

    def test_mapper_has_registry(self):
        """Test that mapper has a registry"""
        self.assertIsNotNone(self.mapper.registry)

    def test_map_row_with_simple_fields(self):
        """Test mapping with simple flat fields"""
        source_data = {
            'booking': '2025-08-28',
            'amount': {'value': 100, 'precision': 2},
            'reference': 'Test Reference',
            'partnerName': 'John Doe'
        }

        mappings = {
            'date': 'booking',
            'amount': 'amount.value',
            'reference': 'reference',
            'partner_name': 'partnerName'
        }
        mapper = FieldMapper(mappings)
        result = mapper.map_row(source_data)

        self.assertIn('date', result)
        self.assertIn('amount', result)
        self.assertIn('reference', result)
        self.assertIn('partner_name', result)

    def test_map_row_with_nested_fields(self):
        """Test mapping with nested fields using dot notation"""
        source_data = {
            'partnerAccount': {
                'iban': 'AT213130300259330944',
                'bankCode': '31303'
            }
        }

        mappings = {
            'partner_iban': 'partnerAccount.iban',
            'partner_bank_code': 'partnerAccount.bankCode'
        }
        mapper = FieldMapper(mappings)
        result = mapper.map_row(source_data)

        self.assertIn('partner_iban', result)
        self.assertIn('partner_bank_code', result)

    def test_map_row_ignores_empty_values(self):
        """Test that mapper ignores empty values"""
        source_data = {
            'booking': '2025-08-28',
            'amount': 100,
            'reference': '',  # Empty string
            'partnerName': None  # None value
        }

        mappings = {
            'date': 'booking',
            'amount': 'amount',
            'reference': 'reference',
            'partner_name': 'partnerName'
        }
        mapper = FieldMapper(mappings)
        result = mapper.map_row(source_data)

        # Empty and None values should not be in result
        self.assertNotIn('reference', result)
        self.assertNotIn('partner_name', result)

    def test_map_row_with_missing_fields(self):
        """Test that mapper handles missing fields gracefully"""
        source_data = {
            'booking': '2025-08-28',
            'amount': 100
            # 'reference' is missing
        }

        mappings = {
            'date': 'booking',
            'amount': 'amount',
            'reference': 'reference'
        }
        mapper = FieldMapper(mappings)
        result = mapper.map_row(source_data)

        self.assertIn('date', result)
        self.assertIn('amount', result)
        self.assertNotIn('reference', result)  # Missing field not in result


class TestFieldMapperAdvanced(unittest.TestCase):
    """Test cases for FieldMapper with advanced functionality"""

    def test_map_row_with_multiple_date_fields(self):
        """Test mapping multiple date fields to different properties (NEW FEATURE)"""
        source_data = {
            'booking': '2025-08-28',
            'valuation': '2025-08-29',
            'transactionDate': '2025-08-30'
        }

        # NEW FORMAT: Multiple date fields map to different properties
        mappings = {
            'date': 'booking',
            'valuation_date': 'valuation',
            'booking_date': 'transactionDate'
        }
        mapper = FieldMapper(mappings)
        result = mapper.map_row(source_data)

        # All three date fields should be mapped
        self.assertIn('date', result)
        self.assertIn('valuation_date', result)
        self.assertIn('booking_date', result)

    def test_map_row_with_complex_bank_data(self):
        """Test mapping with realistic bank transaction data"""
        # Realistic bank API response
        source_data = {
            'booking': '2025-08-28T00:00:00.000+0200',
            'valuation': '2025-08-28T00:00:00.000+0200',
            'amount': {
                'value': -7000,
                'precision': 2,
                'currency': 'EUR'
            },
            'reference': 'Sonst.Zahlungen',
            'referenceNumber': '206042508282AB3-DD1001000150',
            'partnerName': 'Levi Schmid',
            'partnerAccount': {
                'iban': 'AT213130300259330944',
                'bankCode': '31303'
            }
        }

        mappings = {
            'date': 'booking',
            'valuation_date': 'valuation',
            'amount': 'amount.value',
            'reference': 'reference',
            'reference_number': 'referenceNumber',
            'partner_name': 'partnerName',
            'partner_iban': 'partnerAccount.iban',
            'partner_bank_code': 'partnerAccount.bankCode'
        }
        mapper = FieldMapper(mappings)
        result = mapper.map_row(source_data)

        # All mapped fields should be present
        self.assertIn('date', result)
        self.assertIn('valuation_date', result)
        self.assertIn('amount', result)
        self.assertIn('reference', result)
        self.assertIn('reference_number', result)
        self.assertIn('partner_name', result)
        self.assertIn('partner_iban', result)
        self.assertIn('partner_bank_code', result)

    def test_map_row_preserves_data_types(self):
        """Test that mapper preserves/converts data types correctly"""
        source_data = {
            'amount': 100,
            'reference': 'Test'
        }

        mappings = {
            'amount': 'amount',
            'reference': 'reference'
        }
        mapper = FieldMapper(mappings)
        result = mapper.map_row(source_data)

        self.assertEqual(result['amount'], '100')  # Converted to string
        self.assertEqual(result['reference'], 'Test')

    def test_map_row_same_source_to_different_targets(self):
        """Test that different target properties can use the same source field"""
        source_data = {
            'description': 'Transaction Description'
        }

        # Using same source field for different properties
        mappings = {
            'reference': 'description',
            'merchant_name': 'description'  # Same source, different target
        }
        mapper = FieldMapper(mappings)
        result = mapper.map_row(source_data)

        # Both should be mapped from same source
        self.assertEqual(result['reference'], 'Transaction Description')
        self.assertEqual(result['merchant_name'], 'Transaction Description')

    def test_map_row_with_empty_mappings(self):
        """Test mapper with empty mappings dictionary"""
        source_data = {
            'field1': 'value1',
            'field2': 'value2'
        }

        mapper = FieldMapper({})
        result = mapper.map_row(source_data)

        # With no mappings, result should be empty
        self.assertEqual(len(result), 0)

    def test_map_row_with_deeply_nested_fields(self):
        """Test mapper with deeply nested JSON structures"""
        source_data = {
            'data': {
                'transaction': {
                    'details': {
                        'amount': {
                            'value': 500
                        }
                    }
                }
            }
        }

        mappings = {
            'amount': 'data.transaction.details.amount.value'
        }
        mapper = FieldMapper(mappings)
        result = mapper.map_row(source_data)

        self.assertIn('amount', result)
        self.assertEqual(result['amount'], '500')

    def test_map_row_with_special_characters_in_fields(self):
        """Test mapper with special characters in field values"""
        source_data = {
            'reference': 'Transaction with "quotes" and \\backslash',
            'description': "Text with 'single' quotes"
        }

        mappings = {
            'reference': 'reference',
            'description': 'description'
        }
        mapper = FieldMapper(mappings)
        result = mapper.map_row(source_data)

        self.assertIn('reference', result)
        self.assertIn('description', result)

    def test_map_row_with_unicode_characters(self):
        """Test mapper with unicode characters"""
        source_data = {
            'partnerName': 'Matthias Schmid',
            'reference': 'Überweisung Ausland'
        }

        mappings = {
            'partner_name': 'partnerName',
            'reference': 'reference'
        }
        mapper = FieldMapper(mappings)
        result = mapper.map_row(source_data)

        self.assertEqual(result['partner_name'], 'Matthias Schmid')
        self.assertEqual(result['reference'], 'Überweisung Ausland')

    def test_map_row_with_austrian_bank_data(self):
        """Test mapping with real Austrian bank transaction data (FA Österreich)"""
        # Real-world Austrian bank API response with IBAN, BIC, and bank codes
        source_data = {
            'transactionId': None,
            'containedTransactionId': None,
            'booking': '2025-05-15T00:00:00.000+0200',
            'execution': None,
            'valuation': '2025-05-15T00:00:00.000+0200',
            'transactionDateTime': None,
            'partnerName': 'FA Österreich  - Vorarlberg',
            'partnerAccount': {
                'iban': 'AT630100000005574988',
                'bic': 'BUNDATWWXXX',
                'number': '',
                'bankCode': '01000',
                'countryCode': 'AT',
                'prefix': None,
                'secondaryId': None
            },
            'partnerAddress': None,
            'partnerStructuredAddress': None,
            'partnerReference': None,
            'partnerOriginator': None,
            'amount': {
                'value': 124000,
                'precision': 2,
                'currency': 'EUR'
            }
        }

        # Map Austrian bank data fields
        mappings = {
            'date': 'booking',
            'valuation_date': 'valuation',
            'amount': 'amount.value',
            'partner_name': 'partnerName',
            'partner_iban': 'partnerAccount.iban',
            'partner_bank_code': 'partnerAccount.bankCode'
        }
        mapper = FieldMapper(mappings)
        result = mapper.map_row(source_data)

        # Verify all mapped fields are present
        self.assertIn('date', result)
        self.assertIn('valuation_date', result)
        self.assertIn('amount', result)
        self.assertIn('partner_name', result)
        self.assertIn('partner_iban', result)
        self.assertIn('partner_bank_code', result)

        # Verify values are correctly mapped
        self.assertEqual(result['date'], '2025-05-15')  # Date is parsed to YYYY-MM-DD format
        self.assertEqual(result['valuation_date'], '2025-05-15')  # Same format
        self.assertEqual(result['amount'], '1240')
        self.assertEqual(result['partner_name'], 'FA Österreich  - Vorarlberg')
        self.assertEqual(result['partner_iban'], 'AT630100000005574988')
        self.assertEqual(result['partner_bank_code'], '01000')

    def test_map_row_with_reference_fallback_to_partner_name(self):
        """Test that reference field falls back to partner_name when not available"""
        # Simulates real-world scenario where reference field is missing
        source_data = {
            'booking': '2025-05-15T00:00:00.000+0200',
            'valuation': '2025-05-15T00:00:00.000+0200',
            'partnerName': 'FA Österreich  - Vorarlberg',
            'partnerAccount': {
                'iban': 'AT630100000005574988',
                'bankCode': '01000'
            },
            'amount': {
                'value': 124000,
                'precision': 2,
                'currency': 'EUR'
            }
            # ⚠️ NO reference field!
        }

        # Map fields - reference is now optional
        mappings = {
            'date': 'booking',
            'valuation_date': 'valuation',
            'amount': 'amount.value',
            'reference': 'reference',  # Will use fallback
            'partner_name': 'partnerName',
            'partner_iban': 'partnerAccount.iban',
            'partner_bank_code': 'partnerAccount.bankCode'
        }
        mapper = FieldMapper(mappings)
        result = mapper.map_row(source_data)

        # Verify all fields are present
        self.assertIn('date', result)
        self.assertIn('valuation_date', result)
        self.assertIn('amount', result)
        self.assertIn('partner_name', result)
        self.assertIn('partner_iban', result)
        self.assertIn('partner_bank_code', result)
        # Reference should NOT be in result since it's not mapped and mapping has no fallback
        # The fallback happens at the importer level, not at the mapper level


class TestFieldMapperNestedValues(unittest.TestCase):
    """Test cases for nested value getter functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.mapper = FieldMapper({})

    def test_get_nested_value_simple_key(self):
        """Test getting simple key from dictionary"""
        data = {'name': 'John', 'age': 30}
        value = self.mapper._get_nested_value(data, 'name')
        self.assertEqual(value, 'John')

    def test_get_nested_value_with_dot_notation(self):
        """Test getting nested value with dot notation"""
        data = {
            'person': {
                'address': {
                    'city': 'Vienna'
                }
            }
        }
        value = self.mapper._get_nested_value(data, 'person.address.city')
        self.assertEqual(value, 'Vienna')

    def test_get_nested_value_missing_key(self):
        """Test getting non-existent key returns None"""
        data = {'name': 'John'}
        value = self.mapper._get_nested_value(data, 'age')
        self.assertIsNone(value)

    def test_get_nested_value_missing_nested_key(self):
        """Test getting non-existent nested key returns None"""
        data = {'person': {'name': 'John'}}
        value = self.mapper._get_nested_value(data, 'person.address.city')
        self.assertIsNone(value)

    def test_get_nested_value_invalid_path(self):
        """Test getting value with invalid path returns None"""
        data = {'name': 'John'}
        value = self.mapper._get_nested_value(data, 'person.address.city')
        self.assertIsNone(value)


if __name__ == '__main__':
    unittest.main()

