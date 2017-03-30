from functools import partial


def lowerFirst(s):
    if not s:
        return s
    return s[0].lower() + s[1:]


class QremisElement:
    def __init__(self, *args, **kwargs):
        # Structural requirement for child classes
        # (abc doesn't have an appropriate dectorator for this,
        # from what I can find)
        if not hasattr(self, "_spec"):
            raise AssertionError("Incorrectly defined child class")
        # Be sure we can build a valid element
        if len(args) == 0 and len(kwargs) == 0:
            raise ValueError("No empty elements!")
        mandatory_fields = set(x for x in self._spec if self._spec[x]['mandatory'] is True)
        provided_fields = set(lowerFirst(x.__class__.__name__) for x in args)
        provided_fields = provided_fields.union(set([x for x in kwargs]))
        for x in provided_fields:
            if x not in self._spec:
                raise TypeError("Erroneous field! - {}".format(x))
        if not mandatory_fields.issubset(provided_fields):
            raise ValueError(
                "The following are required for init, but were not present: {}".format(
                    ", ".join(mandatory_fields - provided_fields)
                )
            )

        # Dynamically build getters, setters, dellers, adders from spec
        for x in self._spec:
            setattr(self, "get_{}".format(x), partial(self.get_field, x))
            setattr(self, "set_{}".format(x),
                    partial(self.set_field, x, _type=self._spec[x]['type'],
                            repeatable=self._spec[x]['repeatable']))
            setattr(self, "del_{}".format(x), partial(self.del_field, x))
            if self._spec[x]['repeatable']:
                setattr(self, "add_{}".format(x), partial(self.add_to_field, x, _type=self._spec[x]['type']))

            # Set the object properties
            # TODO: Unbreak? Remove?
            # I think this has something to do with attribute search order?
            setattr(self, "{}".format(x), property(fget=getattr(self, "get_{}".format(x)),
                                                   fset=getattr(self, "set_{}".format(x)),
                                                   fdel=getattr(self, "del_{}".format(x))))

        # Build the element with the init args
        self._fields = {}
        for x in args:
            if not isinstance(x, QremisElement):
                raise ValueError("Only QremisElement instance are accepted as args")
            if self._spec[lowerFirst(x.__class__.__name__)]['repeatable']:
                getattr(self, "add_{}".format(lowerFirst(x.__class__.__name__)))(x)
            else:
                getattr(self, "set_{}".format(lowerFirst(x.__class__.__name__)))(x)
        for x in kwargs:
            if self._spec[x]['repeatable']:
                getattr(self, "add_{}".format(x))(kwargs[x])
            else:
                getattr(self, "set_{}".format(x))(kwargs[x])

    def set_field(self, fieldname, fieldvalue, _type=None, repeatable=False):
        if repeatable:
            try:
                self.add_to_field(fieldname, fieldvalue, _type=_type)
            except TypeError:  # Maybe its an iter of values
                for x in fieldvalue:
                    self.add_to_field(fieldname, x, _type=_type)
        else:
            if _type is not None:
                if not isinstance(fieldvalue, _type):
                    raise TypeError()
            self._fields[fieldname] = fieldvalue

    def add_to_field(self, fieldname, fieldvalue, _type=None):
        if _type is not None:
            if not isinstance(fieldvalue, _type):
                raise TypeError()
        if fieldname not in self._fields:
            self._fields[fieldname] = []
        self._fields[fieldname].append(fieldvalue)

    def get_field(self, fieldname):
        return self._fields[fieldname]

    def del_field(self, fieldname, index=None):
        # Dynamically removes empty fields
        if index:
            del self._fields[fieldname][index]
            if len(self._fields[fieldname]) == 0:
                del self._fields[fieldname]
        else:
            del self._fields[fieldname]

    def to_dict(self):
        r = {}
        return r


class ObjectExtension(QremisElement):
    _spec = {}


