import re

import frappe


def validate_employee_pin(doc, method):
	pin = (doc.custom_pos_pin or "").strip()

	if not pin:
		return

	# Format: digits only, 4–6 characters
	if not re.fullmatch(r"\d{4,6}", pin):
		frappe.throw(
			"POS PIN must be <b>4 to 6 digits only</b> (no letters or special characters).",
			title="Invalid PIN",
		)

	# Uniqueness per company — Employee → Branch → custom_pos_company
	if not doc.branch:
		return

	company = frappe.db.get_value("Branch", doc.branch, "custom_pos_company")
	if not company:
		return

	duplicate = frappe.db.sql(
		"""
		SELECT e.name, e.employee_name
		FROM `tabEmployee` e
		INNER JOIN `tabBranch` b ON b.name = e.branch
		WHERE b.custom_pos_company = %s
		  AND e.custom_pos_pin = %s
		  AND e.name != %s
		LIMIT 1
		""",
		(company, pin, doc.name or "__new__"),
		as_dict=True,
	)

	if duplicate:
		frappe.throw(
			f"PIN <b>{pin}</b> is already assigned to employee "
			f"<b>{duplicate[0]['employee_name']}</b> ({duplicate[0]['name']}) "
			f"in company <b>{company}</b>. Each employee in a company must have a unique PIN.",
			title="Duplicate PIN",
		)
