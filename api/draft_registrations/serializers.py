from rest_framework import serializers as ser

from website.project.model import Q
from website.project.views import drafts
from api.base.serializers import JSONAPISerializer
from website.project.metadata.schemas import OSF_META_SCHEMAS


class DraftRegSerializer(JSONAPISerializer):
    schema_choices = [schema['name'] for schema in OSF_META_SCHEMAS]

    id = ser.CharField(read_only=True, source='_id')
    branched_from = ser.CharField(read_only=True, help_text="Source node")
    initiator = ser.CharField(read_only=True)
    registration_schema = ser.CharField(read_only=True)
    registration_form = ser.ChoiceField(choices=schema_choices, required=True, write_only=True, help_text="Please select a registration form to initiate registration.")
    registration_metadata = ser.CharField(required=False, help_text="Responses to supplemental registration questions")
    schema_version = ser.IntegerField(help_text="Registration schema version", write_only=True, required=False)
    datetime_initiated = ser.DateTimeField(read_only=True)
    datetime_updated = ser.DateTimeField(read_only=True)

    class Meta:
        type_ = 'draft-registrations'

    def update(self, instance, validated_data):
        """Update instance with the validated data. Requires
        the request to be in the serializer context.
        """
        schema_version = int(validated_data.get('schema_version', 1))
        if "registration_form" in validated_data.keys():
            schema_name = validated_data['registration_form']
            meta_schema = drafts.get_schema_or_fail(
                Q('name', 'eq', schema_name) &
                Q('schema_version', 'eq', schema_version)
            )
        if "registration_metadata" in validated_data.keys():
            instance.registration_metadata = validated_data.get('registration_metadata', {})

        instance.save()
        return instance
