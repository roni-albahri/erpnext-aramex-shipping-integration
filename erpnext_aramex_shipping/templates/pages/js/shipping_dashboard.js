// Aramex Shipping Dashboard JavaScript test
class ShippingDashboard {
    constructor() {
        this.shipments = [];
        this.filteredShipments = [];
        this.currentPage = 1;
        this.itemsPerPage = 10;
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadShipments();
        this.setupRealTimeUpdates();
    }

    bindEvents() {
        // Refresh button
        document.getElementById('refreshBtn').addEventListener('click', () => this.refreshData());
        
        // New shipment button
        document.getElementById('newShipmentBtn').addEventListener('click', () => this.openNewShipmentModal());
        
        // Search functionality
        document.getElementById('searchInput').addEventListener('input', (e) => this.handleSearch(e.target.value));
        
        // Filter functionality
        document.getElementById('statusFilter').addEventListener('change', (e) => this.handleFilter());
        document.getElementById('dateFilter').addEventListener('change', (e) => this.handleFilter());
        
        // Modal events
        document.getElementById('newShipmentForm').addEventListener('submit', (e) => this.handleNewShipment(e));
        
        // Close modal when clicking outside
        document.getElementById('newShipmentModal').addEventListener('click', (e) => {
            if (e.target.id === 'newShipmentModal') {
                this.closeModal();
            }
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
            if (e.ctrlKey && e.key === 'r') {
                e.preventDefault();
                this.refreshData();
            }
        });
    }

    async loadShipments() {
        this.showLoading(true);
        
        try {
            const response = await fetch('/api/method/erpnext_aramex_shipping.api.aramex.get_shipments', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Frappe-CSRF-Token': frappe.csrf_token
                }
            });
            
