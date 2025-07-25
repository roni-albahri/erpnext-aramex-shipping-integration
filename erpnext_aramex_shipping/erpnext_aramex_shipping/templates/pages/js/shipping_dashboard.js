/**
 * Shipping Dashboard JavaScript
 * Handles all client-side interactions for the Aramex shipping integration
 */
/**test */
class ShippingDashboard {
    constructor() {
        this.selectedRate = null;
        this.currentShipment = null;
        this.configuration = null;
        
        this.init();
    }

    /**
     * Initialize the dashboard
     */
    async init() {
        try {
            // Load configuration data
            await this.loadConfiguration();
            
            // Setup event listeners
            this.setupEventListeners();
            
            // Load initial data
            this.loadShipmentHistory();
            
            console.log('Shipping Dashboard initialized successfully');
        } catch (error) {
            console.error('Error initializing dashboard:', error);
            this.showAlert('Error initializing dashboard. Please refresh the page.', 'error');
        }
    }

    /**
     * Load configuration data from the server
     */
    async loadConfiguration() {
        try {
            const response = await this.makeAPICall('erpnext_aramex_shipping.shipment.shipment.get_shipping_configuration');
            
            if (response.success) {
                this.configuration = response;
                this.populateDropdowns();
            } else {
                throw new Error(response.message || 'Failed to load configuration');
            }
        } catch (error) {
            console.error('Error loading configuration:', error);
            // Use fallback configuration
            this.configuration = this.getFallbackConfiguration();
            this.populateDropdowns();
        }
    }

    /**
     * Get fallback configuration if API fails
     */
    getFallbackConfiguration() {
        return {
            success: true,
            country_codes: [
                {code: 'AE', name: 'United Arab Emirates'},
                {code: 'SA', name: 'Saudi Arabia'},
                {code: 'US', name: 'United States'},
                {code: 'GB', name: 'United Kingdom'}
            ],
            dimension_units: [
                {code: 'CM', name: 'Centimeters'},
                {code: 'IN', name: 'Inches'}
            ],
            weight_units: [
                {code: 'KG', name: 'Kilograms'},
                {code: 'LB', name: 'Pounds'}
            ],
            currency_codes: [
                {code: 'AED', name: 'UAE Dirham'},
                {code: 'USD', name: 'US Dollar'}
            ]
        };
    }

    /**
     * Populate dropdown menus with configuration data
     */
    populateDropdowns() {
        // Populate country dropdowns
        const countrySelects = ['shipper_country_code', 'consignee_country_code'];
        countrySelects.forEach(selectId => {
            const select = document.getElementById(selectId);
            if (select && this.configuration.country_codes) {
                this.configuration.country_codes.forEach(country => {
                    const option = document.createElement('option');
                    option.value = country.code;
                    option.textContent = country.name;
                    select.appendChild(option);
                });
            }
        });

        // Set default values
        document.getElementById('shipper_country_code').value = 'AE';
        document.getElementById('consignee_country_code').value = 'AE';
    }

