# Copyright (c) 2025, lamnl and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters: dict | None = None):
    """Return columns and data for the report.

    This is the main entry point for the report. It accepts the filters as a
    dictionary and should return columns and data. It is called by the framework
    every time the report is refreshed or a filter is updated.
    """
    if not filters:
        filters = {}

    if filters.from_date > filters.to_date:
        frappe.throw(_("From Date must be before To Date"))

    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns() -> list[dict]:
    """Return columns for the report.

    One field definition per column, just like a DocType field definition.
    """
    return [
        {
            "label": "Đơn vị",
            "fieldname": "branch",
            "fieldtype": "Data",
        },
        {
            "label": "Nhóm khách hàng",
            "fieldname": "party_group",
            "fieldtype": "Data",
        },
        {
            "label": "Mã đối tượng",
            "fieldname": "party_code",
            "fieldtype": "Data",
        },
        {
            "label": "Tên đối tượng",
            "fieldname": "party_name",
            "fieldtype": "Data",
        },
        {
            "label": "Đơn vị tiền",
            "fieldname": "currency",
            "fieldtype": "Data",
        },
        {
            "label": "Tài khoản",
            "fieldname": "account",
            "fieldtype": "Data",
        },
        {
            "label": "Nợ đầu kỳ",
            "fieldname": "opening_debit",
            "fieldtype": "Float",
        },
        {
            "label": "Có đầu kỳ",
            "fieldname": "opening_credit",
            "fieldtype": "Float",
        },
        {
            "label": "Phát sinh nợ",
            "fieldname": "arising_debit",
            "fieldtype": "Float",
        },
        {
            "label": "Phát sinh có",
            "fieldname": "arising_credit",
            "fieldtype": "Float",
        },
        {
            "label": "Nợ cuối kỳ",
            "fieldname": "closing_debit",
            "fieldtype": "Float",
        },
        {
            "label": "Có cuối kỳ",
            "fieldname": "closing_credit",
            "fieldtype": "Float",
        },
    ]


