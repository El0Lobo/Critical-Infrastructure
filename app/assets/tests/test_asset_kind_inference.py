"""Tests for Asset kind inference algorithm."""

from django.test import TestCase

from app.assets.models import Asset, Collection, infer_kind


class AssetKindInferenceTests(TestCase):
    """Test the infer_kind function that determines asset type."""

    def test_infer_kind_text_content_takes_priority(self):
        """Text content should always result in 'note' kind."""
        kind = infer_kind("image.jpg", "image/jpeg", has_text=True)
        self.assertEqual(kind, "note")

    def test_infer_kind_image_from_mime(self):
        """Image MIME types should return 'image'."""
        test_cases = [
            ("file.jpg", "image/jpeg"),
            ("file.png", "image/png"),
            ("file.gif", "image/gif"),
            ("file.webp", "image/webp"),
            ("file.svg", "image/svg+xml"),
        ]
        for filename, mime in test_cases:
            with self.subTest(filename=filename, mime=mime):
                kind = infer_kind(filename, mime, has_text=False)
                self.assertEqual(kind, "image")

    def test_infer_kind_video_from_mime(self):
        """Video MIME types should return 'video'."""
        test_cases = [
            ("file.mp4", "video/mp4"),
            ("file.webm", "video/webm"),
            ("file.mov", "video/quicktime"),
            ("file.ogv", "video/ogg"),
        ]
        for filename, mime in test_cases:
            with self.subTest(filename=filename, mime=mime):
                kind = infer_kind(filename, mime, has_text=False)
                self.assertEqual(kind, "video")

    def test_infer_kind_audio_from_mime(self):
        """Audio MIME types should return 'audio'."""
        test_cases = [
            ("file.mp3", "audio/mpeg"),
            ("file.wav", "audio/wav"),
            ("file.ogg", "audio/ogg"),
            ("file.m4a", "audio/m4a"),
        ]
        for filename, mime in test_cases:
            with self.subTest(filename=filename, mime=mime):
                kind = infer_kind(filename, mime, has_text=False)
                self.assertEqual(kind, "audio")

    def test_infer_kind_font_from_mime(self):
        """Font MIME types should return 'font'."""
        test_cases = [
            ("file.woff2", "font/woff2"),
            ("file.woff", "font/woff"),
            ("file.ttf", "font/ttf"),
            ("file.otf", "font/otf"),
            ("file.woff", "application/font-woff"),
        ]
        for filename, mime in test_cases:
            with self.subTest(filename=filename, mime=mime):
                kind = infer_kind(filename, mime, has_text=False)
                self.assertEqual(kind, "font")

    def test_infer_kind_pdf_from_mime(self):
        """PDF MIME type should return 'pdf'."""
        kind = infer_kind("document.pdf", "application/pdf", has_text=False)
        self.assertEqual(kind, "pdf")

    def test_infer_kind_doc_from_mime(self):
        """Document MIME types should return 'doc'."""
        test_cases = [
            ("file.doc", "application/msword"),
            (
                "file.docx",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
            ("file.xls", "application/vnd.ms-excel"),
            ("file.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            ("file.ppt", "application/vnd.ms-powerpoint"),
            (
                "file.pptx",
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ),
            ("file.txt", "text/plain"),
            ("file.rtf", "application/rtf"),
            ("file.odt", "application/vnd.oasis.opendocument.text"),
        ]
        for filename, mime in test_cases:
            with self.subTest(filename=filename, mime=mime):
                kind = infer_kind(filename, mime, has_text=False)
                self.assertEqual(kind, "doc")

    def test_infer_kind_archive_from_mime(self):
        """Archive MIME types should return 'archive'."""
        test_cases = [
            ("file.zip", "application/zip"),
            ("file.zip", "application/x-zip-compressed"),
            ("file.tar", "application/x-tar"),
            ("file.gz", "application/gzip"),
            ("file.7z", "application/x-7z-compressed"),
        ]
        for filename, mime in test_cases:
            with self.subTest(filename=filename, mime=mime):
                kind = infer_kind(filename, mime, has_text=False)
                self.assertEqual(kind, "archive")

    def test_infer_kind_font_from_extension_fallback(self):
        """Font extensions should return 'font' even without MIME."""
        test_cases = [
            ("file.woff2", None),
            ("file.woff", None),
            ("file.ttf", None),
            ("file.otf", None),
        ]
        for filename, mime in test_cases:
            with self.subTest(filename=filename):
                kind = infer_kind(filename, mime, has_text=False)
                self.assertEqual(kind, "font")

    def test_infer_kind_image_from_extension_fallback(self):
        """Image extensions should return 'image' even without MIME."""
        test_cases = [
            "file.jpg",
            "file.jpeg",
            "file.png",
            "file.gif",
            "file.webp",
            "file.avif",
            "file.svg",
        ]
        for filename in test_cases:
            with self.subTest(filename=filename):
                kind = infer_kind(filename, None, has_text=False)
                self.assertEqual(kind, "image")

    def test_infer_kind_video_from_extension_fallback(self):
        """Video extensions should return 'video' even without MIME."""
        test_cases = ["file.mp4", "file.webm", "file.mov", "file.m4v", "file.ogv"]
        for filename in test_cases:
            with self.subTest(filename=filename):
                kind = infer_kind(filename, None, has_text=False)
                self.assertEqual(kind, "video")

    def test_infer_kind_audio_from_extension_fallback(self):
        """Audio extensions should return 'audio' even without MIME."""
        test_cases = ["file.mp3", "file.wav", "file.ogg", "file.m4a", "file.flac"]
        for filename in test_cases:
            with self.subTest(filename=filename):
                kind = infer_kind(filename, None, has_text=False)
                self.assertEqual(kind, "audio")

    def test_infer_kind_pdf_from_extension_fallback(self):
        """PDF extension should return 'pdf' even without MIME."""
        kind = infer_kind("document.pdf", None, has_text=False)
        self.assertEqual(kind, "pdf")

    def test_infer_kind_doc_from_extension_fallback(self):
        """Document extensions should return 'doc' even without MIME."""
        test_cases = [
            "file.doc",
            "file.docx",
            "file.xls",
            "file.xlsx",
            "file.ppt",
            "file.pptx",
            "file.txt",
            "file.rtf",
            "file.odt",
        ]
        for filename in test_cases:
            with self.subTest(filename=filename):
                kind = infer_kind(filename, None, has_text=False)
                self.assertEqual(kind, "doc")

    def test_infer_kind_archive_from_extension_fallback(self):
        """Archive extensions should return 'archive' even without MIME."""
        test_cases = ["file.zip", "file.tar", "file.gz", "file.7z"]
        for filename in test_cases:
            with self.subTest(filename=filename):
                kind = infer_kind(filename, None, has_text=False)
                self.assertEqual(kind, "archive")

    def test_infer_kind_unknown_returns_other(self):
        """Unknown file types should return 'other'."""
        kind = infer_kind("file.xyz", "application/unknown", has_text=False)
        self.assertEqual(kind, "other")

    def test_infer_kind_no_filename_no_mime(self):
        """No filename and no MIME should return 'other'."""
        kind = infer_kind("", None, has_text=False)
        self.assertEqual(kind, "other")

    def test_infer_kind_case_insensitive_extension(self):
        """Extension matching should be case-insensitive."""
        test_cases = [
            ("FILE.JPG", None, "image"),
            ("FILE.PDF", None, "pdf"),
            ("FILE.ZIP", None, "archive"),
            ("FILE.MP4", None, "video"),
            ("FILE.MP3", None, "audio"),
        ]
        for filename, mime, expected in test_cases:
            with self.subTest(filename=filename):
                kind = infer_kind(filename, mime, has_text=False)
                self.assertEqual(kind, expected)


class AssetModelTests(TestCase):
    """Test Asset model integration with kind inference."""

    def setUp(self):
        self.collection = Collection.objects.create(title="Test Collection", slug="test-collection")

    def test_asset_with_text_content_is_note(self):
        """Assets with text_content should be 'note' kind."""
        asset = Asset.objects.create(
            collection=self.collection,
            title="Test Note",
            slug="test-note",
            text_content="This is a note",
            kind="note",
        )
        self.assertEqual(asset.kind, "note")

    def test_asset_visibility_inherit_default(self):
        """Assets should default to 'inherit' visibility."""
        asset = Asset.objects.create(
            collection=self.collection,
            title="Test Asset",
            slug="test-asset",
            text_content="content",
        )
        self.assertEqual(asset.visibility, "inherit")

    def test_asset_visibility_choices(self):
        """Test all visibility choice values."""
        choices = ["inherit", "public", "internal"]
        for choice in choices:
            with self.subTest(visibility=choice):
                asset = Asset.objects.create(
                    collection=self.collection,
                    title=f"Asset {choice}",
                    slug=f"asset-{choice}",
                    visibility=choice,
                    text_content="test",
                )
                self.assertEqual(asset.visibility, choice)


class CollectionModelTests(TestCase):
    """Test Collection model."""

    def test_collection_slug_auto_generated(self):
        """Collection should auto-generate slug from title."""
        collection = Collection.objects.create(title="Test Collection")
        self.assertEqual(collection.slug, "test-collection")

    def test_collection_hierarchy(self):
        """Collections should support parent-child relationships."""
        parent = Collection.objects.create(title="Parent", slug="parent")
        child = Collection.objects.create(title="Child", slug="child", parent=parent)

        self.assertEqual(child.parent, parent)
        self.assertIn(child, parent.children.all())

    def test_collection_visibility_modes(self):
        """Test all visibility mode choices."""
        modes = ["public", "internal", "groups"]
        for mode in modes:
            with self.subTest(mode=mode):
                collection = Collection.objects.create(
                    title=f"Collection {mode}", slug=f"collection-{mode}", visibility_mode=mode
                )
                self.assertEqual(collection.visibility_mode, mode)

    def test_collection_default_visibility_public(self):
        """Collections should default to public visibility."""
        collection = Collection.objects.create(title="Test", slug="test")
        self.assertEqual(collection.visibility_mode, "public")

    def test_collection_ordering(self):
        """Collections should be ordered by parent, sort_order, title."""
        Collection.objects.create(title="Zebra", slug="zebra", sort_order=10)
        Collection.objects.create(title="Alpha", slug="alpha", sort_order=5)
        Collection.objects.create(title="Beta", slug="beta", sort_order=5)

        collections = list(Collection.objects.all())
        # Sort order 5 comes first, then alphabetically
        self.assertEqual(collections[0].slug, "alpha")
        self.assertEqual(collections[1].slug, "beta")
        self.assertEqual(collections[2].slug, "zebra")
