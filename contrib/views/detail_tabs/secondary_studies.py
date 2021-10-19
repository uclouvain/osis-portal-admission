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
from django.views.generic import TemplateView

from admission.services.person import AdmissionPersonService
from admission.services.reference import CountriesService


class DoctorateAdmissionEducationDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'admission/doctorate/detail_education.html'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        high_school_diploma = AdmissionPersonService.retrieve_high_school_diploma(person=self.request.user.person)
        translated_field = 'name_en' if settings.LANGUAGE_CODE == "en" else 'name'

        if high_school_diploma.get('belgian_diploma'):
            context_data["belgian_diploma"] = high_school_diploma["belgian_diploma"]
        else:
            context_data["foreign_diploma"] = high_school_diploma["foreign_diploma"]
            if context_data["foreign_diploma"].get("country"):
                contact_country = CountriesService.get_country(iso_code=context_data["foreign_diploma"].get("country"))
                context_data['contact_country'] = getattr(contact_country, translated_field)
        return context_data
