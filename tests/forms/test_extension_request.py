# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################
import datetime

from django.test import TestCase
from django.utils.translation import gettext as _

from admission.contrib.forms.extension_request import ExtensionRequestForm


class ExtensionRequestFormTestCase(TestCase):
    def test_extension_request_form_valid_data(self):
        form = ExtensionRequestForm(data={
            'nouvelle_echeance': datetime.date(2022, 12, 31),
            'justification_succincte': 'My reason',
            'lettre_justification': [],
        })

        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.cleaned_data,
            {
                'nouvelle_echeance': datetime.date(2022, 12, 31),
                'justification_succincte': 'My reason',
                'lettre_justification': [],
            },
        )

    def test_extension_request_form_without_required_data(self):
        form = ExtensionRequestForm(data={})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors.get('nouvelle_echeance'), [_('This field is required.')])
        self.assertEqual(form.errors.get('justification_succincte'), [_('This field is required.')])
