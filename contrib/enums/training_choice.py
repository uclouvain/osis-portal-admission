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


ADMISSION_EDUCATION_TYPE_BY_ADMISSION_CONTEXT = {
    'general-education': {
        TypeFormation.BACHELIER.name,
        TypeFormation.MASTER.name,
        TypeFormation.AGREGATION_CAPES.name,
        TypeFormation.CERTIFICAT.name,
    },
    'continuing-education': {TypeFormation.FORMATION_CONTINUE.name},
    'doctorate': {TypeFormation.DOCTORAT.name},
}


TYPES_FORMATION_GENERALE = ADMISSION_EDUCATION_TYPE_BY_ADMISSION_CONTEXT['general-education']


class TrainingType(ChoiceEnum):
    AGGREGATION = "Aggregation"
    CERTIFICATE_OF_PARTICIPATION = "Certificate of participation"
    CERTIFICATE_OF_SUCCESS = "Certificate of success"
    CERTIFICATE_OF_HOLDING_CREDITS = "Certificate of holding credits"
    BACHELOR = "Bachelor"
    CERTIFICATE = "Certificate"
    CAPAES = "CAPAES"
    RESEARCH_CERTIFICATE = "Research certificate"
    UNIVERSITY_FIRST_CYCLE_CERTIFICATE = "University first cycle certificate"
    UNIVERSITY_SECOND_CYCLE_CERTIFICATE = "University second cycle certificate"
    ACCESS_CONTEST = "Access contest"
    LANGUAGE_CLASS = "Language classes"
    ISOLATED_CLASS = "Isolated classes"
    PHD = "Ph.D"
    FORMATION_PHD = "Formation PhD"
    JUNIOR_YEAR = "Junior year"
    PGRM_MASTER_120 = "Program master 120"
    MASTER_MA_120 = "Master MA 120"
    MASTER_MD_120 = "Master MD 120"
    MASTER_MS_120 = "Master MS 120"
    PGRM_MASTER_180_240 = "Program master 180-240"
    MASTER_MA_180_240 = "Master MA 180-240"
    MASTER_MD_180_240 = "Master MD 180-240"
    MASTER_MS_180_240 = "Master MS 180-240"
    MASTER_M1 = "Master in 60 credits"
    MASTER_MC = "Master of specialist"
    INTERNSHIP = "Internship"


VETERINARY_BACHELOR_CODE = 'VETE1BA'


OSIS_ADMISSION_EDUCATION_TYPES_MAPPING = {
    TypeFormation.BACHELIER.name: [
        TrainingType.BACHELOR.name,
    ],
    TypeFormation.MASTER.name: [
        TrainingType.MASTER_MA_120.name,
        TrainingType.MASTER_MD_120.name,
        TrainingType.MASTER_MS_120.name,
        TrainingType.MASTER_MS_180_240.name,
        TrainingType.MASTER_M1.name,
        TrainingType.MASTER_MC.name,
    ],
    TypeFormation.DOCTORAT.name: [
        TrainingType.PHD.name,
    ],
    TypeFormation.AGREGATION_CAPES.name: [
        TrainingType.AGGREGATION.name,
        TrainingType.CAPAES.name,
    ],
    TypeFormation.FORMATION_CONTINUE.name: [
        TrainingType.CERTIFICATE_OF_PARTICIPATION.name,
        TrainingType.CERTIFICATE_OF_SUCCESS.name,
        TrainingType.UNIVERSITY_FIRST_CYCLE_CERTIFICATE.name,
        TrainingType.UNIVERSITY_SECOND_CYCLE_CERTIFICATE.name,
    ],
    TypeFormation.CERTIFICAT.name: [
        TrainingType.CERTIFICATE.name,
        TrainingType.RESEARCH_CERTIFICATE.name,
    ],
}


ADMISSION_EDUCATION_TYPE_BY_OSIS_TYPE = {
    osis_type: admission_type
    for admission_type, osis_types in OSIS_ADMISSION_EDUCATION_TYPES_MAPPING.items()
    for osis_type in osis_types
}


ADMISSION_CONTEXT_BY_ADMISSION_EDUCATION_TYPE = {
    admission_type: admission_context
    for admission_context, admission_types in ADMISSION_EDUCATION_TYPE_BY_ADMISSION_CONTEXT.items()
    for admission_type in admission_types
}