class LinkingRelationshipIdentifier(QremisElement):
    _spec = {
        'linkingRelationshipIdentifierType': {'repeatable': False, 'mandatory': True, 'type': str},
        'linkingRelationshipIdentifierValue': {'repeatable': False, 'mandatory': True, 'type': str}
    }


class LinkingRelationships(QremisElement):
    _spec = {
        'linkingRelationshipIdentifier': {'repeatable': True, 'mandatory': True, 'type': LinkingRelationshipIdentifier}
    }


class EnvironmentExtension(QremisElement):
    _spec = {}


class EnvironmentRegistry(QremisElement):
    _spec = {
        'environmentRegistryName': {'repeatable': False, 'mandatory': True, 'type': str},
        'environmentRegistryKey': {'repeatable': False, 'mandatory': True, 'type': str},
        'environmentRegistryRole': {'repeatable': False, 'mandatory': False, 'type': str}
    }


class EnvironmentDesignationExtension(QremisElement):
    _spec = {}


class EnvironmentDesignation(QremisElement):
    _spec = {
        'environmentName': {'repeatable': False, 'mandatory': True, 'type': str},
        'environmentVersion': {'repeatable': False, 'mandatory': False, 'type': str},
        'environmentOrigin': {'repeatable': False, 'mandatory': False, 'type': str},
        'environmentDesignationNote': {'repeatable': True, 'mandatory': False, 'type': str},
        'environmentDesignationExtension': {'repeatable': True, 'mandatory': False,
                                            'type': EnvironmentDesignationExtension}
    }


class EnvironmentFunction(QremisElement):
    _spec = {
        'environmentFunctionType': {'repeatable': False, 'mandatory': True, 'type': str},
        'environmentFunctionValue': {'repeatable': False, 'mandatory': True, 'type': str}
    }


class KeyInformation(QremisElement):
    _spec = {}


class SignatureInformationExtension(QremisElement):
    _spec = {}


class Signature(QremisElement):
    _spec = {
        'signatureEncoding': {'repeatable': False, 'mandatory': True, 'type': str},
        'signer': {'repeatable': False, 'mandatory': False, 'type': str},
        'signatureMethod': {'repeatable': False, 'mandatory': False, 'type': str},
        'signatureValue': {'repeatable': False, 'mandatory': False, 'type': str},
        'signatureValidationRules': {'repeatable': False, 'mandatory': True, 'type': str},
        'signatureProperties': {'repeatable': True, 'mandatory': False, 'type': str},
        'keyInformation': {'repeatable': False, 'mandatory': False, 'type': KeyInformation}
    }


class SignatureInformation(QremisElement):
    _spec = {
        'signature': {'repeatable': True, 'mandatory': False, 'type': Signature},
        'signatureInformationExtension': {'repeatable': True, 'mandatory': False, 'type': SignatureInformationExtension}
    }


class ContentLocation(QremisElement):
    _spec = {
        'contentLocationType': {'repeatable': False, 'mandatory': True, 'type': str},
        'contentLocationValue': {'repeatable': False, 'mandatory': True, 'type': str}
    }


class Storage(QremisElement):
    _spec = {
        'contentLocation': {'repeatable': False, 'mandatory': False, 'type': ContentLocation},
        'storageMedium': {'repeatable': False, 'mandatory': False, 'type': str}
    }


class Fixity(QremisElement):
    _spec = {
        'messageDigestAlgorithm': {'repeatable': False, 'mandatory': True, 'type': str},
        'messageDigest': {'repeatable': False, 'mandatory': True, 'type': str},
        'messageDigestOriginator': {'repeatable': False, 'mandatory': False, 'type': str}
    }


class FormatRegistry(QremisElement):
    _spec = {
        'formatRegistryName': {'repeatable': False, 'mandatory': True, 'type': str},
        'formatRegistryKey': {'repeatable': False, 'mandatory': True, 'type': str},
        'formatRegistryRole': {'repeatable': False, 'mandatory': False, 'type': str}
    }


