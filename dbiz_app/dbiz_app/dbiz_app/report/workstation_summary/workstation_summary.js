// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Workstation Summary"] = {
	filters: [
		// {
		// 	label: __("Company"),
		// 	fieldname: "company",
		// 	fieldtype: "Link",
		// 	options: "Company",
		// 	default: frappe.defaults.get_user_default("Company"),
		// 	reqd: 1,
		// },
		{
			label: __("From Date"),
			fieldname: "from_date",
			fieldtype: "Date",
			default: frappe.datetime.add_days(frappe.datetime.get_today(), -7),
			reqd: 1,
		},
		{
			label: __("To Date"),
			fieldname: "to_date",
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			label: __("Work Order"),
			fieldname: "work_order",
			fieldtype: "Link",
			options: "Work Order",
			default: "",
			get_query: function() {
				return {
					filters: {
						'planned_start_date': ['between', [frappe.query_report.get_filter_value('from_date'), frappe.query_report.get_filter_value('to_date')]]
					}
				};
			}
		},
		{
			label: __("Job Card"),
			fieldname: "job_card",
			fieldtype: "Link",
			options: "Job Card",
			default: "",
			order_by: "posting_date",
			get_query: function() {
				let work_order = frappe.query_report.get_filter_value('work_order');
				if(work_order) {
					return {
						filters: {
							'work_order': work_order
						}
					};
				}else{
					return {
						filters: {
							'posting_date': ['between', [frappe.query_report.get_filter_value('from_date'), frappe.query_report.get_filter_value('to_date')]]
						}
					};
				}
			}
		},
		{
			label: __("Operation"),
			fieldname: "operation",
			fieldtype: "Link",
			options: "Operation",
			default: "",
			get_query: function() {
				let work_order = frappe.query_report.get_filter_value('work_order');
				
				if(work_order) {
					let arr = [];
					frappe.call({
						method: 'frappe.client.get',
						args: {
							doctype: 'Work Order',
							name: work_order
						},
						async: false,
						callback: function(response) {
							if (response.message && response.message.operations) {
								arr = response.message.operations.map(op => op.operation);
							}
						}
					});

					return {
						filters: {
							'name': ['in', arr]
						}
					};
				} else {
					return {
						filters: {
							'name': ['in', ['CONGDOANTRON','CONGDOANTHOI','CONGDOANCAT']]
						}
					};
				}
			}
		},
		{
			label: __("Production Item"),
			fieldname: "production_item",
			fieldtype: "Link",
			options: "Item",
			default: "",
			get_query: function() {
				let work_order = frappe.query_report.get_filter_value('work_order');
				let job_card = frappe.query_report.get_filter_value('job_card');
				
				if(work_order) {
					let item = null;
					frappe.call({
						method: 'frappe.client.get',
						args: {
							doctype: 'Work Order',
							name: work_order
						},
						async: false,
						callback: function(response) {
							if (response.message && response.message.production_item) {
								item = response.message.production_item
							}
						}
					});

					return {
						filters: {
							'name': item
						}
					};
				}else if(job_card) {
					let item = null;
					frappe.call({
						method: 'frappe.client.get',
						args: {
							doctype: 'Job Card',
							name: job_card
						},
						async: false,
						callback: function(response) {
							if (response.message && response.message.production_item) {
								item = response.message.production_item
							}
						}
					});

					return {
						filters: {
							'name': item
						}
					};
				} else {
					return {
						filters: {
							'item_group': 'THANHPHAM'
						}
					};
				}
			}
		},
		{
			label: __("Workstation"),
			fieldname: "workstation",
			fieldtype: "Link",
			options: "Workstation",
			default: "",
			get_query: function() {
				let work_order = frappe.query_report.get_filter_value('work_order');
				let job_card = frappe.query_report.get_filter_value('job_card');
				
				if(work_order) {
					let arr = [];
					frappe.call({
						method: 'frappe.client.get_list',
						args: {
							doctype: 'Job Card',
							filters: {
								work_order: work_order,
								workstation: ['!=', ''] 
							},
							fields: ['workstation']
						},
						async: false,
						callback: function(response) {
							if (response.message && response.message.length > 0) {
								arr = response.message.map(jc => jc.workstation);
							}
						}
					});

					return {
						filters: {
							'name': ['in', arr]
						}
					};
				}else if(job_card) {
					let item = null;
					frappe.call({
						method: 'frappe.client.get',
						args: {
							doctype: 'Job Card',
							name: job_card
						},
						async: false,
						callback: function(response) {
							if (response.message && response.message.workstation) {
								item = response.message.workstation
							}
						}
					});

					return {
						filters: {
							'name': item
						}
					};
				} else {
					return {
						filters: {
							'workstation_type': ['in', ['TRON','THOIIN','CAT']]
						}
					};
				}
			}
		},
	],
};
