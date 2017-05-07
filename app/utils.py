import os
from collections import OrderedDict

from app import app
from app.models import Page, Link
import sqlalchemy
from flask import render_template, url_for

def render_with_navbar(template, **kwargs):
    # unions Links and Pages, then sorts by index
    query_pages = Page.query.with_entities(Page.id_, Page.title, Page.name, sqlalchemy.null().label("url"), Page.index, Page.category, Page.divider_below)
    query_links = Link.query.with_entities(Link.id_, Link.title, sqlalchemy.null().label("name"), Link.url, Link.index, Link.category, Link.divider_below)
    query_all = query_pages.union_all(query_links).order_by(Page.index)

    pages = OrderedDict([('Hidden', query_all.filter_by(category='Hidden').all()),
                         ('Calendars', query_all.filter_by(category='Calendars').all()),
                         ('About Us', query_all.filter_by(category='About Us').all()),
                         ('Academics', query_all.filter_by(category='Academics').all()),
                         ('Students', query_all.filter_by(category='Students').all()),
                         ('Parents', query_all.filter_by(category='Parents').all()),
                         ('Admissions', query_all.filter_by(category='Admissions').all())])
    return render_template(template, pages=pages, **kwargs)

def get_uploads():
    """gets the images and other files from the uploads directory
    and returns two lists of tuples in the form (name, path)
    """

    images = [('none', '')]
    others = [('none', '')]

    uploads = os.listdir(os.path.join(app.root_path, app.config['UPLOAD_FOLDER']))
    uploads.remove(".gitignore")
    # sort by time last modified
    uploads.sort(key=lambda filename: os.stat(os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], filename)).st_mtime)
    image_extensions = ["png", "jpg", "jpeg", "gif", "bmp"]

    for upload in uploads:
        if '.' in upload and upload.rsplit('.', 1)[1].lower() in image_extensions:
            images.append(('/uploads/' + upload, upload))
        else:
            others.append(('/uploads/' + upload, upload))
    return images, others

# custom widget for rendering a TinyMCE input
def TinyMCE(field):
    images, links = get_uploads()
    image_list = link_list = "["
    for image in images[1:]:
        image_list += "{{title: '{1}', value: '{0}'}},".format(*image)
    for link in links[1:]:
        link_list += "{{title: '{1}', value: '{0}'}},".format(*link)

    hidden_pages = Page.query.filter_by(category="Hidden").all()
    for page in hidden_pages:
        link_list += "{{title: '{}', value: '/page/{}'}},".format(page.title, page.name)

    image_list = "[]" if image_list == "[" else image_list[:-1] + "]"
    link_list = "[]" if link_list == "[" else link_list[:-1] + "]"

    return """  <script src=' """ + url_for('static', filename='js/tinymce/tinymce.full.min.js') + """ '></script>
                <script src=' """ + url_for('static', filename='js/tinymce-form.js') + """ '></script>
         <script>
            tinymce.init({
            selector:'#editor',
            theme: 'modern',
            height: 800,
            convert_urls: false,
            fontsize_formats: '8pt 10pt 11pt 12pt 14pt 18pt 24pt 36pt',
			plugins: [
            'advlist autolink link image lists charmap preview hr anchor',
            'wordcount visualblocks visualchars code nonbreaking',
            'table contextmenu paste textcolor'
            ],
            table_default_attributes: {
            class: 'table-condensed'
            },
            content_css: '/static/css/tinymce.css',
            toolbar: 'styleselect | fontsizeselect | bold italic underline | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | link image | forecolor backcolor',
            plugin_preview_height: 600,
            plugin_preview_width: 925,
            link_context_toolbar: true,
            link_title: false,
            image_advtab: true,
            image_title: true,
            image_description: false,
            image_list: %s,
            link_list: %s
         });
         </script>
         <textarea id='editor'> %s </textarea>""" % (image_list, link_list, field._value())
