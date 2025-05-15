# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from datetime import date
from unittest.mock import ANY, Mock, patch

import freezegun
from django.shortcuts import resolve_url
from django.test import TestCase, override_settings
from django.utils.translation import gettext_lazy as _

from admission.contrib.enums import ChoixStatutPropositionGenerale
from base.tests.factories.person import PersonFactory
from frontoffice.settings.osis_sdk.utils import (
    ApiBusinessException,
    MultipleApiBusinessException,
)
from osis_admission_sdk.model.pool_enum import PoolEnum
from osis_admission_sdk.model.submit_proposition import SubmitProposition


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/')
class ConfirmSubmitTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()
        cls.url = resolve_url('admission:doctorate:update:confirm-submit', pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        cls.default_kwargs = {
            'accept_language': ANY,
            'x_user_first_name': ANY,
            'x_user_last_name': ANY,
            'x_user_email': ANY,
            'x_user_global_id': ANY,
        }

    def setUp(self):
        self.data_ok = {
            'pool': 'DOCTORATE_EDUCATION_ENROLLMENT',
            'annee': 2020,
            'foo': "I allow Test",
            'bar': "I do not authorize Test to do something with my data",
            'declaration_sur_lhonneur': "<ul><li>Element1</li></ul>",
            'justificatifs': 'I understand',
        }
        self.client.force_login(self.person.user)

        propositions_api_patcher = patch("osis_admission_sdk.api.propositions_api.PropositionsApi")
        self.mock_proposition_api = propositions_api_patcher.start()
        api = self.mock_proposition_api.return_value
        api.retrieve_doctorate_proposition.return_value = Mock(
            uuid='3c5cdc60-2537-4a12-a396-64d2e9e34876',
            erreurs=[],
            date_fin_pot=None,
            institut_these='',
            links={
                'retrieve_person': {'url': 'ok'},
                'retrieve_supervision': {'url': 'ok'},
            },
            code_secteur_formation='SSH',
        )
        api.verify_proposition.return_value.to_dict.return_value = {
            'errors': [],
            'elements_confirmation': [
                {
                    'nom': 'foo',
                    'titre': "Foo title",
                    'texte': "I allow Test",
                    'type': 'checkbox',
                },
                {
                    'nom': 'bar',
                    'titre': "Bar title",
                    'reponses': ['I authorize', 'I do not authorize'],
                    'texte': "Test to do something with my data",
                    'type': 'radio',
                },
                {
                    'nom': 'declaration_sur_lhonneur',
                    'titre': "Déclaration",
                    'texte': "<ul><li>Element1</li></ul>",
                    'type': 'checkbox',
                },
                {
                    'nom': 'justificatifs',
                    'titre': "justificatifs",
                    'texte': "I understand",
                    'type': 'checkbox',
                },
            ],
        }
        api.submit_proposition.return_value.to_dict.return_value = {"uuid": "3c5cdc60-2537-4a12-a396-64d2e9e34876"}
        self.addCleanup(propositions_api_patcher.stop)

    def test_redirect(self):
        response = self.client.get(
            resolve_url('admission:doctorate:confirm-submit', pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        )
        self.assertRedirects(response, self.url)

    def test_get_without_errors(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.mock_proposition_api.return_value.retrieve_doctorate_proposition.assert_called()
        self.mock_proposition_api.return_value.verify_proposition.return_value.to_dict.assert_called()

        self.assertContains(response, 'Foo title')
        self.assertContains(response, 'I allow Test')
        self.assertContains(response, 'I do not authorize')
        self.assertContains(response, 'Test to do something with my data')
        self.assertContains(response, '<ul><li>Element1</li></ul>')
        self.assertContains(response, _('Your application is complete and may be submitted.'))

    def test_get_with_incomplete_admission(self):
        self.mock_proposition_api.return_value.verify_proposition.return_value.to_dict.return_value = {
            'errors': [
                dict(status_code='PROPOSITION-25', detail='Some data is missing.'),
                dict(status_code='PROPOSITION-38', detail='Every promoter must approve the proposition.'),
            ]
        }

        response = self.client.get(self.url)
        # Display an error message as some conditions aren't meet
        self.assertContains(
            response,
            _('Your enrolment cannot be confirmed. All of the following requirements must be met.'),
        )

    def test_get_with_additional_conditions_not_respected(self):
        self.mock_proposition_api.return_value.verify_proposition.return_value.to_dict.return_value = {
            'errors': [
                dict(status_code='ADMISSION-24', detail='Some additional condition is not respected.'),
            ]
        }

        response = self.client.get(self.url)

        # Display an error message as some conditions aren't meet but not the errors by tabs
        self.assertContains(response, 'Some additional condition is not respected.')
        self.assertNotContains(
            response,
            _('Your enrolment cannot be confirmed. All of the following requirements must be met.'),
        )

        self.mock_proposition_api.return_value.verify_proposition.return_value.to_dict.return_value = {
            'errors': [
                dict(status_code='ADMISSION-24', detail='Some additional condition is not respected.'),
                dict(status_code='PROPOSITION-25', detail='Some data is missing.'),
            ]
        }

        response = self.client.get(self.url)

        # Display an error message as some conditions aren't meet and also the errors by tabs
        self.assertContains(response, 'Some additional condition is not respected.')
        self.assertContains(
            response,
            _('Your enrolment cannot be confirmed. All of the following requirements must be met.'),
        )

    @freezegun.freeze_time('2022-10-01')
    def test_get_late_message(self):
        date_fin = date(2022, 10, 31)
        self.mock_proposition_api.return_value.retrieve_doctorate_proposition.return_value.date_fin_pot = date_fin
        self.mock_proposition_api.return_value.retrieve_doctorate_proposition.return_value.pot_calcule = (
            'ADMISSION_POOL_UE5_BELGIAN'
        )
        response = self.client.get(self.url)
        # Display a message for late enrollment
        self.assertContains(
            response,
            _(
                "On the basis of the information you have provided, you are requesting consideration "
                'of <a href="https://uclouvain.be/en/study/inscriptions/special-follow-up.html#Late_enrolment" '
                'target="_blank">a late enrolment application</a>. This must be confirmed as soon as '
                'possible and no '
                "later than %(date)s. The admission panel reserves the right to accept or refuse this "
                "late application."
            )
            % {'date': date_fin.strftime('%d/%m/%Y')},
        )

    def test_post_with_incomplete_elements_confirmation(self):
        data = {
            'pool': 'DOCTORATE_EDUCATION_ENROLLMENT',
            'annee': 2022,
        }
        response = self.client.post(self.url, data=data)

        self.assertEqual(response.status_code, 200)

        self.assertFormError(response.context['confirmation_form'], 'foo', _('This field is required.'))
        self.assertFormError(response.context['confirmation_form'], 'bar', _('This field is required.'))

    def test_post_with_complete_form_but_bad_values(self):
        self.mock_proposition_api.return_value.submit_proposition.side_effect = MultipleApiBusinessException(
            exceptions={
                ApiBusinessException(
                    status_code='ADMISSION-14',
                    detail="The submitted information is not consistent with information requested.",
                ),
            }
        )
        response = self.client.post(self.url, data=self.data_ok, follow=True)
        self.mock_proposition_api.return_value.submit_proposition.assert_called_with(
            uuid="3c5cdc60-2537-4a12-a396-64d2e9e34876",
            submit_proposition=SubmitProposition(**{
                'pool': PoolEnum(value='DOCTORATE_EDUCATION_ENROLLMENT'),
                'annee': 2020,
                'elements_confirmation': {
                    'foo': "I allow Test",
                    'bar': "I do not authorize Test to do something with my data",
                    'declaration_sur_lhonneur': "<ul><li>Element1</li></ul>",
                    'justificatifs': 'I understand',
                },
            }),
            **self.default_kwargs,
        )
        self.assertRedirects(response, self.url)
        self.assertContains(response, _("An error has occurred, please check fields and try again."))

    def test_post_doctorate_with_complete_form(self):
        autocomplete_api_patcher = patch("osis_admission_sdk.api.autocomplete_api.AutocompleteApi")
        mock_autocomplete_api = autocomplete_api_patcher.start()
        mock_autocomplete_api.return_value.list_sector_dtos.return_value = [
            Mock(sigle='SSH', intitule='Foobar'),
            Mock(sigle='SST', intitule='Barbaz'),
            Mock(sigle='SSS', intitule='Foobarbaz'),
        ]
        self.addCleanup(autocomplete_api_patcher.stop)
        self.mock_proposition_api.return_value.retrieve_doctorate_proposition.return_value.links = {}

        response = self.client.post(self.url, data=self.data_ok, follow=True)
        self.mock_proposition_api.return_value.submit_proposition.assert_called_with(
            uuid="3c5cdc60-2537-4a12-a396-64d2e9e34876",
            submit_proposition=SubmitProposition(**{
                'pool': PoolEnum(value='DOCTORATE_EDUCATION_ENROLLMENT'),
                'annee': 2020,
                'elements_confirmation': {
                    'foo': "I allow Test",
                    'bar': "I do not authorize Test to do something with my data",
                    'declaration_sur_lhonneur': "<ul><li>Element1</li></ul>",
                    'justificatifs': 'I understand',
                },
            }),
            **self.default_kwargs,
        )
        url = resolve_url('admission:list')
        self.assertRedirects(response, url)
        self.assertContains(response, _("Your application has been submitted"))

    def test_post_continuing_with_complete_form(self):
        api = self.mock_proposition_api.return_value
        verification = api.verify_continuing_education_proposition.return_value.to_dict
        verification.return_value = api.verify_proposition.return_value.to_dict.return_value
        uuid = "3c5cdc60-2537-4a12-a396-64d2e9e34876"
        url = resolve_url('admission:continuing-education:update:confirm-submit', pk=uuid)
        data = {**self.data_ok, 'pool': 'CONTINUING_EDUCATION_ENROLLMENT'}

        response = self.client.post(url, data=data, follow=True)
        url = resolve_url('admission:list')
        self.assertRedirects(response, url)
        api.submit_continuing_education_proposition.assert_called_with(
            uuid=uuid,
            submit_proposition=SubmitProposition(**{
                'pool': PoolEnum(value='CONTINUING_EDUCATION_ENROLLMENT'),
                'annee': 2020,
                'elements_confirmation': {
                    'foo': "I allow Test",
                    'bar': "I do not authorize Test to do something with my data",
                    'declaration_sur_lhonneur': "<ul><li>Element1</li></ul>",
                    'justificatifs': 'I understand',
                },
            }),
            **self.default_kwargs,
        )
        self.assertContains(response, _("Your application has been submitted"))

    def test_post_general_with_complete_form(self):
        api = self.mock_proposition_api.return_value
        verification = api.verify_general_education_proposition.return_value.to_dict
        verification.return_value = api.verify_proposition.return_value.to_dict.return_value
        uuid = "3c5cdc60-2537-4a12-a396-64d2e9e34876"
        url = resolve_url('admission:general-education:update:confirm-submit', pk=uuid)
        data = {**self.data_ok, 'pool': 'ADMISSION_POOL_UE5_BELGIAN'}
        api.submit_general_education_proposition.return_value.to_dict.return_value = {
            'status': ChoixStatutPropositionGenerale.CONFIRMEE.name,
            'uuid': uuid,
        }

        response = self.client.post(url, data=data, follow=True)
        url = resolve_url('admission:list')
        self.assertRedirects(response, url)
        api.submit_general_education_proposition.assert_called_with(
            uuid=uuid,
            submit_proposition=SubmitProposition(**{
                'pool': PoolEnum(value='ADMISSION_POOL_UE5_BELGIAN'),
                'annee': 2020,
                'elements_confirmation': {
                    'foo': "I allow Test",
                    'bar': "I do not authorize Test to do something with my data",
                    'declaration_sur_lhonneur': "<ul><li>Element1</li></ul>",
                    'justificatifs': 'I understand',
                },
            }),
            **self.default_kwargs,
        )
        self.assertContains(response, _("Your application has been submitted"))

    def test_post_general_with_complete_form_and_require_application_fees_payment(self):
        api = self.mock_proposition_api.return_value
        verification = api.verify_general_education_proposition.return_value.to_dict
        verification.return_value = api.verify_proposition.return_value.to_dict.return_value
        uuid = "3c5cdc60-2537-4a12-a396-64d2e9e34876"
        url = resolve_url('admission:general-education:update:confirm-submit', pk=uuid)
        data = {**self.data_ok, 'pool': 'ADMISSION_POOL_UE5_BELGIAN'}
        api.submit_general_education_proposition.return_value.to_dict.return_value = {
            'status': ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE.name,
            'uuid': uuid,
        }
        response = self.client.post(url, data=data)
        url = resolve_url('admission:general-education:payment', pk=uuid)
        self.assertRedirects(response, url, fetch_redirect_response=False)
        api.submit_general_education_proposition.assert_called_with(
            uuid=uuid,
            submit_proposition=SubmitProposition(**{
                'pool': PoolEnum(value='ADMISSION_POOL_UE5_BELGIAN'),
                'annee': 2020,
                'elements_confirmation': {
                    'foo': "I allow Test",
                    'bar': "I do not authorize Test to do something with my data",
                    'declaration_sur_lhonneur': "<ul><li>Element1</li></ul>",
                    'justificatifs': 'I understand',
                },
            }),
            **self.default_kwargs,
        )
