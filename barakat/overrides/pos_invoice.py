import frappe
from frappe import _
from frappe.utils import flt, getdate
from erpnext.accounts.doctype.pos_invoice.pos_invoice import POSInvoice


class BarakatPOSInvoice(POSInvoice):
	def set_outstanding_amount(self):
		# ERPNext's base computes `total = flt(rounded_total) or flt(grand_total)`.
		# Python's `or` treats a legitimate rounded_total of 0 as falsy and wrongly
		# falls back to grand_total — so a small total that rounds down to 0 (e.g. a
		# 0.5 cash sale) is left Unpaid even though the customer owes nothing. The
		# rounding difference is already booked to the Round Off account via
		# rounding_adjustment, so nothing is actually receivable. Run the standard
		# logic, then settle the invoice to Paid in exactly this rounded-to-0 case.
		# Every other invoice is untouched.
		super().set_outstanding_amount()
		if flt(self.rounding_adjustment) and not flt(self.rounded_total):
			self.outstanding_amount = 0.0

	def validate_pos_opening_entry(self):
		opening_entries = frappe.get_all(
			"POS Opening Entry",
			fields=["name", "period_start_date"],
			filters={"pos_profile": self.pos_profile, "status": "Open"},
			order_by="period_start_date desc",
		)
		if not opening_entries:
			frappe.throw(
				title=_("POS Opening Entry Missing"),
				msg=_("No open POS Opening Entry found for POS Profile {0}.").format(
					frappe.bold(self.pos_profile)
				),
			)
		if len(opening_entries) > 1:
			frappe.throw(
				title=_("Multiple POS Opening Entry"),
				msg=_(
					"POS Profile - {0} has multiple open POS Opening Entries. Please close or cancel the existing entries before proceeding."
				).format(self.pos_profile),
			)
		# Offline-first: only reject if the invoice is dated before the shift
		# opened. The standard today() check breaks offline sync — orders created
		# on Day 1 with internet back on Day 2 still have the correct posting_date
		# and belong to this shift.
		if getdate(self.posting_date) < getdate(opening_entries[0].get("period_start_date")):
			frappe.throw(
				title=_("Invalid Posting Date"),
				msg=_(
					"Invoice posting date cannot be before the POS Opening Entry {0} start date."
				).format(opening_entries[0].get("name")),
			)
