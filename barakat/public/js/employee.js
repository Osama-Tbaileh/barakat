frappe.ui.form.on("Employee", {
	custom_pos_pin: function (frm) {
		let pin = (frm.doc.custom_pos_pin || "").trim();
		if (!pin) return;

		// Strip any non-digit characters silently
		const cleaned = pin.replace(/\D/g, "");
		if (cleaned !== pin) {
			frm.set_value("custom_pos_pin", cleaned);
			pin = cleaned;
		}

		// Enforce max length of 6
		if (pin.length > 6) {
			frm.set_value("custom_pos_pin", pin.slice(0, 6));
			pin = pin.slice(0, 6);
		}

		// Show inline warning if length is out of range (but not while still typing)
		if (pin.length > 0 && pin.length < 4) {
			frm.set_df_property("custom_pos_pin", "description", __("PIN must be 4 to 6 digits."));
		} else {
			frm.set_df_property("custom_pos_pin", "description", __("4 to 6 digits only."));
		}
	},
});
