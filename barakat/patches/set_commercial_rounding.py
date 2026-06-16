import frappe


def execute():
	frappe.db.set_single_value("System Settings", "rounding_method", "Commercial Rounding")
