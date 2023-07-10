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

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import BadRequest, ImproperlyConfigured
from django.forms import Form
from django.http import HttpResponseRedirect
from django.shortcuts import resolve_url
from django.utils.functional import cached_property
from django.utils.translation import gettext as _
from django.views.generic import FormView

from admission.contrib.views.mixins import LoadDossierViewMixin
from admission.services.proposition import AdmissionPropositionService
from admission.templatetags.admission import can_make_action

__all__ = [
    'AdmissionPaymentView',
]


class AdmissionPaymentView(LoadDossierViewMixin, PermissionRequiredMixin, FormView):
    template_name = 'admission/forms/payment.html'
    form_class = Form
    urlpatterns = 'payment'

    @cached_property
    def can_pay_after_submission(self) -> bool:
        return can_make_action(admission=self.admission, action_name='pay_after_submission')

    @cached_property
    def can_pay_after_request(self) -> bool:
        return can_make_action(admission=self.admission, action_name='pay_after_request')

    def has_permission(self):
        return self.can_pay_after_request or self.can_pay_after_submission

    def post(self, request, *args, **kwargs):
        if 'valid-payment' in self.request.POST:
            if self.can_pay_after_submission and self.can_pay_after_request:
                raise ImproperlyConfigured(
                    _('An user can pay either after submitting its application or after a request from a manager.')
                )

            if self.can_pay_after_submission:
                AdmissionPropositionService.pay_application_fees_after_submission(
                    person=self.person,
                    uuid=self.admission_uuid,
                )
                self.request.session['submitted'] = True
            elif self.can_pay_after_request:
                AdmissionPropositionService.pay_application_fees_after_request(
                    person=self.person,
                    uuid=self.admission_uuid,
                )
                messages.success(self.request, _('The payment has been processed.'))

        elif 'invalid-payment' in self.request.POST:
            messages.error(self.request, _('An error occurred during your payment.'))
            return self.get(request, *args, **kwargs)
        else:
            raise BadRequest

        return HttpResponseRedirect(resolve_url(self.base_namespace, pk=self.admission_uuid))
