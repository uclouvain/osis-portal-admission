# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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

__all__ = [
    # "DoctorateAdmissionTrainingDetailView",
    # "DoctorateAdmissionDetailsDetailView",
    # "DoctorateAdmissionCurriculumDetailView",
    # "DoctorateAdmissionCotutelleDetailView",
    # "DoctorateAdmissionSupervisionDetailView",
    # "DoctorateAdmissionConfirmDetailView",
    # "DoctorateAdmissionConfirmPaperDetailView",
    # "DoctorateAdmissionEducationDetailView",
    # "DoctorateAdmissionJuryDetailView",
    # "DoctorateAdmissionPersonDetailView",
    # "DoctorateAdmissionPrivateDefenseDetailView",
    # "DoctorateAdmissionPublicDefenseDetailView",
    # "DoctorateAdmissionMessagesDetailView",
]


# class DoctorateAdmissionPersonDetailView(DoctorateDetailMixin):
#     template_name = 'admission/doctorate/detail_person.html'
#
#     def get_context_data(self, **kwargs):
#         kwargs['admission'] = self.get_object()
#         return super().get_context_data(**kwargs)
#
#
# class DoctorateAdmissionDetailsDetailView(DetailView):
#     model = DoctorateAdmission
#
#     def get_context_data(self, **kwargs):
#         kwargs['admission'] = self.get_object()
#         return super().get_context_data(**kwargs)
#
#
# class DoctorateAdmissionEducationDetailView(DetailView):
#     model = DoctorateAdmission
#
#     def get_context_data(self, **kwargs):
#         kwargs['admission'] = self.get_object()
#         return super().get_context_data(**kwargs)
#
#
# class DoctorateAdmissionCurriculumDetailView(DetailView):
#     model = DoctorateAdmission
#
#     def get_context_data(self, **kwargs):
#         kwargs['admission'] = self.get_object()
#         return super().get_context_data(**kwargs)


#
# class DoctorateAdmissionCotutelleDetailView(TemplateView):
#     template_name = 'admission/doctorate/detail_cotutelle.html'
#
#     def get_context_data(self, **kwargs):
#         context_data = super().get_context_data(**kwargs)
#         context_data['admission'] = AdmissionPropositionService.get_proposition(self.kwargs['pk'])
#         context_data['cotutelle'] = AdmissionCotutelleService.get_cotutelle(self.kwargs['pk'])
#         return context_data

# class DoctorateAdmissionConfirmDetailView(DetailView):
#     model = DoctorateAdmission
#
#
# class DoctorateAdmissionConfirmPaperDetailView(DetailView):
#     model = DoctorateAdmission
#
#
# class DoctorateAdmissionJuryDetailView(DetailView):
#     model = DoctorateAdmission
#
#
# class DoctorateAdmissionSupervisionDetailView(DetailView):
#     model = DoctorateAdmission
#
#
# class DoctorateAdmissionTrainingDetailView(DetailView):
#     model = DoctorateAdmission
#
#
# class DoctorateAdmissionPrivateDefenseDetailView(DetailView):
#     model = DoctorateAdmission
#
#
# class DoctorateAdmissionPublicDefenseDetailView(DetailView):
#     model = DoctorateAdmission
#
#
# class DoctorateAdmissionMessagesDetailView(DetailView):
#     model = DoctorateAdmission
