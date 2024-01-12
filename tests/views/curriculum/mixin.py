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

import datetime
import uuid
from unittest.mock import ANY, patch, MagicMock

from django.http import Http404
from django.test import TestCase, override_settings
from osis_admission_sdk.model.action_link import ActionLink
from osis_admission_sdk.model.activity_sector import ActivitySector
from osis_admission_sdk.model.activity_type import ActivityType
from osis_admission_sdk.model.continuing_education_proposition_dto import ContinuingEducationPropositionDTO
from osis_admission_sdk.model.continuing_education_proposition_dto_links import ContinuingEducationPropositionDTOLinks
from osis_admission_sdk.model.curriculum_details_educational_experiences import CurriculumDetailsEducationalExperiences
from osis_admission_sdk.model.curriculum_details_educationalexperienceyear_set import (
    CurriculumDetailsEducationalexperienceyearSet,
)
from osis_admission_sdk.model.curriculum_details_professional_experiences import (
    CurriculumDetailsProfessionalExperiences,
)
from osis_admission_sdk.model.doctorate_proposition_dto import DoctoratePropositionDTO
from osis_admission_sdk.model.doctorate_proposition_dto_links import DoctoratePropositionDTOLinks
from osis_admission_sdk.model.educational_experience import EducationalExperience
from osis_admission_sdk.model.educational_experience_educationalexperienceyear_set import (
    EducationalExperienceEducationalexperienceyearSet,
)
from osis_admission_sdk.model.evaluation_system import EvaluationSystem
from osis_admission_sdk.model.general_education_proposition_dto import GeneralEducationPropositionDTO
from osis_admission_sdk.model.general_education_proposition_dto_links import GeneralEducationPropositionDTOLinks
from osis_admission_sdk.model.grade import Grade
from osis_admission_sdk.model.professional_experience import ProfessionalExperience
from osis_admission_sdk.model.proposition_search_doctorat import PropositionSearchDoctorat
from osis_admission_sdk.model.proposition_search_formation import PropositionSearchFormation
from osis_admission_sdk.model.result import Result
from osis_admission_sdk.model.teaching_type_enum import TeachingTypeEnum
from osis_admission_sdk.model.transcript_type import TranscriptType
from osis_reference_sdk.model.academic_year import AcademicYear
from osis_reference_sdk.model.country import Country
from osis_reference_sdk.model.diploma import Diploma
from osis_reference_sdk.model.language import Language
from osis_reference_sdk.model.paginated_country import PaginatedCountry
from osis_reference_sdk.model.paginated_diploma import PaginatedDiploma
from osis_reference_sdk.model.paginated_language import PaginatedLanguage
from osis_reference_sdk.model.paginated_superior_non_university import PaginatedSuperiorNonUniversity
from osis_reference_sdk.model.paginated_university import PaginatedUniversity
from osis_reference_sdk.model.superior_non_university import SuperiorNonUniversity
from osis_reference_sdk.model.university import University

