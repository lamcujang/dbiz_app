# Copyright (c) 2025, lamnl and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    if not filters:
        filters = {}

    # Validate the dates before proceeding
    validate_dates(filters)

    # Define columns
    columns = get_columns()

    # SQL query with parameters from filters
    data = get_data(filters)

    return columns, data


def get_columns():
    return [
        {
            "label": "Mã chứng từ ghi tăng",
            "fieldname": "Mã chứng từ ghi tăng",
            "fieldtype": "Data",
        },
        {
            "label": "Thời gian ghi tăng",
            "fieldname": "Thời gian ghi tăng",
            "fieldtype": "Date",
        },
        {
            "label": "Tên, đặc điểm, ký hiệu TSCĐ",
            "fieldname": "Tên, đặc điểm, ký hiệu TSCĐ",
            "fieldtype": "Data",
        },
        {
            "label": "Nước sản xuất",
            "fieldname": "Nước sản xuất",
            "fieldtype": "Data",
        },
        {
            "label": "Tháng năm đưa vào sử dụng",
            "fieldname": "Tháng năm đưa vào sử dụng",
            "fieldtype": "Date",
        },
        {
            "label": "Số hiệu TSCĐ",
            "fieldname": "Số hiệu TSCĐ",
            "fieldtype": "Data",
        },
        {
            "label": "Nguyên giá TSCĐ",
            "fieldname": "Nguyên giá TSCĐ",
            "fieldtype": "Float",
        },
        {
            "label": "TYLE",
            "fieldname": "TYLE",
            "fieldtype": "Float",
        },
        {
            "label": "Mức khấu hao",
            "fieldname": "MUC_KHAU_HAO",
            "fieldtype": "Float",
        },
        {
            "label": "Khai hao đã tính",
            "fieldname": "KHAU_HAO_DA_TINH",
            "fieldtype": "Float",
        },
        {
            "label": "Số hiệu ghi giảm",
            "fieldname": "Số hiệu ghi giảm",
            "fieldtype": "Data",
        },
        {
            "label": "Ngày ghi giảm",
            "fieldname": "Ngày ghi giảm",
            "fieldtype": "Date",
        },
        {
            "label": "Ghi chú",
            "fieldname": "Ghi chú",
            "fieldtype": "Data",
        },
    ]


