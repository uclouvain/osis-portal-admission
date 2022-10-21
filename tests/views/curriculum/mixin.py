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
import datetime
import uuid
from unittest.mock import ANY, patch

from django.test import TestCase, override_settings
from osis_reference_sdk.model.paginated_superior_non_university import PaginatedSuperiorNonUniversity
from osis_reference_sdk.model.superior_non_university import SuperiorNonUniversity

from admission.tests.factories import PropositionDTOComptabiliteFactory

from osis_admission_sdk.model.proposition_search_doctorat import PropositionSearchDoctorat
from osis_reference_sdk.model.paginated_academic_years import PaginatedAcademicYears

from osis_admission_sdk.model.educational_experience_educationalexperienceyear_set import (
    EducationalExperienceEducationalexperienceyearSet,
)

from osis_admission_sdk.model.curriculum_educationalexperienceyear_set import CurriculumEducationalexperienceyearSet
from osis_reference_sdk.model.paginated_diploma import PaginatedDiploma

from osis_admission_sdk.model.curriculum import Curriculum

from admission.contrib.enums.admission_type import AdmissionType
from admission.contrib.enums.projet import ChoixStatutProposition
from osis_admission_sdk.model.activity_sector import ActivitySector

from osis_admission_sdk.model.activity_type import ActivityType
from osis_admission_sdk.model.curriculum_file import CurriculumFile
from osis_admission_sdk.model.evaluation_system import EvaluationSystem
from osis_admission_sdk.model.grade import Grade
from osis_admission_sdk.model.proposition_dto_links import PropositionDTOLinks
from osis_admission_sdk.model.result import Result
from osis_admission_sdk.model.teaching_type_enum import TeachingTypeEnum

from osis_admission_sdk.model.transcript_type import TranscriptType
from osis_reference_sdk.model.country import Country
from osis_reference_sdk.model.language import Language

from osis_admission_sdk.model.curriculum_professional_experiences import CurriculumProfessionalExperiences

from osis_admission_sdk.model.curriculum_educational_experiences import CurriculumEducationalExperiences
from osis_reference_sdk.model.academic_year import AcademicYear
from osis_reference_sdk.model.paginated_country import PaginatedCountry
from osis_reference_sdk.model.paginated_language import PaginatedLanguage

from osis_admission_sdk.model.professional_experience import ProfessionalExperience
from osis_reference_sdk.model.diploma import Diploma

from base.tests.factories.person import PersonFactory

