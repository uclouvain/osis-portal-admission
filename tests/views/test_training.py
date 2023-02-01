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
import datetime
from unittest.mock import Mock, patch

from django.shortcuts import resolve_url
from django.test import TestCase, override_settings
from django.utils.translation import gettext_lazy as _
from rest_framework import status

from admission.contrib.enums import CategorieActivite, ContexteFormation
from admission.contrib.enums.doctorat import ChoixStatutDoctorat
from admission.contrib.enums.training import StatutActivite
from admission.contrib.forms.training import INSTITUTION_UCL
from base.tests.factories.person import PersonFactory
from osis_admission_sdk import ApiException
from osis_admission_sdk.model.seminar_communication import SeminarCommunication


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class TrainingTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.phd_student = PersonFactory()

    def setUp(self):
        self.client.force_login(self.phd_student.user)
        self.url = resolve_url("admission:doctorate:doctoral-training", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")

        api_patcher = patch("osis_admission_sdk.api.propositions_api.PropositionsApi")
        self.mock_api = api_patcher.start()

        self.mock_api.return_value.retrieve_doctorate_dto.return_value = Mock(
            links={'add_training': {'url': 'ok'}},
            reference='21-300001',
            doctorat=None,
            intitule_formation='Informatique',
            statut=ChoixStatutDoctorat.ADMITTED.name,
            sigle_formation='INFO',
            annee_formation=2022,
            matricule_doctorant=self.phd_student.global_id,
            prenom_doctorant='John',
            nom_doctorantig='Doe',
            uuid='uuid1',
            erreurs=[],
        )
        self.mock_api.return_value.list_doctoral_training.return_value = []
        self.mock_api.return_value.create_doctoral_training.return_value = dict(
            uuid='uuid-created',
        )
        self.mock_api.return_value.update_training.return_value = dict(
            uuid='uuid-edited',
        )

        self.mock_api.return_value.retrieve_training.return_value = Mock(
            category=CategorieActivite.CONFERENCE.name,
        )
        self.mock_api.return_value.retrieve_training.return_value.to_dict.return_value = dict(
            category=CategorieActivite.CONFERENCE.name,
            type="",
            participating_proof=[],
            parent=None,
        )

        self.addCleanup(api_patcher.stop)

    def test_doctoral_training_list(self):
        # This is mostly for testing {% training_categories %}
        self.mock_api.return_value.list_doctoral_training.return_value = [
            Mock(
                spec=SeminarCommunication,
                category="COMMUNICATION",
                status=StatutActivite.NON_SOUMISE.name,
                uuid="ac5cdc60-2537-4a12-a396-64d2e9e34876",
            ),
            Mock(
                category="COMMUNICATION",
                status=StatutActivite.NON_SOUMISE.name,
                uuid="4c5cdc60-2537-4a12-a396-64d2e9e34876",
                ects=0,
            ),
            Mock(
                category="COMMUNICATION",
                status=StatutActivite.SOUMISE.name,
                uuid="5c5cdc60-2537-4a12-a396-64d2e9e34876",
                object_type="Communication",
                ects=5,
            ),
            Mock(
                category="CONFERENCE",
                status=StatutActivite.ACCEPTEE.name,
                uuid="6c5cdc60-2537-4a12-a396-64d2e9e34876",
                ects=5,
            ),
            Mock(
                category="PUBLICATION",
                status=StatutActivite.SOUMISE.name,
                uuid="7c5cdc60-2537-4a12-a396-64d2e9e34876",
                object_type="Publication",
                ects=5,
            ),
            Mock(
                category="VAE",
                status=StatutActivite.SOUMISE.name,
                uuid="8c5cdc60-2537-4a12-a396-64d2e9e34876",
                object_type="Valorisation",
                ects=2,
            ),
            Mock(
                category="UCL_COURSE",
                status=StatutActivite.SOUMISE.name,
                uuid="9c5cdc60-2537-4a12-a396-64d2e9e34876",
                object_type="UclCourse",
                ects=5,
            ),
            Mock(
                category="PAPER",
                status=StatutActivite.SOUMISE.name,
                uuid="bc5cdc60-2537-4a12-a396-64d2e9e34876",
                object_type="Paper",
                type="CONFIRMATION_PAPER",
                ects=5,
            ),
            Mock(
                category="SERVICE",
                status=StatutActivite.SOUMISE.name,
                uuid="cc5cdc60-2537-4a12-a396-64d2e9e34876",
                object_type="Paper",
                type="CONFIRMATION_PAPER",
                ects=5,
            ),
            Mock(
                category="PAPER",
                status=StatutActivite.SOUMISE.name,
                uuid="dc5cdc60-2537-4a12-a396-64d2e9e34876",
                object_type="Paper",
                ects=5,
            ),
            Mock(
                category="RESIDENCY",
                status=StatutActivite.SOUMISE.name,
                uuid="dc5cdc60-2537-4a12-a396-64d2e9e34876",
                object_type="Residency",
                ects=8,
            ),
        ]
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "Informatique")
        self.assertContains(response, "45")

    def test_complementary_training_list(self):
        url = resolve_url("admission:doctorate:complementary-training", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "Informatique")

    def test_course_enrollment_list(self):
        url = resolve_url("admission:doctorate:course-enrollment", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "Informatique")

    def test_create_wrong_category(self):
        url = resolve_url(
            "admission:doctorate:doctoral-training:add",
            pk="3c5cdc60-2537-4a12-a396-64d2e9e34876",
            category="UNKNOWN",
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create(self):
        url = resolve_url(
            "admission:doctorate:doctoral-training:add",
            pk="3c5cdc60-2537-4a12-a396-64d2e9e34876",
            category=CategorieActivite.CONFERENCE.name,
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, _("Add a conference"))

        data = {
            'ects': 10,
            'type': 'A great conference',
            'title': '',
            'participating_proof': [],
            'comment': '',
            'participating_days': 0.0,
            'city': '',
            'organizing_institution': '',
            'website': '',
            'is_online': False,
        }
        response = self.client.post(url, data, follow=True)
        self.assertRedirects(response, f'{self.url}#uuid-created')

    def test_create_with_parent(self):
        url = resolve_url(
            "admission:doctorate:doctoral-training:add",
            pk="3c5cdc60-2537-4a12-a396-64d2e9e34876",
            category=CategorieActivite.COMMUNICATION.name,
        )
        response = self.client.get(f"{url}?parent=uuid-parent")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update(self):
        url = resolve_url(
            "admission:doctorate:doctoral-training:edit",
            pk="3c5cdc60-2537-4a12-a396-64d2e9e34876",
            activity_id="64d2e9e3-2537-4a12-a396-48763c5cdc60",
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, _("Edit"))

        data = {
            'type': 'A great conference',
            'title': '',
            'participating_proof': [],
            'comment': '',
            'participating_days': 0.0,
            'city': '',
            'organizing_institution': '',
            'website': '',
            'is_online': False,
        }
        response = self.client.post(url, data, follow=True)
        self.assertRedirects(response, f'{self.url}#uuid-edited')

    def test_update_child(self):
        def side_effect(*args, **kwargs):
            if kwargs['activity_id'] == "64d2e9e3-2537-4a12-a396-48763c5cdc60":
                return Mock(
                    to_dict=Mock(
                        return_value=dict(
                            category="COMMUNICATION",
                            title="child",
                            parent="uuid-parent",
                            type="",
                            participating_proof=[],
                            status=StatutActivite.NON_SOUMISE.name,
                        )
                    )
                )
            return Mock(
                category=CategorieActivite.CONFERENCE.name,
                title="parent",
            )

        self.mock_api.return_value.retrieve_training.side_effect = side_effect

        url = resolve_url(
            "admission:doctorate:doctoral-training:edit",
            pk="3c5cdc60-2537-4a12-a396-64d2e9e34876",
            activity_id="64d2e9e3-2537-4a12-a396-48763c5cdc60",
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, _("Edit the communication of this conference"))

        data = {
            'ects': 0,
            'type': 'A great conference',
            'title': '',
            'participating_proof': [],
            'comment': '',
            'participating_days': 0.0,
            'city': '',
            'organizing_institution': '',
            'website': '',
        }
        response = self.client.post(url, data, follow=True)
        self.assertRedirects(response, f'{self.url}#uuid-edited')

    def test_submit(self):
        activity_mock = Mock(uuid='test', ects=10)
        activity_mock.get = dict(uuid='test', ects=10).get
        self.mock_api.return_value.list_doctoral_training.return_value = [activity_mock]
        data = {
            'activity_ids': ['test'],
        }
        self.mock_api.return_value.submit_training.return_value = data
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertRedirects(response, self.url)

    def test_submit_with_errors(self):
        activity_mock = Mock(uuid='test', ects=10)
        activity_mock.get = dict(uuid='test', ects=10).get
        self.mock_api.return_value.list_doctoral_training.return_value = [activity_mock]
        data = {
            'activity_ids': ['test'],
        }
        # Exception related to an activity
        self.mock_api.return_value.submit_training.side_effect = ApiException(
            http_resp=Mock(
                status=status.HTTP_400_BAD_REQUEST,
                data='{"errors":[{"activite_id": "test", "detail": "Pas bon", "status_code": 0}]}',
            ),
        )
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFormError(response, "activities_form", None, "Pas bon")

        # Any other exception
        self.mock_api.return_value.submit_training.side_effect = ApiException(
            http_resp=Mock(
                status=status.HTTP_502_BAD_GATEWAY,
            ),
        )
        with self.assertRaises(ApiException):
            self.client.post(self.url, data)

    @patch("osis_reference_sdk.api.academic_years_api.AcademicYearsApi")
    def test_create_course_dates(self, acad_api):
        acad_api.return_value.get_academic_years.return_value = Mock(
            results=[
                Mock(
                    start_date=datetime.date(2021, 9, 2),
                    end_date=datetime.date(2022, 9, 1),
                    year=2021,
                )
            ]
        )

        url = resolve_url(
            "admission:doctorate:doctoral-training:add",
            pk="3c5cdc60-2537-4a12-a396-64d2e9e34876",
            category=CategorieActivite.COURSE.name,
        )
        data = {
            'type': 'A Course',
            'organizing_institution': INSTITUTION_UCL,
            'academic_year': '2021',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        call_data = self.mock_api.return_value.create_doctoral_training.call_args[1]['doctoral_training_activity']
        self.assertNotIn('academic_year', call_data)
        self.assertEqual(call_data['start_date'].year, 2021)
        self.assertEqual(call_data['end_date'].year, 2022)

    @patch("osis_reference_sdk.api.academic_years_api.AcademicYearsApi")
    @patch('osis_learning_unit_sdk.api.learning_units_api.LearningUnitsApi')
    def test_update_course_enrollment(self, learning_unit_api, acad_api):
        learning_unit_api.return_value.learningunitstitle_read.return_value = {'title': "dumb text"}
        current_year = datetime.date.today().year
        acad_api.return_value.get_academic_years.return_value = Mock(
            results=[
                Mock(
                    start_date=datetime.date(current_year, 9, 2),
                    end_date=datetime.date(current_year + 1, 9, 1),
                    year=current_year,
                )
            ]
        )
        url = resolve_url(
            "admission:doctorate:course-enrollment:edit",
            pk="3c5cdc60-2537-4a12-a396-64d2e9e34876",
            activity_id="64d2e9e3-2537-4a12-a396-48763c5cdc60",
        )
        self.mock_api.return_value.retrieve_training.return_value = Mock(
            category=CategorieActivite.UCL_COURSE.name,
        )
        self.mock_api.return_value.retrieve_training.return_value.to_dict.return_value = dict(
            category=CategorieActivite.UCL_COURSE.name,
            learning_unit_year='ESA2004',
            learning_unit_title='Something',
            academic_year=current_year,
            academic_year_title="2022-2023",
        )
        response = self.client.post(
            url,
            data={
                'context': ContexteFormation.FREE_COURSE.name,
                'academic_year': current_year,
                'learning_unit_year': 'ESA2004',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    def test_assent(self):
        url = resolve_url(
            "admission:doctorate:course-enrollment:assent",
            pk="3c5cdc60-2537-4a12-a396-64d2e9e34876",
            activity_id="64d2e9e3-2537-4a12-a396-48763c5cdc60",
        )
        activity_data = dict(
            object_type="Communication",
            title="Foo bar",
            category=CategorieActivite.COMMUNICATION.name,
            reference_promoter_assent=None,
            reference_promoter_comment="",
            status=[StatutActivite.SOUMISE.name],
        )
        self.mock_api.return_value.retrieve_training.return_value = Mock(**activity_data)
        self.mock_api.return_value.retrieve_training.return_value.to_dict.return_value = activity_data
        response = self.client.get(url)
        self.assertContains(response, "Foo bar")
        data = {
            'approbation': True,
            'commentaire': "Ok",
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    def test_delete(self):
        url = resolve_url(
            "admission:doctorate:course-enrollment:delete",
            pk="3c5cdc60-2537-4a12-a396-64d2e9e34876",
            activity_id="64d2e9e3-2537-4a12-a396-48763c5cdc60",
        )
        self.mock_api.return_value.retrieve_training.return_value = Mock(
            category=CategorieActivite.UCL_COURSE.name,
        )
        self.mock_api.return_value.retrieve_training.return_value.to_dict.return_value = dict(
            category=CategorieActivite.UCL_COURSE.name,
            reference_promoter_assent=None,
            reference_promoter_comment="",
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
