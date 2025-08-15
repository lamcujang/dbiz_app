frappe.pages['chuyenhanggiacong'].on_page_load = function(wrapper) {
	
	var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __("Chuyển hàng gia công"),
        single_column: true,
    });

    $(wrapper).html('<div style="text-align:center;margin-top:40px;"><button class="btn btn-primary" id="create-ojc">Chuyển hàng gia công</button></div>');

    $(wrapper).find('#create-ojc').on('click', function() {
        frappe.route_options = {
			'transfer_type': "CHUYENHANGGIACONG",
			'transfer_time': frappe.datetime.now_datetime()
		};

		frappe.new_doc('Stock Transfer Job Card');
    });

	$(wrapper).find('#create-ojc').trigger('click');
}