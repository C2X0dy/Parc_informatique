{
    'name': 'Gestion de Parc IT',
    'version': '1.0',
    'summary': 'Gérer les équipements et services informatiques',
    'description': """
        Ce module permet de gérer:
        - Les équipements et matériels informatiques
        - La gestion des clients
        - Les contrats
        - Le suivi des incidents
        - La maintenance
        - La facturation
    """,
    'category': 'Services/IT',
    'author': 'Divine',
    'website': '',
    'depends': ['base', 'mail', 'portal', 'web'],  # Ajout du module web pour le QR code
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/mail_template_data.xml',  # Ajout de cette ligne
        'views/client_views.xml',
        'views/contrat_views.xml',
        'views/facture_views.xml',
        'views/incident_views.xml',
        'views/parc_views.xml',
        'views/maintenance_views.xml',
        'views/affectation_views.xml',
        'views/dashboard_views.xml',
        'views/ticket_views.xml',
        'views/abonnement_views.xml',  # Ajout de cette ligne
        'report/contrat_report.xml',
        'report/facture_report.xml',
        'data/alert_cron.xml',
        'data/demo_data.xml',
    ],
    'demo': [
       'data/demo_data.xml',
     ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'assets': {
        'web.assets_backend': [
            'it_parc/static/src/css/it_parc.css',
        ],
    },
}


