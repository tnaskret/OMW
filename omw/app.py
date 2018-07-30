from flask import Flask, render_template, g, request, make_response, Response

from collections import OrderedDict as od

from lib.common_sql import connect_admin, connect_omw, query_omw_direct, query_omw, fetch_allusers

from lib.omw_sql import f_rate_summary, fetch_ssrel, fetch_labels, fetch_src_for_ss_id, fetch_src_meta, \
    fetch_core, fetch_ili, fetch_ss_basic, fetch_langs, fetch_pos, f_ss_id_by_ili_id, fetch_sense, fetch_forms, \
    fetch_src_for_s_id, f_src_id_by_proj_ver, fetch_ss_id_by_src_orginalkey, fetch_src, dd, fetch_ssrel_stats, \
    fetch_src_id_pos_stats, fetch_src_id_stats, fetch_ili_status, fetch_proj

from lib.wn_syntax import licenses

from math import log

from omw.blueprints.api import api
from omw.blueprints.ili import ili
from omw.blueprints.page.views import page
from omw.blueprints.user import user
from omw.blueprints.user.decorator import login_required
from omw.blueprints.user.models import User
from omw.extensions import (
    login_manager,
    csrf)


def create_app(settings_override=None):
    """
    Create a Flask application using the app factory pattern.

    :param settings_override: Override settings
    :return: Flask app
    """
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_object('config.settings')
    app.config.from_pyfile('settings.py', silent=True)

    if settings_override:
        app.config.update(settings_override)

    error_templates(app)
    app.register_blueprint(user)
    app.register_blueprint(api)
    app.register_blueprint(page)
    app.register_blueprint(ili)
    extensions(app)
    authentication(app)

    @app.before_request
    def before_request():
        g.admin = connect_admin()
        g.omw = connect_omw()

    @app.teardown_request
    def teardown_request(exception):
        if hasattr(g, 'db'):
            g.admin.close()
            g.omw.close()

    ################################################################################
    # VIEWS
    ################################################################################


    @app.route('/omw', methods=['GET', 'POST'])
    def omw_welcome(name=None):
        lang_id, lang_code = fetch_langs()
        src_meta = fetch_src_meta()
        ### sort by language, project version (Newest first)
        src_sort = od()
        keys = list(src_meta.keys())
        keys.sort(key=lambda x: src_meta[x]['version'], reverse=True)
        keys.sort(key=lambda x: src_meta[x]['id'])
        keys.sort(key=lambda x: lang_id[lang_code['code'][src_meta[x]['language']]][1])
        for k in keys:
            src_sort[k] = src_meta[k]
        return render_template('omw_welcome.html',
                               src_meta=src_sort,
                               lang_id=lang_id,
                               lang_code=lang_code,
                               licenses=licenses)

    @app.route('/wordnet', methods=['GET', 'POST'])
    def wordnet_license(name=None):
        return render_template('wordnet_license.html')

    @app.route('/omw_wns', methods=['GET', 'POST'])
    def omw_wns(name=None):
        src_meta = fetch_src_meta()
        stats = []
        lang_id, lang_code = fetch_langs()
        ### sort by language name (1), id, version (FIXME -- reverse version)
        for src_id in sorted(src_meta, key=lambda x: (lang_id[lang_code['code'][src_meta[x]['language']]][1],
                                                      src_meta[x]['id'],
                                                      src_meta[x]['version'])):
            stats.append((src_meta[src_id], fetch_src_id_stats(src_id)))
        return render_template('omw_wns.html',
                               stats=stats,
                               lang_id=lang_id,
                               lang_code=lang_code,
                               licenses=licenses)

    @app.route("/useradmin", methods=["GET"])
    @login_required(role=99, group='admin')
    def useradmin():
        users = fetch_allusers()
        return render_template("useradmin.html", users=users)

    @app.route("/langadmin", methods=["GET"])
    @login_required(role=99, group='admin')
    def langadmin():
        lang_id, lang_code = fetch_langs()
        return render_template("langadmin.html", langs=lang_id)

    @app.route("/projectadmin", methods=["GET"])
    @login_required(role=99, group='admin')
    def projectadmin():
        projs = fetch_proj()
        return render_template("projectadmin.html", projs=projs)

    @app.route('/allconcepts', methods=['GET', 'POST'])
    def allconcepts():
        ili, ili_defs = fetch_ili()
        rsumm, up_who, down_who = f_rate_summary(list(ili.keys()))
        return render_template('concept-list.html', ili=ili,
                               rsumm=rsumm, up_who=up_who, down_who=down_who)

    @app.route('/temporary', methods=['GET', 'POST'])
    def temporary():
        ili = fetch_ili_status(2)
        rsumm, up_who, down_who = f_rate_summary(list(ili.keys()))
        return render_template('concept-list.html', ili=ili,
                               rsumm=rsumm, up_who=up_who, down_who=down_who)

    @app.route('/deprecated', methods=['GET', 'POST'])
    def deprecated():
        ili = fetch_ili_status(0)
        rsumm, up_who, down_who = f_rate_summary(list(ili.keys()))
        return render_template('concept-list.html', ili=ili,
                               rsumm=rsumm, up_who=up_who, down_who=down_who)

    @app.route('/upload', methods=['GET', 'POST'])
    @login_required(role=0, group='open')
    def upload():
        return render_template('upload.html')

    @app.route('/metadata', methods=['GET', 'POST'])
    def metadata():
        return render_template('metadata.html')

    @app.route('/join', methods=['GET', 'POST'])
    def join():
        return render_template('join.html')


    @app.route('/omw/search', methods=['GET', 'POST'])
    @app.route('/omw/search/<lang>,<lang2>/<q>', methods=['GET', 'POST'])
    def search_omw(lang=None, lang2=None, q=None):

        if lang and q:
            lang_id = lang
            lang_id2 = lang2
            query = q
        else:
            lang_id = request.form['lang']
            lang_id2 = request.form['lang2']
            query = request.form['query']
            query = query.strip()

        sense = dd(list)
        lang_sense = dd(lambda: dd(list))

        # GO FROM FORM TO SENSE
        for s in query_omw("""
            SELECT s.id as s_id, ss_id,  wid, fid, lang_id, pos_id, lemma
            FROM (SELECT w_id as wid, form.id as fid, lang_id, pos_id, lemma
                  FROM (SELECT id, lang_id, pos_id, lemma
                        FROM f WHERE lemma GLOB ? AND lang_id in (?,?)) as form
                  JOIN wf_link ON form.id = wf_link.f_id) word
            JOIN s ON wid=w_id
            """, ['[' + query[0].upper() + query[0].lower() + ']' + query[1:],
                  lang_id,
                  lang_id2]):
            sense[s['ss_id']] = [s['s_id'], s['wid'], s['fid'],
                                 s['lang_id'], s['pos_id'], s['lemma']]

            lang_sense[s['lang_id']][s['ss_id']] = [s['s_id'], s['wid'], s['fid'],
                                                    s['pos_id'], s['lemma']]

        pos = fetch_pos()
        lang_dct, lang_code = fetch_langs()
        ss, senses, defs, exes, links = fetch_ss_basic(sense.keys())

        labels = fetch_labels(lang_id, set(senses.keys()))

        resp = make_response(render_template('omw_results.html',
                                             langsel=int(lang_id),
                                             langsel2=int(lang_id2),
                                             pos=pos,
                                             lang_dct=lang_dct,
                                             sense=sense,
                                             senses=senses,
                                             ss=ss,
                                             links=links,
                                             defs=defs,
                                             exes=exes,
                                             labels=labels))

        resp.set_cookie('selected_lang', lang_id)
        resp.set_cookie('selected_lang2', lang_id2)
        return resp

    @app.route('/omw/core', methods=['GET', 'POST'])
    def omw_core():  ### FIXME add lang as a paramater?
        return render_template('omw_core.html')

    @app.route('/omw/concepts/<ssID>', methods=['GET', 'POST'])
    @app.route('/omw/concepts/ili/<iliID>', methods=['GET', 'POST'])
    def concepts_omw(ssID=None, iliID=None):

        if iliID:
            ss_ids = f_ss_id_by_ili_id(iliID)
            ili, ilidefs = fetch_ili([iliID])
        else:
            ss_ids = [ssID]
            ili, ili_defs = dict(), dict()
        pos = fetch_pos()
        langs_id, langs_code = fetch_langs()

        ss, senses, defs, exes, links = fetch_ss_basic(ss_ids)
        if (not iliID) and int(ssID) in ss:
            iliID = ss[int(ssID)][0]
            ili, ilidefs = fetch_ili([iliID])

        sss = list(ss.keys())
        for s in links:
            for l in links[s]:
                sss.extend(links[s][l])
        selected_lang = request.cookies.get('selected_lang')
        labels = fetch_labels(selected_lang, set(sss))

        ssrels = fetch_ssrel()

        ss_srcs = fetch_src_for_ss_id(ss_ids)
        src_meta = fetch_src_meta()
        core_ss, core_ili = fetch_core()
        return render_template('omw_concept.html',
                               ssID=ssID,
                               iliID=iliID,
                               pos=pos,
                               langs=langs_id,
                               senses=senses,
                               ss=ss,
                               links=links,
                               ssrels=ssrels,
                               defs=defs,
                               exes=exes,
                               ili=ili,
                               selected_lang=selected_lang,
                               selected_lang2=request.cookies.get('selected_lang2'),
                               labels=labels,
                               ss_srcs=ss_srcs,
                               src_meta=src_meta,
                               core=core_ss)

    @app.route('/omw/senses/<sID>', methods=['GET', 'POST'])
    def omw_sense(sID=None):
        langs_id, langs_code = fetch_langs()
        pos = fetch_pos()
        sense = fetch_sense(sID)
        forms = fetch_forms(sense[3])
        selected_lang = request.cookies.get('selected_lang')
        labels = fetch_labels(selected_lang, [sense[4]])
        src_meta = fetch_src_meta()
        src_sid = fetch_src_for_s_id([sID])
        return render_template('omw_sense.html',
                               s_id=sID,
                               sense=sense,
                               forms=forms,
                               langs=langs_id,
                               pos=pos,
                               labels=labels,
                               src_sid=src_sid,
                               src_meta=src_meta)

    # URIs FOR ORIGINAL CONCEPT KEYS, BY INDIVIDUAL SOURCES
    @app.route('/omw/src/<src>/<originalkey>', methods=['GET', 'POST'])
    def src_omw(src=None, originalkey=None):

        try:
            proj = src[:src.index('-')]
            ver = src[src.index('-') + 1:]
            src_id = f_src_id_by_proj_ver(proj, ver)
        except:
            src_id = None

        if src_id:
            ss = fetch_ss_id_by_src_orginalkey(src_id, originalkey)
        else:
            ss = None

        return concepts_omw(ss)

    # show wn statistics
    @app.route('/omw/src/<src>', methods=['GET', 'POST'])
    def omw_wn(src=None):
        if src:
            try:
                proj = src[:src.index('-')]
                ver = src[src.index('-') + 1:]
                src_id = f_src_id_by_proj_ver(proj, ver)
            except:
                src_id = None
            srcs_meta = fetch_src_meta()
            src_info = srcs_meta[src_id]

        return render_template('omw_wn.html',
                               wn=src,
                               src_id=src_id,
                               src_info=src_info,
                               ssrel_stats=fetch_ssrel_stats(src_id),
                               pos_stats=fetch_src_id_pos_stats(src_id),
                               src_stats=fetch_src_id_stats(src_id),
                               licenses=licenses)

    @app.route('/omw/src-latex/<src>', methods=['GET', 'POST'])
    def omw_wn_latex(src=None):
        if src:
            try:
                proj = src[:src.index('-')]
                ver = src[src.index('-') + 1:]
                src_id = f_src_id_by_proj_ver(proj, ver)
            except:
                src_id = None
            srcs_meta = fetch_src_meta()
            src_info = srcs_meta[src_id]

        return render_template('omw_wn_latex.html',
                               wn=src,
                               src_id=src_id,
                               src_info=src_info,
                               ssrel_stats=fetch_ssrel_stats(src_id),
                               pos_stats=fetch_src_id_pos_stats(src_id),
                               src_stats=fetch_src_id_stats(src_id))

    @app.route('/cili.tsv')
    def generate_cili_tsv():
        tsv = """# omw_id	ili_id	projects\n"""
        srcs = fetch_src()
        ss = dict()
        r = query_omw_direct("SELECT id, ili_id from ss")
        for (ss_id, ili_id) in r:
            ss[ss_id] = [ili_id]
        src = dd(list)
        r = query_omw_direct("SELECT ss_id, src_id, src_key from ss_src")
        for (ss_id, src_id, src_key) in r:
            src[ss_id].append("{}-{}:{}".format(srcs[src_id][0],
                                                srcs[src_id][1],
                                                src_key))

        for ss_id in ss:
            ili = 'i' + str(ss[ss_id][0]) if ss[ss_id][0] else 'None'

            tsv += "{}\t{}\t{}\n".format(ss_id, ili, ";".join(src[ss_id]))
        return Response(tsv, mimetype='text/tab-separated-values')

    @app.context_processor
    def utility_processor():
        def scale_freq(f, maxfreq=1000):
            if f > 0:
                return 100 + 100 * log(f) / log(maxfreq)
            else:
                return 100

        return dict(scale_freq=scale_freq)
    return app


