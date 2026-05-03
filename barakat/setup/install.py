import frappe


def after_install():
	_enable_negative_stock()
	_set_session_expiry()
	_create_misc_item()
	_create_default_customer()
	frappe.db.commit()


def _enable_negative_stock():
	frappe.db.set_single_value("Stock Settings", "allow_negative_stock", 1)


def _set_session_expiry():
	doc = frappe.get_doc("System Settings")
	doc.session_expiry = "8760:00"
	doc.save(ignore_permissions=True)


def _create_misc_item():
	if frappe.db.exists("Item", "MISC"):
		return
	frappe.get_doc(
		{
			"doctype": "Item",
			"item_code": "MISC",
			"item_name": "Miscellaneous",
			"item_group": "Products",
			"is_stock_item": 0,
			"include_item_in_manufacturing": 0,
			"is_sales_item": 1,
			"is_purchase_item": 0,
			"description": "Generic line for ad-hoc cashier items without a catalog entry.",
		}
	).insert(ignore_permissions=True)


def _create_default_customer():
	if frappe.db.exists("Customer", "Default Customer"):
		return
	frappe.get_doc(
		{
			"doctype": "Customer",
			"customer_name": "Default Customer",
			"customer_group": "All Customer Groups",
			"territory": "All Territories",
		}
	).insert(ignore_permissions=True)
