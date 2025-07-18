# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.utils.functional import cached_property
from django.utils.translation import activate
from django.views.generic import FormView

from admission.constants import BE_ISO_CODE
from admission.contrib.enums.person import IdentificationType, PersonUpdateMode
from admission.contrib.forms.person import DoctorateAdmissionPersonForm
from admission.contrib.views.mixins import LoadDossierViewMixin
from admission.services.mixins import WebServiceFormMixin
from admission.services.person import (
    AdmissionPersonService,
    ContinuingEducationAdmissionPersonService,
    GeneralEducationAdmissionPersonService,
)
from admission.services.proposition import (
    AdmissionPropositionService,
    BelgianNissBusinessException,
)
from admission.templatetags.admission import can_make_action
from osis_common.middlewares.locale import LANGUAGE_SESSION_KEY

__all__ = ['AdmissionPersonFormView']


class AdmissionPersonFormView(LoadDossierViewMixin, WebServiceFormMixin, FormView):
    service_mapping = {
        'create': AdmissionPersonService,
        'doctorate': AdmissionPersonService,
        'general-education': GeneralEducationAdmissionPersonService,
        'continuing-education': ContinuingEducationAdmissionPersonService,
    }
    template_name = 'admission/forms/person.html'
    form_class = DoctorateAdmissionPersonForm
    error_mapping = {
        BelgianNissBusinessException.BelgianNISSCharactersException: 'national_number',
        BelgianNissBusinessException.BelgianNISSLengthException: 'national_number',
        BelgianNissBusinessException.BelgianNISSBirthDateException: 'national_number',
        BelgianNissBusinessException.BelgianNISSSexException: 'national_number',
        BelgianNissBusinessException.BelgianNISSChecksumException: 'national_number',
        BelgianNissBusinessException.BelgianMissingBirthDataException: 'national_number',
    }

    @cached_property
    def create_permissions(self):
        """Return the permissions for the create (not related-admission) views."""
        return AdmissionPropositionService.list_proposition_create_permissions(self.request.user.person)

    @cached_property
    def person_update_mode(self):
        """Return the person update mode depending on the permissions of the current user."""
        update_mode = PersonUpdateMode.NO

        if self.admission_uuid:
            if can_make_action(self.admission, 'update_person'):
                update_mode = PersonUpdateMode.ALL
            elif can_make_action(self.admission, 'update_person_last_enrolment'):
                update_mode = PersonUpdateMode.LAST_ENROLMENT
        else:
            permissions = self.create_permissions
            if can_make_action(permissions, 'create_person'):
                update_mode = PersonUpdateMode.ALL
            elif can_make_action(permissions, 'create_person_last_enrolment'):
                update_mode = PersonUpdateMode.LAST_ENROLMENT

        return update_mode

    def get(self, request, *args, **kwargs):
        # In case of a creation and if we don't have permission to update the person, we show the read-only template
        if not self.admission_uuid:
            if self.person_update_mode == PersonUpdateMode.NO:
                permissions = self.create_permissions
                if self.request.GET.get('from_redirection') and can_make_action(permissions, 'create_training_choice'):
                    return redirect(self.request.resolver_match.namespace + ':training-choice')
                person = self.person_info
                context = super().get_context_data(
                    with_submit=False,
                    person=person,
                    contact_language=dict(settings.LANGUAGES).get(person.get('language')),
                )
                return render(request, 'admission/details/person.html', context)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['BE_ISO_CODE'] = BE_ISO_CODE
        return context

    @cached_property
    def person_info(self):
        return (
            self.service_mapping[self.current_context]
            .retrieve_person(
                self.person,
                uuid=self.admission_uuid,
            )
            .to_dict()
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['person'] = self.person
        kwargs['person_update_mode'] = self.person_update_mode
        return kwargs

    def get_initial(self):
        return self.person_info

    def prepare_data(self, data):
        is_belgian = data.get('country_of_citizenship') == BE_ISO_CODE

        if not data['already_registered']:
            data['last_registration_year'] = None
            data['last_registration_id'] = ''
        else:
            data['last_registration_year'] = (
                int(data['last_registration_year']) if data['last_registration_year'] else None
            )

        if data['unknown_birth_date']:
            data['birth_date'] = None
        else:
            data['birth_year'] = None

        if is_belgian or data.get('has_national_number'):
            data['id_card_number'] = ''
            data['passport_number'] = ''
            data['passport'] = []
            data['passport_expiry_date'] = None

        elif data.get('identification_type') == IdentificationType.ID_CARD_NUMBER.name:
            data['national_number'] = ''
            data['passport_number'] = ''
            data['passport'] = []
            data['passport_expiry_date'] = None

        elif data.get('identification_type') == IdentificationType.PASSPORT_NUMBER.name:
            data['national_number'] = ''
            data['id_card_number'] = ''
            data['id_card'] = []
            data['id_card_expiry_date'] = None

        else:
            data['national_number'] = ''
            data['id_card_number'] = ''
            data['passport_number'] = ''
            data['passport'] = []
            data['id_card'] = []
            data['id_card_expiry_date'] = None
            data['passport_expiry_date'] = None

        for field in ['already_registered', 'unknown_birth_date', 'identification_type', 'has_national_number']:
            data.pop(field, None)

        return data

    def call_webservice(self, data):
        if self.person_update_mode == PersonUpdateMode.ALL:
            updated_person = self.service_mapping[self.current_context].update_person(
                person=self.person,
                data=data,
                uuid=self.admission_uuid,
            )
        elif self.person_update_mode == PersonUpdateMode.LAST_ENROLMENT:
            updated_person = self.service_mapping[self.current_context].update_person_last_enrolment(
                person=self.person,
                data=data,
                uuid=self.admission_uuid,
            )
        else:
            raise PermissionDenied

        # Update local person to make sure future requests to API don't rollback person
        update_fields = []
        for field in data.keys():
            if (
                hasattr(self.person, field)
                and updated_person.get(field) is not None
                and getattr(self.person, field) != updated_person.get(field)
            ):
                update_fields.append(field)
                setattr(self.person, field, updated_person.get(field))
        self.person.save(update_fields=update_fields)
        activate(self.person.language)
        self.request.session[LANGUAGE_SESSION_KEY] = self.person.language
