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
from unittest.mock import Mock, patch

from django.shortcuts import resolve_url
from django.test import TestCase, override_settings
from django.utils.translation import gettext_lazy as _
from rest_framework import status

from admission.contrib.enums.doctorat import ChoixStatutDoctorat
from admission.contrib.enums.training import StatutActivite
from admission.services.proposition import ActivityApiBusinessException
from base.tests.factories.person import PersonFactory
from frontoffice.settings.osis_sdk.utils import MultipleApiBusinessException


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class TrainingTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.phd_student = PersonFactory()

    def setUp(self):
        self.client.force_login(self.phd_student.user)
        self.url = resolve_url("admission:doctorate:training", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")

        api_patcher = patch("osis_admission_sdk.api.propositions_api.PropositionsApi")
        self.mock_api = api_patcher.start()

        self.mock_api.return_value.retrieve_doctorate_dto.return_value = Mock(
            links={'add_training': {'url': 'ok'}},
            reference='21-300001',
            intitule_formation='Informatique',
            statut=ChoixStatutDoctorat.ADMITTED.name,
            sigle_formation='INFO',
            annee_formation=2022,
            matricule_doctorant=self.phd_student.global_id,
            prenom_doctorant='John',
            nom_doctorantig='Doe',
            uuid='uuid1',
        )
        self.mock_api.return_value.list_doctoral_trainings.return_value = []
        self.mock_api.return_value.create_doctoral_training.return_value = dict(
            uuid='uuid-created',
        )
        self.mock_api.return_value.update_doctoral_training.return_value = dict(
            uuid='uuid-edited',
        )

        self.mock_api.return_value.retrieve_doctoral_training.return_value = Mock(
            category="CONFERENCE",
        )
        self.mock_api.return_value.retrieve_doctoral_training.return_value.to_dict.return_value = dict(
            category="CONFERENCE",
            type="",
            participating_proof=[],
            parent=None,
        )

        self.addCleanup(api_patcher.stop)

    def test_activity_list(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "Informatique")

    def test_create_wrong_category(self):
        url = resolve_url(
            "admission:doctorate:training:add",
            pk="3c5cdc60-2537-4a12-a396-64d2e9e34876",
            category="UNKNOWN",
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create(self):
        url = resolve_url(
            "admission:doctorate:training:add",
            pk="3c5cdc60-2537-4a12-a396-64d2e9e34876",
            category="CONFERENCE",
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
            "admission:doctorate:training:add",
            pk="3c5cdc60-2537-4a12-a396-64d2e9e34876",
            category="COMMUNICATION",
        )
        response = self.client.get(f"{url}?parent=uuid-parent")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update(self):
        url = resolve_url(
            "admission:doctorate:training:edit",
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
                category="CONFERENCE",
                title="parent",
            )

        self.mock_api.return_value.retrieve_doctoral_training.side_effect = side_effect

        url = resolve_url(
            "admission:doctorate:training:edit",
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
        self.mock_api.return_value.list_doctoral_trainings.return_value = [activity_mock]
        data = {
            'activity_ids': ['test'],
        }
        self.mock_api.return_value.submit_doctoral_training.return_value = data
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertRedirects(response, self.url)

    def test_submit_with_errors(self):
        activity_mock = Mock(uuid='test', ects=10)
        activity_mock.get = dict(uuid='test', ects=10).get
        self.mock_api.return_value.list_doctoral_trainings.return_value = [activity_mock]
        data = {
            'activity_ids': ['test'],
        }
        self.mock_api.return_value.submit_doctoral_training.side_effect = MultipleApiBusinessException(
            {ActivityApiBusinessException(status_code='FORMATION-1', detail="Pas bon", activite_id='test')}
        )
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFormError(response, "form", None, "Pas bon")
