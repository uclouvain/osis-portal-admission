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
import uuid
from datetime import datetime
from unittest.mock import ANY, patch

import freezegun
from django.shortcuts import resolve_url
from django.test import TestCase, override_settings
from django.utils.translation import gettext_lazy as _

from admission.tests import get_paginated_years
from base.tests.factories.person import PersonFactory
from base.tests.test_case import OsisPortalTestCase


@freezegun.freeze_time('2022-01-01')
@override_settings(OSIS_DOCUMENT_BASE_URL="http://dummyurl.com/document/")
class ExamTestCase(OsisPortalTestCase):
    REQUIRED_TEXT = _("This field is required.")

    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()
        cls.proposition_uuid = uuid.uuid4()

        cls.detail_url = resolve_url("admission:general-education:exam", pk=cls.proposition_uuid)
        cls.form_url = resolve_url("admission:general-education:update:exam", pk=cls.proposition_uuid)

        cls.default_kwargs = {
            'accept_language': ANY,
            'x_user_first_name': ANY,
            'x_user_last_name': ANY,
            'x_user_email': ANY,
            'x_user_global_id': ANY,
        }

    def setUp(self):
        self.client.force_login(self.person.user)

        propositions_api_patcher = patch("osis_admission_sdk.api.propositions_api.PropositionsApi")
        self.mock_proposition_api = propositions_api_patcher.start()
        self.addCleanup(propositions_api_patcher.stop)

        person_api_patcher = patch("osis_admission_sdk.api.person_api.PersonApi")
        self.mock_person_api = person_api_patcher.start()
        person_api_ret = self.mock_person_api.return_value
        person_api_ret.retrieve_exam_general_education_admission.return_value.to_dict.return_value = {
            "required": True,
            "title_fr": "title_fr",
            "title_en": "title_en",
            "certificate": [],
            "year": None,
            "is_valuated": False,
        }
        self.addCleanup(person_api_patcher.stop)

        academic_year_api_patcher = patch("osis_reference_sdk.api.academic_years_api.AcademicYearsApi")
        self.mock_academic_year_api = academic_year_api_patcher.start()
        year = datetime.today().year
        self.mock_academic_year_api.return_value.get_academic_years.return_value = get_paginated_years(
            year - 2,
            year + 2,
        )
        self.addCleanup(academic_year_api_patcher.stop)

    def test_detail(self):
        response = self.client.get(self.detail_url)

        # Check response status
        self.assertEqual(response.status_code, 200)

        # Check api calls
        self.mock_person_api.return_value.retrieve_exam_general_education_admission.assert_called_with(
            uuid=str(self.proposition_uuid),
            **self.default_kwargs,
        )

    def test_form_get(self):
        response = self.client.get(self.form_url)

        # Check response status
        self.assertEqual(response.status_code, 200)

        # Check api calls
        self.mock_person_api.return_value.retrieve_exam_general_education_admission.assert_called_with(
            uuid=str(self.proposition_uuid),
            **self.default_kwargs,
        )

    def test_form_post(self):
        data = {'certificate': [], 'year': 2021}
        response = self.client.post(self.form_url, data=data)

        # Check response status
        self.assertEqual(response.status_code, 302)

        # Check api calls
        self.mock_person_api.return_value.retrieve_exam_general_education_admission.assert_called_with(
            uuid=str(self.proposition_uuid),
            **self.default_kwargs,
        )
        self.mock_person_api.return_value.update_exam_general_education_admission.assert_called_with(
            uuid=str(self.proposition_uuid),
            exam=data,
            **self.default_kwargs,
        )
