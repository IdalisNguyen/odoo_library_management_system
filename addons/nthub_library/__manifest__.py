# -*- coding: utf-8 -*-
{
    'name': "Library Management System",
    'version': '17.0.0.1',
    'summary': """Library Management System""",
    'description': 
    """
    """,
    'category': 'Productivity',
    'author': "",
    'company': '',
    'live_test_url': '',
    'price': 0.0,
    'currency': 'D',
    'website': "",
    'depends': ['base', 'website', 'board', 'mail','contacts','purchase','stock','mail','portal','web','project'],

    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/report.xml',
        'views/report_warnning.xml',
        'views/Books_data.xml',
        'views/Author.xml',
        'views/Publisher.xml',
        'views/Borrows.xml',
        'views/Book_copies.xml',
        'views/Card_Details.xml',        
        'views/Book_Category.xml',
        'views/res_partner.xml',
        'views/configuration.xml',
        'views/dashboard.xml',
        'views/templates.xml',
        'data/scheduled.xml',
        'report/books_borrows_report.xml',
        'views/endogenous_document.xml',
        'views/menu.xml',
        'views/stock_quant.xml',
        
        'views/portal.xml',
        'report/button_book_copy_labels.xml',
        'report/library_labels_report.xml',
        'views/product_template.xml',
        'views/project_task.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'nthub_library/static/src/js/button_return.js',
            'nthub_library/static/src/js/button_check_reserve.js',
            'nthub_library/static/src/xml/button_return.xml',
            'nthub_library/static/src/xml/button_check_reserve.xml',
            'nthub_library/static/src/js/button_report.js',
            'nthub_library/static/src/xml/button_report.xml',
        ],
    },


    'demo': [
    ],
    'images': ['static/description/banner.gif'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
