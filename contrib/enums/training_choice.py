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

from django.utils.translation import gettext_lazy as _

from base.models.utils.utils import ChoiceEnum


class TypeFormation(ChoiceEnum):
    BACHELIER = _('Bachelor')
    MASTER = _('Master')
    DOCTORAT = _('Doctorate')
    AGREGATION_CAPES = _('Aggregation and CAPAES')
    FORMATION_CONTINUE = _('Continuing education')
    CERTIFICAT = _("Certificate")

    @classmethod
    def general_choices(cls):
        return tuple((x.name, x.value) for x in cls if x.name in TYPES_FORMATION_GENERALE)


TYPES_FORMATION_GENERALE = {
    TypeFormation.BACHELIER.name,
    TypeFormation.MASTER.name,
    TypeFormation.AGREGATION_CAPES.name,
    TypeFormation.CERTIFICAT.name,
}

OSIS_ADMISSION_EDUCATION_TYPES_MAPPING = {
    TypeFormation.BACHELIER.name: [
        'BACHELOR',
    ],
    TypeFormation.MASTER.name: [
        'MASTER_MA_120',
        'MASTER_MD_120',
        'MASTER_MS_120',
        'MASTER_MS_180_240',
        'MASTER_M1',
        'MASTER_MC',
    ],
    TypeFormation.DOCTORAT.name: [
        'PHD',
    ],
    TypeFormation.AGREGATION_CAPES.name: [
        'AGGREGATION',
        'CAPAES',
    ],
    TypeFormation.FORMATION_CONTINUE.name: [
        'CERTIFICATE_OF_PARTICIPATION',
        'CERTIFICATE_OF_SUCCESS',
        'UNIVERSITY_FIRST_CYCLE_CERTIFICATE',
        'UNIVERSITY_SECOND_CYCLE_CERTIFICATE',
    ],
    TypeFormation.CERTIFICAT.name: [
        'CERTIFICATE',
        'RESEARCH_CERTIFICATE',
    ],
}

GENERAL_EDUCATION_TYPES = set(
    OSIS_ADMISSION_EDUCATION_TYPES_MAPPING.get(TypeFormation.BACHELIER.name)
    + OSIS_ADMISSION_EDUCATION_TYPES_MAPPING.get(TypeFormation.MASTER.name)
    + OSIS_ADMISSION_EDUCATION_TYPES_MAPPING.get(TypeFormation.AGREGATION_CAPES.name)
    + OSIS_ADMISSION_EDUCATION_TYPES_MAPPING.get(TypeFormation.CERTIFICAT.name)
)

CONTINUING_EDUCATION_TYPES = set(OSIS_ADMISSION_EDUCATION_TYPES_MAPPING.get(TypeFormation.FORMATION_CONTINUE.name))

DOCTORATE_EDUCATION_TYPES = set(OSIS_ADMISSION_EDUCATION_TYPES_MAPPING.get(TypeFormation.DOCTORAT.name))

ADMISSION_EDUCATION_TYPE_BY_OSIS_TYPE = {
    osis_type: admission_type
    for admission_type, osis_types in OSIS_ADMISSION_EDUCATION_TYPES_MAPPING.items()
    for osis_type in osis_types
}
