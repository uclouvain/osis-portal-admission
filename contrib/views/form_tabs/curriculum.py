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
import enum

from django.contrib import messages
from django.utils.translation import gettext as _

from django.http import HttpResponseRedirect
from django.shortcuts import resolve_url


from osis_admission_sdk import ApiException

from admission.contrib.forms.curriculum import DoctorateAdmissionCurriculumExperienceForm, \
    DoctorateAdmissionCurriculumFileForm
from admission.contrib.views import DoctorateAdmissionCurriculumDetailView
from admission.services.person import AdmissionPersonService


class CurriculumForm(enum.Enum):
    EXPERIENCE_CREATION = 'experience_creation'
    EXPERIENCE_UPDATE = 'experience_update'
    EXPERIENCE_DELETION = 'confirm'
    CURRICULUM_UPLOAD = 'curriculum_upload'


class DoctorateAdmissionCurriculumFormView(DoctorateAdmissionCurriculumDetailView):
    template_name = 'admission/doctorate/form_tab_curriculum.html'

    def get_context_data(self, submitted_form=None, **kwargs):
        # The admission (if available), the experience list and the curriculum file are loaded from the parent
        context_data = super().get_context_data(**kwargs)
        experience_id = str(self.kwargs.get('experience_id', ''))

        # Add the necessary forms (initialize them and add the submitted one)
        submitted_form_prefix = submitted_form.prefix if submitted_form else ''

        # Form to upload a CV file
        context_data['curriculum_upload'] = DoctorateAdmissionCurriculumFileForm(
            prefix=CurriculumForm.CURRICULUM_UPLOAD.value,
            initial=context_data['curriculum_file'],
        ) if submitted_form_prefix != CurriculumForm.CURRICULUM_UPLOAD.value else submitted_form

        context_data['forms'] = dict()

        # Form to create a new experience
        context_data['forms']['creation_form'] = DoctorateAdmissionCurriculumExperienceForm(
            prefix=CurriculumForm.EXPERIENCE_CREATION.value,
            person=self.request.user.person,
        ) if submitted_form_prefix != CurriculumForm.EXPERIENCE_CREATION.value else submitted_form

        # Form to update an existing experience
        if experience_id:
            if submitted_form_prefix == CurriculumForm.EXPERIENCE_UPDATE.value:
                context_data['forms']['update_form'] = submitted_form
            else:
                experience = next(
                    (exp for exp in context_data.get('curriculum_experiences') if exp.uuid == experience_id), None,
                )
                if experience:
                    context_data['forms']['update_form'] = DoctorateAdmissionCurriculumExperienceForm(
                        prefix=CurriculumForm.EXPERIENCE_UPDATE.value,
                        initial=experience.to_dict(),
                        person=self.request.user.person,
                    )
                    context_data['form_to_display'] = CurriculumForm.EXPERIENCE_UPDATE.value

        return context_data

    def post(self, request, *args, **kwargs):
        proposition_uuid = str(self.kwargs.get('pk', ''))

        if CurriculumForm.CURRICULUM_UPLOAD.value in self.request.POST:
            # Upload the CV file
            form = DoctorateAdmissionCurriculumFileForm(
                prefix=CurriculumForm.CURRICULUM_UPLOAD.value,
                data=self.request.POST,
            )
            if form.is_valid():
                try:
                    AdmissionPersonService.update_curriculum_file(
                        person=self.request.user.person,
                        data=form.cleaned_data,
                        uuid=proposition_uuid,
                    )
                    return self.redirect_after_valid_form()

                except ApiException:
                    messages.error(self.request, _("An error has happened when uploading the file."))

            return self.re_render_after_invalid_form(self.get_context_data(form), form.prefix)

        elif CurriculumForm.EXPERIENCE_CREATION.value in self.request.POST:
            # Create an experience
            form = DoctorateAdmissionCurriculumExperienceForm(
                prefix=CurriculumForm.EXPERIENCE_CREATION.value,
                data=self.request.POST,
                person=self.request.user.person,
            )
            if form.is_valid():
                try:
                    AdmissionPersonService.create_curriculum_experience(
                        person=self.request.user.person,
                        data=self.prepare_data(form.cleaned_data),
                        uuid=proposition_uuid,
                    )
                    return self.redirect_after_valid_form()

                except ApiException:
                    messages.error(self.request, _("An error has happened when adding the experience."))

            return self.re_render_after_invalid_form(self.get_context_data(form), form.prefix)

        elif CurriculumForm.EXPERIENCE_UPDATE.value in self.request.POST:
            # Update an experience
            form = DoctorateAdmissionCurriculumExperienceForm(
                prefix=CurriculumForm.EXPERIENCE_UPDATE.value,
                data=self.request.POST,
                person=self.request.user.person
            )
            if form.is_valid():
                experience_id = str(self.kwargs.get('experience_id', ''))
                try:
                    AdmissionPersonService.update_curriculum_experience(
                        experience_id=experience_id,
                        person=self.request.user.person,
                        data=self.prepare_data(form.cleaned_data),
                        uuid=proposition_uuid,
                    )
                    return self.redirect_after_valid_form()

                except ApiException:
                    messages.error(self.request, _("An error has happened when updating the experience."))

            return self.re_render_after_invalid_form(self.get_context_data(form), form.prefix)

        elif CurriculumForm.EXPERIENCE_DELETION.value in self.request.POST:
            # Delete an experience
            try:
                AdmissionPersonService.delete_curriculum_experience(
                    experience_id=self.request.POST.get('confirmed-id'),
                    person=self.request.user.person,
                    uuid=proposition_uuid,
                )
            except ApiException:
                messages.error(self.request, _("An error has happened when deleting the experience."))
                return self.re_render_after_invalid_form(self.get_context_data())

        return self.redirect_after_valid_form()

    @classmethod
    def prepare_data(cls, data):
        # Remove redundant data
        redundant_fields = [
            'other_program',
            'program_not_found',
            'institute_not_found',
            'institute_city_be',
            'activity_institute_city',
            'activity_institute_name',
        ]
        for f in redundant_fields:
            data.pop(f, None)

        # Format some fields values
        data['academic_year'] = int(data['academic_year'])
        if data.get('dissertation_score'):
            data['dissertation_score'] = str(data['dissertation_score'])

        return data

    def redirect_after_valid_form(self):
        messages.info(self.request, _('The curriculum has correctly been updated.'))
        return HttpResponseRedirect(self.get_success_url())

    def re_render_after_invalid_form(self, context_data, form_to_display=None):
        if form_to_display:
            context_data['form_to_display'] = form_to_display
        return self.render_to_response(context_data)

    def get_success_url(self):
        pk = self.kwargs.get('pk')
        if pk:
            return resolve_url('admission:doctorate-update:curriculum', pk=pk)
        else:
            return resolve_url('admission:doctorate-create:curriculum')
