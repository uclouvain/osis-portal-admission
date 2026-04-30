# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _, gettext

from base.models.utils.utils import ChoiceEnum


class RaisonPlusieursDemandesMemesCycleEtAnnee(ChoiceEnum):
    ANNULER_PRECEDENTES_DEMANDES = _('Create this new application and cancel your other ones')
    SUIVRE_EN_PARALLELE = _('Take several courses at the same time')

    @classmethod
    def choices_with_training_name(cls, training):
        return (
            (
                cls.ANNULER_PRECEDENTES_DEMANDES.name,
                format_html(
                    gettext(
                        'Create an application for <em>{training_name} ({training_campus}) {training_acronym}</em> '
                        'and cancel your other applications'
                    ),
                    training_name=training.intitule or training.intitule_fr,
                    training_campus=training.campus,
                    training_acronym=training.sigle,
                )
            ),
            (cls.SUIVRE_EN_PARALLELE.name, cls.SUIVRE_EN_PARALLELE.value),
        )
