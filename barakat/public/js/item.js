frappe.ui.form.on("Item", {
	disabled: function (frm) {
		if (!frm.doc.disabled) return;
		if (frm.doc.__islocal) return;

		const company = frm.doc.custom_company;
		if (!company) return;

		frappe.call({
			method: "frappe.client.get_list",
			args: {
				doctype: "POS Opening Entry",
				filters: { status: "Open", company: company },
				fields: ["name", "pos_profile"],
				limit_page_length: 5,
			},
			callback: function (r) {
				const shifts = r.message || [];
				if (shifts.length === 0) return;

				const lines = shifts
					.map((s) => `<li><b>${s.name}</b> — ${s.pos_profile}</li>`)
					.join("");

				frappe.msgprint({
					title: __("Open POS Shifts Detected"),
					indicator: "orange",
					message: __(
						"There are <b>{0}</b> open POS shift(s) for company <b>{1}</b>. " +
						"You must close all open POS Opening Entries before disabling this item:" +
						"<ul>{2}</ul>",
						[shifts.length, company, lines]
					),
				});
			},
		});
	},
});
