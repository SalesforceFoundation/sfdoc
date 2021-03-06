import os
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from django.conf import settings

from .exceptions import HtmlError
from .utils import is_html
from .utils import is_url_whitelisted
from .utils import skip_html_file
from . import utils
from sfdoc.publish.models import Image


class HTML:
    """Article HTML utility class."""

    def __init__(self, htmlpath, rootpath):
        """Parse article fields from HTML."""
        with open(htmlpath, "r") as f:
            html = f.read()
        soup = BeautifulSoup(html, 'html.parser')

        self.htmlpath = htmlpath
        self.rootpath = rootpath

        # meta (Python attrname, HTML Name, Optional or not)
        for attr, tag_name, optional in (
            ('url_name', 'UrlName', False),
            ('summary', 'description', True),
            ('is_visible_in_csp', 'is-visible-in-csp', False),
            ('is_visible_in_pkb', 'is-visible-in-pkb', False),
            ('is_visible_in_prm', 'is-visible-in-prm', False),
            ('author', settings.ARTICLE_AUTHOR, False),
            ('docset_id', 'ProductMapUUID', True),  # Should be required but will break a lot of tests,
            ('Topics__c', "HubTopics", True),
            ('Article_Type__c', "ArticleType", True),
        ):
            tag = soup.find('meta', attrs={'name': tag_name})
            if optional and (not tag or not tag['content']):
                setattr(self, attr, None)
                continue
            if not tag:
                raise HtmlError('Meta tag name={} not found'.format(tag_name))
            elif not tag['content']:
                raise HtmlError('Meta tag name={} has no content'.format(
                    tag_name,
                ))
            setattr(self, attr, tag['content'])

        # convert some attributes to booleans
        for attr in (
            'is_visible_in_csp',
            'is_visible_in_pkb',
            'is_visible_in_prm',
        ):
            val = True if getattr(self, attr).lower() == 'true' else False
            setattr(self, attr, val)

        # author override (Salesforce org user ID)
        tag = soup.find(
            'meta',
            attrs={'name': settings.ARTICLE_AUTHOR_OVERRIDE},
        )
        self.author_override = tag['content'] if tag else None

        # title
        if not soup.title:
            raise HtmlError('Article title not found')
        self.title = str(soup.title.string)

        # body
        body_tag = soup.find('div', class_=settings.ARTICLE_BODY_CLASS)
        if not body_tag:
            raise HtmlError('Body tag <div class={} ...> not found'.format(
                settings.ARTICLE_BODY_CLASS,
            ))
        self.body = body_tag.renderContents().decode('utf-8')

    def create_article_data(self):
        return {
            'UrlName': self.url_name,
            'Title': self.title,
            'Summary': self.summary,
            'IsVisibleInCsp': self.is_visible_in_csp,
            'IsVisibleInPkb': self.is_visible_in_pkb,
            'IsVisibleInPrm': self.is_visible_in_prm,
            "Article_Type__c": self.Article_Type__c,
            "Topics__c": self.Topics__c,
            settings.SALESFORCE_ARTICLE_BODY_FIELD: self.body,
            settings.SALESFORCE_ARTICLE_AUTHOR_FIELD: self.author,
            settings.SALESFORCE_ARTICLE_AUTHOR_OVERRIDE_FIELD: self.author_override,
        }

    def get_image_paths(self):
        """Get paths to linked images."""
        image_paths = set([])
        soup = BeautifulSoup(self.body, 'html.parser')
        for img in soup('img'):
            image_paths.add(img['src'])
        return image_paths

    def same_as_record(self, record, logger):
        """Compare this object with an article from a Salesforce query."""
        def compare(item1, item2, name):
            if not item1 and not item2:
                return True
            else:
                if item1 == item2:
                    return True
                else:
                    item1_summary = (item1[:20] + '...') if item1 and len(item1) > 75 else item1
                    item2_summary = (item2[:20] + '...') if item2 and len(item2) > 75 else item2

                    diff = (name, item1_summary, item2_summary)
                    differences.append(diff)
        differences = []
        compare(
            self.author,
            record[settings.SALESFORCE_ARTICLE_AUTHOR_FIELD],
            "author"
        )
        compare(
            self.author_override,
            record[settings.SALESFORCE_ARTICLE_AUTHOR_OVERRIDE_FIELD],
            "author_override"
        )
        compare(
            self.is_visible_in_csp,
            record['IsVisibleInCsp'],
            "is_visible_in_csp"
        )
        compare(
            self.is_visible_in_pkb,
            record['IsVisibleInPkb'],
            "is_visible_in_pkb"
        )
        compare(
            self.is_visible_in_prm,
            record['IsVisibleInPrm'],
            "is_visible_in_prm"
        )
        compare(
            self.title,
            record['Title'],
            "title"
        )
        compare(
            self.summary,
            record['Summary'],
            "summary"
        )
        compare(
            self.update_links_production(self.body).strip(),
            record[settings.SALESFORCE_ARTICLE_BODY_FIELD].strip(),
            "body"
        )
        if differences:
            logger.info("Article updated:\n {}", repr(differences))
        return not differences

    def scrub(self):
        """Scrub article body using whitelists for tags/attributes and links."""
        problems = []

        def scrub_tree(tree):
            for child in tree.children:
                if hasattr(child, 'contents'):
                    if child.name not in settings.WHITELIST_HTML:
                        problems.append('Tag "{}" not in whitelist'.format(child.name))
                    else:
                        for attr in child.attrs:
                            if attr not in settings.WHITELIST_HTML[child.name]:
                                problems.append('Tag "{}" attribute "{}" not in whitelist'.format(child.name, attr))
                            if attr in ('href', 'src'):
                                if not is_url_whitelisted(child[attr]):
                                    problems.append('URL {} not whitelisted'.format(child[attr]))
                        scrub_tree(child)
        soup = BeautifulSoup(self.body, 'html.parser')
        scrub_tree(soup)
        return problems

    def update_links_draft(self, docset_id, base_url=""):
        """Update links to draft location."""
        soup = BeautifulSoup(self.body, 'html.parser')

        article_link_count = 1

        for a in soup('a'):
            if 'href' in a.attrs:
                o = urlparse(a['href'])
                if o.scheme or not o.path or not is_html(o.path):
                    continue
                base_url_prefix = ''
                if article_link_count > settings.SALESFORCE_ARTICLE_LINK_LIMIT:
                    base_url_prefix = base_url
                a['href'] = self.update_href(o, base_url_prefix)
                article_link_count += 1
        for img in soup('img'):
            htmldir = os.path.dirname(self.htmlpath)
            abspath_for_img = os.path.abspath(os.path.join(htmldir, img["src"]))
            assert os.path.exists(abspath_for_img), abspath_for_img
            relname = utils.bundle_relative_path(self.rootpath, abspath_for_img)
            img["src"] = Image.get_url(docset_id, relname, draft=True)
        self.body = str(soup)

    def update_href(self, parsed_url, base_url):
        basename = os.path.basename(parsed_url.path)
        new_href = '{}{}{}'.format(
            base_url,
            settings.SALESFORCE_ARTICLE_URL_PATH_PREFIX,
            os.path.splitext(basename)[0]
            )

        if parsed_url.fragment:
            new_href += '#' + parsed_url.fragment

        return new_href

    @staticmethod
    def update_links_production(html):
        """Update links to production location."""
        soup = BeautifulSoup(html, 'html.parser')

        for img in soup('img'):
            img["src"] = Image.draft_url_or_path_to_public(img["src"])
        return str(soup)


def collect_html_paths(path, logger):
    """Collect the HTML files referenced by the top-level HTMLs in a directory"""
    html_files = set()
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            filename_full = os.path.join(dirpath, filename)
            if is_html(filename):
                if skip_html_file(filename):
                    logger.info(
                        "Skipping file: %s",
                        filename_full.replace(path + os.sep, ""),
                    )
                    continue
                html_files.add(filename_full)

    return html_files
