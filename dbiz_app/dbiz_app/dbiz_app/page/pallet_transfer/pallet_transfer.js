frappe.pages['pallet_transfer'].on_page_load = function(wrapper) {
	
	var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __("Pallet Transfer"),
        single_column: true,
    });

    $(wrapper).html('<div style="text-align:center;margin-top:40px;"><button class="btn btn-primary" id="create-ojc">New Pallet Transfer</button></div>');

    $(wrapper).find('#create-ojc').on('click', function() {
        frappe.route_options = {
			'date_transfer': frappe.datetime.get_today(),
		};

		frappe.new_doc('Pallet Transfer');
    });

	$(wrapper).find('#create-ojc').trigger('click');

}