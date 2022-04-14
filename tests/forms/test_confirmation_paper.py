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

from admission.contrib.forms.confirmation_paper import ConfirmationPaperForm


class ConfirmationPaperFormTestCase(TestCase):
    def test_confirmation_paper_form_valid_data(self):
        form = ConfirmationPaperForm(data={'date': datetime.date(2022, 12, 31)})

        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.cleaned_data,
            {
                'date': datetime.date(2022, 12, 31),
                'rapport_recherche': [],
                'proces_verbal_ca': [],
                'avis_renouvellement_mandat_recherche': [],
            },
        )

    def test_confirmation_paper_form_without_required_data(self):
        form = ConfirmationPaperForm(data={})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors.get('date'), ['Ce champ est requis.'])