def get_data(filters):
    conditions = get_conditions(filters)
    data = frappe.db.sql(
        """
        SELECT PURCHASE.NAME AS 'Mã chứng từ ghi tăng',
       PURCHASE.POSTING_DATE AS 'Thời gian ghi tăng',
       AST.NAME AS 'Tên, đặc điểm, ký hiệu TSCĐ',
       AST.quốc_gia AS 'Nước sản xuất',
       AST.available_for_use_date AS 'Tháng năm đưa vào sử dụng',
       AST.NAME AS 'Số hiệu TSCĐ',
       AST.TOTAL_ASSET_COST AS 'Nguyên giá TSCĐ',
       DS.DEPRECIATION_AMOUNT/AST.TOTAL_ASSET_COST*100 TYLE,
       DS.DEPRECIATION_AMOUNT MUC_KHAU_HAO,
       DS.DEPRECIATION_AMOUNT KHAU_HAO_DA_TINH,
       SALES.NAME AS 'Số hiệu ghi giảm',
       SALES.posting_date AS 'Ngày ghi giảm',
       PURCHASE.DESCRIPTION AS 'Ghi chú'
FROM `tabAsset` AST
LEFT JOIN
  (SELECT PR.NAME,
          PR.REMARKS,
          PRI.QTY,
          PRI.AMOUNT,
          PR.POSTING_DATE,
          PRI.DESCRIPTION,
          PRI.UOM,
          PRI.ITEM_CODE
   FROM `tabPurchase Receipt` PR
   LEFT JOIN `tabPurchase Receipt Item` PRI ON PRI.PARENT = PR.NAME
   WHERE PR.COMPANY = %(company)s
     AND PRI.IS_FIXED_ASSET = 1
     AND PR.POSTING_DATE BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)) PURCHASE ON PURCHASE.NAME = AST.PURCHASE_RECEIPT
LEFT JOIN `tabAsset Depreciation Schedule` ADS ON AST.NAME = ADS.ASSET
LEFT JOIN
  (SELECT SUM(DEPRECIATION_AMOUNT) DEPRECIATION_AMOUNT,
          PARENT
   FROM `tabDepreciation Schedule`
   WHERE SCHEDULE_DATE BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
   GROUP BY PARENT) AS DS ON DS.PARENT = ADS.NAME
LEFT JOIN
  (SELECT SI.NAME,
          SI.REMARKS,
          SII.QTY,
          SII.AMOUNT,
          SII.ASSET,
          SI.POSTING_DATE
   FROM `tabSales Invoice` SI
   LEFT JOIN `tabSales Invoice Item` SII ON SII.PARENT = SI.NAME
   WHERE SI.COMPANY = %(company)s
     AND SI.POSTING_DATE BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)) SALES ON SALES.ASSET = AST.NAME
WHERE (PURCHASE.POSTING_DATE BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
       OR SALES.POSTING_DATE BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s))
  AND ADS.DOCSTATUS = 1
  AND ADS.finance_book = %(finance_book)s
  AND AST.STATUS IN ('Submitted', 'Partially Depreciated', 'Fully Depreciated', 'Sold','Scrapped')
UNION ALL
SELECT PURCHASE.NAME AS 'Mã chứng từ ghi tăng',
       PURCHASE.POSTING_DATE AS 'Thời gian ghi tăng',
       AST.NAME AS 'Tên, đặc điểm, ký hiệu TSCĐ',
       AST.quốc_gia AS 'Nước sản xuất',
       AST.available_for_use_date AS 'Tháng năm đưa vào sử dụng',
       AST.NAME AS 'Số hiệu TSCĐ',
       AST.TOTAL_ASSET_COST AS 'Nguyên giá TSCĐ',
       DS.DEPRECIATION_AMOUNT/AST.TOTAL_ASSET_COST*100 TYLE,
       DS.DEPRECIATION_AMOUNT MUC_KHAU_HAO,
       DS.DEPRECIATION_AMOUNT KHAU_HAO_DA_TINH,
       SALES.NAME AS 'Số hiệu ghi giảm',
       SALES.posting_date AS 'Ngày ghi giảm',
       PURCHASE.DESCRIPTION AS 'Ghi chú'
FROM `tabAsset` AST
LEFT JOIN
  (SELECT PI.NAME,
          PI.POSTING_DATE,
          PI.REMARKS,
          PII.QTY,
          PII.AMOUNT,
          PII.DESCRIPTION,
          PII.UOM,
          PII.ITEM_CODE
   FROM `tabPurchase Invoice` PI
   LEFT JOIN `tabPurchase Invoice Item` PII ON PII.PARENT = PI.NAME
   WHERE PI.COMPANY = %(company)s
     AND PII.IS_FIXED_ASSET = 1
     AND PI.UPDATE_STOCK = 1
     AND PI.POSTING_DATE BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)) PURCHASE ON PURCHASE.NAME = AST.PURCHASE_INVOICE
LEFT JOIN
  (SELECT SI.NAME,
          SI.REMARKS,
          SII.QTY,
          SII.ASSET,
          SII.AMOUNT,
          SI.POSTING_DATE
   FROM `tabSales Invoice` SI
   LEFT JOIN `tabSales Invoice Item` SII ON SII.PARENT = SI.NAME
   WHERE SII.IS_FIXED_ASSET = 1
     AND SI.COMPANY = %(company)s
     AND SI.POSTING_DATE BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)) SALES ON SALES.ASSET = AST.NAME
LEFT JOIN `tabAsset Depreciation Schedule` ADS ON AST.NAME = ADS.ASSET
LEFT JOIN
  (SELECT SUM(DEPRECIATION_AMOUNT) DEPRECIATION_AMOUNT,
          PARENT
   FROM `tabDepreciation Schedule`
   WHERE SCHEDULE_DATE BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
   GROUP BY PARENT) AS DS ON DS.PARENT = ADS.NAME
WHERE (PURCHASE.POSTING_DATE BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s)
       OR SALES.POSTING_DATE BETWEEN DATE(%(start_date)s) AND DATE(%(end_date)s))
  AND ADS.DOCSTATUS = 1
  AND ADS.finance_book = %(finance_book)s
  AND AST.STATUS IN ('Submitted', 'Partially Depreciated', 'Fully Depreciated', 'Sold','Scrapped')
        """,
        conditions,  # filters
        as_dict=True,
    )
    return data


def get_conditions(filters):
    conditions = {}
    for key, value in filters.items():
        if filters.get(key):
            conditions[key] = value
    return conditions


def validate_dates(filters):
    if filters.start_date > filters.end_date:
        frappe.throw(_("From Date must be before To Date"))
