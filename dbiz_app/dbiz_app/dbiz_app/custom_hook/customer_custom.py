import frappe
import requests
import re

@frappe.whitelist()
def get_tax_information(tax_id):
    # api https://api.vietqr.io/v2/business/{taxId}
    url = f"https://api.vietqr.io/v2/business/{tax_id}"
    response = requests.get(url)
    return response.json()

@frappe.whitelist()
def address_from_tax_id(addressId,name, address):
    if addressId:
        address_data = frappe.get_doc('Address', addressId)
        address_data.address_line1 = address
        address_data.address_title = name
        # Extract city from address
        city_match = re.search(r'(Thành phố|Tỉnh)\s+([^,]+)', address)
        if city_match:
            address_data.city = city_match.group(2).strip()  # group(2) contains the city name
        else:
            # If no match found, set empty or handle as needed
            address_data.city = "TP HCM"
        address_data.save(ignore_permissions=True)
    else:
        if frappe.db.exists('Address', name):
            address_data = frappe.get_doc('Address', name)
            address_data.address_line1 = address
            address_data.address_title = name
            # Extract city from address
            city_match = re.search(r'(Thành phố|Tỉnh)\s+([^,]+)', address)
            if city_match:
                address_data.city = city_match.group(2).strip()  # group(2) contains the city name
            else:
                # If no match found, set empty or handle as needed
                address_data.city = "TP HCM"
            address_data.save(ignore_permissions=True)
        else:
            address_data = frappe.new_doc('Address')
            address_data.name = name
            address_data.address_line1 = address
            address_data.address_type = 'Office'
            address_data.country = 'Vietnam'
            address_data.address_title = name
            # Extract city from address
            city_match = re.search(r'(Thành phố|Tỉnh)\s+([^,]+)', address)
            if city_match:
                address_data.city = city_match.group(2).strip()  # group(2) contains the city name
            else:
                # If no match found, set empty or handle as needed
                address_data.city = "TP HCM"
                
            address_data.insert(ignore_permissions=True)
    return address_data.name
