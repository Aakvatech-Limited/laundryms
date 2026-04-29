import json
import os

import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

folder = "../patches/property_setter/property_setter_json"


def load_json(file):
	CURR_DIR = os.path.abspath(os.path.dirname(__file__))
	json_file_path = os.path.join(CURR_DIR, folder, file)
	with open(json_file_path, "r") as file:
		data = json.load(file)
	return data


def create_property_setter_from_json(property_setters_obj):
	disallowed_fields = [
		"name", "owner", "creation", "modified", "modified_by",
		"docstatus", "idx", "is_system_generated", "__last_sync_on",
	]
	existing_setters = {d.name for d in frappe.db.get_all("Property Setter", fields=["name"], page_length=10000)}

	for property_setter in property_setters_obj:
		if property_setter.get("name") in existing_setters:
			continue
		if not frappe.db.exists("DocType", property_setter.get("doc_type")):
			continue

		for_doctype = property_setter.get("doctype_or_field") == "DocType"

		make_property_setter(
			doctype=property_setter["doc_type"],
			fieldname=property_setter.get("field_name"),
			property=property_setter["property"],
			value=property_setter["value"],
			property_type=property_setter["property_type"],
			for_doctype=for_doctype,
		)


def execute():
	files = list(filter(
		lambda x: x.endswith(".json"),
		os.listdir(os.path.join(os.path.abspath(os.path.dirname(__file__)), folder)),
	))
	for file in files:
		data = load_json(file)
		create_property_setter_from_json(data)
