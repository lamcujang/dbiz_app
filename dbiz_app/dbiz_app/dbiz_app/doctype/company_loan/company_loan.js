// Copyright (c) 2024, lamnl and contributors
// For license information, please see license.txt
async function get_data_from_doctype(doctype, Id) {
    return await frappe.db.get_doc(doctype, Id).then(doc => {
        return doc;
    }).catch(err => {
        console.error(err);
        return null;
    });
}
frappe.ui.form.on('Company Loan', {
	refresh(frm) {
	    let currentDate = frappe.datetime.now_date();
        let oneMonthFromNow = frappe.datetime.add_months(currentDate, 1);
	    if (!frm.doc.rp_start) {
            frm.set_value('rp_start', oneMonthFromNow);
        }
	    if(!frm.doc.is_finish && frm.doc.current_balance === 0 && frm.doc.paid_amt !== 0){
	        frm.doc.is_finish = 1;
	        frm.refresh_field('is_finish');
	    }
	    fetchCompanyIntoLoanSchedule(frm,frm.doc.company);
	    
        
        
        //set Query
        setupQueries(frm,'contract',{
			company: frm.doc.company,
		});
        setupQueries(frm,'advance_account',{
            company: frm.doc.company,
            is_group: 0,
            root_type: 'Asset'
        });
        setupQueries(frm,'credit_account_for_advance',{
            company: frm.doc.company,
            account_type: ["in", ["Bank", "Cash"]],
            is_group: 0,
        });
        setupQueriesLoanAccount(frm, frm.doc.loan_type);
        
        //Tạo các button thao tác
        setupButtons(frm);
        
        applyButtonStyles(frm,'calc');
        
	},
	loan_type: function(frm){
	    frm.doc.party = '';
	    frm.refresh_field('party');
	    fetchLoanAccount(frm);
	    
	    
	    setupQueriesLoanAccount(frm, frm.doc.loan_type);
	    
	    setPartyType(frm,frm.doc.loan_type);
	},
	party_type:function(frm){
	    frm.doc.party ='';
	    frm.refresh_field('party');
	},
	contract: async function(frm){
	    if (frm.doc.contract) {
            const contract = await get_data_from_doctype("Loan Contract", frm.doc.contract);
            frm.set_value('party', contract.party);
            frm.set_value("short_loan_account", contract.short_loan_account);
            frm.set_value("long_loan_account", contract.long_loan_account);
            frm.set_value("currency", contract.currency);
        } else {
            frm.set_value('party', null);
        }
        frm.refresh_field('party');
	},
	calc(frm) {
        if (validateFields(frm)) return;
        make_schedule_table(frm);
    },
    rp_method(frm){
        if(frm.doc.rp_method === 'Trả cả gốc và lãi khi đáo hạn' || !frm.doc.rp_method){
            frm.doc.advance_check=0;
            frm.refresh_field('advance_check');
        }
        frm.toggle_display('advance_check',frm.doc.rp_method !== 'Manual');
        if(frm.doc.rp_method === 'Manual'){
            frm.doc.advance_check=0;
            frm.refresh_field('advance_check');
        }
        frm.clear_table('rp_scd');
        frm.refresh_field('rp_scd');
    },
    company: function(frm) {
		setupQueries(frm,'contract',{
            company: frm.doc.company,
        });

	    fetchLoanAccount(frm);
	    
        fetchCompanyIntoLoanSchedule(frm,frm.doc.company);
    }
});



frappe.ui.form.on('Company Loan Repayment Schedule', {
	refresh(frm) {
		
	},
	payment_button: function(frm,cdt,cdn){
        var row = locals[cdt][cdn];
        if (validateLoanStatus(frm)) return;
        if(row.pmt_amt===0){
            frappe.msgprint(__('Không có số tiền cần thanh toán!'));
            return;
        }else if(row.paid_amt >= row.pmt_amt){
            frappe.msgprint(__('Đã thanh toán hết!'));
            return; 
        }else if(row.pe_name){
            frappe.msgprint(__('Chứng từ thanh toán đã tồn tại: '+ row.pe_name));
            return; 
        }
	    frappe.call({
            method: "interest_payment_entry",
            args: {
                name: row.name,
                paid_to_account: frm.doc.short_loan_account,
                default_currency: frm.doc.currency,
                method: frm.doc.rp_method,
                loan_type: frm.doc.loan_type,
            },
            callback: function(result) {
                if (result.name) {
                    frappe.set_route("Form", "Payment Entry", result.name);
                }
            }
        });
	}
});

