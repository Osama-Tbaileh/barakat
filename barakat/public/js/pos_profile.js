frappe.ui.form.on("POS Profile", {
	setup: function (frm) {
		frm.set_query("custom_cash_account", function (doc) {
			return {
				filters: [
					["account_type", "=", "Cash"],
					["company", "=", doc.company],
					["is_group", "=", 0],
				],
			};
		});
		frm.set_query("custom_salary_advance_account", function (doc) {
			return {
				filters: [
					["account_type", "=", "Receivable"],
					["company", "=", doc.company],
					["is_group", "=", 0],
				],
			};
		});
		frm.set_query("custom_expense_account", function (doc) {
			return {
				filters: [
					["root_type", "=", "Expense"],
					["company", "=", doc.company],
					["is_group", "=", 0],
				],
			};
		});
		frm.set_query("custom_owner_deposit_account", function (doc) {
			return {
				filters: [
					["root_type", "in", ["Equity", "Liability"]],
					["company", "=", doc.company],
					["is_group", "=", 0],
				],
			};
		});
		frm.set_query("custom_bank_account", function (doc) {
			return {
				filters: [
					["account_type", "=", "Bank"],
					["company", "=", doc.company],
					["is_group", "=", 0],
				],
			};
		});
	},
});
