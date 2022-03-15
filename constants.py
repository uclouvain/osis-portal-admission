# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
# ############################################################################

# Association between a read-only tab name (path name) and an action link key
READ_ACTIONS_BY_TAB = {
    'coordonnees': 'retrieve_coordinates',
    'cotutelle': 'retrieve_cotutelle',
    'curriculum': 'retrieve_curriculum',
    'education': 'retrieve_secondary_studies',
    'person': 'retrieve_person',
    'languages': 'retrieve_languages',
    'project': 'retrieve_proposition',
    'supervision': 'retrieve_supervision',
    'confirm': 'submit_proposition',
    'confirm-paper': '',
    'training': '',
    'jury': '',
    'private-defense': '',
    'public-defense': '',
    'messages': '',
}

# Association between a write-only tab name (path name) and an action link key
UPDATE_ACTIONS_BY_TAB = {
    'coordonnees': 'update_coordinates',
    'cotutelle': 'update_cotutelle',
    'curriculum': 'update_curriculum',
    'education': 'update_secondary_studies',
    'person': 'update_person',
    'languages': 'update_languages',
    'project': 'update_proposition',
    'supervision': 'request_signatures',
    'confirm': 'submit_proposition',
    'confirm-paper': '',
    'training': '',
    'jury': '',
    'private-defense': '',
    'public-defense': '',
    'messages': '',
}

UCL_CODE = 'UCL'

BE_ISO_CODE = 'BE'