async function fetchLoanAccount(frm) {
	frm.doc.short_loan_account = '';
	frm.doc.long_loan_account = '';
    if (frm.doc.loan_type && frm.doc.company) {
        const loan_account = await frappe.db.get_value("Closing Period Accounting",  frm.doc.company,  ['long_loan_acc','short_loan_acc'])
        if(loan_account){
            frm.set_value('short_loan_account', loan_account.message.short_loan_acc);
            frm.set_value('long_loan_account', loan_account.message.long_loan_acc);
        }
    }
	frm.refresh_field('short_loan_account');
    frm.refresh_field('long_loan_account');
}

function fetchCompanyIntoLoanSchedule(frm,company){
	(frm.doc.rp_scd || []).forEach(row => {
		if(!row.company){
			row.company = company;
		}
	});
	frm.refresh_field('rp_scd');
}

function applyButtonStyles(frm, fieldName) {
    frm.toggle_display(fieldName, !frm.doc.docstatus ? 1 : 0); 
    const button = frm.fields_dict[fieldName].$wrapper.find('button');
    button.css({
        backgroundColor: 'white',
        color: 'black',
        border: '0.6px solid #ddd',
        borderRadius: '5px',
        padding: '8px 15px',
        cursor: 'pointer',
        transition: 'background-color 0.3s ease'
    });

    button.hover(
        () => button.css('background-color', '#e0e0eb'),
        () => button.css('background-color', 'white')
    );
}



function setupQueries(frm,field,filter) {
    frm.set_query(field, () => ({ filters: filter }));
    frm.refresh_field(field);
}

function setupQueriesLoanAccount(frm, loanType) {
	setupQueries(frm,'short_loan_account',{
		'is_group': 0, 
		'company': frm.doc.company,
		'account_type': loanType === 'Borrow' ? 'Payable' : 'Receivable'
	});
	setupQueries(frm,'long_loan_account',{
		'is_group': 0, 
		'company': frm.doc.company,
		'account_type': loanType === 'Borrow' ? 'Payable' : 'Receivable'
	});
}

function setPartyType(frm,loanType){
    if (loanType === 'Borrow'){
        frm.set_df_property('party_type', 'options', [
            'Supplier'
        ]);
        frm.doc.party_type = 'Supplier';
    }else if (loanType === 'Lend'){
        frm.set_df_property('party_type', 'options', [
            'Customer',
            'Employee'
        ]);
        frm.doc.party_type = 'Employee';
    }
    frm.refresh_field('party_type');
}

function setupButtons(frm) {
    if (frm.doc.docstatus) {
        addCustomButton(frm, __('Tạo chứng từ Giải ngân'), () => handleDisbursement(frm),'');
        addCustomButton(frm, __('Kết thúc hợp đồng'), () => handleContractEnd(frm),"Thao tác");
        addCustomButton(frm, __('Tất toán hợp đồng'), () => handleContractSettlement(frm),"Thao tác");
        // if (frm.doc.paid_amt !== 0) {
        //     addCustomButton(frm, __('Tạo bút toán Lãi vay'), () => createInterestJournalEntries(frm),"Thao tác");
        // }
    }
}

function addCustomButton(frm, label, action, wrapper) {
    frm.add_custom_button(label, action, wrapper);
}

function handleDisbursement(frm) {
    if (validateLoanStatus(frm,'disbursement')) return;

    const dialog= frappe.prompt(
        [
            {
                fieldname: 'cash_account',
                label: frm.doc.loan_type === 'Borrow' ? 'Tài khoản nhận tiền vay' : 'Tài khoản gửi tiền vay',
                fieldtype: 'Link',
                options: 'Account',
                reqd: 1,
                get_query: () => ({
                    filters: { 
						account_type: ['in', ['Bank', 'Cash']], 
						company: frm.doc.company, 
						is_group: 0 
					}
                }),
				onchange: function(field) {
					const cash_account = this.get_value();
					if (cash_account) {
						frappe.call({
							method: "frappe.client.get",
							args: {
								doctype: "Account",
								name: cash_account,
							},
							callback: function(result) {
								if (result.message) {
									const acc_currency = result.message.account_currency;
									dialog.set_value('acc_currency', acc_currency);
								}
							}
						});
					}
				}
            },
            {
                fieldname: 'acc_currency',
                label: 'Loại tiền tài khoản',
                fieldtype: 'Link',
                options: 'Currency',
                reqd: 1,
                read_only: 1 
            }
        ],
        (values) => createDisbursementEntry(frm, values, frm.doc.loan_type, frm.doc.currency),
        __('Chọn Tài Khoản'),
        __('Tạo')
    );
}


