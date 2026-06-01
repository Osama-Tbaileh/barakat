frappe.ui.form.on("POS Profile", {
	refresh: function (frm) {
		frm.set_query("custom_cash_account", function () {
			return { filters: { account_type: "Cash", company: frm.doc.company } };
		});
		frm.set_query("custom_salary_advance_account", function () {
			return { filters: { account_type: "Receivable", company: frm.doc.company } };
		});
		frm.set_query("custom_expense_account", function () {
			return { filters: { root_type: "Expense", company: frm.doc.company } };
		});
		frm.set_query("custom_owner_deposit_account", function () {
			return {
				filters: {
					root_type: ["in", ["Equity", "Liability"]],
					company: frm.doc.company,
				},
			};
		});
		frm.set_query("custom_bank_account", function () {
			return { filters: { account_type: "Bank", company: frm.doc.company } };
		});
	},
});
