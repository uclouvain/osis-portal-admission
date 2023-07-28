# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from unittest.mock import Mock, patch

from django.shortcuts import resolve_url
from django.test import TestCase, override_settings
from django.utils.translation import gettext_lazy as _
from rest_framework import status

from admission.contrib.enums import ChoixStatutPropositionDoctorale
from admission.tests.utils import MockLanguage
from base.tests.factories.person import PersonFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/')
class LanguagesTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()
        cls.detail_url = resolve_url('admission:doctorate:languages', pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        cls.form_url = resolve_url('admission:doctorate:update:languages', pk='3c5cdc60-2537-4a12-a396-64d2e9e34876')
        cls.create_url = resolve_url('admission:create:languages')

    def setUp(self):
        self.data_ok = {
            "form-0-language": 'FR',
            "form-0-listening_comprehension": "1",
            "form-0-speaking_ability": "1",
            "form-0-writing_ability": "3",
            "form-1-language": 'EN',
            "form-1-listening_comprehension": "5",
            "form-1-speaking_ability": "6",
            "form-1-writing_ability": "1",
            "form-INITIAL_FORMS": 0,
            "form-TOTAL_FORMS": 2,
        }
        self.client.force_login(self.person.user)

        propositions_api_patcher = patch("osis_admission_sdk.api.propositions_api.PropositionsApi")
        self.mock_proposition_api = propositions_api_patcher.start()
        self.addCleanup(propositions_api_patcher.stop)

        person_api_patcher = patch("osis_admission_sdk.api.person_api.PersonApi")
        self.mock_person_api = person_api_patcher.start()
        mock_languages = [
            Mock(
                **{
                    "language": 'FR',
                    "listening_comprehension": "A1",
                    "speaking_ability": "A1",
                    "writing_ability": "B1",
                    "certificate": [],
                }
            ),
            Mock(
                **{
                    "language": 'EN',
                    "listening_comprehension": "C1",
                    "speaking_ability": "C2",
                    "writing_ability": "A1",
                    "certificate": [],
                }
            ),
        ]
        mock_languages_dict_0 = {
            "language": 'FR',
            "listening_comprehension": "A1",
            "speaking_ability": "A1",
            "writing_ability": "B1",
            "certificate": [],
        }
        mock_languages_dict_1 = {
            "language": 'EN',
            "listening_comprehension": "C1",
            "speaking_ability": "C2",
            "writing_ability": "A1",
            "certificate": [],
        }
        mock_list = self.mock_person_api.return_value.list_language_knowledges
        mock_list.return_value = mock_languages
        mock_list.return_value[0].to_dict.return_value = mock_languages_dict_0
        mock_list.return_value[1].to_dict.return_value = mock_languages_dict_1

        mock_list_admission = self.mock_person_api.return_value.list_language_knowledges_admission
        mock_list_admission.return_value = mock_languages
        mock_list_admission.return_value[0].to_dict.return_value = mock_languages_dict_0
        mock_list_admission.return_value[1].to_dict.return_value = mock_languages_dict_1

        self.addCleanup(person_api_patcher.stop)

        languages_api_patcher = patch("osis_reference_sdk.api.languages_api.LanguagesApi")
        self.mock_languages_api = languages_api_patcher.start()

        def get_languages(**kwargs):
            languages = [
                MockLanguage(code='FR', name='Français', name_en='French'),
                MockLanguage(code='EN', name='Anglais', name_en='English'),
            ]
            if kwargs.get('code'):
                return Mock(results=[c for c in languages if c.code == kwargs.get('code')])
            return Mock(results=languages)

        self.mock_languages_api.return_value.languages_list.side_effect = get_languages
        self.addCleanup(languages_api_patcher.stop)

        academic_year_api_patcher = patch("osis_reference_sdk.api.academic_years_api.AcademicYearsApi")
        self.mock_academic_year_api = academic_year_api_patcher.start()
        self.addCleanup(academic_year_api_patcher.stop)

    def test_form_empty(self):
        self.mock_proposition_api.return_value.retrieve_proposition.return_value = Mock(
            statut=ChoixStatutPropositionDoctorale.EN_BROUILLON.name,
            erreurs=[],
            links={},
        )
        response = self.client.get(self.form_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, '<form class="osis-form"')
        self.assertContains(response, _("Save and continue"))
        self.mock_person_api.return_value.list_language_knowledges_admission.assert_called()
        self.mock_proposition_api.assert_called()

        response = self.client.post(self.form_url, {"form-INITIAL_FORMS": 0, "form-TOTAL_FORMS": 0})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.mock_person_api.return_value.create_language_knowledge_admission.assert_not_called()
        self.assertFormsetError(response, "formset", None, None, _("Mandatory languages are missing."))

    def test_create(self):
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "osis-document.umd.min.js", count=1)
        self.mock_person_api.return_value.list_language_knowledges.assert_not_called()
        self.mock_proposition_api.assert_not_called()
        self.assertContains(
            response,
            _("You must choose your training before filling in your previous experience."),
        )

    def test_form_language_duplicate(self):
        response = self.client.post(
            self.form_url,
            {
                **self.data_ok,
                "form-2-language": 'EN',
                "form-2-listening_comprehension": "4",
                "form-2-speaking_ability": "5",
                "form-2-writing_ability": "1",
                "form-TOTAL_FORMS": 3,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.mock_person_api.return_value.create_language_knowledge_admission.assert_not_called()
        self.assertFormsetError(
            response,
            "formset",
            None,
            None,
            _("You cannot enter a language more than once, please correct the form."),
        )

    def test_form_language_required(self):
        self.mock_person_api.return_value.list_language_knowledges.return_value = []
        response = self.client.post(
            self.form_url,
            {
                "form-0-language": 'FR',
                "form-0-listening_comprehension": "1",
                "form-1-language": 'EN',
                "form-1-speaking_ability": "6",
                "form-1-writing_ability": "1",
                "form-INITIAL_FORMS": 0,
                "form-TOTAL_FORMS": 2,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.mock_person_api.return_value.create_language_knowledge_admission.assert_not_called()
        self.assertFormsetError(response, "formset", 0, 'speaking_ability', _("This field is required."))

    def test_form_ok(self):
        response = self.client.post(self.form_url, self.data_ok)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.mock_person_api.return_value.create_language_knowledge_admission.assert_called()
        sent = self.mock_person_api.return_value.create_language_knowledge_admission.call_args[1]["language_knowledge"]
        self.assertEqual(
            sent,
            [
                {
                    "language": 'FR',
                    "listening_comprehension": "A1",
                    "speaking_ability": "A1",
                    "writing_ability": "B1",
                    "certificate": [],
                },
                {
                    "language": 'EN',
                    "listening_comprehension": "C1",
                    "speaking_ability": "C2",
                    "writing_ability": "A1",
                    "certificate": [],
                },
            ],
        )

    def test_form_ok_redirects_on_continue(self):
        self.mock_proposition_api.return_value.retrieve_proposition.return_value = Mock(
            matricule_candidat=self.person.global_id,
            statut=ChoixStatutPropositionDoctorale.EN_BROUILLON.name,
            links={'update_accounting': {'url': 'ok'}},
        )
        response = self.client.post(self.form_url, {**self.data_ok, '_submit_and_continue': ''})
        self.mock_person_api.return_value.create_language_knowledge_admission.assert_called()
        redirect_url = resolve_url('admission:doctorate:update:accounting', pk='3c5cdc60-2537-4a12-a396-64d2e9e34876')
        self.assertRedirects(response, redirect_url)

    def test_update_admission_in_context(self):
        url = resolve_url('admission:doctorate:update:languages', pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.mock_person_api.return_value.list_language_knowledges_admission.assert_called()
        self.mock_proposition_api.assert_called()
        self.assertIn('admission', response.context)

    def test_detail_without_knowledge(self):
        self.mock_person_api.return_value.list_language_knowledges.return_value = []

        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_detail(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "osis-document.umd.min.js", count=1)
        self.assertContains(response, "Français")
        self.mock_person_api.return_value.list_language_knowledges_admission.assert_called()
        self.assertIn('admission', response.context)
