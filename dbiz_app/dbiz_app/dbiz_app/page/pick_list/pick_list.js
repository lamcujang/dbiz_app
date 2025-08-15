frappe.pages['pick_list'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __("Pick List"),
        single_column: true,
    });

    $(wrapper).html('<div style="text-align:center;margin-top:40px;"><button class="btn btn-primary" id="create-ojc">New Pick List</button></div>');

    $(wrapper).find('#create-ojc').on('click', function() {
        frappe.route_options = {
			'purpose': 'Delivery',
		};

		frappe.new_doc('Pick List');
    });	

	$(wrapper).find('#create-ojc').trigger('click');
}