class FormatDesignation(QremisElement):
    _spec = {
        'formatName': {'repeatable': False, 'mandatory': True, 'type': str},
        'formatVersion': {'repeatable': False, 'mandatory': False, 'type': str}
    }


class Format(QremisElement):
    _spec = {
        'formatDesignation': {'repeatable': False, 'mandatory': False, 'type': FormatDesignation},
        'formatRegistry': {'repeatable': False, 'mandatory': False, 'type': FormatRegistry},
        'formatNote': {'repeatable': True, 'mandatory': False, 'type': str}
    }


class CreatingApplicationExtension(QremisElement):
    _spec = {}


class CreatingApplication(QremisElement):
    _spec = {
        'creatingApplicationName': {'repeatable': False, 'mandatory': False, 'type': str},
        'creatingApplicationVersion': {'repeatable': False, 'mandatory': True, 'type': str},
        'dateCreatedByApplication': {'repeatable': False, 'mandatory': True, 'type': str},
        'creatingApplicationExtension': {'repeatable': True, 'mandatory': False, 'type': CreatingApplicationExtension}
    }


class Inhibitors(QremisElement):
    _spec = {
        'inhibitorType': {'repeatable': False, 'mandatory': True, 'type': str},
        'inhinitorTarget': {'repeatable': True, 'mandatory': False, 'type': str},
        'inhibitorKey': {'repeatable': False, 'mandatory': False, 'type': str}
    }


class ObjectCharacteristicsExtension(QremisElement):
    _spec = {}


class ObjectCharacteristics(QremisElement):
    _spec = {
        'compositionLevel': {'repeatable': False, 'mandatory': False, 'type': str},
        'fixity': {'repeatable': True, 'mandatory': False, 'type': Fixity},
        'size': {'repeatable': False, 'mandatory': False, 'type': str},
        'format': {'repeatable': True, 'mandatory': True, 'type': Format},
        'creatingApplication': {'repeatable': True, 'mandatory': False, 'type': CreatingApplication},
        'inhibitors': {'repeatable': True, 'mandatory': False, 'type': Inhibitors},
        'objectCharacteristicsExtension': {'repeatable': True, 'mandatory': False,
                                           'type': ObjectCharacteristicsExtension}
    }


class SignificantPropertiesExtension(QremisElement):
    _spec = {}


class SignificantProperties(QremisElement):
    _spec = {
        'significantPropertiesType': {'repeatable': False, 'mandatory': False, 'type': str},
        'significantPropertiesValue': {'repeatable': False, 'mandatory': False, 'type': str},
        'significantPropertiesExtension': {'repeatable': True, 'mandatory': False,
                                           'type': SignificantPropertiesExtension}
    }


class PreservationLevel(QremisElement):
    _spec = {
        'preservationLevelType': {'repeatable': False, 'mandatory': False, 'type': str},
        'preservationLevelValue': {'repeatable': False, 'mandatory': True, 'type': str},
        'preservationLevelRole': {'repeatable': False, 'mandatory': False, 'type': str},
        'preservationLevelRationale': {'repeatable': True, 'mandatory': False, 'type': str},
        'preservationLevelDateAssigned': {'repeatable': False, 'mandatory': False, 'type': str}
    }


class ObjectIdentifier(QremisElement):
    _spec = {
        'objectIdentifierType': {'repeatable': False, 'mandatory': True, 'type': str},
        'objectIdentifierValue': {'repeatable': False, 'mandatory': True, 'type': str}
    }


