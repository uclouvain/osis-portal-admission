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
import itertools
from typing import List

from dal import autocomplete
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.utils.translation import get_language, gettext_lazy as _
from osis_organisation_sdk.model.entite_type_enum import EntiteTypeEnum
from osis_reference_sdk.model.university import University
from waffle import switch_is_active

from admission.constants import BE_ISO_CODE
from admission.contrib.enums import TypeFormation
from admission.contrib.enums.diploma import StudyType
from admission.contrib.forms import EMPTY_VALUE
from admission.services.autocomplete import AdmissionAutocompleteService
from admission.services.organisation import EntitiesService
from admission.services.reference import (
    CitiesService,
    CountriesService,
    DiplomaService,
    HighSchoolService,
    LanguageService,
    SuperiorNonUniversityService,
    UniversityService,
)
from admission.utils import (
    format_entity_address,
    format_entity_title,
    format_high_school_title,
    format_scholarship,
    format_training,
    format_training_with_year,
)
from base.models.enums.entity_type import INSTITUTE
from osis_admission_sdk.model.scholarship import Scholarship

__all__ = [
    "DoctorateAutocomplete",
    "CountryAutocomplete",
    "CityAutocomplete",
    "LanguageAutocomplete",
    "TutorAutocomplete",
    "PersonAutocomplete",
    "InstituteAutocomplete",
    "InstituteLocationAutocomplete",
    "HighSchoolAutocomplete",
    "DiplomaAutocomplete",
    "LearningUnitYearsAutocomplete",
    "SuperiorNonUniversityAutocomplete",
    "GeneralEducationAutocomplete",
    "MixedTrainingAutocomplete",
    "ScholarshipAutocomplete",
    "UniversityAutocomplete",
    "SuperiorInstituteAutocomplete",
]


class DoctorateAutocomplete(LoginRequiredMixin, autocomplete.Select2ListView):
    urlpatterns = 'doctorate'

    def get_list(self):
        selected_campus = self.forwarded.get('campus', EMPTY_VALUE)
        return AdmissionAutocompleteService.get_doctorates(
            person=self.request.user.person,
            sigle=self.forwarded['sector'],
            campus=selected_campus if selected_campus != EMPTY_VALUE else '',
        )

    def results(self, results):
        format_method = format_training_with_year if switch_is_active('debug') else format_training
        return [
            dict(
                id="{result.sigle}-{result.annee}".format(result=result),
                sigle=result.sigle,
                sigle_entite_gestion=result.sigle_entite_gestion,
                text=format_method(result),
            )
            for result in results
        ]

    def autocomplete_results(self, results):
        """Return list of strings that match the autocomplete query."""
        return [
            x
            for x in results
            if self.q.lower() in "{sigle} - {intitule}".format(sigle=x.sigle, intitule=x.intitule).lower()
        ]


class GeneralEducationAutocomplete(LoginRequiredMixin, autocomplete.Select2ListView):
    urlpatterns = 'general-education'

    def get_list(self):
        selected_campus = self.forwarded.get('campus', EMPTY_VALUE)
        return AdmissionAutocompleteService.get_general_education_trainings(
            person=self.request.user.person,
            training_type=self.forwarded.get('training_type'),
            name=self.q,
            campus=selected_campus if selected_campus != EMPTY_VALUE else '',
        )

    def results(self, results):
        format_method = format_training_with_year if switch_is_active('debug') else format_training
        return [
            dict(
                id="{result.sigle}-{result.annee}".format(result=result),
                text=format_method(result),
            )
            for result in results
        ]

    def autocomplete_results(self, results):
        return results


class MixedTrainingAutocomplete(GeneralEducationAutocomplete):
    urlpatterns = 'mixed-training'

    def get_list(self):
        selected_campus = self.forwarded.get('campus', EMPTY_VALUE)
        if not switch_is_active('admission-iufc'):
            iufc_trainings = []
        else:
            iufc_trainings = AdmissionAutocompleteService.get_continuing_education_trainings(
                person=self.request.user.person,
                name=self.q,
                campus=selected_campus if selected_campus != EMPTY_VALUE else '',
            )
        certificate = AdmissionAutocompleteService.get_general_education_trainings(
            person=self.request.user.person,
            training_type=TypeFormation.CERTIFICAT.name,
            name=self.q,
            campus=selected_campus if selected_campus != EMPTY_VALUE else '',
        )
        # Mix the two types
        return iufc_trainings + certificate


