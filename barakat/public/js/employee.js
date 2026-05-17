frappe.ui.form.on("Employee", {
	refresh: function (frm) {
		const field = frm.get_field("custom_pos_pin");
		if (!field || !field.$input) return;

		// Native input listener fires on every keystroke — strips non-digits
		// immediately so the character never visibly appears in the field.
		field.$input.off("input.pin_validate").on("input.pin_validate", function () {
			const el = this;
			const pos = el.selectionStart;
			const cleaned = el.value.replace(/\D/g, "").slice(0, 6);
			if (cleaned !== el.value) {
				el.value = cleaned;
				const cursor = Math.min(pos, cleaned.length);
				el.setSelectionRange(cursor, cursor);
			}
		});
	},

	custom_pos_pin: function (frm) {
		const pin = (frm.doc.custom_pos_pin || "").trim();
		if (pin.length > 0 && pin.length < 4) {
			frm.set_df_property("custom_pos_pin", "description", __("PIN must be 4 to 6 digits."));
		} else {
			frm.set_df_property("custom_pos_pin", "description", __("4 to 6 digits only."));
		}
	},
});