from osis_admission_sdk.model.educational_experience import EducationalExperience
from osis_admission_sdk.model.proposition_dto import PropositionDTO


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

        # Languages
        cls.language_without_translation = Language(code='FR', name='Français', name_en='French')
        cls.language_with_translation = Language(code='IS', name='Islandais', name_en='Icelandic')

        # Diplomas
        cls.first_diploma = Diploma(uuid=str(uuid.uuid4()), title="Computer science")
        cls.second_diploma = Diploma(uuid=str(uuid.uuid4()), title="Biology")

        # Institute
        cls.institute = SuperiorNonUniversity(uuid=str(uuid.uuid4()), name="Institute of Technology")

        # Academic years
        cls.academic_year_2018 = AcademicYear(year=2018)
        cls.academic_year_2019 = AcademicYear(year=2019)
        cls.academic_year_2020 = AcademicYear(year=2020)

        cls.educational_experience = EducationalExperience._from_openapi_data(
            country=cls.be_country.iso_code,
            institute=cls.institute.uuid,
            institute_name='UCL',
            institute_address='Place de l\'Université',
            program=cls.first_diploma.uuid,
            education_name='Other computer science',
            study_system=TeachingTypeEnum(value='FULL_EXERCICES'),
            evaluation_type=EvaluationSystem(value='ECTS_CREDITS'),
            linguistic_regime=cls.language_without_translation.code,
            transcript_type=TranscriptType(value='ONE_FOR_ALL_YEARS'),
            obtained_diploma=True,
            obtained_grade=Grade(value='GREAT_DISTINCTION'),
            graduate_degree=['f1.pdf'],
            graduate_degree_translation=['f11.pdf'],
            transcript=['f2.pdf'],
            transcript_translation=['f22.pdf'],
            bachelor_cycle_continuation=True,
            diploma_equivalence=['f3.pdf'],
            rank_in_diploma='10 on 100',
            expected_graduation_date=datetime.date(2022, 8, 30),
            dissertation_title='Title',
            dissertation_score='15/20',
            dissertation_summary=['f4.pdf'],
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
        )

        cls.lite_educational_experience = CurriculumEducationalExperiences._from_openapi_data(
            uuid=cls.educational_experience.uuid,
            institute_name=cls.educational_experience.institute_name,
            program=cls.educational_experience.program,
            education_name=cls.educational_experience.education_name,
            educationalexperienceyear_set=[
                CurriculumEducationalexperienceyearSet(academic_year=cls.academic_year_2020.year),
                CurriculumEducationalexperienceyearSet(academic_year=cls.academic_year_2018.year),
            ],
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
            certificate=[],
        )

        cls.lite_professional_experience = CurriculumProfessionalExperiences._from_openapi_data(
            uuid=cls.professional_experience.uuid,
            institute_name=cls.professional_experience.institute_name,
            type=cls.professional_experience.type,
            start_date=cls.professional_experience.start_date,
            end_date=cls.professional_experience.start_date,
        )

        # Proposition
        cls.proposition = PropositionDTO._from_openapi_data(
            uuid=str(uuid.uuid4()),
            type_admission=AdmissionType.ADMISSION.name,
            reference='22-300001',
            links=PropositionDTOLinks(),
            doctorat=PropositionSearchDoctorat._from_openapi_data(
                sigle='CS1',
                annee=cls.academic_year_2020.year,
                intitule='Doctorate name',
                sigle_entite_gestion="CDSS",
                campus="Mons",
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
            statut=ChoixStatutProposition.IN_PROGRESS.name,
            erreurs=[],
            comptabilite=PropositionDTOComptabiliteFactory(),
        )

        cls.curriculum_file = CurriculumFile(curriculum=[])

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

        self.mock_academic_years_api.return_value.get_academic_years.return_value = PaginatedAcademicYears(
            results=[
                self.academic_year_2018,
                self.academic_year_2019,
                self.academic_year_2020,
            ]
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

        patcher = patch('osis_document.api.utils.get_remote_metadata', return_value={'name': 'myfile'})
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
            return next(
                (institute for institute in [self.institute] if institute.uuid == institute_uuid),
                None,
            )

        self.mock_superior_non_universities_api.return_value.superior_non_universities_list.return_value = (
            PaginatedSuperiorNonUniversity(results=[self.institute])
        )

        self.mock_superior_non_universities_api.return_value.superior_non_university_read.side_effect = get_institute
        self.addCleanup(superior_non_universities_api_patcher.stop)

    def mock_person_api(self):
        api_person_patcher = patch("osis_admission_sdk.api.person_api.PersonApi")
        self.mock_person_api = api_person_patcher.start()

        curriculum_data = Curriculum._from_openapi_data(
            educational_experiences=[self.lite_educational_experience],
            professional_experiences=[self.lite_professional_experience],
            file=self.curriculum_file,
            minimal_year=self.academic_year_2020.year,
        )
        self.mock_person_api.return_value.retrieve_curriculum_admission.return_value = curriculum_data
        self.mock_person_api.return_value.retrieve_curriculum.return_value = curriculum_data

        self.mock_person_api.return_value.retrieve_educational_experience_admission.return_value = (
            self.educational_experience
        )
        self.mock_person_api.return_value.retrieve_educational_experience.return_value = self.educational_experience

        self.mock_person_api.return_value.retrieve_professional_experience_admission.return_value = (
            self.professional_experience
        )
        self.mock_person_api.return_value.retrieve_professional_experience.return_value = self.professional_experience

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
