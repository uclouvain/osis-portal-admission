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
import uuid
from django.test import TestCase
from unittest.mock import Mock, ANY, patch

from admission.contrib.enums import (
    ChoixStatutPropositionDoctorale,
    ChoixStatutPropositionContinue,
    ChoixStatutPropositionGenerale,
)
from admission.contrib.enums.scholarship import TypeBourse
from admission.contrib.enums.specific_question import TypeItemFormulaire
from admission.contrib.enums.training_choice import TrainingType
from admission.contrib.forms import PDF_MIME_TYPE
from admission.contrib.forms.project import COMMISSION_CDSS, SCIENCE_DOCTORATE
from admission.tests.utils import MockCountry
from base.tests.factories.person import PersonFactory
from osis_admission_sdk.model.campus import Campus
from osis_admission_sdk.model.formation_continue_dto import FormationContinueDTO
from osis_admission_sdk.model.formation_generale_dto import FormationGeneraleDTO
from osis_admission_sdk.model.scholarship import Scholarship
from osis_admission_sdk.model.specific_question import SpecificQuestion


class AdmissionTrainingChoiceFormViewTestCase(TestCase):
    @classmethod
    def get_training(cls, acronym, year, **kwargs):
        return {
            'TR1': Mock(
                to_dict=lambda: {
                    'acronym': 'TR1',
                    'academic_year': year,
                    'title': 'Formation 1',
                    'title_en': 'Training 1',
                    'main_teaching_campus': {
                        'name': 'Louvain-La-Neuve',
                    },
                    'education_group_type': 'MASTER_MA_120',
                    'management_entity': 'ME1',
                },
            ),
            'TR2': Mock(
                to_dict=lambda: {
                    'acronym': 'TR2',
                    'academic_year': year,
                    'title': 'Formation 2',
                    'title_en': 'Training 2',
                    'main_teaching_campus': {
                        'name': 'Louvain-La-Neuve',
                    },
                    'education_group_type': 'CERTIFICATE_OF_PARTICIPATION',
                    'management_entity': 'ME2',
                },
            ),
            'TR3': Mock(
                to_dict=lambda: {
                    'acronym': 'TR3',
                    'academic_year': year,
                    'title': 'Formation 3',
                    'title_en': 'Training 3',
                    'main_teaching_campus': {
                        'name': 'Louvain-La-Neuve',
                    },
                    'education_group_type': 'PHD',
                    'management_entity': 'CDE',
                },
            ),
            'TR4': Mock(
                to_dict=lambda: {
                    'acronym': 'TR4',
                    'academic_year': year,
                    'title': 'Formation 4',
                    'title_en': 'Training 4',
                    'main_teaching_campus': {
                        'name': 'Louvain-La-Neuve',
                    },
                    'education_group_type': 'PHD',
                    'management_entity': 'CDSS',
                },
            ),
            'SC3DP': Mock(
                to_dict=lambda: {
                    'acronym': 'SC3DP',
                    'academic_year': year,
                    'title': 'Formation 5',
                    'title_en': 'Training 5',
                    'main_teaching_campus': {
                        'name': 'Louvain-La-Neuve',
                    },
                    'education_group_type': 'PHD',
                    'management_entity': 'ME3',
                },
            ),
        }.get(acronym)

    @classmethod
    def init_training_choice(cls, **kwargs):
        return {
            'uuid': cls.proposition_uuid,
        }

    @classmethod
    def get_scholarship(cls, uuid, **kwargs):
        return next((scholarship for scholarship in cls.mock_scholarships if scholarship.uuid == uuid), None)

    @classmethod
    def get_general_education_admission(cls, **kwargs):
        return cls.general_proposition

    @classmethod
    def get_doctorate_education_admission(cls, **kwargs):
        return cls.doctorate_proposition

    @classmethod
    def get_continuing_education_admission(cls, **kwargs):
        return cls.continuing_proposition

    @classmethod
    def get_campuses(cls, **kwargs):
        return cls.campuses

    @classmethod
    def get_scholarships(cls, **kwargs):
        return {
            'results': cls.mock_scholarships,
        }

    @classmethod
    def get_specific_questions(cls, **kwargs):
        return cls.specific_questions

    @classmethod
    def get_countries(cls, **kwargs):
        countries = [
            MockCountry(iso_code="FR", name="France", name_en="France", european_union=True),
            MockCountry(iso_code="BE", name="Belgique", name_en="Belgium", european_union=True),
            MockCountry(
                iso_code="US",
                name="États-Unis d'Amérique",
                name_en="United States of America",
                european_union=False,
            ),
        ]
        if kwargs.get("iso_code"):
            return Mock(results=[c for c in countries if c.iso_code == kwargs.get("iso_code")])
        return Mock(results=countries)

    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()
        cls.default_kwargs = {
            'accept_language': ANY,
            'x_user_first_name': ANY,
            'x_user_last_name': ANY,
            'x_user_email': ANY,
            'x_user_global_id': ANY,
        }
        cls.proposition_uuid = str(uuid.uuid4())
        cls.louvain_campus_uuid = str(uuid.uuid4())
        cls.mons_campus_uuid = str(uuid.uuid4())
        cls.first_question_uuid = str(uuid.uuid4())
        cls.first_erasmus_mundus_scholarship = Scholarship._from_openapi_data(
            uuid=str(uuid.uuid4()),
            short_name="EM-1",
            long_name="Erasmus Mundus 1",
            type=TypeBourse.ERASMUS_MUNDUS.name,
        )
        cls.second_erasmus_mundus_scholarship = Scholarship._from_openapi_data(
            uuid=str(uuid.uuid4()),
            short_name="EM-2",
            long_name="",
            type=TypeBourse.ERASMUS_MUNDUS.name,
        )
        cls.double_degree_scholarship = Scholarship._from_openapi_data(
            uuid=str(uuid.uuid4()),
            short_name="DD-1",
            long_name="",
            type=TypeBourse.DOUBLE_TRIPLE_DIPLOMATION.name,
        )
        cls.international_scholarship = Scholarship._from_openapi_data(
            uuid=str(uuid.uuid4()),
            short_name="IN-2",
            long_name="",
            type=TypeBourse.BOURSE_INTERNATIONALE_FORMATION_GENERALE.name,
        )

        cls.mock_scholarships = [
            cls.first_erasmus_mundus_scholarship,
            cls.second_erasmus_mundus_scholarship,
            cls.double_degree_scholarship,
            cls.international_scholarship,
        ]

        cls.general_proposition = Mock(
            uuid=cls.proposition_uuid,
            formation={
                'annee': 2020,
                'intitule': 'Formation',
                'campus': 'Louvain-La-Neuve',
                'sigle': 'TR1',
                'type': TrainingType.MASTER_M1.name,
                'sigle_entite_gestion': 'CMG',
                'campus_inscription': 'Mons',
            },
            reference='M-CMG20-000.001',
            matricule_candidat=cls.person.global_id,
            prenom_candidat=cls.person.first_name,
            nom_candidat=cls.person.last_name,
            statut=ChoixStatutPropositionGenerale.EN_BROUILLON.name,
            links={'update_specific_question': {'url': 'ok'}},
            erreurs={},
            bourse_double_diplome=Mock(
                uuid=cls.double_degree_scholarship.uuid,
                nom_court=cls.double_degree_scholarship.short_name,
                nom_long=cls.double_degree_scholarship.long_name,
                type=cls.double_degree_scholarship.type,
            ),
            bourse_internationale=Mock(
                uuid=cls.international_scholarship.uuid,
                nom_court=cls.international_scholarship.short_name,
                nom_long=cls.international_scholarship.long_name,
                type=cls.international_scholarship.type,
            ),
            bourse_erasmus_mundus=Mock(
                uuid=cls.first_erasmus_mundus_scholarship.uuid,
                nom_court=cls.first_erasmus_mundus_scholarship.short_name,
                nom_long=cls.first_erasmus_mundus_scholarship.long_name,
                type=cls.first_erasmus_mundus_scholarship.type,
            ),
            reponses_questions_specifiques={
                cls.first_question_uuid: 'My answer',
            },
        )
        cls.bachelor_proposition = Mock(
            uuid=cls.proposition_uuid,
            formation={
                'annee': 2020,
                'intitule': 'Formation',
                'campus': 'Louvain-La-Neuve',
                'sigle': 'TR0',
                'type': TrainingType.BACHELOR.name,
                'sigle_entite_gestion': 'CMG',
                'campus_inscription': 'Mons',
            },
            reference='M-CMG20-000.002',
            matricule_candidat=cls.person.global_id,
            prenom_candidat=cls.person.first_name,
            nom_candidat=cls.person.last_name,
            statut=ChoixStatutPropositionGenerale.EN_BROUILLON.name,
            links={'update_specific_question': {'url': 'ok'}},
            erreurs={},
            bourse_double_diplome=None,
            bourse_internationale=None,
            bourse_erasmus_mundus=None,
            reponses_questions_specifiques={
                cls.first_question_uuid: 'My answer',
            },
        )

        cls.continuing_proposition_dict = {
            'uuid': cls.proposition_uuid,
            'reference': 'M-CMC20-000.003',
            'formation': {
                'annee': 2020,
                'intitule': 'Formation',
                'campus': 'Louvain-La-Neuve',
                'sigle': 'TR2',
                'type': TrainingType.CERTIFICATE_OF_PARTICIPATION.name,
                'sigle_entite_gestion': 'CMC',
                'campus_inscription': 'Mons',
            },
            'matricule_candidat': cls.person.global_id,
            'prenom_candidat': cls.person.first_name,
            'nom_candidat': cls.person.last_name,
            'statut': ChoixStatutPropositionContinue.EN_BROUILLON.name,
            'links': {'update_specific_question': {'url': 'ok'}},
            'erreurs': {},
            'reponses_questions_specifiques': {
                cls.first_question_uuid: 'My answer',
            },
            'inscription_a_titre': 'PROFESSIONNEL',
            'nom_siege_social': 'UCL',
            'numero_unique_entreprise': '1',
            'numero_tva_entreprise': '1A',
            'adresse_mail_professionnelle': 'john.doe@example.be',
            'type_adresse_facturation': 'AUTRE',
            'adresse_facturation': {
                'destinataire': 'Mr Doe',
                'rue': 'Rue des Pins',
                'numero_rue': '10',
                'lieu_dit': 'Dit',
                'boite_postale': 'B1',
                'code_postal': '1348',
                'ville': 'Louvain-La-Neuve',
                'pays': 'BE',
            },
            'pays_nationalite': 'FR',
            'pays_nationalite_ue_candidat': True,
            'copie_titre_sejour': [],
        }
        cls.continuing_proposition = Mock(
            uuid=cls.proposition_uuid,
            formation={
                'annee': 2020,
                'intitule': 'Formation',
                'campus': 'Louvain-La-Neuve',
                'sigle': 'TR2',
                'type': TrainingType.CERTIFICATE_OF_PARTICIPATION.name,
                'sigle_entite_gestion': 'CMC',
                'campus_inscription': 'Mons',
            },
            reference='M-CMC20-000.003',
            matricule_candidat=cls.person.global_id,
            prenom_candidat=cls.person.first_name,
            nom_candidat=cls.person.last_name,
            statut=ChoixStatutPropositionContinue.EN_BROUILLON.name,
            links={'update_specific_question': {'url': 'ok'}},
            erreurs={},
            reponses_questions_specifiques={
                cls.first_question_uuid: 'My answer',
            },
            inscription_a_titre='PROFESSIONNEL',
            nom_siege_social='UCL',
            numero_unique_entreprise='1',
            numero_tva_entreprise='1A',
            adresse_mail_professionnelle='john.doe@example.be',
            type_adresse_facturation='AUTRE',
            adresse_facturation=Mock(
                destinataire='Mr Doe',
                rue='Rue des Pins',
                numero_rue='10',
                lieu_dit='Dit',
                boite_postale='B1',
                code_postal='1348',
                ville='Louvain-La-Neuve',
                pays='BE',
            ),
            to_dict=lambda: cls.continuing_proposition_dict,
            pays_nationalite='FR',
            pays_nationalite_ue_candidat=True,
            copie_titre_sejour=[],
        )

        cls.doctorate_proposition = Mock(
            uuid=cls.proposition_uuid,
            doctorat={
                'annee': 2020,
                'intitule': 'Formation',
                'campus': 'Louvain-La-Neuve',
                'sigle': 'TR3',
                'type': TrainingType.PHD.name,
                'sigle_entite_gestion': 'CDE',
                'campus_inscription': 'Mons',
            },
            reference='M-CDE20-000.004',
            code_secteur_formation="SSH",
            documents_projet=[],
            graphe_gantt=[],
            proposition_programme_doctoral=[],
            projet_formation_complementaire=[],
            lettres_recommandation=[],
            links={'update_proposition': {'url': 'ok'}},
            commission_proximite='MANAGEMENT',
            statut=ChoixStatutPropositionDoctorale.EN_BROUILLON.name,
            bourse_erasmus_mundus=Mock(
                uuid=cls.first_erasmus_mundus_scholarship.uuid,
                nom_court=cls.first_erasmus_mundus_scholarship.short_name,
                nom_long=cls.first_erasmus_mundus_scholarship.long_name,
                type=cls.first_erasmus_mundus_scholarship.type,
            ),
            reponses_questions_specifiques={
                cls.first_question_uuid: 'My answer',
            },
        )

        cls.specific_questions = [
            SpecificQuestion._from_openapi_data(
                uuid=str(uuid.uuid4()),
                type=TypeItemFormulaire.MESSAGE.name,
                title={},
                text={'en': 'My message', 'fr-be': 'Mon message'},
                help_text={},
                configuration={},
                required=True,
                values=[],
            ),
            SpecificQuestion._from_openapi_data(
                uuid=cls.first_question_uuid,
                type=TypeItemFormulaire.TEXTE.name,
                title={'en': 'My first question', 'fr-be': 'Ma première question'},
                text={'en': 'Informations about the question', 'fr-be': 'Informations au sujet de la question'},
                help_text={'en': 'Write here', 'fr-be': 'Ecrivez-ici'},
                configuration={},
                required=True,
                values=[],
            ),
        ]

        cls.sectors = [
            Mock(sigle='SSH', intitule='Foobar'),
            Mock(sigle='SST', intitule='Barbaz'),
            Mock(sigle='SSS', intitule='Foobarbaz'),
        ]

        cls.doctorate_trainings = [
            Mock(
                sigle='FOOBAR',
                intitule='Foobar',
                annee=2021,
                sigle_entite_gestion="CDE",
                links=[],
                type=TrainingType.PHD.name,
                campus_inscription='Mons',
            ),
            Mock(
                sigle='FOOBARBAZ',
                intitule='Foobarbaz',
                annee=2021,
                sigle_entite_gestion=COMMISSION_CDSS,
                links=[],
                type=TrainingType.PHD.name,
                campus_inscription='Mons',
            ),
            Mock(
                sigle='BARBAZ',
                intitule='Barbaz',
                annee=2021,
                sigle_entite_gestion="AZERT",
                links=[],
                type=TrainingType.PHD.name,
                campus_inscription='Mons',
            ),
            Mock(
                sigle=SCIENCE_DOCTORATE,
                intitule='FooBarbaz',
                annee=2021,
                sigle_entite_gestion="AZERT",
                links=[],
                type=TrainingType.PHD.name,
                campus_inscription='Mons',
            ),
        ]

        cls.general_trainings = [
            FormationContinueDTO(
                sigle='FOOBAR',
                intitule='Foobar',
                annee=2021,
                campus="Louvain-La-Neuve",
                type=TrainingType.CERTIFICATE_OF_PARTICIPATION.name,
                code_domaine='10C',
                sigle_entite_gestion='CMG',
                campus_inscription='Mons',
            ),
            FormationContinueDTO(
                sigle='BARBAZ',
                intitule='Barbaz',
                annee=2021,
                campus="Mons",
                type=TrainingType.CERTIFICATE_OF_PARTICIPATION.name,
                code_domaine='10C',
                sigle_entite_gestion='CMG',
                campus_inscription='Mons',
            ),
        ]

        cls.continuing_trainings = [
            FormationGeneraleDTO(
                sigle='FOOBAR',
                intitule='Foobar',
                annee=2021,
                campus="Louvain-La-Neuve",
                type=TrainingType.MASTER_M1.name,
                code_domaine='10C',
                sigle_entite_gestion='CMC',
                campus_inscription='Mons',
            ),
            FormationGeneraleDTO(
                sigle='BARBAZ',
                intitule='Barbaz',
                annee=2021,
                campus="Mons",
                type=TrainingType.MASTER_M1.name,
                code_domaine='10C',
                sigle_entite_gestion='CMC',
                campus_inscription='Mons',
            ),
        ]

        cls.campuses = [
            Campus._from_openapi_data(name='Louvain-La-Neuve', uuid=cls.louvain_campus_uuid),
            Campus._from_openapi_data(name='Mons', uuid=cls.mons_campus_uuid),
        ]

    def setUp(self):
        # Mock proposition sdk api
        propositions_api_patcher = patch("osis_admission_sdk.api.propositions_api.PropositionsApi")
        self.mock_proposition_api = propositions_api_patcher.start()
        self.mock_proposition_api.return_value.retrieve_general_education_proposition.side_effect = (
            self.get_general_education_admission
        )
        self.mock_proposition_api.return_value.retrieve_proposition.side_effect = self.get_doctorate_education_admission
        self.mock_proposition_api.return_value.retrieve_continuing_education_proposition.return_value = (
            self.continuing_proposition
        )
        self.mock_proposition_api.return_value.create_continuing_training_choice.side_effect = self.init_training_choice
        self.mock_proposition_api.return_value.create_general_training_choice.side_effect = self.init_training_choice
        self.mock_proposition_api.return_value.create_doctorate_training_choice.side_effect = self.init_training_choice
        self.mock_proposition_api.return_value.update_general_training_choice.side_effect = self.init_training_choice
        self.mock_proposition_api.return_value.update_continuing_training_choice.side_effect = self.init_training_choice
        self.mock_proposition_api.return_value.update_doctorate_training_choice.side_effect = self.init_training_choice
        self.mock_proposition_api.return_value.list_doctorate_specific_questions.side_effect = (
            self.get_specific_questions
        )
        self.mock_proposition_api.return_value.list_general_specific_questions.side_effect = self.get_specific_questions
        self.mock_proposition_api.return_value.list_continuing_specific_questions.side_effect = (
            self.get_specific_questions
        )
        self.addCleanup(propositions_api_patcher.stop)

        # Mock autocomplete sdk api
        autocomplete_api_patcher = patch("osis_admission_sdk.api.autocomplete_api.AutocompleteApi")
        self.mock_autocomplete_api = autocomplete_api_patcher.start()
        self.mock_autocomplete_api.return_value.list_sector_dtos.return_value = self.sectors
        self.mock_autocomplete_api.return_value.list_doctorat_dtos.return_value = self.doctorate_trainings
        self.mock_autocomplete_api.return_value.list_formation_generale_dtos.return_value = self.continuing_trainings
        self.mock_autocomplete_api.return_value.list_formation_generale_dtos.return_value = self.general_trainings
        self.mock_autocomplete_api.return_value.list_scholarships.return_value = {
            'results': self.mock_scholarships,
        }
        self.addCleanup(autocomplete_api_patcher.stop)

        # Mock scholarship sdk api
        scholarships_api_patcher = patch("osis_admission_sdk.api.scholarship_api.ScholarshipApi")
        self.mock_scholarship_api = scholarships_api_patcher.start()
        self.mock_scholarship_api.return_value.retrieve_scholarship.side_effect = self.get_scholarship
        self.addCleanup(scholarships_api_patcher.stop)

        # Mock education group sdk api
        education_group_api_patcher = patch("osis_education_group_sdk.api.trainings_api.TrainingsApi")
        self.mock_education_group_api = education_group_api_patcher.start()
        self.mock_education_group_api.return_value.trainings_read.side_effect = self.get_training
        self.addCleanup(education_group_api_patcher.stop)

        # Mock campus sdk api
        campus_api_patcher = patch("osis_admission_sdk.api.campus_api.CampusApi")
        self.mock_campus_api = campus_api_patcher.start()
        self.mock_campus_api.return_value.list_campus.side_effect = self.get_campuses
        self.addCleanup(campus_api_patcher.stop)

        countries_api_patcher = patch("osis_reference_sdk.api.countries_api.CountriesApi")
        self.mock_countries_api = countries_api_patcher.start()

        # Mock country sdk api
        self.mock_countries_api.return_value.countries_list.side_effect = self.get_countries
        self.addCleanup(countries_api_patcher.stop)

        # Mock document api
        patcher = patch('osis_document.api.utils.get_remote_token', return_value='foobar')
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch(
            'osis_document.api.utils.get_remote_metadata',
            return_value={'name': 'myfile', 'mimetype': PDF_MIME_TYPE},
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        self.client.force_login(self.person.user)