from admission.contrib.enums.admission_type import AdmissionType
from admission.contrib.enums.projet import (
    ChoixStatutPropositionDoctorale,
    ChoixStatutPropositionGenerale,
    ChoixStatutPropositionContinue,
)
from admission.contrib.enums.state_iufc import StateIUFC
from admission.contrib.enums.training_choice import TrainingType
from admission.contrib.forms import PDF_MIME_TYPE
from admission.tests import get_paginated_years
from base.tests.factories.person import PersonFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class MixinTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()

        # Countries
        cls.be_country = Country(iso_code='BE', name='Belgique', name_en='Belgium', european_union=True)
        cls.ue_country = Country(iso_code='FR', name='France', name_en='France', european_union=True)
        cls.not_ue_country = Country(
            iso_code='US',
            name='Etats-Unis d\'Amérique',
            name_en='United States of America',
            european_union=False,
        )
        cls.first_question_uuid = str(uuid.uuid4())
        cls.document_uuid = str(uuid.uuid4())

        # Languages
        cls.language_without_translation = Language(code='FR', name='Français', name_en='French')
        cls.language_with_translation = Language(code='IS', name='Islandais', name_en='Icelandic')

        # Diplomas
        cls.first_diploma = Diploma(uuid=str(uuid.uuid4()), title="Computer science")
        cls.second_diploma = Diploma(uuid=str(uuid.uuid4()), title="Biology")

        # Institute
        cls.institute = SuperiorNonUniversity(
            uuid=str(uuid.uuid4()),
            name="Institute of Technology",
            city="Louvain-la-Neuve",
            zipcode="1348",
            street="Boulevard de l'Université",
            street_number="1",
        )
        cls.university = University(
            uuid=str(uuid.uuid4()),
            name="University of Technology",
            city="Louvain-la-Neuve",
            zipcode="1348",
            street="Boulevard de l'Université",
            street_number="2",
        )

        # Academic years
        cls.academic_year_2018 = AcademicYear(
            year=2018,
            start_date=datetime.date(2018, 9, 15),
            end_date=datetime.date(2019, 7, 5),
        )
        cls.academic_year_2019 = AcademicYear(
            year=2019,
            start_date=datetime.date(2019, 9, 15),
            end_date=datetime.date(2020, 7, 5),
        )
        cls.academic_year_2020 = AcademicYear(
            year=2020,
            start_date=datetime.date(2020, 9, 15),
            end_date=datetime.date(2021, 7, 5),
        )

        cls.educational_experience = EducationalExperience._from_openapi_data(
            country=cls.be_country.iso_code,
            institute=cls.institute.uuid,
            institute_name='UCL',
            institute_address='Place de l\'Université',
            program=cls.first_diploma.uuid,
            education_name='Other computer science',
            study_system=TeachingTypeEnum(value='FULL_TIME'),
            evaluation_type=EvaluationSystem(value='ECTS_CREDITS'),
            linguistic_regime=cls.language_without_translation.code,
            transcript_type=TranscriptType(value='ONE_FOR_ALL_YEARS'),
            obtained_diploma=True,
            obtained_grade=Grade(value='GREAT_DISTINCTION'),
            graduate_degree=['f1.pdf'],
            graduate_degree_translation=['f11.pdf'],
            transcript=['f2.pdf'],
            transcript_translation=['f22.pdf'],
            rank_in_diploma='10 on 100',
            expected_graduation_date=datetime.date(2022, 8, 30),
            dissertation_title='Title',
            dissertation_score='15/20',
            dissertation_summary=[cls.document_uuid],
            uuid=str(uuid.uuid4()),
            educationalexperienceyear_set=[
                EducationalExperienceEducationalexperienceyearSet(
                    academic_year=cls.academic_year_2020.year,
                    result=Result(value='SUCCESS'),
                    graduate_degree=['f1_2020.pdf'],
                    graduate_degree_translation=['f11_2020.pdf'],
                ),
                EducationalExperienceEducationalexperienceyearSet(
                    academic_year=cls.academic_year_2018.year,
                    result=Result(value='SUCCESS'),
                    graduate_degree=['f1_2018.pdf'],
                    graduate_degree_translation=['f11_2018.pdf'],
                ),
            ],
            valuated_from_trainings=[],
        )

        cls.lite_educational_experience = CurriculumDetailsEducationalExperiences._from_openapi_data(
            uuid=cls.educational_experience.uuid,
            institute_name=cls.educational_experience.institute_name,
            program=cls.educational_experience.program,
            education_name=cls.educational_experience.education_name,
            educationalexperienceyear_set=[
                CurriculumDetailsEducationalexperienceyearSet(
                    academic_year=cls.academic_year_2020.year,
                    result=Result(value='SUCCESS'),
                ),
                CurriculumDetailsEducationalexperienceyearSet(
                    academic_year=cls.academic_year_2018.year,
                    result=Result(value='WAITING_RESULT'),
                ),
            ],
            country=cls.be_country.iso_code,
            valuated_from_trainings=[],
            obtained_diploma=True,
        )
        cls.foreign_lite_educational_experience = CurriculumDetailsEducationalExperiences._from_openapi_data(
            uuid=cls.educational_experience.uuid,
            institute_name=cls.educational_experience.institute_name,
            program=cls.educational_experience.program,
            education_name=cls.educational_experience.education_name,
            educationalexperienceyear_set=[
                CurriculumDetailsEducationalexperienceyearSet(
                    academic_year=cls.academic_year_2020.year,
                    result=Result(value='SUCCESS'),
                ),
            ],
            country=cls.not_ue_country.iso_code,
            valuated_from_trainings=[],
            obtained_diploma=True,
        )

        cls.professional_experience = ProfessionalExperience._from_openapi_data(
            institute_name='First institute',
            start_date=datetime.date(2020, 1, 1),
            end_date=datetime.date(2021, 1, 1),
            type=ActivityType(value='WORK'),
            role='Librarian',
            sector=ActivitySector(value='PUBLIC'),
            activity='Work - activity',
            uuid=str(uuid.uuid4()),
            certificate=[cls.document_uuid],
            valuated_from_trainings=[],
        )

        cls.lite_professional_experience = CurriculumDetailsProfessionalExperiences._from_openapi_data(
            uuid=cls.professional_experience.uuid,
            institute_name=cls.professional_experience.institute_name,
            type=cls.professional_experience.type,
            start_date=cls.professional_experience.start_date,
            end_date=cls.professional_experience.start_date,
            valuated_from_trainings=[],
        )

        # Proposition
        cls.proposition = DoctoratePropositionDTO._from_openapi_data(
            uuid=str(uuid.uuid4()),
            type_admission=AdmissionType.ADMISSION.name,
            reference='M-CDSS20-000.001',
            links=DoctoratePropositionDTOLinks(
                retrieve_curriculum=ActionLink(method='GET', url='url'),
                update_curriculum=ActionLink(method='POST', url='url'),
                update_specific_question=ActionLink(method='POST', url='url'),
                retrieve_specific_question=ActionLink(method='GET', url='url'),
                update_accounting=ActionLink(method='POST', url='url'),
                retrieve_accounting=ActionLink(method='POST', url='url'),
            ),
            date_fin_pot=None,
            doctorat=PropositionSearchDoctorat._from_openapi_data(
                sigle='CS1',
                annee=cls.academic_year_2020.year,
                intitule='Doctorate name',
                sigle_entite_gestion="CDSS",
                campus="Mons",
                type=TrainingType.PHD.name,
                campus_inscription="Mons",
            ),
            matricule_candidat=cls.person.global_id,
            code_secteur_formation='CS',
            intitule_secteur_formation='Computer science',
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
            reponses_questions_specifiques={},
            curriculum=['file1.pdf'],
            pdf_recapitulatif=[],
            nom_institut_these='',
            sigle_institut_these='',
        )

        cls.general_proposition = GeneralEducationPropositionDTO._from_openapi_data(
            uuid=str(uuid.uuid4()),
            formation=PropositionSearchFormation._from_openapi_data(
                annee=2020,
                intitule='Formation',
                intitule_fr='Formation',
                intitule_en='Course',
                campus='Louvain-La-Neuve',
                sigle='TR1',
                type=TrainingType.MASTER_M1.name,
                code_domaine='10C',
                sigle_entite_gestion="CMG",
                campus_inscription="Mons",
                code='TR1',
            ),
            reference='M-CMG20-000.002',
            matricule_candidat=cls.person.global_id,
            prenom_candidat=cls.person.first_name,
            nom_candidat=cls.person.last_name,
            statut=ChoixStatutPropositionGenerale.EN_BROUILLON.name,
            links=GeneralEducationPropositionDTOLinks(
                retrieve_curriculum=ActionLink(method='GET', url='url'),
                update_curriculum=ActionLink(method='POST', url='url'),
                update_specific_question=ActionLink(method='POST', url='url'),
                retrieve_specific_question=ActionLink(method='GET', url='url'),
                update_accounting=ActionLink(method='POST', url='url'),
                retrieve_accounting=ActionLink(method='POST', url='url'),
            ),
            date_fin_pot=None,
            erreurs=[],
            bourse_double_diplome=None,
            bourse_internationale=None,
            bourse_erasmus_mundus=None,
            reponses_questions_specifiques={
                cls.first_question_uuid: 'My answer',
            },
            curriculum=['file1.pdf'],
            creee_le=datetime.datetime(2022, 12, 1),
            equivalence_diplome=['file2.pdf'],
            pdf_recapitulatif=[],
            documents_additionnels=[],
            poste_diplomatique=None,
        )

        cls.continuing_proposition = ContinuingEducationPropositionDTO._from_openapi_data(
            uuid=str(uuid.uuid4()),
            reference='M-CMC20-000.003',
            formation=PropositionSearchFormation._from_openapi_data(
                annee=2020,
                intitule='Formation',
                intitule_fr='Formation',
                intitule_en='Course',
                campus='Louvain-La-Neuve',
                sigle='TR2',
                type=TrainingType.CERTIFICATE_OF_PARTICIPATION.name,
                code_domaine='10C',
                campus_inscription="Mons",
                sigle_entite_gestion="CMC",
                code='TR2',
            ),
            date_fin_pot=None,
            matricule_candidat=cls.person.global_id,
            prenom_candidat=cls.person.first_name,
            nom_candidat=cls.person.last_name,
            statut=ChoixStatutPropositionContinue.EN_BROUILLON.name,
            links=ContinuingEducationPropositionDTOLinks(
                retrieve_curriculum=ActionLink(method='GET', url='url'),
                update_curriculum=ActionLink(method='POST', url='url'),
                update_specific_question=ActionLink(method='POST', url='url'),
                retrieve_specific_question=ActionLink(method='GET', url='url'),
                update_accounting=ActionLink(method='POST', url='url'),
                retrieve_accounting=ActionLink(method='POST', url='url'),
            ),
            erreurs=[],
            reponses_questions_specifiques={},
            curriculum=['file1.pdf'],
            creee_le=datetime.datetime(2022, 12, 1),
            equivalence_diplome=['file2.pdf'],
            pays_nationalite_candidat='FR',
            pays_nationalite_ue_candidat=True,
            copie_titre_sejour=[],
            pdf_recapitulatif=[],
            documents_additionnels=[],
            motivations='Motivation',
            moyens_decouverte_formation=[],
            aide_a_la_formation=False,
            inscription_au_role_obligatoire=True,
            etat_formation=StateIUFC.OPEN.name,
        )

        cls.api_default_params = {
            'accept_language': ANY,
            'x_user_first_name': ANY,
            'x_user_last_name': ANY,
            'x_user_email': ANY,
            'x_user_global_id': ANY,
        }

    def mock_proposition_api(self):
        # Mock proposition api
        propositions_api_patcher = patch("osis_admission_sdk.api.propositions_api.PropositionsApi")
        self.mock_proposition_api = propositions_api_patcher.start()

        self.mock_proposition_api.return_value.retrieve_proposition.return_value = self.proposition
        self.mock_proposition_api.return_value.retrieve_general_education_proposition.return_value = (
            self.general_proposition
        )
        self.mock_proposition_api.return_value.retrieve_continuing_education_proposition.return_value = (
            self.continuing_proposition
        )
        self.addCleanup(propositions_api_patcher.stop)

    def mock_countries_api(self):
        # Mock countries api
        countries_api_patcher = patch("osis_reference_sdk.api.countries_api.CountriesApi")
        self.mock_countries_api = countries_api_patcher.start()

        def get_countries(**kwargs):
            countries = [self.be_country, self.ue_country, self.not_ue_country]

            if kwargs.get('iso_code'):
                return PaginatedCountry(results=[c for c in countries if c.iso_code == kwargs.get('iso_code')])

            return PaginatedCountry(results=countries)

        self.mock_countries_api.return_value.countries_list.side_effect = get_countries
        self.addCleanup(countries_api_patcher.stop)

    def mock_academic_years_api(self):
        # Mock academic years api
        academic_years_api_patcher = patch("osis_reference_sdk.api.academic_years_api.AcademicYearsApi")
        self.mock_academic_years_api = academic_years_api_patcher.start()

        current_year = datetime.date.today().year

        self.mock_academic_years_api.return_value.get_academic_years.return_value = get_paginated_years(
            current_year - 5,
            current_year + 2,
        )
        self.addCleanup(academic_years_api_patcher.stop)

    def mock_languages_api(self):
        languages_api_patcher = patch("osis_reference_sdk.api.languages_api.LanguagesApi")
        self.mock_languages_api = languages_api_patcher.start()

        def get_languages(**kwargs):
            languages = [self.language_without_translation, self.language_with_translation]

            if kwargs.get('code'):
                return PaginatedLanguage(results=[c for c in languages if c.code == kwargs.get('code')])

            return PaginatedLanguage(results=languages)

        self.mock_languages_api.return_value.languages_list.side_effect = get_languages
        self.addCleanup(languages_api_patcher.stop)

    def mock_documents_api(self):
        patcher = patch('osis_document.api.utils.get_remote_token', return_value='foobar')
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            'osis_document.api.utils.get_remote_metadata',
            return_value={'name': 'myfile', 'mimetype': PDF_MIME_TYPE},
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def mock_diplomas_api(self):
        diplomas_api_patcher = patch("osis_reference_sdk.api.diplomas_api.DiplomasApi")
        self.mock_diplomas_api = diplomas_api_patcher.start()

        def get_diploma(**kwargs):
            diploma_uuid = kwargs.get('uuid')
            return next(
                (diploma for diploma in [self.first_diploma, self.second_diploma] if diploma.uuid == diploma_uuid),
                None,
            )

        self.mock_diplomas_api.return_value.diplomas_list.return_value = PaginatedDiploma(
            results=[self.first_diploma, self.second_diploma]
        )

        self.mock_diplomas_api.return_value.diploma_read.side_effect = get_diploma
        self.addCleanup(diplomas_api_patcher.stop)

    def mock_superior_non_university_api(self):
        superior_non_universities_api_patcher = patch(
            "osis_reference_sdk.api.superior_non_universities_api.SuperiorNonUniversitiesApi",
        )
        self.mock_superior_non_universities_api = superior_non_universities_api_patcher.start()

        def get_institute(**kwargs):
            institute_uuid = kwargs.get('uuid')
            try:
                return next(institute for institute in [self.institute] if institute.uuid == institute_uuid)
            except StopIteration:
                raise Http404

        self.mock_superior_non_universities_api.return_value.superior_non_universities_list.return_value = (
            PaginatedSuperiorNonUniversity(results=[self.institute])
        )

        self.mock_superior_non_universities_api.return_value.superior_non_university_read.side_effect = get_institute
        self.addCleanup(superior_non_universities_api_patcher.stop)

    def mock_university_api(self):
        universities_api_patcher = patch("osis_reference_sdk.api.universities_api.UniversitiesApi")
        self.mock_universities_api = universities_api_patcher.start()

        def get_institute(**kwargs):
            institute_uuid = kwargs.get('uuid')
            try:
                return next(institute for institute in [self.university] if institute.uuid == institute_uuid)
            except StopIteration:
                raise Http404

        self.mock_universities_api.return_value.universities_list.return_value = PaginatedUniversity(
            results=[self.university]
        )

        self.mock_universities_api.return_value.university_read.side_effect = get_institute
        self.addCleanup(universities_api_patcher.stop)

    def mock_person_api(self):
        api_person_patcher = patch("osis_admission_sdk.api.person_api.PersonApi")
        self.mock_person_api = api_person_patcher.start()

        curriculum_data = MagicMock(
            educational_experiences=[self.lite_educational_experience],
            professional_experiences=[self.lite_professional_experience],
            minimal_date=datetime.date(self.academic_year_2020.year, 9, 1),
            maximal_date=datetime.date(2022, 11, 1),
            incomplete_periods=[
                'De Septembre 2020 à Janvier 2021',
                'De Septembre 2021 à Janvier 2022',
                'De Septembre 2022 à Octobre 2022',
            ],
            incomplete_experiences={
                self.educational_experience.uuid: ['Cette expérience académique est incomplète.'],
            },
        )
        person_api_return = self.mock_person_api.return_value

        person_api_return.retrieve_curriculum_details_admission.return_value = curriculum_data
        person_api_return.retrieve_curriculum_details_general_education_admission.return_value = curriculum_data
        person_api_return.retrieve_curriculum_details_continuing_education_admission.return_value = curriculum_data
        person_api_return.retrieve_curriculum_details.return_value = curriculum_data

        person_api_return.retrieve_educational_experience_admission.return_value = self.educational_experience
        person_api_return.retrieve_educational_experience_general_education_admission.return_value = (
            self.educational_experience
        )
        person_api_return.retrieve_educational_experience_continuing_education_admission.return_value = (
            self.educational_experience
        )
        person_api_return.retrieve_educational_experience.return_value = self.educational_experience

        person_api_return.retrieve_professional_experience_admission.return_value = self.professional_experience
        person_api_return.retrieve_professional_experience_general_education_admission.return_value = (
            self.professional_experience
        )
        person_api_return.retrieve_professional_experience_continuing_education_admission.return_value = (
            self.professional_experience
        )
        person_api_return.retrieve_professional_experience.return_value = self.professional_experience

        self.addCleanup(api_person_patcher.stop)

    def setUp(self):
        self.client.force_login(self.person.user)

        self.mock_person_api()
        self.mock_proposition_api()
        self.mock_countries_api()
        self.mock_languages_api()
        self.mock_academic_years_api()
        self.mock_documents_api()
        self.mock_diplomas_api()
        self.mock_superior_non_university_api()
        self.mock_university_api()
