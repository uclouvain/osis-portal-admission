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
from django.contrib.messages import add_message, info
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.utils.functional import cached_property
from django.utils.translation import gettext as _
from django.views.generic import TemplateView

from admission.constants import PROPOSITION_JUST_SUBMITTED
from admission.contrib.enums.payment import PaymentStatus, PaymentSessionValue
from admission.contrib.views.mixins import LoadDossierViewMixin
from admission.services.proposition import AdmissionPropositionService
from admission.templatetags.admission import can_make_action
from frontoffice.settings.osis_sdk.utils import MultipleApiBusinessException

__all__ = [
    'AdmissionPaymentView',
]


class AdmissionPaymentView(LoadDossierViewMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'admission/details/payment.html'
    urlpatterns = 'payment'

    @cached_property
    def can_pay_after_submission(self) -> bool:
        return can_make_action(admission=self.admission, action_name='pay_after_submission')

    @cached_property
    def can_pay_after_request(self) -> bool:
        return can_make_action(admission=self.admission, action_name='pay_after_request')

    @property
    def session_key(self):
        return f'pay_fees_{self.admission_uuid}'

    def has_permission(self):
        return can_make_action(admission=self.admission, action_name='view_payment')

    def get(self, request, *args, **kwargs):
        all_payments = AdmissionPropositionService.list_application_fees_payments(
            person=self.person,
            uuid=self.admission_uuid,
        )
        paid_payments = [payment for payment in all_payments if payment.statut == PaymentStatus.PAID.name]
        already_paid = bool(paid_payments)
        from_mollie = bool(self.request.GET.get('from_mollie'))
        recent_session_payment = self.request.session.get(self.session_key)
        can_pay = self.can_pay_after_submission or self.can_pay_after_request

        # The candidate has already paid the application fee
        if already_paid:
            # The proposition has been updated since the payment
            if not can_pay and recent_session_payment:
                event, payment_id = recent_session_payment.split(':')
                del self.request.session[self.session_key]

                if any(payment.identifiant_paiement == payment_id for payment in paid_payments):
                    if event == PaymentSessionValue.CANDIDATE_JUST_PAID_AFTER_SUBMISSION.name:
                        # Display a popup
                        self.request.session[PROPOSITION_JUST_SUBMITTED] = self.current_context
                    elif event == PaymentSessionValue.CANDIDATE_JUST_PAID_AFTER_MANAGER_REQUEST.name:
                        # Display a message
                        info(
                            request,
                            _('Your payment for the application {reference} has been taken into account.').format(
                                reference=self.admission.reference
                            ),
                        )
                    return redirect(self.base_namespace, pk=self.admission_uuid)

        elif not from_mollie:
            # The candidate has not paid the application fee and doesn't come from Mollie
            try:
                created_payment = None
                if self.can_pay_after_submission:
                    created_payment = AdmissionPropositionService.open_application_fees_payment_after_submission(
                        person=self.person,
                        uuid=self.admission_uuid,
                    )
                elif self.can_pay_after_request:
                    created_payment = AdmissionPropositionService.open_application_fees_payment_after_request(
                        person=self.person,
                        uuid=self.admission_uuid,
                    )

                if created_payment and created_payment.url_checkout:
                    # The candidate can pay the application fee and doesn't come from Mollie
                    self.request.session[self.session_key] = '{}:{}'.format(
                        PaymentSessionValue.CANDIDATE_JUST_PAID_AFTER_SUBMISSION.name
                        if self.can_pay_after_submission
                        else PaymentSessionValue.CANDIDATE_JUST_PAID_AFTER_MANAGER_REQUEST.name,
                        created_payment.identifiant_paiement,
                    )
                    return HttpResponseRedirect(created_payment.url_checkout)

            except MultipleApiBusinessException as multiple_exception:
                for exception in multiple_exception.exceptions:
                    add_message(request, messages.ERROR, exception.detail)

        return super().get(request, *args, **kwargs, already_paid=already_paid, payments=paid_payments, can_pay=can_pay)
