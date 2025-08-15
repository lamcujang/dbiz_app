app_name = "dbiz_app"
app_title = "DBIZ APP"
app_publisher = "lamnl"
app_description = "DBIZ APP"
app_email = "lamnl@digitalbiz.com.vn"
app_license = "mit"
# required_apps = []

# Includes in <head>
# ------------------

# web_include_js = "/assets/dbiz_app/js/dbiz_app.js"
app_include_js = ["/assets/dbiz_app/js/custom.js"]
# include js, css files in header of desk.html
# app_include_css = "/assets/dbiz_app/css/dbiz_app.css"
# app_include_js = "/assets/dbiz_app/js/dbiz_app.js"

# include js, css files in header of web template
# web_include_css = "/assets/dbiz_app/css/dbiz_app.css"
# web_include_js = "/assets/dbiz_app/js/dbiz_app.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "dbiz_app/public/scss/website"

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
doctype_js = {"Customer": "public/js/customer.js"}
# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "dbiz_app/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
jinja = {
    "methods": [
        "dbiz_app.api.convert_pdf_to_image",
        # "dbiz_app.api.convert_to_eu_format",
        "dbiz_app.api.format_number_jinja",
        "dbiz_app.api.format_currency_jinja",
    ],
    # "methods": "dbiz_app.utils.jinja_methods",
    # "filters": "dbiz_app.utils.jinja_filters"
}

# Installation
# ------------

# before_install = "dbiz_app.install.before_install"
# after_install = "dbiz_app.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "dbiz_app.uninstall.before_uninstall"
# after_uninstall = "dbiz_app.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "dbiz_app.utils.before_app_install"
# after_app_install = "dbiz_app.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "dbiz_app.utils.before_app_uninstall"
# after_app_uninstall = "dbiz_app.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "dbiz_app.notifications.get_notification_config"

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

override_doctype_class = {
    "Production Plan": "dbiz_app.overrides.cus_production_plan.cusproductionplan",
    "Sales Order": "dbiz_app.overrides.cus_sales_order.cus_sales_order",
    "BOM": "dbiz_app.overrides.cus_bom.cus_bom",
    "Work Order": "dbiz_app.overrides.cus_work_order.cus_work_order",
    "Item": "dbiz_app.overrides.cus_item.cus_item",
    "Job Card": "dbiz_app.overrides.cus_job_card.cus_job_card",
    "Purchase Invoice": "dbiz_app.overrides.cus_purchase_invoice.cus_purchase_invoice",
    "Payment Entry": "dbiz_app.overrides.cus_payment_entry.cus_payment_entry",
    "Stock Entry": "dbiz_app.overrides.cus_stock_entry.cus_stock_entry",
    "Pick List": "dbiz_app.overrides.cus_pick_list.cus_pick_list",
}

# Translation paths
translation_paths = ["translations"]
# Document Events
# ---------------
# Hook on document methods and events
doc_events = {
    "Production Plan": {
        "after_delete": "dbiz_app.overrides.cus_production_plan.pp_before_delete",
    }
}
override_whitelisted_methods = {
	"frappe.model.workflow.apply_workflow": "dbiz_app.overrides.cus_workflow.apply_workflow"
}
# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"dbiz_app.tasks.all"
# 	],
# 	"daily": [
# 		"dbiz_app.tasks.daily"
# 	],
# 	"hourly": [
# 		"dbiz_app.tasks.hourly"
# 	],
# 	"weekly": [
# 		"dbiz_app.tasks.weekly"
# 	],
# 	"monthly": [
# 		"dbiz_app.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "dbiz_app.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "dbiz_app.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "dbiz_app.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["dbiz_app.utils.before_request"]
# after_request = ["dbiz_app.utils.after_request"]

# Job Events
# ----------
# before_job = ["dbiz_app.utils.before_job"]
# after_job = ["dbiz_app.utils.after_job"]

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
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"dbiz_app.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }
# override_whitelisted_methods = {
#     "erpnext.accounts.doctype.gl_entry.gl_entry.rename_temporarily_named_docs": "dbiz_app.dbiz_app.custom_hook.gl_custom.rename_temporarily_named_docs"
# }
# override_doctype_class = {
# 	"PurchaseInvoice": "dbiz_app.overrides.purchase_invoice_custom.PurchaseInvoiceCustom"
# }