class Object(QremisElement):
    _spec = {
        'objectIdentifier': {'repeatable': True, 'mandatory': True, 'type': ObjectIdentifier},
        'objectCategory': {'repeatable': False, 'mandatory': True, 'type': str},
        'preservationLevel': {'repeatable': True, 'mandatory': False, 'type': PreservationLevel},
        'significantProperties': {'repeatable': True, 'mandatory': False, 'type': SignificantProperties},
        'objectCharacteristics': {'repeatable': True, 'mandatory': True, 'type': ObjectCharacteristics},
        'originalName': {'repeatable': False, 'mandatory': False, 'type': str},
        'storage': {'repeatable': True, 'mandatory': False, 'type': Storage},
        'signatureInformation': {'mandatory': False, 'repeatable': True, 'type': SignatureInformation},
        'environmentFunction': {'mandatory': False, 'repeatable': True, 'type': EnvironmentFunction},
        'environmentDesignation': {'mandatory': False, 'repeatable': True, 'type': EnvironmentDesignation},
        'environmentRegistry':  {'mandatory': False, 'repeatable': True, 'type': EnvironmentRegistry},
        'environmentExtension': {'mandatory': False, 'repeatable': True, 'type': EnvironmentExtension},
        'linkingRelationships': {'mandatory': False, 'repeatable': False, 'type': LinkingRelationships},
        'objectExtension': {'mandatory': False, 'repeatable': True, 'type': ObjectExtension}
    }


class EventExtension(QremisElement):
    _spec = {}


class EventDetailInformation(QremisElement):
    _spec = {
        'eventDetail': {'repeatable': False, 'mandatory': False, 'type': str},
        'eventDetailExtension': {'repeatable': True, 'mandatory': False, 'type': str}
    }


class EventOutcomeDetailExtension(QremisElement):
    _spec = {}


class EventOutcomeDetail(QremisElement):
    _spec = {
        'eventOutcomeDetailNote': {'repeatable': False, 'mandatory': False, 'type': str},
        'eventOutcomeDetailExtension': {'repeatable': True, 'mandatory': False, 'type': EventOutcomeDetailExtension}
    }


class EventOutcomeInformation(QremisElement):
    _spec = {
        'eventOutcome': {'repeatable': False, 'mandatory': False, 'type': str},
        'eventOutcomeDetail': {'repeatable': True, 'mandatory': False, 'type': EventOutcomeDetail}
    }


class EventIdentifier(QremisElement):
    _spec = {
        'eventIdentifierType': {'repeatable': False, 'mandatory': True, 'type': str},
        'eventIdentifierValue': {'repeatable': False, 'mandatory': True, 'type': str}
    }


class Event(QremisElement):
    _spec = {
        'eventIdentifier': {'repeatable': True, 'mandatory': True, 'type': ObjectIdentifier},
        'eventType': {'repeatable': False, 'mandatory': True, 'type': str},
        'eventDateTime': {'repeatable': False, 'mandatory': True, 'type': str},
        'eventDetailInformation': {'repeatable': True, 'mandatory': False, 'type': EventDetailInformation},
        'eventOutcomeInformation': {'repeatable': True, 'mandatory': False, 'type': EventOutcomeInformation},
        'linkingRelationships': {'repeatable': False, 'mandatory': False, 'type': LinkingRelationships},
        'eventExtension': {'repeatable': True, 'mandatory': False, 'type': EventExtension}
    }


class AgentIdentifier(QremisElement):
    _spec = {
        'agentIdentifierType': {'repeatable': False, 'mandatory': True, 'type': str},
        'agentIdentifierValue': {'repeatable': False, 'mandatory': True, 'type': str}
    }


class Agent(QremisElement):
    _spec = {
        'agentIdentifier': {'repeatable': True, 'mandatory': True, 'type': AgentIdentifier},
        'agentName': {'repeatable': True, 'mandatory': False, 'type': str},
        'agentType': {'repeatable': False, 'mandatory': False, 'type': str},
        'agentVersion': {'repeatable': False, 'mandatory': False, 'type': str},
        'agentNote': {'repeatable': True, 'mandatory': False, 'type': str},
        'linkingRelationships': {'repeatable': False, 'mandatory': False, 'type': LinkingRelationshipIdentifier}
    }


