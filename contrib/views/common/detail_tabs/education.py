# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.conf import settings
from django.utils.translation import get_language
from django.views.generic import TemplateView

from admission.constants import LINGUISTIC_REGIMES_WITHOUT_TRANSLATION
from admission.contrib.enums import TrainingType
from admission.contrib.enums.specific_question import Onglets
from admission.contrib.views.mixins import LoadDossierViewMixin
from admission.services.person import (
    AdmissionPersonService,
    ContinuingEducationAdmissionPersonService,
    GeneralEducationAdmissionPersonService,
)
from admission.services.reference import HighSchoolService, LanguageService, CountriesService
from admission.utils import is_med_dent_training, format_address

__all__ = ['AdmissionEducationDetailView']


class AdmissionEducationDetailView(LoadDossierViewMixin, TemplateView):
    template_name = 'admission/details/education.html'
    service_mapping = {
        'create': AdmissionPersonService,
        'doctorate': AdmissionPersonService,
        'general-education': GeneralEducationAdmissionPersonService,
        'continuing-education': ContinuingEducationAdmissionPersonService,
    }
    tab_of_specific_questions = Onglets.ETUDES_SECONDAIRES.name

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        high_school_diploma = (
            self.service_mapping[self.current_context]
            .retrieve_high_school_diploma(
                person=self.request.user.person,
                uuid=self.admission_uuid,
            )
            .to_dict()
        )

        context_data.update(high_school_diploma)

        translated_field = 'name' if get_language() == settings.LANGUAGE_CODE else 'name_en'

        belgian_diploma = high_school_diploma.get('belgian_diploma')
        foreign_diploma = high_school_diploma.get('foreign_diploma')

        context_data['is_bachelor'] = (
            self.admission.formation.type == TrainingType.BACHELOR.name if self.admission else False
        )

        if belgian_diploma:
            institute_uuid = context_data['belgian_diploma'].get('institute')
            if institute_uuid:
                institute = HighSchoolService.get_high_school(
                    uuid=institute_uuid,
                    person=self.request.user.person,
                )
                context_data['belgian_diploma']['institute_name'] = institute['name']
                context_data['belgian_diploma']['institute_address'] = format_address(
                    street=institute['street'],
                    street_number=institute['street_number'],
                    postal_code=institute['zipcode'],
                    city=institute['city'],
                )
            else:
                context_data['belgian_diploma']['institute_name'] = context_data['belgian_diploma'].pop(
                    'other_institute_name'
                )
                context_data['belgian_diploma']['institute_address'] = context_data['belgian_diploma'].pop(
                    'other_institute_address'
                )

        elif foreign_diploma:
            if context_data["foreign_diploma"].get("linguistic_regime"):
                linguistic_regime = LanguageService.get_language(
                    code=context_data["foreign_diploma"]["linguistic_regime"],
                    person=self.request.user.person,
                )
                context_data["foreign_diploma"]['linguistic_regime'] = getattr(linguistic_regime, translated_field)
                context_data["need_translations"] = linguistic_regime.code not in LINGUISTIC_REGIMES_WITHOUT_TRANSLATION

            if context_data["foreign_diploma"].get('country'):
                country = CountriesService.get_country(
                    iso_code=context_data["foreign_diploma"].get('country'),
                    person=self.request.user.person,
                )
                context_data["foreign_diploma"]['country'] = {
                    'name': getattr(country, translated_field),
                    'european_union': country.european_union or is_med_dent_training(self.admission.formation),
                }

        return context_data