            const data = await response.json();
            this.shipments = data.message || [];
            this.filteredShipments = [...this.shipments];
            this.updateDashboard();
        } catch (error) {
            console.error('Error loading shipments:', error);
            this.showError('Failed to load shipments. Please try again.');
        } finally {
            this.showLoading(false);
        }
    }

    updateDashboard() {
        this.updateStats();
        this.renderShipments();
    }

    updateStats() {
        const stats = {
            total: this.shipments.length,
            delivered: this.shipments.filter(s => s.status === 'delivered').length,
            inTransit: this.shipments.filter(s => s.status === 'in_transit').length,
            failed: this.shipments.filter(s => s.status === 'failed').length
        };

        document.getElementById('totalShipments').textContent = stats.total;
        document.getElementById('deliveredShipments').textContent = stats.delivered;
        document.getElementById('inTransitShipments').textContent = stats.inTransit;
        document.getElementById('failedShipments').textContent = stats.failed;
    }

    renderShipments() {
        const tbody = document.getElementById('shipmentsTableBody');
        
        if (this.filteredShipments.length === 0) {
            this.showEmptyState(true);
            return;
        }
        
        this.showEmptyState(false);
        
        tbody.innerHTML = this.filteredShipments
            .slice((this.currentPage - 1) * this.itemsPerPage, this.currentPage * this.itemsPerPage)
            .map(shipment => this.createShipmentRow(shipment))
            .join('');
    }

    createShipmentRow(shipment) {
        const statusClass = this.getStatusClass(shipment.status);
        const statusText = this.getStatusText(shipment.status);
        
        return `
            <tr class="table-row">
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm font-medium text-gray-900">${shipment.tracking_id}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm text-gray-900">${shipment.customer_name}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm text-gray-900">${shipment.destination}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="status-badge ${statusClass}">${statusText}</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${new Date(shipment.created_at).toLocaleDateString()}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button onclick="dashboard.viewShipment('${shipment.tracking_id}')" 
                            class="text-blue-600 hover:text-blue-900 mr-3">
                        View
                    </button>
                    <button onclick="dashboard.trackShipment('${shipment.tracking_id}')" 
                            class="text-green-600 hover:text-green-900">
                        Track
                    </button>
                </td>
            </tr>
        `;
    }

    getStatusClass(status) {
        const statusMap = {
            'pending': 'pending',
            'in_transit': 'in_transit',
            'delivered': 'delivered',
            'failed': 'failed'
        };
        return statusMap[status] || 'pending';
    }

    getStatusText(status) {
        const statusMap = {
            'pending': 'Pending',
            'in_transit': 'In Transit',
            'delivered': 'Delivered',
            'failed': 'Failed'
        };
        return statusMap[status] || 'Unknown';
    }

    handleSearch(query) {
        if (!query.trim()) {
            this.filteredShipments = [...this.shipments];
        } else {
            this.filteredShipments = this.shipments.filter(shipment =>
                shipment.tracking_id.toLowerCase().includes(query.toLowerCase()) ||
                shipment.customer_name.toLowerCase().includes(query.toLowerCase()) ||
                shipment.destination.toLowerCase().includes(query.toLowerCase())
            );
        }
        this.currentPage = 1;
        this.renderShipments();
    }

    handleFilter() {
        const statusFilter = document.getElementById('statusFilter').value;
        const dateFilter = document.getElementById('dateFilter').value;
        
        this.filteredShipments = this.shipments.filter(shipment => {
            let matchesStatus = !statusFilter || shipment.status === statusFilter;
            let matchesDate = true;
            
            if (dateFilter !== 'all') {
                const shipmentDate = new Date(shipment.created_at);
                const today = new Date();
                
                switch (dateFilter) {
                    case 'today':
                        matchesDate = shipmentDate.toDateString() === today.toDateString();
                        break;
                    case 'week':
                        const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
                        matchesDate = shipmentDate >= weekAgo;
                        break;
                    case 'month':
                        const monthAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000);
                        matchesDate = shipmentDate >= monthAgo;
                        break;
                }
            }
            
            return matchesStatus && matchesDate;
        });
        
        this.currentPage = 1;
        this.renderShipments();
    }

    async handleNewShipment(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const shipmentData = Object.fromEntries(formData.entries());
        
        try {
            const response = await fetch('/api/method/erpnext_aramex_shipping.api.aramex.create_shipment', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Frappe-CSRF-Token': frappe.csrf_token
                },
                body: JSON.stringify(shipmentData)
            });
            
            const result = await response.json();
            
            if (result.message) {
                this.showSuccess('Shipment created successfully!');
                this.closeModal();
                event.target.reset();
                this.loadShipments();
            } else {
                this.showError(result.error || 'Failed to create shipment');
            }
        } catch (error) {
            console.error('Error creating shipment:', error);
            this.showError('Failed to create shipment. Please try again.');
        }
    }

    async viewShipment(trackingId) {
        try {
            const response = await fetch(`/api/method/erpnext_aramex_shipping.api.aramex.get_shipment_details?tracking_id=${trackingId}`, {
                headers: {
                    'X-Frappe-CSRF-Token': frappe.csrf_token
                }
            });
            
            const data = await response.json();
            if (data.message) {
                this.showShipmentDetails(data.message);
            }
        } catch (error) {
            console.error('Error fetching shipment details:', error);
            this.showError('Failed to load shipment details');
        }
    }

    async trackShipment(trackingId) {
        try {
            const response = await fetch(`/api/method/erpnext_aramex_shipping.api.aramex.track_shipment?tracking_id=${trackingId}`, {
                headers: {
                    'X-Frappe-CSRF-Token': frappe.csrf_token
                }
            });
            
            const data = await response.json();
            if (data.message) {
                this.showTrackingDetails(data.message);
            }
        } catch (error) {
            console.error('Error tracking shipment:', error);
            this.showError('Failed to track shipment');
        }
    }

    setupRealTimeUpdates() {
        // Set up periodic refresh every 30 seconds
        setInterval(() => {
            this.loadShipments();
        }, 30000);
        
        // Listen for WebSocket updates if available
        if (window.frappe.realtime) {
            frappe.realtime.on('shipment_updated', (data) => {
                this.updateShipmentStatus(data);
            });
        }
    }

    updateShipmentStatus(data) {
        const shipmentIndex = this.shipments.findIndex(s => s.tracking_id === data.tracking_id);
        if (shipmentIndex !== -1) {
            this.shipments[shipmentIndex] = { ...this.shipments[shipmentIndex], ...data };
            this.handleSearch(document.getElementById('searchInput').value);
        }
    }

    refreshData() {
        this.loadShipments();
    }

    openNewShipmentModal() {
        document.getElementById('newShipmentModal').classList.remove('hidden');
    }

    closeModal() {
        document.getElementById('newShipmentModal').classList.add('hidden');
    }

    showLoading(show) {
        const loadingState = document.getElementById('loadingState');
        const table = document.querySelector('table');
        
        if (show) {
            loadingState.classList.remove('hidden');
            table.classList.add('hidden');
        } else {
            loadingState.classList.add('hidden');
            table.classList.remove('hidden');
        }
    }

    showEmptyState(show) {
        const emptyState = document.getElementById('emptyState');
        const table = document.querySelector('table');
        
        if (show) {
            emptyState.classList.remove('hidden');
            table.classList.add('hidden');
        } else {
            emptyState.classList.add('hidden');
            table.classList.remove('hidden');
        }
    }

    showSuccess(message) {
        frappe.show_alert({
            message: message,
            indicator: 'green'
        });
    }

    showError(message) {
        frappe.show_alert({
            message: message,
            indicator: 'red'
        });
    }

    showShipmentDetails(shipment) {
        const dialog = new frappe.ui.Dialog({
            title: 'Shipment Details',
            fields: [
                { fieldname: 'tracking_id', fieldtype: 'Data', label: 'Tracking ID', read_only: 1, default: shipment.tracking_id },
                { fieldname: 'customer_name', fieldtype: 'Data', label: 'Customer Name', read_only: 1, default: shipment.customer_name },
                { fieldname: 'destination', fieldtype: 'Data', label: 'Destination', read_only: 1, default: shipment.destination },
                { fieldname: 'status', fieldtype: 'Data', label: 'Status', read_only: 1, default: shipment.status },
                { fieldname: 'weight', fieldtype: 'Float', label: 'Weight (kg)', read_only: 1, default: shipment.weight },
                { fieldname: 'created_at', fieldtype: 'Date', label: 'Created Date', read_only: 1, default: shipment.created_at }
            ]
        });
        dialog.show();
    }

    showTrackingDetails(trackingData) {
        const dialog = new frappe.ui.Dialog({
            title: 'Tracking Details',
            fields: [
                { fieldname: 'current_status', fieldtype: 'Data', label: 'Current Status', read_only: 1, default: trackingData.current_status },
                { fieldname: 'location', fieldtype: 'Data', label: 'Current Location', read_only: 1, default: trackingData.location },
                { fieldname: 'estimated_delivery', fieldtype: 'Date', label: 'Estimated Delivery', read_only: 1, default: trackingData.estimated_delivery },
                { fieldname: 'history', fieldtype: 'Text', label: 'Tracking History', read_only: 1, default: JSON.stringify(trackingData.history, null, 2) }
            ]
        });
        dialog.show();
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new ShippingDashboard();
});

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ShippingDashboard;
}
