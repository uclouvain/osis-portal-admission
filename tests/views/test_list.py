# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
from unittest.mock import Mock, patch, MagicMock

import freezegun
from django.shortcuts import resolve_url
from django.urls import reverse
from django.utils.translation import gettext

from admission.contrib.enums import (
    ChoixStatutPropositionContinue,
    ChoixStatutPropositionDoctorale,
    ChoixStatutPropositionGenerale,
    TrainingType,
    EligibiliteReinscription,
)
from base.tests.factories.person import PersonFactory
from base.tests.test_case import OsisPortalTestCase


class ListTestCase(OsisPortalTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.list_url = reverse('admission:list')
        cls.create_url = resolve_url('admission:create')

    def setUp(self):
        super().setUp()

        # Mock person api
        api_person_patcher = patch("osis_admission_sdk.api.person_api.PersonApi")
        self.mock_person_api = api_person_patcher.start()
        self.addCleanup(api_person_patcher.stop)

    @patch('osis_admission_sdk.api.propositions_api.PropositionsApi')
    def test_list_empty(self, api, *args):
        self.client.force_login(PersonFactory().user)

        api.return_value.list_propositions.return_value = Mock(
            doctorate_propositions=[],
            continuing_education_propositions=[],
            general_education_propositions=[],
            links={
                'create_training_choice': {'url': 'access granted'},
            },
        )

        api.return_value.propositions_ucl_enrolments_list.return_value = []
        api.return_value.propositions_re_enrolment_period_retrieve.return_value.date_debut = datetime.date(2023, 6, 15)
        api.return_value.propositions_re_enrolment_period_retrieve.return_value.date_fin = datetime.date(2023, 10, 31)
        api.return_value.propositions_candidate_re_enrolment_eligibity_retrieve.return_value = MagicMock(
            decision=EligibiliteReinscription.NON_ELIGIBLE_EN_ATTENTE_RESULTATS.name,
            raison_non_eligibilite='My error',
        )

        response = self.client.get(self.list_url)

        self.assertTrue(response.context['can_create_proposition'])

        self.assertContains(response, self.create_url)

        self.assertEqual(response.context['draft_propositions'], [])
        self.assertEqual(response.context['draft_or_in_payment_propositions'], {})
        self.assertEqual(response.context['submitted_propositions'], {})
        self.assertEqual(response.context['ucl_enrolments_list'], [])
        self.assertEqual(response.context['can_create_re_enrolment_proposition'], False)
        self.assertEqual(response.context['re_enrolment_error_message'], '')

    @patch('osis_admission_sdk.api.propositions_api.PropositionsApi')
    def test_list(self, api, *args):
        self.client.force_login(PersonFactory().user)

        api.return_value.list_propositions.return_value = Mock(
            doctorate_propositions=[
                Mock(
                    uuid='3c5cdc60-2537-4a12-a396-64d2e9e34870',
                    links={'retrieve_project': {'url': 'access granted'}},
                    statut=ChoixStatutPropositionDoctorale.EN_BROUILLON.name,
                    erreurs=[],
                    doctorat=Mock(
                        type=TrainingType.PHD.name,
                        sigle='SC3DP0',
                        annee=2023,
                    ),
                    creee_le=datetime.datetime(2023, 1, 1),
                    soumise_le=None,
                    annee_calculee=2023,
                ),
                Mock(
                    uuid='3c5cdc60-2537-4a12-a396-64d2e9e34871',
                    links={'retrieve_project': {'url': 'access granted'}},
                    statut=ChoixStatutPropositionDoctorale.EN_ATTENTE_DE_SIGNATURE.name,
                    erreurs=[],
                    doctorat=Mock(
                        type=TrainingType.PHD.name,
                        sigle='SC3DP1',
                        annee=2023,
                    ),
                    creee_le=datetime.datetime(2023, 1, 2),
                    soumise_le=None,
                    annee_calculee=2023,
                ),
                Mock(
                    uuid='3c5cdc60-2537-4a12-a396-64d2e9e34872',
                    links={'retrieve_project': {'url': 'access granted'}},
                    statut=ChoixStatutPropositionDoctorale.EN_BROUILLON.name,
                    erreurs=[],
                    doctorat=Mock(
                        type=TrainingType.PHD.name,
                        sigle='SC3DP2',
                        annee=2023,
                    ),
                    creee_le=datetime.datetime(2023, 1, 3),
                    soumise_le=None,
                    annee_calculee=2023,
                ),
                Mock(
                    uuid='3c5cdc60-2537-4a12-a396-64d2e9e34873',
                    links={},
                    erreurs=[],
                    statut=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
                    doctorat=Mock(
                        type=TrainingType.PHD.name,
                        sigle='SC3DP3',
                        annee=2023,
                    ),
                    creee_le=datetime.datetime(2023, 1, 4),
                    soumise_le=datetime.datetime(2024, 1, 1),
                    annee_calculee=2023,
                ),
            ],
            continuing_education_propositions=[
                Mock(
                    uuid='4c5cdc60-2537-4a12-a396-64d2e9e34870',
                    links={'retrieve_training_choice': {'url': 'access granted'}},
                    erreurs=[],
                    statut=ChoixStatutPropositionContinue.EN_BROUILLON.name,
                    formation=Mock(
                        type=TrainingType.UNIVERSITY_FIRST_CYCLE_CERTIFICATE.name,
                        annee=2023,
                        sigle='FC0',
                    ),
                    doctorat=None,
                    creee_le=datetime.datetime(2023, 1, 5),
                    soumise_le=None,
                    annee_calculee=2023,
                ),
                Mock(
                    uuid='4c5cdc60-2537-4a12-a396-64d2e9e34871',
                    links={'retrieve_training_choice': {'url': 'access granted'}},
                    erreurs=[],
                    statut=ChoixStatutPropositionDoctorale.ANNULEE.name,
                    formation=Mock(
                        type=TrainingType.UNIVERSITY_FIRST_CYCLE_CERTIFICATE.name,
                        annee=2023,
                        sigle='FC1',
                    ),
                    doctorat=None,
                    creee_le=datetime.datetime(2023, 1, 5),
                    soumise_le=None,
                    annee_calculee=2023,
                ),
            ],
            general_education_propositions=[
                Mock(
                    uuid='5c5cdc60-2537-4a12-a396-64d2e9e34870',
                    links={'retrieve_training_choice': {'url': 'access granted'}},
                    erreurs=[],
                    statut=ChoixStatutPropositionGenerale.EN_BROUILLON.name,
                    formation=Mock(
                        type=TrainingType.BACHELOR.name,
                        annee=2023,
                        sigle='MINF0',
                    ),
                    doctorat=None,
                    creee_le=datetime.datetime(2023, 1, 6),
                    soumise_le=None,
                    annee_calculee=2023,
                ),
                Mock(
                    uuid='5c5cdc60-2537-4a12-a396-64d2e9e34871',
                    links={'retrieve_training_choice': {'url': 'access granted'}},
                    erreurs=[],
                    statut=ChoixStatutPropositionGenerale.CONFIRMEE.name,
                    formation=Mock(
                        type=TrainingType.BACHELOR.name,
                        annee=2023,
                        sigle='MINF1',
                    ),
                    doctorat=None,
                    creee_le=datetime.datetime(2023, 1, 6),
                    soumise_le=datetime.datetime(2024, 1, 1),
                    annee_calculee=2023,
                ),
                Mock(
                    uuid='5c5cdc60-2537-4a12-a396-64d2e9e34872',
                    links={'retrieve_training_choice': {'url': 'access granted'}},
                    erreurs=[],
                    statut=ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE.name,
                    formation=Mock(
                        type=TrainingType.BACHELOR.name,
                        annee=2024,
                        sigle='MINF2',
                    ),
                    doctorat=None,
                    creee_le=datetime.datetime(2023, 1, 6),
                    soumise_le=datetime.datetime(2024, 1, 2),
                    annee_calculee=2024,
                ),
            ],
            links={
                'create_training_choice': {'error': 'My error message'},
            },
        )
        api.return_value.propositions_ucl_enrolments_list.return_value = []
        api.return_value.propositions_re_enrolment_period_retrieve.return_value.date_debut = datetime.date(2023, 6, 15)
        api.return_value.propositions_re_enrolment_period_retrieve.return_value.date_fin = datetime.date(2023, 10, 31)

        response = self.client.get(self.list_url)

        self.assertFalse(response.context['can_create_proposition'])

        draft_propositions = response.context['draft_propositions']
        self.assertEqual(len(draft_propositions), 5)
        self.assertEqual(draft_propositions[0].uuid, '5c5cdc60-2537-4a12-a396-64d2e9e34870')
        self.assertEqual(draft_propositions[1].uuid, '4c5cdc60-2537-4a12-a396-64d2e9e34870')
        self.assertEqual(draft_propositions[2].uuid, '3c5cdc60-2537-4a12-a396-64d2e9e34872')
        self.assertEqual(draft_propositions[3].uuid, '3c5cdc60-2537-4a12-a396-64d2e9e34871')
        self.assertEqual(draft_propositions[4].uuid, '3c5cdc60-2537-4a12-a396-64d2e9e34870')

        draft_or_in_payment_propositions = response.context['draft_or_in_payment_propositions']
        self.assertEqual(len(draft_or_in_payment_propositions), 6)
        self.assertIn('SC3DP0', draft_or_in_payment_propositions)
        self.assertIn('SC3DP1', draft_or_in_payment_propositions)
        self.assertIn('SC3DP2', draft_or_in_payment_propositions)
        self.assertIn('FC0', draft_or_in_payment_propositions)
        self.assertIn('MINF0', draft_or_in_payment_propositions)
        self.assertIn('MINF2', draft_or_in_payment_propositions)

        submitted_propositions = response.context['submitted_propositions']
        self.assertEqual(len(submitted_propositions), 2)

        self.assertIn(2023, submitted_propositions)
        self.assertEqual(len(submitted_propositions[2023]), 3)
        self.assertEqual(submitted_propositions[2023][0].uuid, '5c5cdc60-2537-4a12-a396-64d2e9e34871')
        self.assertEqual(submitted_propositions[2023][1].uuid, '3c5cdc60-2537-4a12-a396-64d2e9e34873')
        self.assertEqual(submitted_propositions[2023][2].uuid, '4c5cdc60-2537-4a12-a396-64d2e9e34871')

        self.assertIn(2024, submitted_propositions)
        self.assertEqual(len(submitted_propositions[2024]), 1)
        self.assertEqual(submitted_propositions[2024][0].uuid, '5c5cdc60-2537-4a12-a396-64d2e9e34872')

    @patch('osis_admission_sdk.api.propositions_api.PropositionsApi')
    def test_re_enrolment_list(self, api, *args):
        self.client.force_login(PersonFactory().user)

        valid_action_links = {
            'create_training_choice': {'url': 'access granted'},
        }
        invalid_action_links = {
            'create_training_choice': {'error': 'error'},
        }
        api.return_value.list_propositions.return_value = Mock(
            doctorate_propositions=[],
            continuing_education_propositions=[],
            general_education_propositions=[
                Mock(
                    uuid='5c5cdc60-2537-4a12-a396-64d2e9e34871',
                    links={'retrieve_training_choice': {'url': 'access granted'}},
                    erreurs=[],
                    statut=ChoixStatutPropositionGenerale.CONFIRMEE.name,
                    formation=Mock(
                        type=TrainingType.BACHELOR.name,
                        annee=2024,
                        sigle='F5',
                    ),
                    doctorat=None,
                    creee_le=datetime.datetime(2023, 1, 6),
                    soumise_le=datetime.datetime(2024, 1, 1),
                    annee_calculee=2024,
                ),
                Mock(
                    uuid='5c5cdc60-2537-4a12-a396-64d2e9e34871',
                    links={'retrieve_training_choice': {'url': 'access granted'}},
                    erreurs=[],
                    statut=ChoixStatutPropositionGenerale.EN_BROUILLON.name,
                    formation=Mock(
                        type=TrainingType.BACHELOR.name,
                        annee=2024,
                        sigle='F6',
                    ),
                    doctorat=None,
                    creee_le=datetime.datetime(2023, 1, 6),
                    soumise_le=datetime.datetime(2024, 1, 1),
                    annee_calculee=2024,
                ),
                Mock(
                    uuid='5c5cdc60-2537-4a12-a396-64d2e9e34871',
                    links={'retrieve_training_choice': {'url': 'access granted'}},
                    erreurs=[],
                    statut=ChoixStatutPropositionGenerale.ANNULEE.name,
                    formation=Mock(
                        type=TrainingType.BACHELOR.name,
                        annee=2024,
                        sigle='F7',
                    ),
                    doctorat=None,
                    creee_le=datetime.datetime(2023, 1, 6),
                    soumise_le=datetime.datetime(2024, 1, 1),
                    annee_calculee=2024,
                ),
            ],
            links=valid_action_links,
        )

        # Included
        not_graduated_ucl_enrolment_2023_f1 = Mock(annee=2023, est_diplome=False, sigle_formation='F1')
        # Graduated => excluded
        graduated_ucl_enrolment_2023_f2 = Mock(annee=2023, est_diplome=True, sigle_formation='F2')
        # Future year => excluded
        not_graduated_ucl_enrolment_2024_f3 = Mock(annee=2024, est_diplome=False, sigle_formation='F3')
        # Already enrolled => excluded
        not_graduated_ucl_enrolment_2023_f4 = Mock(annee=2023, est_diplome=False, sigle_formation='F4')
        not_graduated_ucl_enrolment_2024_f4 = Mock(annee=2024, est_diplome=False, sigle_formation='F4')
        # Admission already submitted => excluded
        not_graduated_ucl_enrolment_2023_f5 = Mock(annee=2023, est_diplome=False, sigle_formation='F5')
        # Admission already created but not submitted => included
        not_graduated_ucl_enrolment_2023_f6 = Mock(annee=2023, est_diplome=False, sigle_formation='F6')
        # PHD => excluded
        not_graduated_ucl_enrolment_2023_f7 = Mock(
            annee=2023,
            est_diplome=False,
            sigle_formation='F7',
            type_formation=TrainingType.PHD.name,
        )
        # Admission already created but cancelled => included
        not_graduated_ucl_enrolment_2023_f8 = Mock(annee=2023, est_diplome=False, sigle_formation='F8')

        api.return_value.propositions_ucl_enrolments_list.return_value = [
            not_graduated_ucl_enrolment_2023_f1,
            graduated_ucl_enrolment_2023_f2,
            not_graduated_ucl_enrolment_2024_f3,
            not_graduated_ucl_enrolment_2023_f4,
            not_graduated_ucl_enrolment_2024_f4,
            not_graduated_ucl_enrolment_2023_f5,
            not_graduated_ucl_enrolment_2023_f6,
            not_graduated_ucl_enrolment_2023_f7,
            not_graduated_ucl_enrolment_2023_f8,
        ]

        re_enrolment_period = Mock(
            date_debut=datetime.date(2023, 6, 15),
            date_fin=datetime.date(2023, 10, 31),
            annee_formation=2024,
        )
        api.return_value.propositions_re_enrolment_period_retrieve.return_value = re_enrolment_period

        re_enrolment_eligibility = MagicMock(
            decision=EligibiliteReinscription.EST_ELIGIBLE.name,
            raison_non_eligibilite='',
        )
        api.return_value.propositions_candidate_re_enrolment_eligibity_retrieve.return_value = re_enrolment_eligibility

        # Outside the enrolment period
        with freezegun.freeze_time('2023-06-14'):
            response = self.client.get(self.list_url)

            self.assertEqual(response.context['ucl_enrolments_list'], [])
            self.assertEqual(response.context['can_create_re_enrolment_proposition'], False)
            self.assertEqual(response.context['re_enrolment_error_message'], '')

        # In the enrolment period
        with freezegun.freeze_time('2023-06-15'):
            # > eligible
            re_enrolment_eligibility.decision=EligibiliteReinscription.EST_ELIGIBLE.name

            # > with the right to create a proposition
            response = self.client.get(self.list_url)

            self.assertEqual(
                response.context['ucl_enrolments_list'],
                [
                    not_graduated_ucl_enrolment_2023_f1,
                    not_graduated_ucl_enrolment_2023_f6,
                    not_graduated_ucl_enrolment_2023_f8,
                ],
            )
            self.assertEqual(response.context['can_create_re_enrolment_proposition'], True)
            self.assertEqual(response.context['re_enrolment_error_message'], '')

            # > without the right to create a proposition
            api.return_value.list_propositions.return_value.links = invalid_action_links

            response = self.client.get(self.list_url)

            self.assertEqual(
                response.context['ucl_enrolments_list'],
                [
                    not_graduated_ucl_enrolment_2023_f1,
                    not_graduated_ucl_enrolment_2023_f6,
                    not_graduated_ucl_enrolment_2023_f8,
                ],
            )
            self.assertEqual(response.context['can_create_re_enrolment_proposition'], False)
            self.assertEqual(response.context['re_enrolment_error_message'], '')

            # > not eligible with the right to create a proposition
            api.return_value.list_propositions.return_value.links = valid_action_links
            re_enrolment_eligibility.decision = EligibiliteReinscription.NON_ELIGIBLE_EN_ATTENTE_RESULTATS.name
            re_enrolment_eligibility.raison_non_eligibilite = 'My error 2'

            response = self.client.get(self.list_url)

            self.assertEqual(
                response.context['ucl_enrolments_list'],
                [
                    not_graduated_ucl_enrolment_2023_f1,
                    graduated_ucl_enrolment_2023_f2,
                    not_graduated_ucl_enrolment_2023_f6,
                    not_graduated_ucl_enrolment_2023_f8,
                ],
            )
            self.assertEqual(response.context['can_create_re_enrolment_proposition'], False)
            self.assertEqual(
                response.context['re_enrolment_error_message'],
                'My error 2',
            )

    @patch('osis_admission_sdk.api.propositions_api.PropositionsApi')
    def test_list_supervised(self, api, *args):
        self.client.force_login(PersonFactory().user)

        api.return_value.list_supervised_propositions.return_value = [
            Mock(
                uuid='3c5cdc60-2537-4a12-a396-64d2e9e34876',
                links={'retrieve_project': {'url': 'access granted'}},
                erreurs=[],
            ),
            Mock(uuid='b3729603-c991-489f-8d8d-1d3a11b64dad', links={}, erreurs=[]),
        ]

        url = reverse('admission:supervised-list')
        response = self.client.get(url)
        detail_url = resolve_url('admission:doctorate:project', pk='3c5cdc60-2537-4a12-a396-64d2e9e34876')
        self.assertContains(response, detail_url)

        url = reverse('gestion_doctorat:supervised-list')
        response = self.client.get(url)
        detail_url = resolve_url('gestion_doctorat:doctorate:project', pk='3c5cdc60-2537-4a12-a396-64d2e9e34876')
        self.assertContains(response, detail_url)
