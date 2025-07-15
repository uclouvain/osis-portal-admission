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
from unittest.mock import ANY, Mock, patch

from django.shortcuts import resolve_url
from django.test import TestCase, override_settings
from django.utils.translation import gettext_lazy as _
from osis_admission_sdk import ApiException
from osis_admission_sdk.model.actor_type_enum import ActorTypeEnum
from osis_admission_sdk.model.approuver_proposition_command import (
    ApprouverPropositionCommand,
)
from osis_admission_sdk.model.identifier_supervision_actor import (
    IdentifierSupervisionActor,
)
from osis_admission_sdk.model.promoteur_dto_nested import PromoteurDTONested
from osis_admission_sdk.model.refuser_proposition_command import (
    RefuserPropositionCommand,
)

from admission.contrib.enums.actor import ActorType, ChoixEtatSignature
from admission.contrib.enums.projet import ChoixStatutPropositionDoctorale
from admission.contrib.enums.supervision import DecisionApprovalEnum
from admission.contrib.forms import PDF_MIME_TYPE
from admission.contrib.forms.supervision import ACTOR_EXTERNAL, EXTERNAL_FIELDS
from base.tests.factories.person import PersonFactory
from base.tests.test_case import OsisPortalTestCase
from frontoffice.settings.osis_sdk.utils import (
    ApiBusinessException,
    MultipleApiBusinessException,
)


