# -*- encoding: utf-8 -*-

{
    'name': 'GST EwayBill',
    'version': '11.0.0.1',
    'category': 'Integration',
    'description': """
        module to allow Eway Bill integration with Taxpro
        Documentation
        https://help.taxprogsp.co.in/ewb/authentication_url___method_get_.htm?ms=AgI%3D&st=MA%3D%3D&sct=MA%3D%3D&mw=MjQw&ms=AgI%3D&st=MA%3D%3D&sct=MA%3D%3D&mw=MjQw
    """,
    'author': 'Geo Technosoft',
    'sequence': 1,
    'website': 'https://www.geotechnosoft.com',
    'depends': ['base', 'mail', 'sale_management'],
    'data': [
        'security/user_groups.xml',
        'security/ir.model.access.csv',
        'wizard/vehicle_view.xml',
        'wizard/consolidate_view.xml',
        'wizard/cancel_bill_view.xml',
        'views/transporter_view.xml',
        # 'views/unit_quantity_code_view.xml',
        # 'views/uom_mapping_view.xml',
        'views/port_code_view.xml',
        'views/company_view.xml',
        'views/sale_order_view.xml',
        'views/eway_configuration_view.xml',
        'views/res_partner_view.xml',
    ],
    'application': True,
    'installable': True,
}
