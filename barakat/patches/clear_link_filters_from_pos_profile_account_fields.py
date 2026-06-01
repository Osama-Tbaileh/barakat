import frappe

FIELDS = [
	"POS Profile-custom_cash_account",
	"POS Profile-custom_salary_advance_account",
	"POS Profile-custom_expense_account",
	"POS Profile-custom_owner_deposit_account",
	"POS Profile-custom_bank_account",
]


def execute():
	for name in FIELDS:
		if frappe.db.exists("Custom Field", name):
			frappe.db.set_value("Custom Field", name, "link_filters", None)
	frappe.db.commit()
