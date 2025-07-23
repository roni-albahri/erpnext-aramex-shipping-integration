
---

# ERPNext Aramex Shipping Integration

## Project Overview

The ERPNext Aramex Shipping Integration project enhances the existing ERPNext shipping integration capabilities by providing a robust solution that works with the Aramex APIs. It features a modern UI/UX, comprehensive shipping functionality, and is built using best practices for web development.

## Features

- **Rate Comparison:** Real-time shipping rates from Aramex API.
- **Shipment Creation:** Create shipments directly through the Aramex integration.
- **Label Printing:** Generate and print shipping labels.
- **Real-time Tracking:** Access detailed shipment status updates.
- **Modern Dashboard:** Responsive UI built with accessibility in mind.
- **Comprehensive Logging:** Detailed error logging for easier maintenance.

## Installation

To install the ERPNext Aramex Shipping Integration, follow these steps:

1. **Navigate to your Frappe bench directory:**
   ```bash
   cd ~/frappe-bench
   ```

2. **Get the app from the repository:**
   ```bash
   bench get-app https://github.com/your-username/erpnext-aramex-shipping.git
   ```

3. **Install the app on your site:**
   ```bash
   bench --site [your-site-name] install-app erpnext_aramex_shipping
   ```

4. **Restart your bench:**
   ```bash
   bench restart
   ```

5. **Configure Aramex API credentials:**
   - Navigate to **Setup > Integrations > Aramex Settings** and enter your API credentials.

## Usage

Once installed, you can start using the app to manage your shipping needs directly from ERPNext. The application integrates with multiple endpoints from the Aramex API to provide functionalities such as rate calculation, shipment creation, and tracking.

### Sample API Usage
```python
# Fetch shipping rates
rates = frappe.call('erpnext_aramex_shipping.shipment.shipment.fetch_shipping_rates', {
    'origin_city': 'Dubai',
    'destination_city': 'Riyadh',
    'weight': 1.5,
    'length': 20,
    'width': 15,
    'height': 10
})

# Create shipment
shipment = frappe.call('erpnext_aramex_shipping.shipment.shipment.create_aramex_shipment', {
    'shipper_name': 'John Doe',
    'consignee_name': 'Jane Smith',
    # ... other shipment data
})
```

## Dependencies

This project uses several dependencies, as outlined in the `pyproject.toml` and `setup.py` files. Below are some key dependencies:

- **Frappe Framework**: The framework on which ERPNext is built.
- **Python 3.7+**: Minimum version required for compatibility.

## Project Structure

Here's the general structure of the project:

```
erpnext_aramex_shipping/
├── .editorconfig                    # Editor configuration
├── .flake8                          # Python linting configuration
├── .gitignore                       # Git ignore patterns
├── LICENSE                          # MIT License
├── MANIFEST.in                      # Package manifest
├── README.md                        # Comprehensive documentation
├── hooks.py                         # Frappe app hooks and configuration
├── pyproject.toml                   # Modern Python packaging
├── setup.py                         # Package setup script
└── erpnext_aramex_shipping/
    ├── __init__.py                 # App version and initialization
    ├── api/
    │   ├── __init__.py
    │   └── aramex.py                # Core Aramex API integration
    ├── shipment/
    │   ├── __init__.py
    │   └── shipment.py              # Business logic and validation
    └── templates/
        └── pages/
            ├── shipping_dashboard.html    # Main dashboard UI
            ├── css/
            │   └── shipping_dashboard.css # Modern responsive styling
            └── js/
                └── shipping_dashboard.js  # Interactive functionality

tests/
├── __init__.py
└── test_aramex_integration.py          # Comprehensive unit tests

demo.html                                # Standalone demo page
PROJECT_OVERVIEW.md                     # Overview file
```

## Support & Contribution

For assistance, view the comprehensive documentation or contribute to the project on GitHub. You can report issues or submit feature requests through GitHub's issue tracker.

### Contribution Steps
1. Fork this repository.
2. Create a feature branch.
3. Make your changes and ensure they comply with our coding standards.
4. Submit a pull request for review.

## License

This project is licensed under the MIT License. For more details, see the [LICENSE](LICENSE) file.

---

**Built with ❤️ for the ERPNext community.** This project showcases modern web development practices while maintaining strong compatibility with the ERPNext ecosystem.# erpnext-aramex-shipping
# erpnext-aramex-shipping-integration
