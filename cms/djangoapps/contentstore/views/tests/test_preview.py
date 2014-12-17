"""
Tests for contentstore.views.preview.py
"""
import re

from django.test import TestCase
from django.test.client import RequestFactory

from xblock.core import XBlockAside
from student.tests.factories import UserFactory

from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from contentstore.views.preview import get_preview_fragment
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.test_asides import AsideTestType
from cms.djangoapps.xblock_config.models import StudioConfig


class GetPreviewHtmlTestCase(TestCase):
    """
    Tests for get_preview_fragment.

    Note that there are other existing test cases in test_contentstore that indirectly execute
    get_preview_fragment via the xblock RESTful API.
    """
    @XBlockAside.register_temp_plugin(AsideTestType, 'test_aside')
    def test_preview_fragment(self):
        """
        Test for calling get_preview_html.

        This test used to be specifically about Locators (ensuring that they did not
        get translated to Locations). The test now has questionable value.
        """
        course = CourseFactory.create(default_store=ModuleStoreEnum.Type.split)
        html = ItemFactory.create(
            parent_location=course.location,
            category="html",
            data={'data': "<html>foobar</html>"}
        )

        config = StudioConfig.current()
        config.enabled = True
        config.save()

        request = RequestFactory().get('/dummy-url')
        request.user = UserFactory()
        request.session = {}

        # Call get_preview_fragment directly.
        context = {
            'reorderable_items': set(),
            'read_only': True
        }
        html = get_preview_fragment(request, html, context).content

        # Verify student view html is returned, and the usage ID is as expected.
        html_pattern = re.escape(unicode(course.id.make_usage_key('html', 'replaceme'))).replace('replaceme', r'html_[0-9]*')
        self.assertRegexpMatches(
            html,
            'data-usage-id="{}"'.format(html_pattern)
        )
        self.assertRegexpMatches(html, '<html>foobar</html>')
        self.assertRegexpMatches(html, r"data-block-type=[\"\']test_aside[\"\']")
        self.assertRegexpMatches(html, "Aside rendered")
        # Now ensure the acid_aside is not in the result
        self.assertNotRegexpMatches(html, r"data-block-type=[\"\']acid_aside[\"\']")

    @XBlockAside.register_temp_plugin(AsideTestType, 'test_aside')
    def test_preview_no_asides(self):
        """
        Test for calling get_preview_html.

        This test used to be specifically about Locators (ensuring that they did not
        get translated to Locations). The test now has questionable value.
        """
        course = CourseFactory.create(default_store=ModuleStoreEnum.Type.split)
        html = ItemFactory.create(
            parent_location=course.location,
            category="html",
            data={'data': "<html>foobar</html>"}
        )

        config = StudioConfig.current()
        config.enabled = False
        config.save()

        request = RequestFactory().get('/dummy-url')
        request.user = UserFactory()
        request.session = {}

        # Call get_preview_fragment directly.
        context = {
            'reorderable_items': set(),
            'read_only': True
        }
        html = get_preview_fragment(request, html, context).content

        self.assertNotRegexpMatches(html, r"data-block-type=[\"\']test_aside[\"\']")
        self.assertNotRegexpMatches(html, "Aside rendered")
