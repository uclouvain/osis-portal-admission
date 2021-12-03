# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import get_language
from django.views.generic import TemplateView

from admission.services.person import AdmissionPersonService
from admission.services.proposition import AdmissionPropositionService
from admission.services.reference import CountriesService, LanguageService


class DoctorateAdmissionEducationDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'admission/doctorate/detail_education.html'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        # Admission
        context_data['admission'] = AdmissionPropositionService.get_proposition(
            person=self.request.user.person, uuid=str(self.kwargs['pk']),
        )
        # Person
        high_school_diploma = AdmissionPersonService.retrieve_high_school_diploma(
            person=self.request.user.person
        ).to_dict()
        translated_field = 'name' if get_language() == settings.LANGUAGE_CODE else 'name_en'

        belgian_diploma = high_school_diploma.get('belgian_diploma')
        foreign_diploma = high_school_diploma.get('foreign_diploma')
        if belgian_diploma:
            context_data["belgian_diploma"] = high_school_diploma["belgian_diploma"]
        elif foreign_diploma:
            context_data["foreign_diploma"] = high_school_diploma["foreign_diploma"]
            if context_data["foreign_diploma"].get("country"):
                country = CountriesService.get_country(
                    iso_code=context_data["foreign_diploma"]["country"],
                    person=self.request.user.person,
                )
                context_data["foreign_diploma"]['country'] = getattr(country, translated_field)
            if context_data["foreign_diploma"].get("linguistic_regime"):
                linguistic_regime = LanguageService.get_language(
                    code=context_data["foreign_diploma"]["linguistic_regime"],
                    person=self.request.user.person,
                )
                context_data["foreign_diploma"]['linguistic_regime'] = getattr(linguistic_regime, translated_field)

        return context_data
