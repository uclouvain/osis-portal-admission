# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from unittest.mock import ANY, Mock, patch, MagicMock

from django.shortcuts import resolve_url
from django.test import TestCase, override_settings

from admission.contrib.enums import (
    TrainingType,
)
from admission.contrib.enums.admission_type import AdmissionType
from admission.contrib.enums.projet import ChoixStatutPropositionDoctorale
from base.tests.factories.person import PersonFactory
from base.tests.test_case import OsisPortalTestCase


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/')
class PDFRecapViewTestCase(OsisPortalTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()
        cls.proposition = MagicMock(
            uuid=str(uuid.uuid4()),
            type_admission=AdmissionType.ADMISSION.name,
            reference='22-300001',
            links={'update_accounting': {'url': 'ok'}},
            doctorat=Mock(
                sigle='CS1',
                annee=2020,
                intitule='Doctorate name',
                sigle_entite_gestion="CDSS",
                campus="Mons",
                type=TrainingType.PHD.name,
            ),
            matricule_candidat=cls.person.global_id,
            code_secteur_formation='CS',
            bourse_preuve=[],
            documents_projet=[],
            graphe_gantt=[],
            proposition_programme_doctoral=[],
            projet_formation_complementaire=[],
            lettres_recommandation=[],
            langue_redaction_these='FR',
            lieu_these='UCL',
            domaine_these='',
            doctorat_deja_realise='',
            fiche_archive_signatures_envoyees=[],
            statut=ChoixStatutPropositionDoctorale.EN_BROUILLON.name,
            erreurs=[],
            curriculum=[],
            pdf_recapitulatif=['saved-pdf-recap-token'],
        )

        cls.doctorate_detail_url = resolve_url('admission:doctorate:pdf-recap', pk=cls.proposition.uuid)
        cls.general_detail_url = resolve_url('admission:general-education:pdf-recap', pk=cls.proposition.uuid)
        cls.continuing_detail_url = resolve_url('admission:continuing-education:pdf-recap', pk=cls.proposition.uuid)

        cls.api_default_params = {
            'accept_language': ANY,
            'x_user_first_name': ANY,
            'x_user_last_name': ANY,
            'x_user_email': ANY,
            'x_user_global_id': ANY,
        }

    def setUp(self):
        # Mock proposition api
        propositions_api_patcher = patch("osis_admission_sdk.api.propositions_api.PropositionsApi")
        self.mock_api = propositions_api_patcher.start().return_value
        # Doctorate
        self.mock_api.retrieve_doctorate_proposition.return_value = self.proposition
        self.mock_api.retrieve_doctorate_education_proposition_pdf_recap.return_value = MagicMock(
            token='new-doctorate-token',
        )
        # General
        self.mock_api.retrieve_general_education_proposition.return_value = self.proposition
        self.mock_api.retrieve_general_education_proposition_pdf_recap.return_value = MagicMock(
            token='new-general-token'
        )
        # Continuing
        self.mock_api.retrieve_continuing_education_proposition.return_value = self.proposition
        self.mock_api.retrieve_continuing_education_proposition_pdf_recap.return_value = MagicMock(
            token='new-continuing-token'
        )
        self.addCleanup(propositions_api_patcher.stop)

        # Mock osis document api
        patcher = patch("admission.contrib.views.common.pdf_recap.get_remote_token", return_value="old-pdf-recap-token")
        self.mock_document_api = patcher.start()
        self.addCleanup(patcher.stop)

    def test_doctorate_pdf_recap_if_it_is_already_generated(self):
        self.client.force_login(self.person.user)
        response = self.client.get(self.doctorate_detail_url)
        self.assertRedirects(
            response,
            'http://dummyurl.com/document/file/old-pdf-recap-token',
            fetch_redirect_response=False,
        )

    def test_doctorate_pdf_recap_if_it_is_not_already_generated(self):
        self.client.force_login(self.person.user)
        self.mock_api.retrieve_doctorate_proposition.return_value.pdf_recapitulatif = []
        response = self.client.get(self.doctorate_detail_url)
        self.mock_api.retrieve_doctorate_education_proposition_pdf_recap.assert_called_once_with(
            uuid=self.proposition.uuid,
            **self.api_default_params,
        )
        self.assertRedirects(
            response,
            'http://dummyurl.com/document/file/new-doctorate-token',
            fetch_redirect_response=False,
        )

    def test_general_pdf_recap_if_it_is_not_already_generated(self):
        self.client.force_login(self.person.user)
        self.mock_api.retrieve_general_education_proposition.return_value.pdf_recapitulatif = []
        response = self.client.get(self.general_detail_url)
        self.mock_api.retrieve_general_education_proposition_pdf_recap.assert_called_once_with(
            uuid=self.proposition.uuid,
            **self.api_default_params,
        )
        self.assertRedirects(
            response,
            'http://dummyurl.com/document/file/new-general-token',
            fetch_redirect_response=False,
        )

    def test_continuing_pdf_recap_if_it_is_not_already_generated(self):
        self.client.force_login(self.person.user)
        self.mock_api.retrieve_continuing_education_proposition.return_value.pdf_recapitulatif = []
        response = self.client.get(self.continuing_detail_url)
        self.mock_api.retrieve_continuing_education_proposition_pdf_recap.assert_called_once_with(
            uuid=self.proposition.uuid,
            **self.api_default_params,
        )
        self.assertRedirects(
            response,
            'http://dummyurl.com/document/file/new-continuing-token',
            fetch_redirect_response=False,
        )
