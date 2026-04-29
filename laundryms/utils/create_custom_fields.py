import json
import os

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

folder = "../patches/custom_fields/custom_fields_json"


def load_json(file):
	CURR_DIR = os.path.abspath(os.path.dirname(__file__))
	json_file_path = os.path.join(CURR_DIR, folder, file)
	with open(json_file_path, "r") as file:
		data = json.load(file)
	return data


def create_fields_from_json(custom_fields_obj):
	disallowed_fields = [
		"name", "owner", "creation", "modified", "modified_by",
		"docstatus", "idx", "is_system_generated", "__last_sync_on",
	]
	doctype_custom_fields_dict = {}

	for custom_field in custom_fields_obj:
		doctype = custom_field["dt"]
		if not frappe.db.exists("DocType", doctype):
			continue
		all_fields = frappe.get_meta("Custom Field").get_valid_columns()
		field_list = set(all_fields).difference(disallowed_fields)
		custom_field_dict = {k: custom_field.get(k) for k in field_list}

		if doctype not in doctype_custom_fields_dict:
			doctype_custom_fields_dict[doctype] = []
		doctype_custom_fields_dict[doctype].append(custom_field_dict)

	create_custom_fields(doctype_custom_fields_dict, update=False)


def execute():
	files = list(filter(
		lambda x: x.endswith(".json"),
		os.listdir(os.path.join(os.path.abspath(os.path.dirname(__file__)), folder)),
	))
	for file in files:
		data = load_json(file)
		create_fields_from_json(data)
