{
    'name': 'IT Parc',
    'version': '1.0',
    'category': 'Services',
    'summary': 'Gestion de parc informatique',
    'description': """
        Module de gestion de parc informatique pour société de services IT.
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['base', 'mail', 'web', 'portal'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/abonnement_views.xml',
        'views/affectation_views.xml',
        'views/client_views.xml',
        'views/contrat_views.xml',
        'views/facture_views.xml',
        'views/incident_views.xml',
        'views/parc_views.xml',
        'views/maintenance_views.xml',
        'views/ticket_views.xml',
        'views/dashboard_views.xml',
        'views/portals_templates.xml',
        'report/contrat_report.xml',
        'report/facture_report.xml',
        'data/alert_cron.xml',
        'data/ir_sequence_data.xml',
        'data/mail_template_data.xml',
        'data/demo_data.xml',
    ],
    'qweb': [],
    'assets': {
        'web.assets_frontend': [
            'it_parc/static/src/css/it_parc_portal.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}



