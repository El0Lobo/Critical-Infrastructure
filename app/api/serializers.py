from __future__ import annotations

from django.contrib.auth.models import Group
from rest_framework import serializers

from app.assets.models import Asset, Collection, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]


class CollectionSerializer(serializers.ModelSerializer):
    allowed_groups = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(), many=True, required=False
    )
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True, required=False)
    parent_title = serializers.CharField(source="parent.title", read_only=True)
    tags_detail = TagSerializer(source="tags", many=True, read_only=True)
    allowed_group_names = serializers.SerializerMethodField()

    class Meta:
        model = Collection
        fields = [
            "id",
            "title",
            "slug",
            "parent",
            "parent_title",
            "visibility_mode",
            "allowed_groups",
            "allowed_group_names",
            "description",
            "tags",
            "tags_detail",
            "sort_order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
            "allowed_group_names",
            "parent_title",
            "tags_detail",
        ]

    def get_allowed_group_names(self, obj):
        return list(obj.allowed_groups.values_list("name", flat=True))


class AssetSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True, required=False)
    collection_title = serializers.CharField(source="collection.title", read_only=True)
    effective_visibility = serializers.CharField(read_only=True)
    file = serializers.FileField(required=False, allow_null=True, write_only=True)
    file_url = serializers.SerializerMethodField()
    tags_detail = TagSerializer(source="tags", many=True, read_only=True)

    class Meta:
        model = Asset
        fields = [
            "id",
            "collection",
            "collection_title",
            "title",
            "slug",
            "visibility",
            "effective_visibility",
            "description",
            "file",
            "file_url",
            "url",
            "text_content",
            "appears_on",
            "mime_type",
            "kind",
            "size_bytes",
            "width",
            "height",
            "duration_seconds",
            "pages",
            "tags",
            "tags_detail",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "collection_title",
            "effective_visibility",
            "mime_type",
            "kind",
            "size_bytes",
            "width",
            "height",
            "duration_seconds",
            "pages",
            "created_at",
            "updated_at",
            "file_url",
            "tags_detail",
        ]

    def get_file_url(self, obj: Asset) -> str | None:
        if obj.file:
            try:
                return obj.file.url
            except ValueError:
                return None
        return None

    def validate(self, attrs):
        provided_sources: list[str] = []
        for key in ("file", "url", "text_content"):
            if key not in attrs:
                continue
            value = attrs[key]
            if isinstance(value, str):
                value = value.strip()
                attrs[key] = value
            if value:
                provided_sources.append(key)

        if self.instance is None:
            if len(provided_sources) != 1:
                raise serializers.ValidationError(
                    "Provide exactly one source (file OR url OR text_content)."
                )
        else:
            if len(provided_sources) > 1:
                raise serializers.ValidationError(
                    "Provide at most one source when updating an asset."
                )
        return attrs

    def _apply_source_updates(self, instance: Asset, attrs: dict) -> None:
        source_keys = ("file", "url", "text_content")
        source_updated = False
        for key in source_keys:
            if key in attrs:
                source_updated = True
                break

        if not source_updated:
            return

        file = attrs.pop("file", None)
        url = attrs.pop("url", "")
        text = attrs.pop("text_content", "")

        if file:
            instance.file = file
            instance.url = ""
            instance.text_content = ""
        elif url:
            instance.url = url
            instance.file = None
            instance.text_content = ""
        elif text:
            instance.text_content = text
            instance.file = None
            instance.url = ""

    def create(self, validated_data):
        tags = validated_data.pop("tags", [])
        file = validated_data.pop("file", None)
        url = validated_data.pop("url", "")
        text = validated_data.pop("text_content", "")

        asset = Asset(**validated_data)
        if file:
            asset.file = file
        elif url:
            asset.url = url
        else:
            asset.text_content = text
        asset.save()
        if tags:
            asset.tags.set(tags)
        return asset

    def update(self, instance, validated_data):
        tags = validated_data.pop("tags", None)
        self._apply_source_updates(instance, validated_data)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if tags is not None:
            instance.tags.set(tags)
        return instance