class TermOfGrant(QremisElement):
    _spec = {
        'startDate': {'repeatable': False, 'mandatory': True, 'type': str},
        'endDate': {'repeatable': False, 'mandatory': False, 'type': str}
    }


class TermOfRestriction(QremisElement):
    _spec = {
        'startDate': {'repeatable': False, 'mandatory': True, 'type': str},
        'endDate': {'repeatable': False, 'mandatory': False, 'type': str}
    }


class RightsExtension(QremisElement):
    _spec = {}


class RightsGranted(QremisElement):
    _spec = {
        'act': {'repeatable': False, 'mandatory': True, 'type': str},
        'restriction': {'repeatable': True, 'mandatory': False, 'type': str},
        'termOfGrant': {'repeatable': False, 'mandatory': False, 'type': TermOfGrant},
        'termOfRestriction': {'repeatable': False, 'mandatory': False, 'type': TermOfRestriction},
        'rightsGrantedNote': {'repeatable': True, 'mandatory': False, 'type': str}
    }


class OtherRightsApplicableDates(QremisElement):
    _spec = {
        'startDate': {'repeatable': False, 'mandatory': False, 'type': str},
        'endDate': {'repeatable': False, 'mandatory': False, 'type': str}
    }


class OtherRightsDocumentationIdentifier(QremisElement):
    _spec = {
        'otherRightsDocumentationIdentifierType': {'repeatable': False, 'mandatory': True, 'type': str},
        'otherRightsDocumentationIdentifierValue': {'repeatable': False, 'mandatory': True, 'type': str},
        'otherRightsDocumentationRole': {'repeatable': False, 'mandatory': False, 'type': str}
    }


class OtherRightsInformation(QremisElement):
    _spec = {
        'otherRightsDocumentationIdentifier': {'repeatable': True, 'mandatory': False,
                                               'type': OtherRightsDocumentationIdentifier},
        'otherRightsBasis': {'repeatable': False, 'mandatory': True, 'type': str},
        'otherRightsApplicableDates': {'repeatable': False, 'mandatory': False, 'type': OtherRightsApplicableDates},
        'otherRightsNote': {'repeatable': True, 'mandatory': False, 'type': str}
    }


class StatuteApplicableDates(QremisElement):
    _spec = {
        'startDate': {'repeatable': False, 'mandatory': False, 'type': str},
        'endDate': {'repeatable': False, 'mandatory': False, 'type': str}
    }


class StatuteDocumentationIdentifier(QremisElement):
    _spec = {
        'statuteDocumentationIdentifierType': {'repeatable': False, 'mandatory': True, 'type': str},
        'statuteDocumentationIdentifierValue': {'repeatable': False, 'mandatory': True, 'type': str},
        'statuteDocumentationIdentifierRole': {'repeatable': False, 'mandatory': False, 'type': str}
    }


class StatuteInformation(QremisElement):
    _spec = {
        'statueJurisdiction': {'repeatable': False, 'mandatory': True, 'type': str},
        'statuteCitation': {'repeatable': False, 'mandatory': True, 'type': str},
        'statuteInformationDeterminationDate': {'repeatable': False, 'mandatory': True, 'type': str},
        'statuteNote': {'repeatable': True, 'mandatory': False, 'type': str},
        'statuteDocumentationIdentifier': {'repeatable': True, 'mandatory': False,
                                           'type': StatuteDocumentationIdentifier},
        'statuteApplicableDates': {'repeatable': False, 'mandatory': False, 'type': StatuteApplicableDates}
    }


class LicenseApplicableDates(QremisElement):
    _spec = {
        'startDate': {'repeatable': False, 'mandatory': False, 'type': str},
        'endDate': {'repeatable': False, 'mandatory': False, 'type': str}
    }


class LicenseDocumentationIdentifier(QremisElement):
    _spec = {
        'licenseDocumentationIdentifierType': {'repeatable': False, 'mandatory': True, 'type': str},
        'licenseDocumentationIdentifierValue': {'repeatable': False, 'mandatory': True, 'type': str},
        'licenseDocumentationRole': {'repeatable': False, 'mandatory': False, 'type': str}
    }


