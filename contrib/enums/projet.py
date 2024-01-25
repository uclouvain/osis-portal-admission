# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.utils.translation import gettext_lazy as _

from base.models.utils.utils import ChoiceEnum


class ChoixLangueRedactionThese(ChoiceEnum):
    FRENCH = _('French')
    ENGLISH = _('English')
    OTHER = _('Other')
    UNDECIDED = _('Undecided')


class ChoixStatutPropositionDoctorale(ChoiceEnum):
    ANNULEE = _('Cancelled application')
    EN_BROUILLON = _('In draft form')
    CONFIRMEE = _('Application confirmed (by student)')
    EN_ATTENTE_DE_SIGNATURE = _('Waiting for signature')
    INSCRIPTION_AUTORISEE = _('Application accepted')


class ChoixStatutPropositionGenerale(ChoiceEnum):
    EN_BROUILLON = _('In draft form')
    FRAIS_DOSSIER_EN_ATTENTE = _('Pending application fee')
    CONFIRMEE = _('Application confirmed (by student)')
    ANNULEE = _('Cancelled application')
    INSCRIPTION_AUTORISEE = _('Application accepted')
    INSCRIPTION_REFUSEE = _('Application denied')
    CLOTUREE = _('Closed')
    # More detailed status are hidden by osis
    A_COMPLETER = _('To be completed')
    TRAITEMENT_UCLOUVAIN_EN_COURS = _('UCLouvain processing in progress')


class ChoixStatutPropositionContinue(ChoiceEnum):
    ANNULEE = _('Cancelled application')
    # During the enrolment step
    EN_BROUILLON = _('In draft form')
    CONFIRMEE = _('Application confirmed (by student)')
    # After the enrolment step
    INSCRIPTION_AUTORISEE = _('Application accepted')


IN_PROGRESS_STATUSES = {
    ChoixStatutPropositionDoctorale.EN_BROUILLON.name,
    ChoixStatutPropositionDoctorale.EN_ATTENTE_DE_SIGNATURE.name,
    ChoixStatutPropositionGenerale.EN_BROUILLON.name,
    ChoixStatutPropositionContinue.EN_BROUILLON.name,
}

CANCELLED_STATUSES = {
    ChoixStatutPropositionDoctorale.ANNULEE.name,
    ChoixStatutPropositionGenerale.ANNULEE.name,
    ChoixStatutPropositionContinue.ANNULEE.name,
}
