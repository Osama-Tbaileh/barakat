import frappe
from frappe import _


def validate_branch(doc, method):
	# custom_pos_profiles only exists after after_install creates the custom field
	if not hasattr(doc, "custom_pos_profiles"):
		return
	_validate_unique_pos_profiles(doc)
	_validate_profiles_not_in_other_branches(doc)
	_sync_branch_back_reference(doc)


def _validate_unique_pos_profiles(doc):
	profiles = [row.pos_profile for row in (doc.custom_pos_profiles or []) if row.pos_profile]
	if len(profiles) != len(set(profiles)):
		frappe.throw(_("Each POS Profile can only appear once in a branch's profile list."))


def _validate_profiles_not_in_other_branches(doc):
	for row in (doc.custom_pos_profiles or []):
		if not row.pos_profile:
			continue
		other = frappe.db.sql(
			"""
			SELECT parent FROM `tabBranch POS Profile`
			WHERE pos_profile = %s AND parent != %s
			""",
			(row.pos_profile, doc.name or "__new__"),
			as_dict=True,
		)
		if other:
			frappe.throw(
				_("POS Profile {0} is already assigned to branch {1}. A profile can only belong to one branch.").format(
					row.pos_profile, other[0].parent
				)
			)


def _sync_branch_back_reference(doc):
	"""Write custom_branch on each POS Profile that belongs to this branch."""
	profiles_in_doc = {row.pos_profile for row in (getattr(doc, "custom_pos_profiles", None) or []) if row.pos_profile}

	# Set custom_branch on profiles now in this branch
	for profile in profiles_in_doc:
		frappe.db.set_value("POS Profile", profile, "custom_branch", doc.name)

	# Clear custom_branch on profiles that were removed from this branch
	previously_linked = frappe.db.get_all(
		"POS Profile",
		filters={"custom_branch": doc.name},
		pluck="name",
	)
	for profile in previously_linked:
		if profile not in profiles_in_doc:
			frappe.db.set_value("POS Profile", profile, "custom_branch", None)