class LicenseInformation(QremisElement):
    _spec = {
        'licenseDocumentationIdentifier': {'repeatable': True, 'mandatory': False,
                                           'type': LicenseDocumentationIdentifier},
        'licenseTerms': {'repeatable': False, 'mandatory': False, 'type': str},
        'licenseNote': {'repeatable': True, 'mandatory': False, 'type': str},
        'licenseApplicableDates': {'repeatable': False, 'mandatory': False, 'type': LicenseApplicableDates}
    }


class CopyrightApplicableDates(QremisElement):
    _spec = {
        'startDate': {'repeatable': False, 'mandatory': False, 'type': str},
        'endDate': {'repeatable': False, 'mandatory': False, 'type': str}
    }


class CopyrightDocumentationIdentifier(QremisElement):
    _spec = {
        'copyrightDocumentationIdentifierType': {'repeatable': False, 'mandatory': True, 'type': str},
        'copyrightDocumentationIdentifierValue': {'repeatable': False, 'mandatory': True, 'type': str},
        'copyrightDocumentationRole': {'repeatable': True, 'mandatory': False, 'type': str}
    }


class CopyrightInformation(QremisElement):
    _spec = {
        'copyrightStatus': {'repeatable': False, 'mandatory': True, 'type': str},
        'copyrightJurisdiction': {'repeatable': False, 'mandatory': True, 'type': str},
        'copyrightStatusDeterminationDate': {'repeatable': False, 'mandatory': False, 'type': str},
        'copyrightNote': {'repeatable': True, 'mandatory': False, 'type': str},
        'copyrightDocumentationIdentifier': {'repeatable': True, 'mandatory': False,
                                             'type': CopyrightDocumentationIdentifier},
        'copyrightApplicableDates': {'repeatable': False, 'mandatory': False, 'type': CopyrightApplicableDates}
    }


class RightsStatementIdentifier(QremisElement):
    _spec = {
        'rightsStatementIdentifierType': {'repeatable': False, 'mandatory': True, 'type': str},
        'rightsStatementIdentifierValue': {'repeatable': False, 'mandatory': False, 'type': str}
    }


class RightsStatement(QremisElement):
    _spec = {
        'rightsStatementIdentifier': {'repeatable': False, 'mandatory': True, 'type': RightsStatementIdentifier},
        'rightsBasis': {'repeatable': False, 'mandatory': True, 'type': str},
        'copyrightInformation': {'repeatable': False, 'mandatory': False, 'type': CopyrightInformation},
        'licenseInformation': {'repeatable': False, 'mandatory': False, 'type': LicenseInformation},
        'statuteInformation': {'repeatable': False, 'mandatory': False, 'type': StatuteInformation},
        'otherRightsInformation': {'repeatable': False, 'mandatory': False, 'type': OtherRightsInformation},
        'rightsGranted': {'repeatable': True, 'mandatory': False, 'type': RightsGranted}
    }


class RightsIdentifier(QremisElement):
    _spec = {
        'rightsIdentifierType': {'repeatable': False, 'mandatory': True, 'type': str},
        'rightsIdentifierValue': {'repeatable': False, 'mandatory': True, 'type': str}
    }


class Rights(QremisElement):
    _spec = {
        'rightsIdentifier': {'repeatable': True, 'mandatory': True, 'type': RightsIdentifier},
        'rightsStatement': {'repeatable': True, 'mandatory': False, 'type': RightsStatement},
        'linkingRelationships': {'repeatable': False, 'mandatory': False, 'type': LinkingRelationships},
        'rightsExtension': {'repeatable': True, 'mandatory': False, 'type': RightsExtension}
    }


class RelationshipExtension(QremisElement):
    _spec = {}


