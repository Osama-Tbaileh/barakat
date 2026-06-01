import frappe


def execute():
    if frappe.db.exists("Custom Field", "POS Profile-custom_counter_account"):
        frappe.delete_doc("Custom Field", "POS Profile-custom_counter_account", ignore_permissions=True)
        frappe.db.commit()
