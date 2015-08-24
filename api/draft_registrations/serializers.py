from framework.auth.core import Auth
from rest_framework import serializers as ser
from django.utils.translation import ugettext_lazy as _
from rest_framework.exceptions import PermissionDenied, NotFound

from website.project.model import Q
from api.base.utils import token_creator
from api.base.utils import get_object_or_404
from api.base.serializers import JSONAPISerializer
from website.project.model import DraftRegistration, Node
from website.project.views.drafts import get_schema_or_fail
from api.nodes.serializers import NodeSerializer, DraftRegistrationSerializer


class DraftRegSerializer(DraftRegistrationSerializer):
    def update(self, instance, validated_data):
        """Update instance with the validated data. Requires
        the request to be in the serializer context.
        """

        schema_data = validated_data.get('registration_metadata', {})
        schema_name = validated_data.get('schema_name')
        schema_version = int(validated_data.get('schema_version', 1))
        if schema_name:
            meta_schema = get_schema_or_fail(
                Q('name', 'eq', schema_name) &
                Q('schema_version', 'eq', schema_version)
            )

            existing_schema = instance.registration_schema
            if existing_schema:
                if (existing_schema.name, existing_schema.schema_version) != (meta_schema.name, meta_schema.schema_version):
                    instance.registration_schema = meta_schema
            else:
                instance.registration_schema = meta_schema

        instance.registration_metadata = schema_data
        instance.save()
        return instance
    class Meta:
        type_ = 'registrations'


class RegistrationCreateSerializer(JSONAPISerializer):
    draft_id = ser.CharField(source='_id')
    warning_message = ser.CharField(read_only=True)

    class Meta:
        type_ = 'registrations'


class RegistrationCreateSerializerWithToken(NodeSerializer):
    draft_id = ser.CharField(write_only=True)
    id = ser.CharField(read_only=True, source='_id')
    title = ser.CharField(read_only=True)
    description = ser.CharField(read_only=True)
    category = ser.CharField(read_only=True)

    def validate(self, data):
        """ First POST request for creating registration. User given a new URL with a token to confirm they want to register. """
        request = self.context['request']
        user = request.user
        if user.is_anonymous():
            raise PermissionDenied
        view = self.context['view']
        draft = get_object_or_404(DraftRegistration, data['draft_id'])
        node = draft.branched_from
        if node.is_deleted:
            raise NotFound(_('This resource has been deleted'))
        given_token = view.kwargs['token']
        correct_token = token_creator(draft._id, user._id)
        if correct_token != given_token:
            raise ser.ValidationError(_("Incorrect token."))
        return data

    def create(self, validated_data):
        """ Second POST request for creating registration using new URL with token."""
        request = self.context['request']
        draft = get_object_or_404(DraftRegistration, validated_data['draft_id'])
        node = draft.branched_from
        schema = draft.registration_schema
        data = draft.registration_metadata
        user = request.user
        registration = node.register_node(
            schema=schema,
            auth=Auth(user),
            data=data
        )
        registration.is_deleted = False
        registration.registered_from = get_object_or_404(Node, node._id)
        registration.save()
        return registration
