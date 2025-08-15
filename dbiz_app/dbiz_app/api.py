import base64
import os
from io import BytesIO
from typing import Optional

import frappe
from frappe.utils import cint, flt
from pdf2image import convert_from_bytes
from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFSyntaxError,
)


@frappe.whitelist()
def convert_pdf_to_image(
    pdf_url: str, dpi: int = 150, cache: bool = True
) -> Optional[str]:
    if not pdf_url:
        return None

    if cache:
        cache_key = f"pdf_image:{pdf_url}:{dpi}"
        cached_result = frappe.cache().get_value(cache_key)
        if cached_result:
            return cached_result

    try:
        if pdf_url.startswith("/private/files/"):
            pdf_path = frappe.get_site_path(pdf_url.lstrip("/"))
        elif pdf_url.startswith("/files/"):
            pdf_path = frappe.get_site_path("public/" + pdf_url.lstrip("/"))
        else:
            frappe.logger().error(f"Invalid PDF URL format: {pdf_url}")
            return None

        if not os.path.exists(pdf_path):
            frappe.logger().error(f"PDF file not found: {pdf_path}")
            return None

        file_size = os.path.getsize(pdf_path)
        adaptive_dpi = min(dpi, 100) if file_size > 5 * 1024 * 1024 else dpi

        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        images = convert_from_bytes(
            pdf_bytes,
            dpi=adaptive_dpi,
            first_page=1,
            last_page=1,
            thread_count=1,  # Faster for single page
            use_cropbox=True,
            grayscale=True,  # Grayscale renders faster and reduces size
        )

        if not images:
            frappe.logger().error(f"No images extracted from {pdf_url}")
            return None

        img_io = BytesIO()
        images[0].save(
            img_io,
            format="PNG",
            optimize=True,
            compress_level=4,  # Slightly faster than 6, still good quality
        )

        img_base64 = base64.b64encode(img_io.getvalue()).decode("utf-8")
        result = f"data:image/png;base64,{img_base64}"

        if cache:
            frappe.cache().set_value(cache_key, result, expires_in_sec=86400)

        return result

    except (PDFInfoNotInstalledError, PDFPageCountError, PDFSyntaxError) as e:
        frappe.logger().error(f"PDF conversion error: {str(e)}")
        return None
    except MemoryError:
        frappe.logger().error("Memory error during PDF conversion.")
        return None
    except Exception as e:
        frappe.logger().error(f"Unexpected error: {str(e)}")
        return None


@frappe.whitelist()
def get_company_address(company):
    address_name = frappe.db.get_value(
        "Dynamic Link",
        {"link_doctype": "Company", "link_name": company, "parenttype": "Address"},
        "parent",
    )

    if address_name:
        addr = frappe.db.get_value(
            "Address",
            address_name,
            [
                "address_title",
                "address_type",
                "address_line1",
                "address_line2",
                "city",
                "county",
                "state",
                "country",
                "pincode",
                "email_id",
                "phone",
                "fax",
            ],
            as_dict=True,
        )
        state = addr.state + ", " if addr.state else ""
        country = "Việt Nam" if addr.country == "Vietnam" else addr.country
        full_address = f"{addr.address_line1}, {addr.city}, {state} {country}"
        return full_address

    return ""


@frappe.whitelist()
def format_number_jinja(value, decimals=0, number_format=None):
    """
    Format a number with the specified decimals and format.

    Args:
        value: The number to format
        decimals: Number of decimal places (default 0)
        number_format: Format string for the number (default None, uses system default)

    Returns:
        Formatted number string
    """
    # Early return for empty values
    if value in (None, ""):
        return ""

    # Get number format if not provided
    number_format = number_format or get_number_format()
    info = get_number_format_info(number_format)

    # Handle default decimals
    if decimals == "default":
        decimals = (
            cint(frappe.db.get_default("float_precision")) or info["precision"] or 0
        )

    # Convert to float with proper precision
    value = flt(value, decimals)

    # Handle negative values
    is_negative = value < 0
    value = abs(value)

    # Format with fixed decimals
    formatted = f"{value:.{decimals}f}"

    # Split integer and decimal parts
    int_part, _, dec_part = formatted.partition(".")

    # Group the integer part digits
    int_part = group_digits(int_part, info["group_sep"], number_format)

    # Construct decimal part with correct separator if needed
    if decimals and info["decimal_str"]:
        dec_part = info["decimal_str"] + dec_part
    else:
        dec_part = ""

    # Return formatted number with sign if needed
    return f"-{int_part}{dec_part}" if is_negative else f"{int_part}{dec_part}"