def get_data(filters: dict | None = None) -> list[list]:
    """Return data for the report.

    The report data is a list of rows, with each row being a list of cell values.
    """

    # Account filter logic
    account_filter_condition = ""
    if filters.get("account"):
        # User chose specific account - filter by account and its children
        accounts = get_account_with_children(
            filters.get("account"), filters.get("company")
        )
        account_list = "'" + "', '".join(accounts) + "'"
        account_filter_condition = f"AND tge.account IN ({account_list})"
    else:
        # User did not choose account - filter by account prefixes
        account_filter_condition = """AND SUBSTR(tge.account, 1, 3) IN (
            '341', '338', '331', '335', '131', '141', '138'
        )"""

    group_query = f"""
        SELECT
            DISTINCT ts.supplier_group AS party_group
        FROM
            `tabGL Entry` tge
        LEFT JOIN tabSupplier ts ON
            ts.name = tge.party
        WHERE
            tge.is_cancelled = 0
            AND tge.party IS NOT NULL
            AND ts.supplier_group IS NOT NULL
            {account_filter_condition}
            AND tge.company = %(company)s
        UNION
        SELECT
            DISTINCT tc.customer_group AS party_group
        FROM
            `tabGL Entry` tge
        LEFT JOIN tabCustomer tc ON
            tc.name = tge.party
        WHERE
            tge.is_cancelled = 0
            AND tge.party IS NOT NULL
            AND tc.customer_group IS NOT NULL
            {account_filter_condition}
            AND tge.company = %(company)s
    """

    group_filters = {
        "company": filters.get("company"),
    }

    # Group 1, Group 2, etc.
    group_list = frappe.db.sql(query=group_query, values=group_filters, as_dict=1)

    result = []

    # Tổng: Đầu kỳ, Phát sinh, cuối kỳ (VND)
    total_dk_no = total_dk_co = 0
    total_ps_no = total_ps_co = 0
    total_ck_no = total_ck_co = 0

    # Tổng: Đầu kỳ, Phát sinh, cuối kỳ (USD)
    total_dk_no_usd = total_dk_co_usd = 0
    total_ps_no_usd = total_ps_co_usd = 0
    total_ck_no_usd = total_ck_co_usd = 0

    for group in group_list:
        party_group = group.get("party_group")

        currency_query = f"""
            SELECT
                DISTINCT tge.account_currency account_currency
            FROM
                `tabGL Entry` tge
            LEFT JOIN tabSupplier ts ON
                ts.name = tge.party
            LEFT JOIN tabCustomer tc ON
                tc.name = tge.party
            WHERE
                tge.is_cancelled = 0
                AND tge.party IS NOT NULL
                {account_filter_condition}
                AND tge.company = %(company)s
                AND (
                    ts.supplier_group = %(party_group)s
                        OR tc.customer_group = %(party_group)s
                )
        """

        currency_filters = {
            "company": filters.get("company"),
            "party_group": party_group,
        }

        # VND, USD, etc.
        currency_list = frappe.db.sql(
            query=currency_query, values=currency_filters, as_dict=1
        )

        for currency in currency_list:
            group_total_query = f"""
                WITH TMP AS (
                    SELECT
                        tge.posting_date,
                        ts.supplier_group AS party_group,
                        tge.party AS party_code,
                        CASE
                            WHEN tge.party_type = 'Supplier' THEN ts.supplier_name
                            WHEN tge.party_type = 'Customer' THEN tc.customer_name
                            ELSE ''
                        END AS party_name,
                        tge.account_currency AS currency,
                        ta.account_number AS account,
                        SUM(tge.debit_in_account_currency) AS debit,
                        SUM(tge.credit_in_account_currency) AS credit
                    FROM
                        `tabGL Entry` tge
                    LEFT JOIN tabSupplier ts ON
                        ts.name = tge.party
                    LEFT JOIN tabCustomer tc ON
                        tc.NAME = tge.party
                    LEFT JOIN tabAccount ta ON
                        ta.name = tge.account
                    WHERE
                        tge.is_cancelled = 0
                        AND tge.party IS NOT NULL
                        {account_filter_condition}
                        AND tge.company = %(company)s
                        AND tge.account_currency = %(currency)s
                        AND (
                            ts.supplier_group = %(party_group)s
                                OR tc.customer_group = %(party_group)s
                        )
                    GROUP BY
                        tge.posting_date,
                        tge.party,
                        tge.account
                )
                SELECT
                    COALESCE(SUM(O.debit), 0) AS opening_debit,
                    COALESCE(SUM(O.credit), 0) AS opening_credit,
                    COALESCE(SUM(A.debit), 0) AS arising_debit,
                    COALESCE(SUM(A.credit), 0) AS arising_credit,
                    COALESCE(SUM(C.debit), 0) AS closing_debit,
                    COALESCE(SUM(C.credit), 0) AS closing_credit
                FROM
                    (
                        SELECT
                            T.party_code,
                            T.currency,
                            T.account,
                            SUM(T.debit) AS debit,
                            SUM(T.credit) AS credit
                        FROM
                            TMP T
                        WHERE
                            T.posting_date BETWEEN DATE(%(from_date)s) AND DATE(%(to_date)s)
                        GROUP BY
                            T.party_code
                    ) A
                LEFT JOIN (
                        SELECT
                            T.party_code,
                            T.currency,
                            T.account,
                            CASE
                                WHEN SUM(T.debit - T.credit) > 0 THEN SUM(T.debit - T.credit)
                                ELSE 0
                            END AS debit,
                            CASE
                                WHEN SUM(T.credit - T.debit) > 0 THEN SUM(T.credit - T.debit)
                                ELSE 0
                            END AS credit
                        FROM
                            TMP T
                        WHERE
                            T.posting_date < DATE(%(from_date)s)
                        GROUP BY
                            T.party_code
                    ) O ON
                    O.party_code = A.party_code
                    AND O.currency = A.currency
                    AND O.account = A.account
                LEFT JOIN (
                        SELECT
                            T.party_code,
                            T.currency,
                            T.account,
                            CASE
                                WHEN SUM(T.debit - T.credit) > 0 THEN SUM(T.debit - T.credit)
                                ELSE 0
                            END AS debit,
                            CASE
                                WHEN SUM(T.credit - T.debit) > 0 THEN SUM(T.credit - T.debit)
                                ELSE 0
                            END AS credit
                        FROM
                            TMP T
                        WHERE
                            T.posting_date <= DATE(%(to_date)s)
                        GROUP BY
                            T.party_code
                    ) C ON
                    C.party_code = A.party_code
                    AND C.currency = A.currency
                    AND C.account = A.account
            """

            group_total_filters = {
                "company": filters.get("company"),
                "party_group": party_group,
                "from_date": filters.get("from_date"),
                "to_date": filters.get("to_date"),
                "currency": currency.get("account_currency"),
            }

            group_total = frappe.db.sql(
                query=group_total_query,
                values=group_total_filters,
                as_dict=1,
            )

            for row in group_total:
                if currency.get("account_currency") == "VND":
                    total_dk_no += row.get("opening_debit")
                    total_dk_co += row.get("opening_credit")
                    total_ps_no += row.get("arising_debit")
                    total_ps_co += row.get("arising_credit")
                    total_ck_no += row.get("closing_debit")
                    total_ck_co += row.get("closing_credit")
                elif currency.get("account_currency") == "USD":
                    total_dk_no_usd += row.get("opening_debit")
                    total_dk_co_usd += row.get("opening_credit")
                    total_ps_no_usd += row.get("arising_debit")
                    total_ps_co_usd += row.get("arising_credit")
                    total_ck_no_usd += row.get("closing_debit")
                    total_ck_co_usd += row.get("closing_credit")

            result.append(
                {
                    "branch": "",
                    "party_group": party_group,
                    "party_code": "",
                    "party_name": "",
                    "currency": currency.get("account_currency"),
                    "account": "",
                    "opening_debit": group_total[0].get("opening_debit"),
                    "opening_credit": group_total[0].get("opening_credit"),
                    "arising_debit": group_total[0].get("arising_debit"),
                    "arising_credit": group_total[0].get("arising_credit"),
                    "closing_debit": group_total[0].get("closing_debit"),
                    "closing_credit": group_total[0].get("closing_credit"),
                }
            )

            detail_query = f"""
                WITH TMP AS (
                    SELECT
                        tge.posting_date,
                        ts.supplier_group AS party_group,
                        tge.party AS party_code,
                        CASE
                            WHEN tge.party_type = 'Supplier' THEN ts.supplier_name
                            WHEN tge.party_type = 'Customer' THEN tc.customer_name
                            ELSE ''
                        END AS party_name,
                        tge.account_currency AS currency,
                        ta.account_number AS account,
                        SUM(tge.debit_in_account_currency) AS debit,
                        SUM(tge.credit_in_account_currency) AS credit
                    FROM
                        `tabGL Entry` tge
                    LEFT JOIN tabSupplier ts ON
                        ts.name = tge.party
                    LEFT JOIN tabCustomer tc ON
                        tc.NAME = tge.party
                    LEFT JOIN tabAccount ta ON
                        ta.name = tge.account
                    WHERE
                        tge.is_cancelled = 0
                        AND tge.party IS NOT NULL
                        {account_filter_condition}
                        AND tge.company = %(company)s
                        AND tge.account_currency = %(currency)s
                        AND (
                            ts.supplier_group = %(party_group)s
                                OR tc.customer_group = %(party_group)s
                        )
                    GROUP BY
                        tge.posting_date,
                        tge.party,
                        tge.account
                )
                SELECT
                    NULL AS branch,
                    NULL AS party_group,
                    A.party_code,
                    A.party_name,
                    A.currency,
                    A.account,
                    CASE
                        WHEN O.debit - O.credit > 0 THEN O.debit - O.credit
                        ELSE 0
                    END opening_debit,
                    CASE
                        WHEN O.credit - O.debit > 0 THEN O.credit - O.debit
                        ELSE 0
                    END opening_credit,
                    COALESCE(A.debit, 0) AS arising_debit,
                    COALESCE(A.credit, 0) AS arising_credit,
                    CASE
                        WHEN C.debit - C.credit > 0 THEN C.debit - C.credit
                        ELSE 0
                    END closing_debit,
                    CASE
                        WHEN C.credit - C.debit > 0 THEN C.credit - C.debit
                        ELSE 0
                    END closing_credit
                FROM
                    (
                        SELECT
                            T.party_code,
                            T.party_name,
                            T.currency,
                            T.account,
                            SUM(T.debit) AS debit,
                            SUM(T.credit) AS credit
                        FROM
                            TMP T
                        WHERE
                            T.posting_date BETWEEN DATE(%(from_date)s) AND DATE(%(to_date)s)
                        GROUP BY
                            T.party_code
                    ) A
                LEFT JOIN (
                        SELECT
                            T.party_code,
                            T.currency,
                            T.account,
                            SUM(T.debit) AS debit,
                            SUM(T.credit) AS credit
                        FROM
                            TMP T
                        WHERE
                            T.posting_date < DATE(%(from_date)s)
                        GROUP BY
                            T.party_code
                    ) O ON
                    O.party_code = A.party_code
                    AND O.currency = A.currency
                    AND O.account = A.account
                LEFT JOIN (
                        SELECT
                            T.party_code,
                            T.currency,
                            T.account,
                            SUM(T.debit) AS debit,
                            SUM(T.credit) AS credit
                        FROM
                            TMP T
                        WHERE
                            T.posting_date <= DATE(%(to_date)s)
                        GROUP BY
                            T.party_code
                    ) C ON
                    C.party_code = A.party_code
                    AND C.currency = A.currency
                    AND C.account = A.account
            """

            detail_filters = {
                "company": filters.get("company"),
                "from_date": filters.get("from_date"),
                "to_date": filters.get("to_date"),
                "currency": currency.get("account_currency"),
                "party_group": party_group,
            }

            detail_data = frappe.db.sql(
                query=detail_query, values=detail_filters, as_dict=1
            )

            for row in detail_data:
                result.append(
                    {
                        "branch": row.get("BRANCH") or "",
                        "party_group": row.get("party_group") or "",
                        "party_code": row.get("party_code") or "",
                        "party_name": row.get("party_name") or "",
                        "currency": row.get("currency") or "",
                        "account": row.get("account") or "",
                        "opening_debit": row.get("opening_debit") or 0,
                        "opening_credit": row.get("opening_credit") or 0,
                        "arising_debit": row.get("arising_debit") or 0,
                        "arising_credit": row.get("arising_credit") or 0,
                        "closing_debit": row.get("closing_debit") or 0,
                        "closing_credit": row.get("closing_credit") or 0,
                    }
                )

    result.append(
        {
            "branch": "",
            "party_group": "Tổng cộng",
            "party_code": "",
            "party_name": "Tổng cộng",
            "currency": "VND",
            "account": "",
            "opening_debit": total_dk_no,
            "opening_credit": total_dk_co,
            "arising_debit": total_ps_no,
            "arising_credit": total_ps_co,
            "closing_debit": total_ck_no,
            "closing_credit": total_ck_co,
        }
    )

    result.append(
        {
            "branch": "",
            "party_group": "Tổng cộng",
            "party_code": "",
            "party_name": "Tổng cộng",
            "currency": "USD",
            "account": "",
            "opening_debit": total_dk_no_usd,
            "opening_credit": total_dk_co_usd,
            "arising_debit": total_ps_no_usd,
            "arising_credit": total_ps_co_usd,
            "closing_debit": total_ck_no_usd,
            "closing_credit": total_ck_co_usd,
        }
    )

    return result


def get_account_with_children(account, company):
    accounts = []

    def fetch_children(parent_account):
        accounts.append(parent_account)
        children = frappe.get_all(
            "Account",
            filters={
                "parent_account": parent_account,
                "company": company,
                "is_group": 1,  # Only groups can have children
            },
            pluck="name",
        )
        for child in children:
            fetch_children(child)

        # Also include non-group children (leaf accounts)
        leaf_children = frappe.get_all(
            "Account",
            filters={
                "parent_account": parent_account,
                "company": company,
                "is_group": 0,
            },
            pluck="name",
        )
        accounts.extend(leaf_children)

    fetch_children(account)
    return accounts
