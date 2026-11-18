{
    'name': 'Portal Attendance Andean Craft',
    'version': '1.0',
    'summary': 'Control de asistencia en el portal mobile-first',
    'category': 'Human Resources/Attendances',
    'depends': ['portal', 'website', 'hr_attendance'],
    'data': [
        'views/portal_templates.xml',
        'views/attendance_report.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'portal_attendance/static/src/scss/attendance_portal.scss',
            'portal_attendance/static/src/js/attendance_portal.js',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}