class ScholarshipAutocomplete(LoginRequiredMixin, autocomplete.Select2ListView):
    urlpatterns = 'scholarship'

    def get_list(self):
        return AdmissionAutocompleteService.get_scholarships(
            person=self.request.user.person,
            scholarship_type=self.forwarded.get('scholarship_type'),
            search=self.q,
        ).get('results')

    def results(self, results: List[Scholarship]):
        return [
            dict(
                id="{result.uuid}".format(result=result),
                text=format_scholarship(result),
            )
            for result in results
        ]

    def autocomplete_results(self, results):
        return results


class CountryAutocomplete(LoginRequiredMixin, autocomplete.Select2ListView):
    paginate_by = 20
    page_kwargs = 'page'
    urlpatterns = 'country'

    def get_page(self):
        try:
            return int(self.request.GET.get(self.page_kwargs, 1))
        except Exception:
            return 1

    def get_list(self):
        return CountriesService.get_countries(
            person=self.request.user.person,
            search=self.q,
            limit=self.paginate_by,
            offset=(self.get_page() - 1) * self.paginate_by,
        )

    def results(self, results):
        page = self.get_page()
        belgique = []
        if not self.q and not self.forwarded.get('exclude_be', False) and page == 1:
            belgique = [
                {
                    'id': BE_ISO_CODE,
                    'text': _('Belgium'),
                    'european_union': True,
                },
                {'id': None, 'text': '----------'},
            ]
        return belgique + [
            dict(
                id=country.iso_code,
                text=country.name if get_language() == settings.LANGUAGE_CODE else country.name_en,
                european_union=country.european_union,
            )
            for country in results
            if not self.forwarded.get('exclude_be', False) or country.iso_code != BE_ISO_CODE
        ]

    def get(self, request, *args, **kwargs):
        """Return option list json response."""
        results = self.get_list()
        return JsonResponse(
            {'results': self.results(results), 'pagination': {'more': len(results) >= self.paginate_by}}
        )


class CityAutocomplete(LoginRequiredMixin, autocomplete.Select2ListView):
    urlpatterns = 'city'

    def get_list(self):
        return CitiesService.get_cities(
            person=self.request.user.person,
            search=self.q,
            zip_code=self.forwarded.get('postal_code', ''),
        )

    def autocomplete_results(self, results):
        return results

    def results(self, results):
        """Return the result dictionary."""
        return [dict(id=city.name, text=city.name) for city in results]


class LanguageAutocomplete(LoginRequiredMixin, autocomplete.Select2ListView):
    urlpatterns = 'language'

    def get_list(self):
        return LanguageService.get_languages(person=self.request.user.person, search=self.q)

    def autocomplete_results(self, results):
        return results

    def results(self, results):
        return [
            dict(
                id=language.code,
                text=language.name if get_language() == settings.LANGUAGE_CODE else language.name_en,
            )
            for language in results
        ]


class TutorAutocomplete(LoginRequiredMixin, autocomplete.Select2ListView):
    urlpatterns = 'tutor'

    def get_list(self):
        return AdmissionAutocompleteService.autocomplete_tutors(
            person=self.request.user.person,
            search=self.q,
        )

    def results(self, results):
        return [
            dict(
                id=result.global_id,
                text="{result.first_name} {result.last_name}".format(result=result),
            )
            for result in results
        ]

    def autocomplete_results(self, results):
        return results


class PersonAutocomplete(TutorAutocomplete):
    urlpatterns = 'person'

    def get_list(self):
        return AdmissionAutocompleteService.autocomplete_persons(
            person=self.request.user.person,
            search=self.q,
        )


class HighSchoolAutocomplete(LoginRequiredMixin, autocomplete.Select2ListView):
    urlpatterns = 'high-school'

    def get_list(self):
        # Return a list of high schools whose name / city / postal code city is specified by the user
        additional_filters = {}
        community = self.forwarded.get('community')
        if community:
            additional_filters['linguistic_regime'] = community

        return HighSchoolService.get_high_schools(
            limit=100,
            person=self.request.user.person,
            search=self.q,
            active=True,
            **additional_filters,
        )

    def autocomplete_results(self, results):
        return results

    def results(self, results):
        return [
            dict(
                id=high_school.uuid,
                text=format_high_school_title(high_school),
            )
            for high_school in results
        ]