def extensions(app):
    """
    Register 0 or more extensions (mutates the app passed in).

    :param app: Flask application instance
    :return: None
    """
    csrf.init_app(app)
    login_manager.init_app(app)

    return None


def authentication(app):
    """
    Initialize the Flask-Login extension (mutates the app passed in).

    :param app: Flask application instance
    :param user_model: Model that contains the authentication information
    :type user_model: SQLAlchemy model
    :return: None
    """
    login_manager.login_view = '/login'
    login_manager.login_message = "You don't seem to have permission to see this content."

    @login_manager.user_loader
    def load_user(userID):
        """ This function, given an user_id, needs to check whether this user
        'is active' / 'exists' [FIXME, this should be done against the DB?],
        and returns an User object. I DONT THINK SO ANYMORE!"""

        """
        Flask-Login user_loader callback.
        The user_loader function asks this function to get a User Object or return
        None based on the userid.
        The userid was stored in the session environment by Flask-Login.
        user_loader stores the returned User object in current_user during every
        flask request.
        """
        return User.get(userID)


def error_templates(app):
    """
    Register 0 or more custom error pages (mutates the app passed in).

    :param app: Flask application instance
    :return: None
    """

    def render_status(status):
        """
         Render a custom template for a specific status.
           Source: http://stackoverflow.com/a/30108946

         :param status: Status as a written name
         :type status: str
         :return: None
         """
        # Get the status code from the status, default to a 500 so that we
        # catch all types of errors and treat them as a 500.
        code = getattr(status, 'code', 500)
        return render_template('errors/{0}.html'.format(code)), code

    for error in [404, 429, 500]:
        app.errorhandler(error)(render_status)

    return None
