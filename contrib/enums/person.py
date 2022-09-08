# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.utils.translation import pgettext_lazy, gettext_lazy as _

from base.models.utils.utils import ChoiceEnum


class GenderEnum(ChoiceEnum):
    F = pgettext_lazy("female gender", "Female")
    H = pgettext_lazy("gender male", "Male")
    X = _('Other')


class SexEnum(ChoiceEnum):
    F = _('Female')
    M = _('Male')


class CivilState(ChoiceEnum):
    LEGAL_COHABITANT = pgettext_lazy("admission", "Legal cohabitant")
    SINGLE = pgettext_lazy("admission", "Single")
    DIVORCED = pgettext_lazy("admission", "Divorced")
    MARRIED = pgettext_lazy("admission", "Married")
    SEPARATE = pgettext_lazy("admission", "Separate")
    WIDOWED = pgettext_lazy("admission", "Widowed")


class IdentificationType(ChoiceEnum):
    ID_CARD_NUMBER = _('Identity card number')
    PASSPORT_NUMBER = _('Passport number')
