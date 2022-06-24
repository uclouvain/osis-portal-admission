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

from admission.contrib.views.mixins import LoadDossierViewMixin
from admission.services.person import AdmissionPersonService
from admission.services.reference import LanguageService


class DoctorateAdmissionLanguagesDetailView(LoadDossierViewMixin, TemplateView):
    template_name = 'admission/doctorate/details/languages.html'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["languages_knowledge"] = AdmissionPersonService.retrieve_languages_knowledge(
            self.request.user.person,
            uuid=self.admission_uuid,
        )
        translated_field = 'name' if get_language() == settings.LANGUAGE_CODE else 'name_en'
        if len(context_data["languages_knowledge"]):
            for language_knowledge in context_data["languages_knowledge"]:
                language = LanguageService.get_language(
                    code=language_knowledge.language,
                    person=self.request.user.person,
                )
                language_knowledge.language = getattr(language, translated_field)
        return context_data
