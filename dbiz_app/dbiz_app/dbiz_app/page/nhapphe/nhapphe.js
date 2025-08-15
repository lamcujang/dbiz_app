frappe.pages['nhapphe'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __("Nhập phế"),
        single_column: true,
    });

    $(wrapper).html('<div style="text-align:center;margin-top:40px;"><button class="btn btn-primary" id="create-ojc">Nhập phế</button></div>');

    $(wrapper).find('#create-ojc').on('click', function() {
        frappe.route_options = {
			'transfer_type': "SCRAP_IMPORT",
		};

		frappe.new_doc('Scrap Items Job Card');
    });

	$(wrapper).find('#create-ojc').trigger('click');
}

