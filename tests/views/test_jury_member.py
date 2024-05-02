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
from django.test import TestCase

from admission.contrib.enums import (
    RoleJury,
    TitreMembre,
    GenreMembre,
)
from admission.contrib.forms.jury.membre import JuryMembreForm
from base.tests.factories.person import PersonFactory
from reference.tests.factories.country import CountryFactory


class JuryMembreUpdateTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()
        cls.country = CountryFactory()

    def setUp(self):
        self.url = resolve_url(
            "admission:doctorate:update:jury-member:update",
            pk="3c5cdc60-2537-4a12-a396-64d2e9e34876",
            member_pk="123cdc60-2537-4a12-a396-64d2e9e34876",
        )

        self.client.force_login(self.person.user)

        api_patcher = patch("osis_admission_sdk.api.propositions_api.PropositionsApi")
        self.mock_api = api_patcher.start()
        self.addCleanup(api_patcher.stop)

        self.mock_api.return_value.retrieve_doctorate_dto.return_value = Mock(
            links={'retrieve_jury_preparation': {'url': 'ok'}, 'update_jury_preparation': {'url': 'ok'}},
            erreurs=[],
        )
        self.mock_api.return_value.retrieve_jury_preparation.return_value = Mock(
            uuid="3c5cdc60-2537-4a12-a396-64d2e9e34876",
        )
        self.mock_api.return_value.retrieve_jury_member.return_value = Mock(
            uuid="123cdc60-2537-4a12-a396-64d2e9e34876",
            role=RoleJury.MEMBRE.name,
            est_promoteur=False,
            matricule='',
            institution='Université',
            autre_institution='',
            pays=self.country.name,
            nom='nom-detail',
            prenom='prenom',
            titre=TitreMembre.DOCTEUR.name,
            justification_non_docteur='',
            genre=GenreMembre.AUTRE.name,
            email='email',
        )

    def test_jury_membre_change_get_form(self):
        response = self.client.get(self.url)
        self.assertContains(response, "nom-detail")
        self.assertContains(response, '<form class="osis-form"')
        self.assertEqual(response.context['form'].initial['nom'], "nom-detail")

    def test_jury_membre_change_post_with_data(self, *args):
        response = self.client.post(
            self.url,
            {
                "institution_principale": JuryMembreForm.InstitutionPrincipaleChoices.OTHER.name,
                "matricule": '',
                "institution": 'Université autre',
                "autre_institution": '',
                "pays": self.country.name,
                "nom": 'nom-nouveau',
                "prenom": 'prenom',
                "titre": TitreMembre.DOCTEUR.name,
                "justification_non_docteur": '',
                "genre": GenreMembre.AUTRE.name,
                "email": 'email@example.org',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.mock_api.return_value.update_jury_member.assert_called()
        last_call_kwargs = self.mock_api.return_value.update_jury_member.call_args[1]
        self.assertIn("nom", last_call_kwargs['modifier_membre_command'])
        self.assertEqual(last_call_kwargs['modifier_membre_command']['nom'], "nom-nouveau")


class JuryMemberRemoveTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()

    def setUp(self):
        self.url = resolve_url(
            "admission:doctorate:update:jury-member:remove",
            pk="3c5cdc60-2537-4a12-a396-64d2e9e34876",
            member_pk="123cdc60-2537-4a12-a396-64d2e9e34876",
        )
        self.client.force_login(self.person.user)

        api_patcher = patch("osis_admission_sdk.api.propositions_api.PropositionsApi")
        self.mock_api = api_patcher.start()
        self.addCleanup(api_patcher.stop)

        self.mock_api.return_value.retrieve_doctorate_dto.return_value = Mock(
            links={'list_jury_members': {'url': 'ok'}, 'create_jury_member': {'url': 'ok'}},
            erreurs=[],
        )
        self.mock_api.return_value.retrieve_jury_preparation.return_value = Mock(
            uuid="3c5cdc60-2537-4a12-a396-64d2e9e34876",
        )
        self.mock_api.return_value.retrieve_jury_member.return_value = Mock(
            uuid="3c5cdc60-2537-4a12-a396-64d2e9e34876",
            role=RoleJury.MEMBRE.name,
            est_promoteur=False,
            matricule='',
            institution='Université',
            autre_institution='',
            pays='pays',
            nom='nom',
            prenom='prenom',
            titre=TitreMembre.DOCTEUR.name,
            justification_non_docteur='',
            genre=GenreMembre.AUTRE.name,
            email='email',
        )

    def test_jury_remove_post(self, *args):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.mock_api.return_value.remove_jury_member.assert_called()


class JuryMemberChangeRoleTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()

    def setUp(self):
        self.url = resolve_url(
            "admission:doctorate:update:jury-member:change-role",
            pk="3c5cdc60-2537-4a12-a396-64d2e9e34876",
            member_pk="123cdc60-2537-4a12-a396-64d2e9e34876",
        )
        self.client.force_login(self.person.user)

        api_patcher = patch("osis_admission_sdk.api.propositions_api.PropositionsApi")
        self.mock_api = api_patcher.start()
        self.addCleanup(api_patcher.stop)

        self.mock_api.return_value.retrieve_doctorate_dto.return_value = Mock(
            links={'list_jury_members': {'url': 'ok'}, 'create_jury_member': {'url': 'ok'}},
            erreurs=[],
        )
        self.mock_api.return_value.retrieve_jury_preparation.return_value = Mock(
            uuid="3c5cdc60-2537-4a12-a396-64d2e9e34876",
        )
        self.mock_api.return_value.retrieve_jury_member.return_value = Mock(
            uuid="3c5cdc60-2537-4a12-a396-64d2e9e34876",
            role=RoleJury.MEMBRE.name,
            est_promoteur=False,
            matricule='',
            institution='Université',
            autre_institution='',
            pays='pays',
            nom='nom',
            prenom='prenom',
            titre=TitreMembre.DOCTEUR.name,
            justification_non_docteur='',
            genre=GenreMembre.AUTRE.name,
            email='email',
        )

    def test_jury_create_with_data(self, *args):
        response = self.client.post(
            self.url,
            {
                "role": RoleJury.PRESIDENT.name,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.mock_api.return_value.update_role_jury_member.assert_called()
        last_call_kwargs = self.mock_api.return_value.update_role_jury_member.call_args[1]
        self.assertIn("role", last_call_kwargs['modifier_role_membre_command'])
        self.assertEqual(last_call_kwargs['modifier_role_membre_command']['role'], RoleJury.PRESIDENT.name)
