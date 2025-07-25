# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################

# Association between a read-only tab name (path name) and an action link key
from django.utils.translation import gettext_lazy as _

READ_ACTIONS_BY_TAB = {
    # Personal data
    'coordonnees': 'retrieve_coordinates',
    'cotutelle': 'retrieve_cotutelle',
    'person': 'retrieve_person',
    # Previous experience
    'curriculum': 'retrieve_curriculum',
    'education': 'retrieve_secondary_studies',
    'exam': 'retrieve_exam',
    'languages': 'retrieve_languages',
    # Project
    'training-choice': 'retrieve_training_choice',
    'project': 'retrieve_project',
    'supervision': 'retrieve_supervision',
    # Accounting
    'accounting': 'retrieve_accounting',
    # Confirmation
    'confirm-submit': 'submit_proposition',
    # Confirmation paper
    'confirmation-paper': 'retrieve_confirmation',
    'extension-request': 'update_confirmation_extension',
    # Additional information
    'specific-questions': 'retrieve_specific_question',
    # Documents
    'documents': 'retrieve_documents',
    # Others
    'doctoral-training': 'retrieve_doctoral_training',
    'complementary-training': 'retrieve_complementary_training',
    'course-enrollment': 'retrieve_course_enrollment',
    'jury-preparation': 'retrieve_jury_preparation',
    'jury': 'list_jury_members',
    'private-defense': '',
    'public-defense': '',
    'messages': '',
}

# Association between a write-only tab name (path name) and an action link key
UPDATE_ACTIONS_BY_TAB = {
    # Personal data
    'coordonnees': 'update_coordinates',
    'cotutelle': 'update_cotutelle',
    'person': ('update_person', 'update_person_last_enrolment'),
    # Previous experience
    'curriculum': 'update_curriculum',
    'education': 'update_secondary_studies',
    'exam': 'update_exam',
    'languages': 'update_languages',
    # Project
    'training-choice': 'update_training_choice',
    'project': 'update_project',
    'supervision': 'request_signatures',
    # Accounting
    'accounting': 'update_accounting',
    # Confirmation
    'confirm-submit': 'submit_proposition',
    # Confirmation paper
    'confirmation-paper': 'update_confirmation',
    'extension-request': 'update_confirmation_extension',
    # Additional information
    'specific-questions': 'update_specific_question',
    # Documents
    'documents': 'update_documents',
    # Others
    'jury-preparation': 'update_jury_preparation',
    'jury': '',
    'private-defense': '',
    'public-defense': '',
    'doctoral-training': '',
    'complementary-training': '',
    'course-enrollment': '',
    'messages': '',
}

UCL_CODE = 'UCL'

BE_ISO_CODE = 'BE'

FIELD_REQUIRED_MESSAGE = _("This field is required.")

FIRST_YEAR_WITH_ECTS_BE = 2004

LINGUISTIC_REGIMES_WITHOUT_TRANSLATION = ['FR', 'NL', 'DE', 'EN', 'IT', 'ES', 'PT']

MINIMUM_YEAR = 1900

MINIMUM_BIRTH_YEAR = 1920

PLUS_5_ISO_CODES = [
    'CH',  # Switzerland
    'IS',  # Island
    'NO',  # Norway
    'LI',  # Liechtenstein
    'MC',  # Monaco
]

PROPOSITION_JUST_SUBMITTED = 'proposition_just_submitted'
MED_DENT_TRAINING_DOMAIN_PREFIXES = ['11', '13']
MED_DENT_TRAINING_DOMAIN_REGEX = f"^({'|'.join(MED_DENT_TRAINING_DOMAIN_PREFIXES)})"
