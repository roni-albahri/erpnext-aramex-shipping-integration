from . import __version__ as app_version

app_name = "erpnext_aramex_shipping"
app_title = "ERPNext Aramex Shipping"
app_publisher = "ERPNext Aramex Shipping"
app_description = "A comprehensive shipping integration for ERPNext with Aramex API"
app_icon = "octicon octicon-package"
app_color = "blue"
app_email = "support@example.com"
app_license = "MIT"
app_version = app_version

# Includes in <head>
# ------------------
#test
# include js, css files in header of desk.html
# app_include_css = "/assets/erpnext_aramex_shipping/css/erpnext_aramex_shipping.css"
# app_include_js = "/assets/erpnext_aramex_shipping/js/erpnext_aramex_shipping.js"

# include js, css files in header of web template
# web_include_css = "/assets/erpnext_aramex_shipping/css/erpnext_aramex_shipping.css"
# web_include_js = "/assets/erpnext_aramex_shipping/js/erpnext_aramex_shipping.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "erpnext_aramex_shipping/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "erpnext_aramex_shipping.utils.jinja_methods",
# 	"filters": "erpnext_aramex_shipping.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "erpnext_aramex_shipping.install.before_install"
# after_install = "erpnext_aramex_shipping.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "erpnext_aramex_shipping.uninstall.before_uninstall"
# after_uninstall = "erpnext_aramex_shipping.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "erpnext_aramex_shipping.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"erpnext_aramex_shipping.tasks.all"
# 	],
# 	"daily": [
# 		"erpnext_aramex_shipping.tasks.daily"
# 	],
# 	"hourly": [
# 		"erpnext_aramex_shipping.tasks.hourly"
# 	],
# 	"weekly": [
# 		"erpnext_aramex_shipping.tasks.weekly"
# 	],
# 	"monthly": [
# 		"erpnext_aramex_shipping.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "erpnext_aramex_shipping.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "erpnext_aramex_shipping.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "erpnext_aramex_shipping.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]


# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"partial": 1,
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"erpnext_aramex_shipping.auth.validate"
# ]

# Translation
# --------------------------------

# Make link fields search translated document names for these DocTypes
# Recommended only for DocTypes which have limited documents with untranslated names
# For example: Role, Gender, etc.
# translated_search_doctypes = []

# Website Pages
# --------------------------------

website_route_rules = [
    {"from_route": "/shipping-dashboard", "to_route": "shipping_dashboard"},
]

# API Whitelisted Methods
# --------------------------------

# Methods that can be called via REST API
# These methods will be accessible via /api/method/{method_name}
whitelisted_methods = [
    "erpnext_aramex_shipping.api.aramex.get_shipping_rates",
    "erpnext_aramex_shipping.api.aramex.create_shipment",
    "erpnext_aramex_shipping.api.aramex.generate_shipping_label",
    "erpnext_aramex_shipping.api.aramex.track_shipment",
    "erpnext_aramex_shipping.shipment.shipment.fetch_shipping_rates",
    "erpnext_aramex_shipping.shipment.shipment.create_aramex_shipment",
    "erpnext_aramex_shipping.shipment.shipment.print_shipping_label",
    "erpnext_aramex_shipping.shipment.shipment.track_aramex_shipment",
]