function validateLoanStatus(frm, type = '') {
    const messages = {
        is_cancelled: 'Hợp đồng đã kết thúc!',
        is_settled: 'Hợp đồng đã tất toán!',
        is_finish: 'Đã trả hết nợ cho khoản vay!',
    };
	
    for (const [key, message] of Object.entries(messages)) {
        if (frm.doc[key] === 1) {
            frappe.msgprint(__(message));
            return true;
        }
    }
	
	if (type==='disbursement'){
		if(frm.doc.not_paid_amt <= 0){
			frappe.msgprint(__('Đã giải ngân hết!'));
			return true; 
		}
	};
    return false;
}


function createDisbursementEntry(frm, values, loanType, docCurrency) {
    let currentDate = frappe.datetime.now_date();
	if(loanType === 'Lend') {
		frappe.call({
			method: "frappe.client.insert",
			args: {
				doc: {
					doctype: "Payment Entry",
					payment_type: "Pay",
					party_type: frm.doc.party_type,
					party: frm.doc.party,
					paid_from: values.cash_account,
					paid_amount: frm.doc.not_paid_amt,
					received_amount: frm.doc.not_paid_amt,
					reference_no: frm.doc.name,
					reference_date: currentDate,
					paid_to_account_currency: frm.doc.currency,
					paid_to: frm.doc.long_loan_account,
					target_exchange_rate: 1,
					company_loan: frm.doc.name,
					company: frm.doc.company,
					remarks: 'Giải ngân ' + frm.doc.total_payable + ' cho khoản vay ' + frm.doc.name,
				}
			},
			callback: function(result) {
				if (result.message) {
					frappe.set_route("Form", "Payment Entry", result.message.name);
				}
			}
		})
	}else if (loanType === 'Borrow' && docCurrency === values.acc_currency) {
		frappe.call({
			method: "frappe.client.insert",
			args: {
				doc: {
					doctype: "Payment Entry",
					payment_type: "Receive",
					party_type: frm.doc.party_type,
					party: frm.doc.party,
					paid_from: frm.doc.long_loan_account,
					paid_amount: frm.doc.not_paid_amt,
					received_amount: frm.doc.not_paid_amt,
					reference_no: frm.doc.name,
					reference_date: currentDate,
					paid_to_account_currency: frm.doc.currency,
					paid_to: values.cash_account,
					source_exchange_rate: 1,
					company_loan: frm.doc.name,
					company: frm.doc.company,
					remarks: 'Giải ngân ' + frm.doc.total_payable + ' cho khế ước vay ' + frm.doc.name,
				}
			},
			callback: function(result) {
				if (result.message) {
					frappe.set_route("Form", "Payment Entry", result.message.name);
				}
			}
		});
	} else if (loanType === 'Borrow' && docCurrency !== values.acc_currency){
		frappe.call({
			method: "frappe.client.get_list",
			args: {
				doctype: "Currency Exchange",
				filters: {
					from_currency: frm.doc.currency,
					to_currency: values.acc_currency,
				},
				fields: ["exchange_rate"],
				order_by: "creation desc", 
				limit_page_length: 1 
			},
			callback: function(rate_result) {
				if (rate_result.message && rate_result.message.length > 0) {
					const exchange_rate = rate_result.message[0].exchange_rate;
					
					const received_amount_converted = frm.doc.not_paid_amt * exchange_rate;

					frappe.call({
						method: "frappe.client.insert",
						args: {
							doc: {
								doctype: "Payment Entry",
								payment_type: "Receive",
								party_type: frm.doc.party_type,
								party: frm.doc.party,
								paid_from: frm.doc.long_loan_account,
								paid_amount: frm.doc.not_paid_amt,
								received_amount: received_amount_converted,
								reference_no: frm.doc.name,
								reference_date: frm.doc.submit_date,
								paid_from_account_currency: frm.doc.currency,
								paid_to: values.cash_account,
								company_loan: frm.doc.name,
								company: frm.doc.company,
								remarks: 'Giải ngân ' + frm.doc.total_payable + ' cho khế ước vay ' + frm.doc.name,
							}
						},
						callback: function(result) {
							if (result.message) {
								frappe.set_route("Form", "Payment Entry", result.message.name);
							}
						}
					});
				} else {
					frappe.msgprint(__('No exchange rate found for the selected currency.'));
				}
			}
		});
	}
}

