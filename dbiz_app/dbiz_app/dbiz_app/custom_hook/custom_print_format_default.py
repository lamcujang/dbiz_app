import frappe
from frappe import _
from frappe.utils import json
def get_matching_print_formats(doc):
    try:
        print_formats = frappe.get_list('Print Format', 
            filters={
                'doc_type': doc.get('doctype', '')
            },
            fields=['name', 'column_in_doc', 'value_in_column']
        )
        
        matching_formats = []
        
        for pf in print_formats:
            if not pf.column_in_doc or not pf.value_in_column:
                continue
            
            doc_value = doc.get(pf.column_in_doc)
            
            if (doc_value is not None and str(doc_value).lower() == str(pf.value_in_column).lower()):
                matching_formats.append({
                    'print_format_name': pf.name,
                    'column': pf.column_in_doc,
                    'value': pf.value_in_column
                })
        
        return matching_formats
    
    except Exception as e:
        frappe.log_error(f"Error in get_matching_print_formats: {str(e)}")
        return []

@frappe.whitelist()
def execute_print_format_matching(doc, format=None):
    try:
        docJson = json.loads(doc)
        matching_formats = get_matching_print_formats(docJson)
        
        if matching_formats:
            return matching_formats[0]['print_format_name']
        else:
            return format
    
    except Exception as e:
        return format
    