class LinkingRightsIdentifier(QremisElement):
    _spec = {
        'linkingRightsIdentifierType': {'repeatable': False, 'mandatory': True, 'type': str},
        'linkingRightsIdentifierValue': {'repeatable': False, 'mandatory': True, 'type': str}
    }


class LinkingAgentIdentifier(QremisElement):
    _spec = {
        'linkingAgentIdentifierType': {'repeatable': False, 'mandatory': True, 'type': str},
        'linkingAgentIdentifierValue': {'repeatable': False, 'mandatory': True, 'type': str}
    }


class LinkingEventIdentifier(QremisElement):
    _spec = {
        'linkingEventIdentifierType': {'repeatable': False, 'mandatory': True, 'type': str},
        'linkingEventIdentifierValue': {'repeatable': False, 'mandatory': True, 'type': str}
    }


class LinkingObjectIdentifier(QremisElement):
    _spec = {
        'linkingObjectIdentifierType': {'repeatable': False, 'mandatory': True, 'type': str},
        'linkingObjectIdentifierValue': {'repeatable': False, 'mandatory': True, 'type': str}
    }


class RelationshipIdentifier(QremisElement):
    _spec = {
        'relationshipIdentifierType': {'repeatable': False, 'mandatory': True, 'type': str},
        'relationshipIdentifierValue': {'repeatable': False, 'mandatory': True, 'type': str}
    }


class Relationship(QremisElement):
    _spec = {
        'relationshipIdentifier': {'repeatable': True, 'mandatory': True, 'type': RelationshipIdentifier},
        'relationshipType': {'repeatable': False, 'mandatory': True, 'type': str},
        'relationshipSubType': {'repeatable': False, 'mandatory': True, 'type': str},
        'linkingObjectIdentifier': {'repeatable': True, 'mandatory': False, 'type': LinkingObjectIdentifier},
        'linkingEventIdentifier':  {'repeatable': True, 'mandatory': False, 'type': LinkingEventIdentifier},
        'linkingAgentIdentifier': {'repeatable': True, 'mandatory': False, 'type': LinkingAgentIdentifier},
        'linkingRightsIdentifier': {'repeatable': True, 'mandatory': False, 'type': LinkingRightsIdentifier},
        'relationshipRole': {'repeatable': False, 'mandatory': False, 'type': str},
        'relationshipSequence': {'repeatable': False, 'mandatory': False, 'type': str},
        'linkingEnvironmentPurpose': {'repeatable': True, 'mandatory': False, 'type': str},
        'linkingEnvironmentCharacteristic': {'repeatable': False, 'mandatory': False, 'type': str},
        'relationshipNote': {'repeatable': True, 'mandatory': False, 'type': str},
        'relationshipExtension': {'repeatable': True, 'mandatory': False, 'type': RelationshipExtension}
    }


class Qremis(QremisElement):
    _spec = {
        'object': {'repeatable': True, 'mandatory': False, 'type': Object},
        'event': {'repeatable': True, 'mandatory': False, 'type': Event},
        'agent': {'repeatable': True, 'mandatory': False, 'type': Agent},
        'rights': {'repeatable': True, 'mandatory': False, 'type': Rights},
        'relationship': {'repeatable': True, 'mandatory': False, 'type': Relationship}
    }


class _RootElement(QremisElement):
    # Makes the recursion for the enumerate_specification function clean
    _spec = {
        'qremis': {'repeatable': False, 'mandatory': True, 'type': Qremis}
    }


def enumerate_specification(kls=_RootElement):
    r = {}
    for x in kls._spec:
        r[x] = {}
        r[x]['repeatable'] = kls._spec[x]['repeatable']
        r[x]['mandatory'] = kls._spec[x]['mandatory']
        r[x]['type'] = kls._spec[x]['type'].__name__
        if kls._spec[x]['type'] not in [str]:  # I'll leave this easily extensible for the moment
            r[x]['spec'] = enumerate_specification(kls=kls._spec[x]['type'])
    return r