    /**
     * Setup event listeners for all interactive elements
     */
    setupEventListeners() {
        // Fetch rates button
        const fetchRatesBtn = document.getElementById('fetch-rates-btn');
        if (fetchRatesBtn) {
            fetchRatesBtn.addEventListener('click', () => this.fetchShippingRates());
        }

        // Create shipment button
        const createShipmentBtn = document.getElementById('create-shipment-btn');
        if (createShipmentBtn) {
            createShipmentBtn.addEventListener('click', () => this.createShipment());
        }

        // Print label button
        const printLabelBtn = document.getElementById('print-label-btn');
        if (printLabelBtn) {
            printLabelBtn.addEventListener('click', () => this.printShippingLabel());
        }

        // Track shipment button (in result section)
        const trackShipmentBtn = document.getElementById('track-shipment-btn');
        if (trackShipmentBtn) {
            trackShipmentBtn.addEventListener('click', () => this.trackCurrentShipment());
        }

        // Track button (in tracking section)
        const trackBtn = document.getElementById('track-btn');
        if (trackBtn) {
            trackBtn.addEventListener('click', () => this.trackShipment());
        }

        // Refresh history button
        const refreshHistoryBtn = document.getElementById('refresh-history-btn');
        if (refreshHistoryBtn) {
            refreshHistoryBtn.addEventListener('click', () => this.loadShipmentHistory());
        }

        // Form validation
        const form = document.getElementById('shipping-form');
        if (form) {
            form.addEventListener('input', () => this.validateForm());
        }

        // Enter key handling for tracking
        const trackingInput = document.getElementById('tracking-number');
        if (trackingInput) {
            trackingInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.trackShipment();
                }
            });
        }
    }

    /**
     * Validate the shipping form
     */
    validateForm() {
        const form = document.getElementById('shipping-form');
        const createBtn = document.getElementById('create-shipment-btn');
        
        if (form && createBtn) {
            const isValid = form.checkValidity();
            createBtn.disabled = !isValid || !this.selectedRate;
        }
    }

    /**
     * Collect form data
     */
    getFormData() {
        const form = document.getElementById('shipping-form');
        const formData = new FormData(form);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            data[key] = value;
        }
        
        // Add origin data (same as shipper for rate calculation)
        data.origin_address_line1 = data.shipper_address_line1;
        data.origin_address_line2 = data.shipper_address_line2;
        data.origin_city = data.shipper_city;
        data.origin_state = data.shipper_state;
        data.origin_postal_code = data.shipper_postal_code;
        data.origin_country_code = data.shipper_country_code;
        
        // Add destination data (same as consignee for rate calculation)
        data.destination_address_line1 = data.consignee_address_line1;
        data.destination_address_line2 = data.consignee_address_line2;
        data.destination_city = data.consignee_city;
        data.destination_state = data.consignee_state;
        data.destination_postal_code = data.consignee_postal_code;
        data.destination_country_code = data.consignee_country_code;
        
        return data;
    }

    /**
     * Fetch shipping rates from Aramex
     */
    async fetchShippingRates() {
        const btn = document.getElementById('fetch-rates-btn');
        const ratesSection = document.getElementById('rates-section');
        
        try {
            this.setButtonLoading(btn, true);
            
            const formData = this.getFormData();
            
            // Validate required fields for rate calculation
            const requiredFields = [
                'origin_city', 'origin_country_code',
                'destination_city', 'destination_country_code',
                'weight', 'length', 'width', 'height'
            ];
            
            const missingFields = requiredFields.filter(field => !formData[field]);
            if (missingFields.length > 0) {
                throw new Error(`Please fill in all required fields: ${missingFields.join(', ')}`);
            }
            
            const response = await this.makeAPICall(
                'erpnext_aramex_shipping.shipment.shipment.fetch_shipping_rates',
                formData
            );
            
            if (response.success) {
                this.displayShippingRates(response.rates);
                ratesSection.style.display = 'block';
                ratesSection.scrollIntoView({ behavior: 'smooth' });
                this.showAlert('Shipping rates retrieved successfully!', 'success');
            } else {
                throw new Error(response.message || 'Failed to fetch shipping rates');
            }
            
        } catch (error) {
            console.error('Error fetching rates:', error);
            this.showAlert(error.message, 'error');
            ratesSection.style.display = 'none';
        } finally {
            this.setButtonLoading(btn, false);
        }
    }

    /**
     * Display shipping rates
     */
    displayShippingRates(rates) {
        const container = document.getElementById('rates-container');
        
        if (!rates || rates.length === 0) {
            container.innerHTML = '<p class="no-rates">No shipping rates available for this route.</p>';
            return;
        }
        
        container.innerHTML = '';
        
        rates.forEach((rate, index) => {
            const rateElement = document.createElement('div');
            rateElement.className = 'rate-item';
            rateElement.dataset.rateIndex = index;
            
            rateElement.innerHTML = `
                <div class="rate-header">
                    <div class="rate-service">${rate.service_name || 'Aramex Service'}</div>
                    <div class="rate-amount">${rate.total_amount} ${rate.currency || 'AED'}</div>
                </div>
                <div class="rate-description">${rate.description || 'Standard shipping service'}</div>
                ${rate.transit_time ? `<div class="rate-transit">Transit Time: ${rate.transit_time}</div>` : ''}
            `;
            
            rateElement.addEventListener('click', () => this.selectRate(rate, rateElement));
            container.appendChild(rateElement);
        });
    }

    /**
     * Select a shipping rate
     */
    selectRate(rate, element) {
        // Remove previous selection
        document.querySelectorAll('.rate-item').forEach(item => {
            item.classList.remove('selected');
        });
        
        // Select current rate
        element.classList.add('selected');
        this.selectedRate = rate;
        
        // Enable create shipment button
        const createBtn = document.getElementById('create-shipment-btn');
        if (createBtn) {
            createBtn.disabled = false;
        }
        
        this.showAlert('Rate selected. You can now create the shipment.', 'info');
    }

    /**
     * Create a shipment
     */
    async createShipment() {
        const btn = document.getElementById('create-shipment-btn');
        const resultSection = document.getElementById('result-section');
        
        try {
            this.setButtonLoading(btn, true);
            
            if (!this.selectedRate) {
                throw new Error('Please select a shipping rate first');
            }
            
            const formData = this.getFormData();
            
            const response = await this.makeAPICall(
                'erpnext_aramex_shipping.shipment.shipment.create_aramex_shipment',
                formData
            );
            
            if (response.success) {
                this.currentShipment = response;
                this.displayShipmentResult(response);
                resultSection.style.display = 'block';
                resultSection.scrollIntoView({ behavior: 'smooth' });
                this.showAlert('Shipment created successfully!', 'success');
                
                // Refresh history
                this.loadShipmentHistory();
            } else {
                throw new Error(response.message || 'Failed to create shipment');
            }
            
        } catch (error) {
            console.error('Error creating shipment:', error);
            this.showAlert(error.message, 'error');
        } finally {
            this.setButtonLoading(btn, false);
        }
    }

    /**
     * Display shipment creation result
     */
    displayShipmentResult(result) {
        const container = document.getElementById('result-container');
        
        container.innerHTML = `
            <div class="result-item">
                <span class="result-label">Shipment ID:</span>
                <span class="result-value">${result.shipment_id || 'N/A'}</span>
            </div>
            <div class="result-item">
                <span class="result-label">Reference:</span>
                <span class="result-value">${result.reference || 'N/A'}</span>
            </div>
            <div class="result-item">
                <span class="result-label">Tracking Number:</span>
                <span class="result-value">${result.foreign_hawb || 'N/A'}</span>
            </div>
            ${result.erpnext_shipment_id ? `
            <div class="result-item">
                <span class="result-label">ERPNext Record:</span>
                <span class="result-value">${result.erpnext_shipment_id}</span>
            </div>
            ` : ''}
        `;
    }

    /**
     * Print shipping label
     */
    async printShippingLabel() {
        const btn = document.getElementById('print-label-btn');
        
        try {
            this.setButtonLoading(btn, true);
            
            if (!this.currentShipment || !this.currentShipment.shipment_id) {
                throw new Error('No shipment ID available');
            }
            
            const response = await this.makeAPICall(
                'erpnext_aramex_shipping.shipment.shipment.print_shipping_label',
                { shipment_id: this.currentShipment.shipment_id }
            );
            
            if (response.success && response.label_url) {
                // Open label in new window
                window.open(response.label_url, '_blank');
                this.showAlert('Shipping label opened in new window', 'success');
            } else {
                throw new Error(response.message || 'Failed to generate shipping label');
            }
            
        } catch (error) {
            console.error('Error printing label:', error);
            this.showAlert(error.message, 'error');
        } finally {
            this.setButtonLoading(btn, false);
        }
    }

    /**
     * Track current shipment
     */
    async trackCurrentShipment() {
        if (!this.currentShipment || !this.currentShipment.shipment_id) {
            this.showAlert('No shipment ID available for tracking', 'error');
            return;
        }
        
        // Set the tracking number and trigger tracking
        const trackingInput = document.getElementById('tracking-number');
        if (trackingInput) {
            trackingInput.value = this.currentShipment.shipment_id;
            await this.trackShipment();
        }
    }

    /**
     * Track a shipment by ID
     */
    async trackShipment() {
        const btn = document.getElementById('track-btn');
        const trackingInput = document.getElementById('tracking-number');
        const resultsContainer = document.getElementById('tracking-results');
        
        try {
            this.setButtonLoading(btn, true);
            
            const shipmentId = trackingInput.value.trim();
            if (!shipmentId) {
                throw new Error('Please enter a shipment ID or tracking number');
            }
            
            const response = await this.makeAPICall(
                'erpnext_aramex_shipping.shipment.shipment.track_aramex_shipment',
                { shipment_id: shipmentId }
            );
            
            if (response.success) {
                this.displayTrackingResults(response.tracking_results);
                resultsContainer.style.display = 'block';
                resultsContainer.scrollIntoView({ behavior: 'smooth' });
                this.showAlert('Tracking information retrieved successfully!', 'success');
            } else {
                throw new Error(response.message || 'Failed to track shipment');
            }
            
        } catch (error) {
            console.error('Error tracking shipment:', error);
            this.showAlert(error.message, 'error');
            document.getElementById('tracking-results').style.display = 'none';
        } finally {
            this.setButtonLoading(btn, false);
        }
    }

    /**
     * Display tracking results
     */
    displayTrackingResults(trackingResults) {
        const container = document.getElementById('tracking-results');
        
        if (!trackingResults || trackingResults.length === 0) {
            container.innerHTML = '<p class="no-tracking">No tracking information available.</p>';
            return;
        }
        
        container.innerHTML = '';
        
        trackingResults.forEach(result => {
            const trackingElement = document.createElement('div');
            trackingElement.className = 'tracking-item';
            
            let eventsHtml = '';
            if (result.events && result.events.length > 0) {
                eventsHtml = result.events.map(event => `
                    <div class="tracking-event">
                        <div class="tracking-date">${this.formatDate(event.date)}</div>
                        <div class="tracking-location">${event.location || 'N/A'}</div>
                        <div class="tracking-description">${event.status || 'N/A'}</div>
                    </div>
                `).join('');
            } else {
                eventsHtml = '<p class="no-events">No tracking events available.</p>';
            }
            
            trackingElement.innerHTML = `
                <div class="tracking-header">
                    <div class="tracking-waybill">${result.waybill_number || result.reference || 'N/A'}</div>
                    <div class="tracking-status">${result.status || 'Unknown'}</div>
                </div>
                <div class="tracking-events">
                    ${eventsHtml}
                </div>
            `;
            
            container.appendChild(trackingElement);
        });
    }

    /**
     * Load shipment history
     */
    async loadShipmentHistory() {
        const btn = document.getElementById('refresh-history-btn');
        const container = document.getElementById('history-container');
        
        try {
            this.setButtonLoading(btn, true);
            
            const response = await this.makeAPICall(
                'erpnext_aramex_shipping.shipment.shipment.get_shipment_history',
                { limit: 20 }
            );
            
            if (response.success) {
                this.displayShipmentHistory(response.shipments);
            } else {
                throw new Error(response.message || 'Failed to load shipment history');
            }
            
        } catch (error) {
            console.error('Error loading history:', error);
            container.innerHTML = '<p class="error-message">Failed to load shipment history.</p>';
        } finally {
            this.setButtonLoading(btn, false);
        }
    }

    /**
     * Display shipment history
     */
    displayShipmentHistory(shipments) {
        const container = document.getElementById('history-container');
        
        if (!shipments || shipments.length === 0) {
            container.innerHTML = '<p class="no-history">No shipment history available.</p>';
            return;
        }
        
        const table = document.createElement('table');
        table.className = 'history-table';
        
        table.innerHTML = `
            <thead>
                <tr>
                    <th>Reference</th>
                    <th>Shipper</th>
                    <th>Consignee</th>
                    <th>Weight</th>
                    <th>Status</th>
                    <th>Created</th>
                </tr>
            </thead>
            <tbody>
                ${shipments.map(shipment => `
                    <tr>
                        <td>${shipment.reference || 'N/A'}</td>
                        <td>${shipment.shipper_name || 'N/A'}</td>
                        <td>${shipment.consignee_name || 'N/A'}</td>
                        <td>${shipment.weight || 'N/A'}</td>
                        <td><span class="status-badge status-${(shipment.status || 'unknown').toLowerCase().replace(' ', '-')}">${shipment.status || 'Unknown'}</span></td>
                        <td>${this.formatDate(shipment.creation_date)}</td>
                    </tr>
                `).join('')}
            </tbody>
        `;
        
        container.innerHTML = '';
        container.appendChild(table);
    }

    /**
     * Make API call to ERPNext
     */
    async makeAPICall(method, args = {}) {
        try {
            const response = await fetch('/api/method/' + method, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Frappe-CSRF-Token': this.getCSRFToken()
                },
                body: JSON.stringify(args)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.exc) {
                throw new Error(data.exc);
            }
            
            return data.message || data;
            
        } catch (error) {
            console.error('API call failed:', error);
            throw error;
        }
    }

    /**
     * Get CSRF token for API calls
     */
    getCSRFToken() {
        return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    }

    /**
     * Set button loading state
     */
    setButtonLoading(button, loading) {
        if (!button) return;
        
        if (loading) {
            button.classList.add('loading');
            button.disabled = true;
        } else {
            button.classList.remove('loading');
            button.disabled = false;
        }
    }

    /**
     * Show alert message
     */
    showAlert(message, type = 'info') {
        const container = document.getElementById('alert-container');
        
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.textContent = message;
        
        container.appendChild(alert);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.parentNode.removeChild(alert);
            }
        }, 5000);
        
        // Scroll to top to show alert
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    /**
     * Format date for display
     */
    formatDate(dateString) {
        if (!dateString) return 'N/A';
        
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
        } catch (error) {
            return dateString;
        }
    }
}

// Initialize the dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ShippingDashboard();
});

// Export for potential external use
window.ShippingDashboard = ShippingDashboard;
