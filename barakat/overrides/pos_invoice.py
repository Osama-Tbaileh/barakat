import math

import frappe
from frappe import _
from frappe.utils import flt, getdate
from erpnext.accounts.doctype.pos_invoice.pos_invoice import POSInvoice

ROUNDING_THRESHOLD = 0.4


class BarakatPOSInvoice(POSInvoice):
	def set_rounded_total(self):
		if not self.meta.get_field("rounded_total"):
			return

		if self.is_rounded_total_disabled():
			self.rounded_total = 0
			self.rounding_adjustment = 0
		else:
			grand = flt(self.grand_total)
			decimal_part = grand - math.floor(grand)

			if decimal_part >= ROUNDING_THRESHOLD:
				self.rounded_total = flt(math.floor(grand) + 1, self.precision("rounded_total"))
			else:
				self.rounded_total = flt(math.floor(grand), self.precision("rounded_total"))

			self.rounding_adjustment = flt(
				self.rounded_total - grand, self.precision("rounding_adjustment")
			)

		self.base_rounded_total = flt(
			self.rounded_total * self.conversion_rate, self.precision("base_rounded_total")
		)
		self.base_rounding_adjustment = flt(
			self.rounding_adjustment * self.conversion_rate,
			self.precision("base_rounding_adjustment"),
		)

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
