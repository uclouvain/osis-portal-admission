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
from django.utils.translation import gettext_lazy as _, pgettext_lazy

from base.models.utils.utils import ChoiceEnum


class FormuleDefense(ChoiceEnum):
    FORMULE_1 = _('Method 1 (the private defense and the public defense are separated by at least a month')
    FORMULE_2 = _(
        'Method 2 (The private defense and the public defense are organised the same day, and subjected to '
        'an admissibility condition)'
    )


class RoleJury(ChoiceEnum):
    PRESIDENT = _('PRESIDENT')
    SECRETAIRE = _('SECRETAIRE')
    MEMBRE = _('MEMBRE')


class TitreMembre(ChoiceEnum):
    DOCTEUR = _('Doctor')
    PROFESSEUR = _('Professor')
    NON_DOCTEUR = _('Does not have a doctor title')


class GenreMembre(ChoiceEnum):
    FEMININ = pgettext_lazy("female gender", "Female")
    MASCULIN = pgettext_lazy("gender male", "Male")
    AUTRE = _('Other')
