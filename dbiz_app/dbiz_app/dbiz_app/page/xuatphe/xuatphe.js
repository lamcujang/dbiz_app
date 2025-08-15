frappe.pages['xuatphe'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __("XUATPHE"),
        single_column: true,
    });

    $(wrapper).html('<div style="text-align:center;margin-top:40px;"><button class="btn btn-primary" id="create-ojc">Tạo mới xuất phế</button></div>');

    $(wrapper).find('#create-ojc').on('click', function() {
        frappe.route_options = {
            'transfer_type': "SCRAP_EXPORT",
        };
        frappe.new_doc('Scrap Items Job Card');
    });
    $(wrapper).find('#create-ojc').trigger('click');
}