class InstituteAutocomplete(LoginRequiredMixin, autocomplete.Select2ListView):
    urlpatterns = 'institute'

    def get_list(self):
        # Return a list of UCL institutes whose title / acronym is specified by the user
        return EntitiesService.get_ucl_entities(
            limit=10,
            person=self.request.user.person,
            entity_type=[
                EntiteTypeEnum(INSTITUTE),
            ],
            search=self.q,
        )

    def autocomplete_results(self, results):
        return results

    def results(self, results):
        return [
            dict(
                id=entity.uuid,
                text=format_entity_title(entity=entity),
            )
            for entity in results
        ]


class InstituteLocationAutocomplete(LoginRequiredMixin, autocomplete.Select2ListView):
    urlpatterns = 'institute-location'

    def get_list(self):
        # Return a list of addresses related to the thesis institute, if defined
        if not self.forwarded['institut_these']:
            return []
        return EntitiesService.get_ucl_entity_addresses(
            person=self.request.user.person,
            uuid=self.forwarded['institut_these'],
        )

    def results(self, results):
        formatted_results = []
        for address in results:
            formatted_address = format_entity_address(address)
            formatted_results.append({'id': formatted_address, 'text': formatted_address})
        return formatted_results


class DiplomaAutocomplete(LoginRequiredMixin, autocomplete.Select2ListView):
    urlpatterns = 'diploma'

    def get_list(self):
        return DiplomaService.get_diplomas(
            person=self.request.user.person,
            search=self.q,
            active=True,
            study_type=self.forwarded.get('institute_type', ''),
        )

    def results(self, results):
        return [
            dict(
                id=result.uuid,
                text=result.title,
            )
            for result in results
        ]

    def autocomplete_results(self, results):
        return results


class LearningUnitYearsAutocomplete(LoginRequiredMixin, autocomplete.Select2ListView):
    urlpatterns = 'learning-unit-years'

    def get_list(self):
        return AdmissionAutocompleteService.autocomplete_learning_unit_years(
            person=self.request.user.person,
            year=self.forwarded['academic_year'],
            acronym_search=self.q,
        )

    def results(self, results):
        return [
            dict(
                id=result['acronym'],
                text=f"{result['acronym']} - {result['title']}",
            )
            for result in results
        ]

    def autocomplete_results(self, results):
        return results


class SuperiorNonUniversityAutocomplete(LoginRequiredMixin, autocomplete.Select2ListView):
    urlpatterns = 'superior-non-university'

    def get_list(self):
        additional_filters = {}
        country = self.forwarded.get('country')
        if country:
            additional_filters['country_iso_code'] = country

        return SuperiorNonUniversityService.get_superior_non_universities(
            person=self.request.user.person,
            search=self.q,
            active=True,
            **additional_filters,
        )

    def results(self, results):
        return [
            dict(
                id=result.uuid,
                text=result.name,
            )
            for result in results
        ]

    def autocomplete_results(self, results):
        return results


class UniversityAutocomplete(LoginRequiredMixin, autocomplete.Select2ListView):
    urlpatterns = 'university'

    def get_list(self):
        additional_filters = {}
        country = self.forwarded.get('country')
        if country:
            additional_filters['country_iso_code'] = country

        return UniversityService.get_universities(
            person=self.request.user.person,
            search=self.q,
            active=True,
            **additional_filters,
        )

    def results(self, results):
        return [
            dict(
                id=result.uuid,
                text=result.name,
            )
            for result in results
        ]

    def autocomplete_results(self, results):
        return results


class SuperiorInstituteAutocomplete(LoginRequiredMixin, autocomplete.Select2ListView):
    urlpatterns = 'superior-institute'

    def get_list(self):
        additional_filters = {}
        country = self.forwarded.get('country')
        if country:
            additional_filters['country_iso_code'] = country

        universities = UniversityService.get_universities(
            person=self.request.user.person,
            search=self.q,
            active=True,
            **additional_filters,
        )
        superior_non_universities = SuperiorNonUniversityService.get_superior_non_universities(
            person=self.request.user.person,
            search=self.q,
            active=True,
            **additional_filters,
        )

        return sorted(
            itertools.chain(universities, superior_non_universities),
            key=lambda institute: institute.name,
        )

    def results(self, results):
        return [
            dict(
                id=result.uuid,
                text=result.name,
                type=StudyType.UNIVERSITY.name if isinstance(result, University) else StudyType.NON_UNIVERSITY.name,
            )
            for result in results
        ]

    def autocomplete_results(self, results):
        return results
