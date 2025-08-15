frappe.pages['material_transfer'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __("Stock Entry"),
        single_column: true,
    });

    $(wrapper).html('<div style="text-align:center;margin-top:40px;"><button class="btn btn-primary" id="create-ojc">Stock Entry</button></div>');

    $(wrapper).find('#create-ojc').on('click', function() {
        frappe.route_options = {
			'posting_date': frappe.datetime.get_today(),
			'posting_time': frappe.datetime.now_time(),
			'stock_entry_type': 'Material Transfer',
		};

		frappe.new_doc('Stock Entry');
    });

	$(wrapper).find('#create-ojc').trigger('click');
}