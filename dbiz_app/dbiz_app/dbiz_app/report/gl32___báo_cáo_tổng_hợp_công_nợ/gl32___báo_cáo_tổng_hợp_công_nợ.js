frappe.query_reports["GL32 - Báo cáo tổng hợp công nợ"] = {
  filters: [
    {
      fieldname: "from_date",
      label: __("From Date"),
      fieldtype: "Date",
      default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
      reqd: 1,
    },
    {
      fieldname: "to_date",
      label: __("To Date"),
      fieldtype: "Date",
      default: frappe.datetime.get_today(),
      reqd: 1,
    },
    {
      fieldname: "company",
      label: __("Company"),
      fieldtype: "Link",
      options: "Company",
      default: frappe.defaults.get_user_default("Company"),
      reqd: 1,
      on_change: function () {
        const company = frappe.query_report.get_filter_value("company");

        // Get Company Name and Tax ID
        frappe.db.get_value("Company", company, ["company_name", "tax_id"], (r) => {
          frappe.query_report.set_filter_value("company_name", r.company_name);
          frappe.query_report.set_filter_value("tax_id", r.tax_id);
        });

        // Get Address Linked to the Company
        frappe.call({
          method: "dbiz_app.api.get_company_address",
          args: {
            company: company,
          },
          callback: function (r) {
            if (r.message) {
              frappe.query_report.set_filter_value("company_address", r.message);
            }
          },
        });
      },
    },
    {
      fieldname: "company_name",
      fieldtype: "Data",
      hidden: 1,
    },
    {
      fieldname: "tax_id",
      fieldtype: "Data",
      hidden: 1,
    },
    {
      fieldname: "company_address",
      fieldtype: "Data",
      hidden: 1,
    },
    {
      fieldname: "account",
      label: "Tài khoản",
      fieldtype: "Link",
      options: "Account",
      get_query: () => ({
        filters: {
          company: frappe.query_report.get_filter_value("company"),
        },
      }),
    },
  ],

  // Trigger on_change manually after the report loads
  onload: function (query_report) {
    const company = frappe.query_report.get_filter_value("company");

    if (company) {
      query_report.get_filter("company").on_change(query_report);
    }

    window.format_number_js = (
      value,
      decimals = 0,
      number_format = frappe.boot.sysdefaults.number_format || "#.###,##"
    ) => {
      const decimal_places = decimals === "default" ? frappe.boot.sysdefaults.float_precision : decimals;
      return !isNaN(value) ? format_number(parseFloat(value), number_format, decimal_places) : "";
    };
  },
};