function handleContractEnd(frm) {
    if (validateLoanStatus(frm)) return;

    frappe.confirm(
        __('Nếu tiếp tục, tất cả bút toán được tạo ghi nhận lãi chưa xảy ra sẽ được thêm bút toán đảo. Bạn có chắc chắn muốn tiếp tục?'),
        () => {
            frappe.call({
                method: 'cancel_loan_int',
                args: { 
					name: frm.doc.name 
				},
                callback: (response) => {
                    if (response) frappe.msgprint(__('Kết thúc khoản vay thành công!'));
                }
            });
        }
    );
}


function handleContractSettlement(frm) {
    if (validateLoanStatus(frm)) return;

    const dialog = frappe.prompt(
        [
            {
                fieldname: 'pay_acc',
                label: frm.doc.loan_type === 'Borrow' ? 'Tài khoản trả tiền' : 'Tài khoản nhận tiền',
                fieldtype: 'Link',
                options: 'Account',
                reqd: 1,
                get_query: function() {
					return {
						filters: {
							account_type: ["in", ["Bank", "Cash"]],
							company: frm.doc.company,
							is_group: 0,
						}
					};
				},
				onchange: function(field) {
					const debit_account = this.get_value();
					if (debit_account) {
						frappe.call({
							method: "frappe.client.get",
							args: {
								doctype: "Account",
								name: debit_account,
							},
							callback: function(result) {
								if (result.message) {
									const pay_currency = result.message.account_currency;
									dialog.set_value('pay_currency', pay_currency);
								}
							}
						});
					}
				}
			},
			{
				fieldname: 'pay_currency',
				label: 'Loại tiền tài khoản',
				fieldtype: 'Link',
				options: 'Currency',
				reqd: 1,
				read_only: 1 
			},
			{
				fieldname: 'settle_amt',
				label: 'Số tiền tất toán',
				fieldtype: 'Currency',
				reqd: 1,
				default: frm.doc.current_balance,
			}
        ],
        (values) => processSettlement(frm, values),
        __('Chọn Tài Khoản'),
        __('Tạo')
    );
}

function processSettlement(frm, values){
	frappe.call({
        method: "loan_settle_payment",
        args: {
			name: frm.doc.name,
			pay_acc: values.pay_acc,
			settle_amt: values.settle_amt,
			pay_currency: values.pay_currency,
			currency: frm.doc.currency,
        },
        callback: function(result) {
			console.log(result);
			if (result) {
				frappe.set_route("Form", "Payment Entry", result.name);
			}
        }
    });
}

function createInterestJournalEntries(frm) {
	if (validateLoanStatus(frm)) return;
	
    frappe.call({
        method: 'make_loan_int_gl',
        args: {
			name: frm.doc.name 
		},
        callback: (response) => {
            if (response) frappe.msgprint(__('Tạo thành công các bút toán lãi vay!'));
        }
    });
}

function validateFields(frm) {
    const requiredFields = [
        { field: 'long_loan_account', message: 'Vui lòng nhập tài khoản vay!' },
        { field: 'short_loan_account', message: 'Vui lòng nhập tài khoản vay!' },
        { field: 'company', message: 'Vui lòng nhập công ty!' },
        { field: 'total_loan', message: 'Vui lòng điền Tổng tiền vay!'},
        { field: 'rp_start', message: 'Vui lòng điền Ngày bắt đầu trả nợ!'},
        { field: 'rp_period', message: 'Vui lòng điền Số kỳ trả nợ!'},
        { field: 'interest', message: 'Vui lòng điền Lãi suất!'},
        { field: 'rp_method', message: 'Vui lòng điền Phương thức tính!'}
    ];

    for (const { field, message } of requiredFields) {
        if (!frm.doc[field]) {
            frappe.throw(__(message));
            return true;
        }
    }
    return false;
}


function make_schedule_table(frm) {
	frappe.call({
		method: 'make_schedule_table',
		args: {
			total_loan: frm.doc.total_loan +  (frm.doc.added_interest ||0),
			rp_start: frm.doc.rp_start,
			rp_period: frm.doc.rp_period,
			interest: frm.doc.interest,
			date_method: frm.doc.date_method,
			rp_method: frm.doc.rp_method,
		},
		callback: function(r) {
			if (r.message) {
				frm.clear_table('rp_scd');
				r.message.forEach(result => {
					let row = frm.add_child('rp_scd');
					row.date = result.date;
					row.pmt_amt= result.pmt_amt;
					row.prin_amt= result.prin_amt;
					row.int_amt= result.int_amt;
					row.balance_amt= result.balance;
					row.mat_int_amt = result.mat_int_amt;

				});
				frm.refresh_field('rp_scd');

			}else if (r.message === 0){
				frappe.msgprint(__('Lỗi API'));
			}
		}
	});
}
