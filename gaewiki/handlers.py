# encoding=utf-8

import logging
import os
import urllib

from django.utils import simplejson
from google.appengine.api import users
from google.appengine.ext import webapp

import access
import data
import view


class RequestHandler(webapp.RequestHandler):
    def reply(self, content, content_type='text/plain', status=200, save_as=None):
        self.response.headers['Content-Type'] = content_type + '; charset=utf-8'
        if save_as:
            self.response.headers['Content-Disposition'] = 'attachment; filename="%s"' % save_as
        self.response.out.write(content)

    def dump_request(self):
        for k in self.request.arguments():
            logging.debug('%s = %s' % (k, self.request.get(k)))

    def check_open_wiki(self):
        if not access.can_see_most_pages(users.get_current_user(), users.is_current_user_admin()):
            raise Exception('Forbidden.')

    def handle_exception(self, e, debug_mode):
        return webapp.RequestHandler.handle_exception(self, e, debug_mode)


class PageHandler(RequestHandler):
    def get(self, page_name):
        self.show_page(urllib.unquote(page_name).decode('utf-8'))

    def show_page(self, title):
        if title.startswith('w/'):
            raise Exception('No such page.')
        if not access.can_read_page(title, users.get_current_user(), users.is_current_user_admin()):
            raise Exception('Forbidden.')
        page = data.get_page_by_name(title)
        self.reply(view.view_page(page, user=users.get_current_user(), is_admin=users.is_current_user_admin()), content_type='text/html')


class StartPageHandler(PageHandler):
    def get(self):
        self.show_page(data.get_start_page_name())


class EditHandler(RequestHandler):
    def get(self):
        title = self.request.get('page')
        page = data.get_page_by_name(title)
        user = users.get_current_user()
        is_admin = users.is_current_user_admin()
        if not access.can_edit_page(title, user, is_admin):
            raise Exception('Forbidden.')
        if not page.is_saved():
            page = data.get_page_template(title, user, is_admin)
        self.reply(view.edit_page(page), content_type='text/html')

    def post(self):
        title = urllib.unquote(str(self.request.get('name'))).decode('utf-8')
        user = users.get_current_user()
        if not access.can_edit_page(title, user, users.is_current_user_admin()):
            raise Exception('Forbidden.')
        data.update_page(title, body=self.request.get('body'), author=user, delete=self.request.get('delete'))
        self.redirect('/' + urllib.quote(title.encode('utf-8')))


class IndexHandler(RequestHandler):
    def get(self):
        self.reply(view.list_pages(self.get_data()), content_type='text/html')

    def get_data(self):
        self.check_open_wiki()
        return data.get_all_pages()


class IndexFeedHandler(IndexHandler):
    def get(self):
        self.reply(view.list_pages_feed(self.get_data()), content_type='text/html')


class PageHistoryHandler(RequestHandler):
    def get(self):
        title = self.request.get('page')
        if not access.can_read_page(title, users.get_current_user(), users.is_current_user_admin()):
            raise Exception('Forbidden.')
        self.reply(view.show_page_history(title, data.get_page_history(title)), content_type='text/html')


class RobotsHandler(RequestHandler):
    def get(self):
        content = "Sitemap: http://%s/sitemap.xml\n" % (self.request.environ['HTTP_HOST'])
        content += "User-agent: *\n"
        content += "Disallow: /gae-wiki-static/\n"
        content += "Disallow: /w/\n"
        self.reply(content, content_type='text/plain')


class SitemapHandler(RequestHandler):
    def get(self):
        self.check_open_wiki()
        pages = data.get_open_pages()
        self.reply(view.get_sitemap(pages, host=self.request.environ['HTTP_HOST']), content_type='text/xml')


class ChangesHandler(RequestHandler):
    def get(self):
        self.reply(view.get_change_list(data.get_changes()), 'text/html')


class ChangesFeedHandler(RequestHandler):
    def get(self):
        self.reply(view.get_change_feed(data.get_changes()), 'text/xml')


class BackLinksHandler(RequestHandler):
    def get(self):
        title = self.request.get('page')
        if not access.can_read_page(title, users.get_current_user(), users.is_current_user_admin()):
            raise Exception('Forbidden.')
        self.reply(view.get_backlinks(*data.get_backlinks(title)), 'text/html')


class UsersHandler(RequestHandler):
    def get(self):
        self.check_open_wiki()
        self.reply(view.get_users(data.get_users()), 'text/html')


class DataExportHandler(RequestHandler):
    def get(self):
        if not users.is_current_user_admin():
            raise Exception('Forbidden.')
        pages = dict([(p.title, {
            'author': p.author and p.author.wiki_user.email(),
            'updated': p.updated.strftime('%Y-%m-%d %H:%M:%S'),
            'body': p.body,
        }) for p in data.get_all_pages()])
        self.reply(simplejson.dumps(pages), 'application/json', save_as='gae-wiki.json')


class DataImportHandler(RequestHandler):
    def get(self):
        if not users.is_current_user_admin():
            raise Exception('Forbidden.')
        self.reply(view.get_import_form(), 'text/html')

    def post(self):
        if not users.is_current_user_admin():
            raise Exception('Forbidden.')
        merge = self.request.get('merge') != ''

        loaded = simplejson.loads(self.request.get('file'))
        for title, content in loaded.items():
            data.update_page(title, content['body'], content['author'] and users.User(content['author']))


class InterwikiHandler(RequestHandler):
    def get(self):
        iw = data.get_interwikis()
        self.reply(view.show_interwikis(iw), 'text/html')


handlers = [
    ('/', StartPageHandler),
    ('/robots\.txt$', RobotsHandler),
    ('/sitemap\.xml$', SitemapHandler),
    ('/w/backlinks$', BackLinksHandler),
    ('/w/changes$', ChangesHandler),
    ('/w/changes\.rss$', ChangesFeedHandler),
    ('/w/data/export$', DataExportHandler),
    ('/w/data/import$', DataImportHandler),
    ('/w/edit$', EditHandler),
    ('/w/history$', PageHistoryHandler),
    ('/w/index$', IndexHandler),
    ('/w/index\.rss$', IndexFeedHandler),
    ('/w/interwiki$', InterwikiHandler),
    ('/w/users$', UsersHandler),
    ('/(.+)$', PageHandler),
]