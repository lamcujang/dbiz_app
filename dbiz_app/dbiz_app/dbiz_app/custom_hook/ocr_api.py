import frappe
from openai import OpenAI
@frappe.whitelist()
def openAI_ocr(image_url):
    try:
        image_url = frappe.db.get_single_value("Global Param Settings", "url") + image_url
        key = frappe.db.get_single_value("Global Param Settings", "open_ai_key")
        client = OpenAI(api_key=key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Return only the decimal number."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url,
                            },
                        },
                    ],
                }
            ],
            max_tokens=300,
        )
        data_str = response.choices[0].message.content
        # Extract float number from string
        import re
        numbers = re.findall(r'\d*\.?\d+', data_str)
        # object return
        return {
            "reponse": response,
            "numbers": numbers[0] if numbers else '0'
        }
    except Exception as e:
        frappe.log_error(f"Error processing image data: {str(e)}")
        frappe.throw(f"Error processing image data: {str(e)}")
        
@frappe.whitelist()
def update_file_public(file_name):
    try:
        file = frappe.get_doc("File", file_name)
        file.is_private = 0
        file.save()
    except Exception as e:
        frappe.log_error(f"Error processing image data: {str(e)}")
        frappe.throw(f"Error processing image data: {str(e)}")