@frappe.whitelist()
def format_currency_jinja(value, currency=None, decimals=None):
    """
    Format a value as currency with proper symbol placement and formatting.

    Args:
        value: The value to format
        currency: Currency code (default None, uses system default)
        decimals: Number of decimal places (default None, uses system settings)

    Returns:
        Formatted currency string with symbol
    """
    # Early return for empty values
    if value in (None, ""):
        return ""

    # Get currency info
    currency = currency or frappe.db.get_default("currency")
    number_format = get_number_format(currency)

    # Get currency symbol and position
    symbol = frappe.db.get_value("Currency", currency, "symbol") or currency
    symbol_on_right = frappe.db.get_value("Currency", currency, "symbol_on_right") == 1

    # Get decimals from settings if not specified
    if decimals is None:
        decimals = cint(frappe.db.get_default("currency_precision") or 0)

    # Format the number
    formatted_number = format_number_jinja(value, decimals, number_format)

    # Return with symbol in correct position
    return (
        f"{formatted_number} {symbol}"
        if symbol_on_right
        else f"{symbol} {formatted_number}"
    )


def get_number_format(currency=None):
    """
    Get the number format to use, either from currency or system defaults.

    Args:
        currency: Currency code (default None)

    Returns:
        Number format string
    """
    if currency:
        # Try to get custom format for the currency
        custom_format = frappe.db.get_value("Currency", currency, "number_format")
        if custom_format:
            return custom_format

    # Fall back to system default
    return frappe.db.get_default("number_format") or "#,###.##"


def get_number_format_info(format):
    """
    Get formatting information for the given number format.

    Args:
        format: Number format string

    Returns:
        Dictionary with decimal_str, group_sep, and precision
    """
    # Define format mapping
    format_map = {
        "#,###.##": {"decimal_str": ".", "group_sep": ","},
        "#.###,##": {"decimal_str": ",", "group_sep": "."},
        "# ###.##": {"decimal_str": ".", "group_sep": " "},
        "# ###,##": {"decimal_str": ",", "group_sep": " "},
        "#'###.##": {"decimal_str": ".", "group_sep": "'"},
        "#, ###.##": {"decimal_str": ".", "group_sep": ", "},
        "#,##,###.##": {"decimal_str": ".", "group_sep": ","},  # Indian format
        "#,###.###": {"decimal_str": ".", "group_sep": ","},
        "#.###": {"decimal_str": "", "group_sep": "."},
        "#,###": {"decimal_str": "", "group_sep": ","},
    }

    # Get format info or use default
    info = format_map.get(format, {"decimal_str": ".", "group_sep": ","})

    # Calculate precision from format
    if info["decimal_str"] and info["decimal_str"] in format:
        parts = format.split(info["decimal_str"])
        info["precision"] = len(parts[1]) if len(parts) > 1 else 0
    else:
        info["precision"] = 0

    return info


def group_digits(number, sep, format):
    """
    Group digits according to the number format

    Args:
        number: String representation of the integer part
        sep: Group separator character
        format: Number format string

    Returns:
        Number with properly grouped digits
    """
    if format == "#,##,###.##":  # Indian format
        if len(number) <= 3:
            return number

        # Split the number into head (all but last 3 digits) and tail (last 3 digits)
        head = number[:-3]
        tail = number[-3:]

        if not head:
            return tail

        # For Indian format, group head in chunks of 2 digits from right to left
        result = []
        for i in range(len(head), 0, -2):
            start = max(0, i - 2)
            result.append(head[start:i])

        # Join the groups in reverse order and append the tail
        return sep.join(result[::-1] + [tail])
    else:
        # Standard 3-digit grouping
        if len(number) <= 3:
            return number

        # Group digits in chunks of 3 from right to left
        result = []
        for i in range(len(number), 0, -3):
            start = max(0, i - 3)
            result.append(number[start:i])

        return sep.join(result[::-1])
