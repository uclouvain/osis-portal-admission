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
from django.test import TestCase

from admission.contrib.enums import (
    FormuleDefense,
    ChoixLangueRedactionThese,
    RoleJury,
    TitreMembre,
    GenreMembre,
)
from admission.contrib.forms.jury.membre import JuryMembreForm
from base.tests.factories.person import PersonFactory


class JuryPreparationTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()

    def setUp(self):
        self.url = resolve_url("admission:doctorate:update:jury-preparation", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        self.client.force_login(self.person.user)

        api_patcher = patch("osis_admission_sdk.api.propositions_api.PropositionsApi")
        self.mock_api = api_patcher.start()
        self.addCleanup(api_patcher.stop)

        self.mock_api.return_value.retrieve_doctorate_dto.return_value = Mock(
            links={'retrieve_jury_preparation': {'url': 'ok'}, 'update_jury_preparation': {'url': 'ok'}},
            erreurs=[],
        )
        self.mock_api.return_value.retrieve_jury_preparation.return_value = Mock(
            titre_propose="titre",
            formule_defense=FormuleDefense.FORMULE_1.name,
            date_indicative=datetime.date(2023, 4, 19),
            langue_redaction=ChoixLangueRedactionThese.FRENCH.name,
            langue_soutenance=ChoixLangueRedactionThese.FRENCH.name,
            commentaire="Foobar",
        )

    def test_update_no_permission(self):
        self.mock_api.return_value.retrieve_doctorate_dto.return_value.links = {
            'update_jury_preparation': {'error': 'no access'},
        }
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_jury_get(self):
        url = resolve_url("admission:doctorate:jury-preparation", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        response = self.client.get(url)
        self.assertContains(response, "Foobar")

    def test_jury_get_form(self):
        response = self.client.get(self.url)
        self.assertContains(response, "Foobar")
        self.assertContains(response, '<form class="osis-form"')
        self.assertEqual(response.context['form'].initial['titre_propose'], "titre")

    def test_jury_update_with_data(self, *args):
        response = self.client.post(
            self.url,
            {
                "titre_propose": "titre bis",
                "formule_defense": FormuleDefense.FORMULE_1.name,
                "date_indicative": '2023-04-01',
                "langue_redaction": ChoixLangueRedactionThese.FRENCH.name,
                "langue_soutenance": ChoixLangueRedactionThese.FRENCH.name,
                "commentaire": "Foobar bis",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.mock_api.return_value.update_jury_preparation.assert_called()
        last_call_kwargs = self.mock_api.return_value.update_jury_preparation.call_args[1]
        self.assertIn("titre_propose", last_call_kwargs['modifier_jury_command'])
        self.assertEqual(last_call_kwargs['modifier_jury_command']['titre_propose'], "titre bis")


class JuryTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()

    def setUp(self):
        self.url = resolve_url("admission:doctorate:jury", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
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
        self.mock_api.return_value.list_jury_members.return_value = [
            Mock(
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
            ),
            Mock(
                uuid="3c5cdc60-2537-4a12-a396-64d2e9e34876",
                role=RoleJury.SECRETAIRE.name,
                est_promoteur=True,
                matricule='0123456',
                institution='UCLouvain',
                autre_institution='',
                pays='pays',
                nom='autre nom',
                prenom='autre prenom',
                titre=TitreMembre.DOCTEUR.name,
                justification_non_docteur='',
                genre=GenreMembre.AUTRE.name,
                email='email',
            ),
        ]

    def test_jury_get(self):
        response = self.client.get(self.url)
        self.assertContains(response, "autre nom")

    def test_jury_create_with_data(self, *args):
        response = self.client.post(
            self.url,
            {
                "institution_principale": JuryMembreForm.InstitutionPrincipaleChoices.OTHER.name,
                "matricule": '',
                "institution": 'Université autre',
                "autre_institution": '',
                "pays": 'pays',
                "nom": 'nom',
                "prenom": 'prenom',
                "titre": TitreMembre.DOCTEUR.name,
                "justification_non_docteur": '',
                "genre": GenreMembre.AUTRE.name,
                "email": 'email@example.org',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.mock_api.return_value.create_jury_members.assert_called()
        last_call_kwargs = self.mock_api.return_value.create_jury_members.call_args[1]
        self.assertIn("matricule", last_call_kwargs['ajouter_membre_command'])
        self.assertEqual(last_call_kwargs['ajouter_membre_command']['email'], "email@example.org")