@override_settings(ADMISSION_TOKEN_EXTERNAL='api-token-external')
class SupervisionTestCase(OsisPortalTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()

    def setUp(self):
        self.external_api_token_header = {'Token': 'api-token-external'}
        self.pk = "3c5cdc60-2537-4a12-a396-64d2e9e34876"

        self.client.force_login(self.person.user)
        self.update_url = resolve_url("admission:doctorate:update:supervision", pk=self.pk)
        self.detail_url = resolve_url("admission:doctorate:supervision", pk=self.pk)
        self.external_url = resolve_url(
            "admission:public-doctorate:external-approval",
            pk=self.pk,
            token="promoter-token",
        )
        self.default_kwargs = {
            'accept_language': ANY,
            'x_user_first_name': ANY,
            'x_user_last_name': ANY,
            'x_user_email': ANY,
            'x_user_global_id': ANY,
        }
        self.external_kwargs = {
            'accept_language': ANY,
            'token': 'promoter-token',
        }

        api_patcher = patch("osis_admission_sdk.api.propositions_api.PropositionsApi")
        self.mock_api = api_patcher.start()
        self.addCleanup(api_patcher.stop)
        self.mock_api.return_value.retrieve_doctorate_proposition.return_value = Mock(
            doctorat={'intitule': 'test_intitule', 'campus': 'test_campus'},
            reference="REF7777",
            code_secteur_formation="SSH",
            institut_these='',
            documents_projet=[],
            graphe_gantt=[],
            proposition_programme_doctoral=[],
            projet_formation_complementaire=[],
            lettres_recommandation=[],
            fiche_archive_signatures_envoyees=[],
            statut=ChoixStatutPropositionDoctorale.EN_ATTENTE_DE_SIGNATURE.name,
            links={
                'add_approval': {'error': 'nope'},
                'request_signatures': {'error': 'nope'},
                'add_member': {'error': 'nope'},
                'edit_external_member': {'url': 'ok'},
            },
            erreurs=[],
        )

        self.mock_api.return_value.retrieve_supervision.return_value.to_dict.return_value = dict(
            signatures_promoteurs=[
                dict(
                    promoteur=dict(
                        uuid="uuid-0123456978",
                        matricule="0123456978",
                        prenom="Marie-Odile",
                        nom="Troufignon",
                    ),
                    statut=ChoixEtatSignature.APPROVED.name,
                    commentaire_externe="A public comment to display",
                ),
                dict(
                    promoteur=dict(
                        uuid="uuid-9876543210",
                        matricule="9876543210",
                        prenom="John",
                        nom="Doe",
                    ),
                    statut=ChoixEtatSignature.DECLINED.name,
                    commentaire_externe="A public comment to display",
                ),
                dict(
                    promoteur=PromoteurDTONested(
                        uuid="uuid-externe",
                        matricule="",
                        prenom="Marcel",
                        nom="Troufignon",
                        est_docteur=True,
                        email="marcel@example.org",
                        institution="isntitution",
                        ville="ville",
                        code_pays="FR",
                        pays="France",
                        est_externe=True,
                    ),
                    statut=ChoixEtatSignature.APPROVED.name,
                ),
            ],
            signatures_membres_ca=[
                dict(
                    membre_ca=dict(
                        uuid=f"uuid-{self.person.global_id}",
                        matricule=self.person.global_id,
                        prenom="Jacques-Eudes",
                        nom="Birlimpette",
                    ),
                    statut=ChoixEtatSignature.INVITED.name,
                ),
            ],
            promoteur_reference="uuid-0123456978",
        )

        self.mock_api.return_value.get_external_proposition.return_value.to_dict.return_value = {
            'proposition': self.mock_api.return_value.retrieve_doctorate_proposition.return_value,
            'supervision': self.mock_api.return_value.retrieve_supervision.return_value.to_dict.return_value,
        }

        countries_api_patcher = patch("osis_reference_sdk.api.countries_api.CountriesApi")
        self.mock_countries_api = countries_api_patcher.start()

        self.mock_countries_api.return_value.countries_list.return_value = Mock(
            results=[Mock(iso_code='BE', name='Belgique', name_en='Belgium', european_union=True)]
        )
        self.addCleanup(countries_api_patcher.stop)

    def test_should_detail_redirect_to_form_when_not_signing(self):
        self.mock_api.return_value.retrieve_doctorate_proposition.return_value.links.update(
            {
                'request_signatures': {'url': 'ok'},
                'add_member': {'url': 'ok'},
            }
        )
        self.mock_api.return_value.retrieve_doctorate_proposition.return_value.statut = (
            ChoixStatutPropositionDoctorale.EN_BROUILLON.name
        )
        response = self.client.get(self.detail_url)
        # Display the signatures
        self.assertRedirects(response, self.update_url)

    def test_should_detail_supervision_member(self):
        response = self.client.get(self.detail_url)
        # Display the signatures
        self.assertContains(response, "Troufignon")
        self.assertContains(response, ChoixEtatSignature.APPROVED.value)
        self.assertContains(response, "A public comment to display")
        self.assertContains(response, ChoixEtatSignature.DECLINED.value)
        self.mock_api.return_value.retrieve_supervision.assert_called()

    def test_should_add_supervision_member(self):
        self.mock_api.return_value.retrieve_doctorate_proposition.return_value.links.update(
            {
                'request_signatures': {'url': 'ok'},
                'add_member': {'url': 'ok'},
            }
        )
        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(self.update_url, {'type': ActorType.CA_MEMBER.name})
        self.assertEqual(response.status_code, 200)
        self.assertIn('__all__', response.context['add_form'].errors)
        self.mock_api.return_value.add_member.assert_not_called()

        data = {
            'type': ActorType.CA_MEMBER.name,
            'internal_external': "INTERNAL",
            'person': "0123456978",
            'email': "test@test.fr",
        }
        response = self.client.post(self.update_url, data)
        self.assertEqual(response.status_code, 302)
        self.mock_api.return_value.add_member.assert_called_with(
            uuid=self.pk,
            identifier_supervision_actor=IdentifierSupervisionActor(
                **{
                    'actor_type': ActorTypeEnum(ActorType.CA_MEMBER.name),
                    'matricule': "0123456978",
                    'est_docteur': False,
                    **{field: "" for field in EXTERNAL_FIELDS},
                }
            ),
            **self.default_kwargs,
        )
        self.mock_api.return_value.add_member.reset_mock()

        response = self.client.post(self.update_url, {'type': ActorType.PROMOTER.name})
        self.assertEqual(response.status_code, 200)
        self.assertIn('__all__', response.context['add_form'].errors)
        self.mock_api.return_value.add_member.assert_not_called()

        data = {
            'type': ActorType.PROMOTER.name,
            'internal_external': "INTERNAL",
            'person': "0123456978",
            'email': "test@test.fr",
        }
        response = self.client.post(self.update_url, data)
        self.assertEqual(response.status_code, 302)
        self.mock_api.return_value.add_member.assert_called_with(
            uuid=self.pk,
            identifier_supervision_actor=IdentifierSupervisionActor(
                **{
                    'actor_type': ActorTypeEnum(ActorType.PROMOTER.name),
                    'matricule': "0123456978",
                    'est_docteur': False,
                    **{field: "" for field in EXTERNAL_FIELDS},
                }
            ),
            **self.default_kwargs,
        )
        self.mock_api.return_value.add_member.reset_mock()

        data = {
            'type': ActorType.PROMOTER.name,
            'internal_external': ACTOR_EXTERNAL,
            'email': "test@test.fr",
        }
        response = self.client.post(self.update_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(EXTERNAL_FIELDS) - 1, len(response.context['add_form'].errors))
        self.assertIn('prenom', response.context['add_form'].errors)
        self.mock_api.return_value.add_member.assert_not_called()

        external_data = {
            'prenom': 'John',
            'nom': 'Doe',
            'email': 'john@example.org',
            'est_docteur': True,
            'institution': 'ins',
            'ville': 'mons',
            'pays': 'BE',
            'langue': 'fr-be',
        }
        data = {
            'type': ActorType.PROMOTER.name,
            'internal_external': ACTOR_EXTERNAL,
            'person': "0123456978",
            **external_data,
        }
        response = self.client.post(self.update_url, data)
        self.assertEqual(response.status_code, 302)
        self.mock_api.return_value.add_member.assert_called_with(
            uuid=self.pk,
            identifier_supervision_actor=IdentifierSupervisionActor(
                **{
                    'actor_type': ActorTypeEnum(ActorType.PROMOTER.name),
                    'matricule': "",
                    **external_data,
                }
            ),
            **self.default_kwargs,
        )

    def test_should_remove_supervision_member(self):
        url = resolve_url(
            "admission:doctorate:remove-actor",
            pk="3c5cdc60-2537-4a12-a396-64d2e9e34876",
            type=ActorType.PROMOTER.name,
            uuid="uuid-0123456978",
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 302)
        self.mock_api.return_value.remove_member.assert_called()

    def test_should_edit_external_supervision_member(self):
        url = resolve_url(
            "admission:doctorate:edit-external-member",
            pk="3c5cdc60-2537-4a12-a396-64d2e9e34876",
            uuid="uuid-0123456978",
        )
        external_data = {
            f'member-uuid-0123456978-{k}': v
            for k, v in {
                'prenom': '',
                'nom': 'Doe',
                'email': 'john@example.org',
                'est_docteur': True,
                'institution': 'ins',
                'ville': 'mons',
                'pays': 'BE',
                'langue': 'fr-be',
            }.items()
        }
        response = self.client.post(url, external_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.detail_url)
        self.mock_api.return_value.edit_external_member.assert_not_called()

        external_data['member-uuid-0123456978-prenom'] = 'John'
        response = self.client.post(url, external_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.detail_url)
        self.mock_api.return_value.edit_external_member.assert_called_with(
            uuid='3c5cdc60-2537-4a12-a396-64d2e9e34876',
            patched_modifier_membre_supervision_externe={
                'uuid_proposition': '3c5cdc60-2537-4a12-a396-64d2e9e34876',
                'uuid_membre': 'uuid-0123456978',
                'prenom': 'John',
                'nom': 'Doe',
                'email': 'john@example.org',
                'est_docteur': True,
                'institution': 'ins',
                'ville': 'mons',
                'pays': 'BE',
                'langue': 'fr-be',
            },
            **self.default_kwargs,
        )

    def test_should_not_remove_supervision_member_if_not_found(self):
        url = resolve_url(
            "admission:doctorate:remove-actor",
            pk="3c5cdc60-2537-4a12-a396-64d2e9e34876",
            type=ActorType.CA_MEMBER.name,
            uuid="uuid-1234569780",
        )
        response = self.client.get(url, {})
        self.assertEqual(response.status_code, 404)

        url = resolve_url(
            "admission:doctorate:remove-actor",
            pk=self.pk,
            type=ActorType.PROMOTER.name,
            uuid="uuid-1234569780",
        )
        response = self.client.get(url, {})
        self.assertEqual(response.status_code, 404)

        self.mock_api.return_value.retrieve_supervision.side_effect = ApiException
        response = self.client.get(url, {})
        self.assertEqual(response.status_code, 404)
        self.mock_api.return_value.remove_member.assert_not_called()

    def test_should_approve_proposition(self):
        # All data is provided and the proposition is approved
        response = self.client.post(
            self.detail_url,
            {
                'decision': DecisionApprovalEnum.APPROVED.name,
                'commentaire_interne': "The internal comment",
                'commentaire_externe': "The public comment",
                'motif_refus': "The reason",  # The reason is provided but will not be used
            },
        )

        self.assertEqual(response.status_code, 302)
        self.mock_api.return_value.approve_proposition.assert_called_with(
            uuid=self.pk,
            approuver_proposition_command=ApprouverPropositionCommand(
                **{
                    'commentaire_interne': "The internal comment",
                    'commentaire_externe': "The public comment",
                    'uuid_membre': f"uuid-{self.person.global_id}",
                }
            ),
            **self.default_kwargs,
        )

    def test_should_error_when_reference_promoter_and_no_institute(self):
        self.mock_api.return_value.retrieve_supervision.return_value.to_dict.return_value = dict(
            signatures_promoteurs=[
                dict(
                    promoteur=dict(
                        uuid="uuid-0123456978",
                        matricule="0123456978",
                        prenom="Marie-Odile",
                        nom="Troufignon",
                    ),
                    statut=ChoixEtatSignature.INVITED.name,
                ),
            ],
            signatures_membres_ca=[],
            promoteur_reference="uuid-0123456978",
        )
        self.client.force_login(PersonFactory(global_id='0123456978').user)
        response = self.client.post(self.detail_url, {'decision': DecisionApprovalEnum.APPROVED.name})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context["approval_form"], 'institut_these', _('This field is required.'))

    def test_should_reject_proposition(self):
        # All data is provided and the proposition is rejected
        response = self.client.post(
            self.detail_url,
            {
                'decision': DecisionApprovalEnum.DECLINED.name,
                'commentaire_interne': "The internal comment",
                'commentaire_externe': "The public comment",
                'motif_refus': "The reason",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.mock_api.return_value.reject_proposition.assert_called_with(
            uuid=self.pk,
            refuser_proposition_command=RefuserPropositionCommand(
                **{
                    'commentaire_externe': "The public comment",
                    'commentaire_interne': "The internal comment",
                    'motif_refus': "The reason",
                    'uuid_membre': f"uuid-{self.person.global_id}",
                }
            ),
            **self.default_kwargs,
        )

    def test_should_error_with_no_decision(self):
        # The decision is missing
        response = self.client.post(
            self.detail_url,
            {
                'commentaire_interne': "The internal comment",
                'commentaire_externe': "The public comment",
                'motif_refus': "The reason",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('decision', response.context['approval_form'].errors)

        self.mock_api.return_value.reject_proposition.assert_not_called()
        self.mock_api.return_value.approve_proposition.assert_not_called()

    def test_should_reject_with_error_when_no_motive(self):
        response = self.client.post(
            self.detail_url,
            {
                'decision': DecisionApprovalEnum.DECLINED.name,
                'commentaire_interne': "The internal comment",
                'commentaire_externe': "The public comment",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('motif_refus', response.context['approval_form'].errors)

        self.mock_api.return_value.reject_proposition.assert_not_called()
        self.mock_api.return_value.approve_proposition.assert_not_called()

    def test_update_should_redirect_to_detail_if_no_permission(self):
        response = self.client.get(self.update_url)
        self.assertRedirects(response, self.detail_url)

    def test_should_not_display_confirmation_if_errors(self):
        self.mock_api.return_value.retrieve_doctorate_proposition.return_value.links.update(
            {
                'request_signatures': {'url': 'ok'},
                'add_member': {'url': 'ok'},
            }
        )
        self.mock_api.return_value.retrieve_verify_project.return_value = [{'detail': "Nope", 'status_code': '1'}]
        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 200)
        self.mock_api.return_value.retrieve_verify_project.assert_called()
        self.assertNotContains(response, _("Are you sure you want to request signatures for this admission?"))
        self.assertContains(response, "Nope")

    def test_should_redirect_to_supervision_without_buttons(self):
        self.mock_api.return_value.retrieve_doctorate_proposition.return_value.links.update(
            {
                'request_signatures': {'url': 'ok'},
            }
        )
        self.mock_api.return_value.retrieve_verify_project.return_value = []
        response = self.client.get(self.update_url, {})
        self.assertEqual(response.status_code, 200)
        self.mock_api.return_value.retrieve_verify_project.assert_called()
        self.assertContains(response, _("Are you sure you want to request signatures for this admission?"))

        # Success
        post_url = resolve_url("admission:doctorate:request-signatures", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        response = self.client.post(post_url, {})
        self.assertRedirects(response, self.detail_url)
        self.mock_api.return_value.create_signatures.assert_called()

        # Failure
        post_url = resolve_url("admission:doctorate:request-signatures", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        self.mock_api.return_value.create_signatures.side_effect = MultipleApiBusinessException(
            exceptions={
                ApiBusinessException(status_code=42, detail="Something went wrong globally"),
            }
        )
        response = self.client.post(post_url, {}, follow=True)
        self.assertRedirects(response, self.update_url)
        self.assertContains(response, _("Please first correct the erros"))
        self.mock_api.return_value.create_signatures.assert_called()

    @patch(
        'osis_document.api.utils.get_remote_metadata',
        return_value={'name': 'myfile', 'mimetype': PDF_MIME_TYPE, 'size': 1},
    )
    def test_should_approval_by_pdf_redirect_without_errors(self, *args):
        url = resolve_url("admission:doctorate:approve-by-pdf", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        response = self.client.post(url, {'matricule': "test", 'pdf_0': 'some_file'})
        expected_url = resolve_url("admission:doctorate:supervision", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        self.assertRedirects(response, expected_url)

    def test_should_approval_by_pdf_redirect_with_errors(self):
        url = resolve_url("admission:doctorate:approve-by-pdf", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        response = self.client.post(url, {})
        self.assertRedirects(response, self.detail_url)

    def test_should_set_reference_promoter(self):
        url = resolve_url(
            "admission:doctorate:set-reference-promoter",
            pk="3c5cdc60-2537-4a12-a396-64d2e9e34876",
            uuid="uuid-9876543210",
        )
        response = self.client.post(url, {})
        self.assertRedirects(response, self.detail_url)
        self.assertTrue(self.mock_api.return_value.set_reference_promoter.called)

        self.mock_api.return_value.set_reference_promoter.side_effect = MultipleApiBusinessException(
            exceptions={
                ApiBusinessException(status_code=42, detail="Something went wrong"),
            }
        )
        response = self.client.post(url, {})
        self.assertRedirects(response, self.detail_url)

    def test_should_resend_invite(self):
        url = resolve_url(
            "admission:doctorate:resend-invite",
            pk="3c5cdc60-2537-4a12-a396-64d2e9e34876",
            uuid="uuid-9876543210",
        )
        response = self.client.post(url, {}, follow=True)
        self.assertRedirects(response, self.detail_url)
        self.assertContains(response, _("An invitation has been sent again."))
        self.assertTrue(self.mock_api.return_value.update_signatures.called)

        self.mock_api.return_value.update_signatures.side_effect = MultipleApiBusinessException(
            exceptions={ApiBusinessException(42, "Something went wrong")}
        )
        response = self.client.post(url, {}, follow=True)
        self.assertRedirects(response, self.detail_url)
        self.assertNotContains(response, _("An invitation has been sent again."))

    def test_should_external_promoter_access_info(self):
        self.client.logout()
        response = self.client.get(self.external_url)
        self.assertContains(response, "REF7777")
        self.assertContains(response, "test_intitule")
        # Display the signatures
        self.assertContains(response, "Troufignon")
        self.assertContains(response, ChoixEtatSignature.APPROVED.value)
        self.assertContains(response, "A public comment to display")
        self.assertContains(response, ChoixEtatSignature.DECLINED.value)
        self.assertNotContains(response, _("Research institute"))
        self.assertEqual(self.mock_api.call_args[0][0].configuration.api_key, self.external_api_token_header)
        self.mock_api.return_value.get_external_proposition.assert_called()

    def test_should_external_promoter_approve_proposition(self):
        self.client.logout()
        response = self.client.post(
            self.external_url,
            {
                'decision': DecisionApprovalEnum.APPROVED.name,
                'commentaire_interne': "The internal comment",
                'commentaire_externe': "The public comment",
                'motif_refus': "The reason",  # The reason is provided but will not be used
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.mock_api.call_args[0][0].configuration.api_key, self.external_api_token_header)
        self.mock_api.return_value.approve_external_proposition.assert_called_with(
            uuid=self.pk,
            approuver_proposition_command=ApprouverPropositionCommand(
                **{
                    'commentaire_interne': "The internal comment",
                    'commentaire_externe': "The public comment",
                    'uuid_membre': "promoter-token",
                }
            ),
            **self.external_kwargs,
        )

    def test_should_external_promoter_reject_proposition(self):
        self.client.logout()
        # All data is provided and the proposition is rejected
        response = self.client.post(
            self.external_url,
            {
                'decision': DecisionApprovalEnum.DECLINED.name,
                'commentaire_interne': "The internal comment",
                'commentaire_externe': "The public comment",
                'motif_refus': "The reason",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.mock_api.call_args[0][0].configuration.api_key, self.external_api_token_header)
        self.mock_api.return_value.reject_external_proposition.assert_called_with(
            uuid=self.pk,
            refuser_proposition_command=RefuserPropositionCommand(
                **{
                    'commentaire_interne': "The internal comment",
                    'commentaire_externe': "The public comment",
                    'motif_refus': "The reason",
                    'uuid_membre': "promoter-token",
                }
            ),
            **self.external_kwargs,
        )

    def test_should_external_promoter_error_with_no_decision(self):
        self.client.logout()
        # The decision is missing
        response = self.client.post(
            self.external_url,
            {
                'commentaire_interne': "The internal comment",
                'commentaire_externe': "The public comment",
                'motif_refus': "The reason",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('decision', response.context['approval_form'].errors)

        self.mock_api.return_value.reject_proposition.assert_not_called()
        self.mock_api.return_value.approve_proposition.assert_not_called()

    def test_should_external_promoter_reject_with_error_when_no_motive(self):
        self.client.logout()
        response = self.client.post(
            self.external_url,
            {
                'decision': DecisionApprovalEnum.DECLINED.name,
                'commentaire_interne': "The internal comment",
                'commentaire_externe': "The public comment",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('motif_refus', response.context['approval_form'].errors)

        self.mock_api.return_value.reject_proposition.assert_not_called()
        self.mock_api.return_value.approve_proposition.assert_not_called()
